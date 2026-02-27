from datetime import datetime
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class PaymentNotificationRequest(BaseModel):
    """Тело запроса от Payment Service (camelCase в JSON). bookingId может быть строкой (Django PK)."""
    payment_id: str = Field(alias="paymentId")
    booking_id: str = Field(alias="bookingId")
    status: str  # SUCCESS | FAILED
    amount: Optional[Decimal] = None
    currency: Optional[str] = None
    failure_reason: Optional[str] = Field(None, alias="failureReason")
    occurred_at: Optional[datetime] = Field(None, alias="occurredAt")

    model_config = {"populate_by_name": True}


class NotificationResponse(BaseModel):
    id: UUID
    type: str
    payload: Optional[dict[str, Any]] = None
    created_at: datetime
    processed: bool
    read: bool

    model_config = {"from_attributes": True}


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    total: int
    limit: int
    offset: int


class MarkReadBody(BaseModel):
    read: bool = True
