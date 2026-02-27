import json
import logging
import uuid

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Notification
from app.schemas import (
    MarkReadBody,
    NotificationListResponse,
    NotificationResponse,
    PaymentNotificationRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["notifications"])


def _notification_to_response(n: Notification) -> NotificationResponse:
    payload = json.loads(n.payload) if n.payload else None
    return NotificationResponse(
        id=uuid.UUID(n.id),
        type=n.type,
        payload=payload,
        created_at=n.created_at,
        processed=n.processed,
        read=n.read,
    )


def _call_booking_confirm(booking_id: str) -> None:
    base = settings.booking_service_url.rstrip("/")
    url = f"{base}/api/bookings/{booking_id}/confirm-payment/"
    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.post(url)
            if r.status_code != 200:
                logger.warning("Booking confirm-payment returned %s: %s", r.status_code, r.text)
    except httpx.RequestError as e:
        logger.exception("Booking service unreachable (confirm): %s", e)


def _call_booking_cancel(booking_id: str) -> None:
    base = settings.booking_service_url.rstrip("/")
    url = f"{base}/api/bookings/{booking_id}/cancel/"
    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.post(url)
            if r.status_code != 200:
                logger.warning("Booking cancel returned %s: %s", r.status_code, r.text)
    except httpx.RequestError as e:
        logger.exception("Booking service unreachable (cancel): %s", e)


@router.post("/notifications/payment")
def handle_payment_notification(
    request: PaymentNotificationRequest,
    db: Session = Depends(get_db),
):
    """Принять событие об оплате от Payment Service; вызвать Booking confirm или cancel."""
    payload = request.model_dump(mode="json")
    payload_str = json.dumps(payload, default=str)
    notification = Notification(
        id=str(uuid.uuid4()),
        type="PAYMENT",
        payload=payload_str,
        processed=True,
    )
    db.add(notification)
    db.commit()

    if request.status == "SUCCESS":
        _call_booking_confirm(request.booking_id)
    elif request.status == "FAILED":
        _call_booking_cancel(request.booking_id)

    return {"ok": True}


@router.get("/notifications", response_model=NotificationListResponse)
def get_all_notifications(
    limit: int = 20,
    offset: int = 0,
    type: str | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(Notification)
    if type:
        q = q.filter(Notification.type == type)
    total = q.count()
    items = q.order_by(Notification.created_at.desc()).offset(offset).limit(limit).all()
    return NotificationListResponse(
        items=[_notification_to_response(n) for n in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/notifications/{notification_id}", response_model=NotificationResponse)
def get_notification(notification_id: uuid.UUID, db: Session = Depends(get_db)):
    n = db.query(Notification).filter(Notification.id == str(notification_id)).first()
    if not n:
        raise HTTPException(status_code=404, detail="Уведомление не найдено")
    return _notification_to_response(n)


@router.patch("/notifications/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_read(
    notification_id: uuid.UUID,
    body: MarkReadBody | None = None,
    db: Session = Depends(get_db),
):
    n = db.query(Notification).filter(Notification.id == str(notification_id)).first()
    if not n:
        raise HTTPException(status_code=404, detail="Уведомление не найдено")
    n.read = body.read if body else True
    db.commit()
    db.refresh(n)
    return _notification_to_response(n)
