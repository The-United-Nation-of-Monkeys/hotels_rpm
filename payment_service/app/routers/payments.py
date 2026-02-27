import json
import logging
import uuid

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
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


def _process_payment_sync(payment: Payment) -> None:
    """
    Синхронная имитация обработки оплаты.
    В реальности здесь вызов платёжного шлюза; затем событие в Notification Service.
    """
    payment.status = PaymentStatus.PROCESSING.value
    # Имитация: например, всегда успех; можно заменить на случай или внешний вызов
    payment.status = PaymentStatus.SUCCESS.value
    # При неудаче: payment.status = PaymentStatus.FAILED.value; payment.failure_reason = "..."


def _notify_payment_result(payment: Payment) -> None:
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
        with httpx.Client(timeout=10.0) as client:
            r = client.post(url, json=payload)
            if r.status_code not in (200, 201):
                logger.warning("Notification service returned %s: %s", r.status_code, r.text)
    except httpx.RequestError as e:
        logger.exception("Notification service unreachable: %s", e)



@router.post("/payments", response_model=PaymentResponse, status_code=201)
def create_payment(request: CreatePaymentRequest, db: Session = Depends(get_db)):
    """
    Создание платежа. Вызывается Booking Service.
    Статус: CREATED → PROCESSING → SUCCESS или FAILED.
    """
    metadata_str = None
    if request.metadata is not None:
        metadata_str = json.dumps(request.metadata)

    payment = Payment(
        id=str(uuid.uuid4()),
        booking_id=request.booking_id,
        status=PaymentStatus.CREATED.value,
        amount=request.amount,
        currency=request.currency,
        description=request.description,
        metadata_=metadata_str,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    # Имитация обработки оплаты в том же запросе
    _process_payment_sync(payment)
    db.commit()
    db.refresh(payment)

    # Уведомить Notification Service (не падать при ошибке сети)
    _notify_payment_result(payment)

    return _payment_to_response(payment)


@router.get("/payments", response_model=PaymentListResponse)
def list_payments(
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
def get_payments_by_booking(booking_id: str, db: Session = Depends(get_db)):
    """Платежи по бронированию."""
    items = (
        db.query(Payment)
        .filter(Payment.booking_id == booking_id)
        .order_by(Payment.created_at.desc())
        .all()
    )
    return [_payment_to_response(p) for p in items]


@router.get("/payments/{payment_id}", response_model=PaymentResponse)
def get_payment(payment_id: uuid.UUID, db: Session = Depends(get_db)):
    """Получить статус платежа по ID."""
    payment = db.query(Payment).filter(Payment.id == str(payment_id)).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Платёж не найден")
    return _payment_to_response(payment)
