import io
import json
import logging
import uuid
from pathlib import Path

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal, get_db
from app.models import Payment, PaymentStatus
from app.schemas import CreatePaymentRequest, PaymentListResponse, PaymentResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["payments"])


def _payment_to_response(p: Payment) -> PaymentResponse:
    return PaymentResponse(
        id=uuid.UUID(p.id),
        booking_id=p.booking_id,
        status=p.status,
        amount=p.amount,
        currency=p.currency,
        created_at=p.created_at,
        updated_at=p.updated_at,
        failure_reason=p.failure_reason,
    )


# Шрифт с кириллицей для чека (регистрируется при первой генерации)
_RECEIPT_FONT_REGISTERED = False


def _register_receipt_font() -> str:
    """Регистрирует шрифт с поддержкой кириллицы. Возвращает имя шрифта для использования."""
    global _RECEIPT_FONT_REGISTERED
    if _RECEIPT_FONT_REGISTERED:
        return "DejaVu"
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
    ):
        if Path(path).is_file():
            try:
                pdfmetrics.registerFont(TTFont("DejaVu", path))
                _RECEIPT_FONT_REGISTERED = True
                return "DejaVu"
            except Exception as e:
                logger.warning("Could not register font %s: %s", path, e)
    return "Helvetica"  # кириллица не отобразится, но чек соберётся


def _build_receipt_pdf(payment: Payment) -> bytes:
    """Формирует чек по платежу в формате PDF (оформление как кассовый чек)."""
    buffer = io.BytesIO()
    font_name = _register_receipt_font()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
    )
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="ReceiptTitle",
            fontName=font_name,
            fontSize=14,
            alignment=1,  # center
            spaceAfter=2 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            name="ReceiptOrg",
            fontName=font_name,
            fontSize=10,
            alignment=1,
            spaceAfter=1 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            name="ReceiptRow",
            fontName=font_name,
            fontSize=10,
            spaceAfter=1 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            name="ReceiptFooter",
            fontName=font_name,
            fontSize=9,
            alignment=1,
            textColor=colors.grey,
        )
    )

    created_str = payment.created_at.strftime("%d.%m.%Y %H:%M") if payment.created_at else "—"
    amount_str = f"{payment.amount:.2f} {payment.currency}"

    # Блок организации
    story = [
        Paragraph(settings.receipt_company_name, styles["ReceiptOrg"]),
        Paragraph(f"ИНН {settings.receipt_inn}", styles["ReceiptOrg"]),
        Spacer(1, 4 * mm),
        Paragraph("—" * 32, styles["ReceiptOrg"]),
        Spacer(1, 4 * mm),
        Paragraph("КАССОВЫЙ ЧЕК / ОПЛАТА", styles["ReceiptTitle"]),
        Spacer(1, 4 * mm),
    ]

    # Таблица полей чека
    data = [
        ["ID платежа:", payment.id],
        ["Номер брони:", payment.booking_id],
        ["Сумма:", amount_str],
        ["Статус:", payment.status],
        ["Дата и время:", created_str],
    ]
    if payment.description:
        data.append(["Назначение:", payment.description])

    t = Table(data, colWidths=[45 * mm, 100 * mm])
    t.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), font_name),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("LINEBELOW", (0, -1), (-1, -1), 0.5, colors.lightgrey),
            ]
        )
    )
    story.append(t)
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph("Спасибо за оплату!", styles["ReceiptFooter"]))
    story.append(Paragraph(f"Чек № {payment.id[:8]}", styles["ReceiptFooter"]))

    doc.build(story)
    return buffer.getvalue()


def _save_receipt_background(payment_id: str) -> None:
    """Фоновая задача: собрать PDF чека и сохранить в папку receipts."""
    receipts_dir = Path(settings.receipts_dir)
    receipts_dir.mkdir(parents=True, exist_ok=True)
    file_path = receipts_dir / f"{payment_id}.pdf"
    db = SessionLocal()
    try:
        payment = db.query(Payment).filter(Payment.id == payment_id).first()
        if not payment:
            logger.warning("Receipt background: payment %s not found", payment_id)
            return
        pdf_bytes = _build_receipt_pdf(payment)
        file_path.write_bytes(pdf_bytes)
        logger.info("Receipt saved: %s", file_path)
    except Exception as e:
        logger.exception("Failed to save receipt for payment %s: %s", payment_id, e)
    finally:
        db.close()


def _process_payment_sync(payment: Payment) -> None:

    payment.status = PaymentStatus.PROCESSING.value
    payment.status = PaymentStatus.SUCCESS.value


async def _notify_payment_result(payment: Payment) -> None:
    """Отправить событие об оплате в Notification Service."""
    base = getattr(settings, "notification_service_url", "http://localhost:8083").rstrip("/")
    url = f"{base}/api/notifications/payment"
    payload = {
        "paymentId": payment.id,
        "bookingId": payment.booking_id,
        "status": payment.status,
        "amount": float(payment.amount),
        "currency": payment.currency,
    }
    if payment.status == PaymentStatus.FAILED.value and payment.failure_reason:
        payload["failureReason"] = payment.failure_reason
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(url, json=payload)
            if r.status_code not in (200, 201):
                logger.warning("Notification service returned %s: %s", r.status_code, r.text)
    except httpx.RequestError as e:
        logger.exception("Notification service unreachable: %s", e)



async def create_and_process_payment(
    *,
    booking_id: int,
    amount,
    currency: str,
    description: str | None,
    metadata_str: str | None,
    db: Session,
) -> Payment:
    """Создаёт платёж, обрабатывает его и уведомляет Notification Service.

    Используется как из REST-обработчика, так и из Kafka consumer.
    Не выполняет фоновые задачи (чек PDF) — вызывающая сторона отвечает за это сама.
    """
    payment = Payment(
        id=str(uuid.uuid4()),
        booking_id=booking_id,
        status=PaymentStatus.CREATED.value,
        amount=amount,
        currency=currency,
        description=description,
        metadata_=metadata_str,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    _process_payment_sync(payment)
    db.commit()
    db.refresh(payment)

    await _notify_payment_result(payment)
    return payment


@router.post("/payments", response_model=PaymentResponse, status_code=201)
async def create_payment(
    request: CreatePaymentRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Создание платежа. Вызывается Booking Service напрямую (REST).
    Статус: CREATED → PROCESSING → SUCCESS или FAILED.
    Чек PDF строится в фоне и сохраняется в папку receipts.
    """
    metadata_str = json.dumps(request.metadata) if request.metadata is not None else None

    payment = await create_and_process_payment(
        booking_id=request.booking_id,
        amount=request.amount,
        currency=request.currency,
        description=request.description,
        metadata_str=metadata_str,
        db=db,
    )

    background_tasks.add_task(_save_receipt_background, payment.id)

    return _payment_to_response(payment)


@router.get("/payments", response_model=PaymentListResponse)
async def list_payments(
    limit: int = 20,
    offset: int = 0,
    status: str | None = None,
    booking_id: str | None = None,
    db: Session = Depends(get_db),
):
    """Список платежей с пагинацией и фильтрами."""
    q = db.query(Payment)
    if status is not None:
        q = q.filter(Payment.status == status)
    if booking_id is not None:
        q = q.filter(Payment.booking_id == booking_id)
    total = q.count()
    items = q.order_by(Payment.created_at.desc()).offset(offset).limit(limit).all()
    return PaymentListResponse(
        items=[_payment_to_response(p) for p in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/payments/by-booking/{booking_id}", response_model=list[PaymentResponse])
async def get_payments_by_booking(booking_id: str, db: Session = Depends(get_db)):
    """Платежи по бронированию."""
    items = (
        db.query(Payment)
        .filter(Payment.booking_id == booking_id)
        .order_by(Payment.created_at.desc())
        .all()
    )
    return [_payment_to_response(p) for p in items]


@router.get("/payments/{payment_id}/receipt", response_class=FileResponse)
async def get_payment_receipt_pdf(payment_id: uuid.UUID):
    """Скачать готовый чек по платежу (PDF из папки receipts)."""
    file_path = Path(settings.receipts_dir) / f"{payment_id}.pdf"
    if not file_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Чек ещё не готов или платёж не найден. Подождите несколько секунд после создания платежа.",
        )
    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=f"receipt_{payment_id}.pdf",
    )


@router.get("/payments/{payment_id}", response_model=PaymentResponse)
async def get_payment(payment_id: uuid.UUID, db: Session = Depends(get_db)):
    """Получить статус платежа по ID."""
    payment = db.query(Payment).filter(Payment.id == str(payment_id)).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Платёж не найден")
    return _payment_to_response(payment)
