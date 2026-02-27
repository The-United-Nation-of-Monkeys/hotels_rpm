from datetime import datetime
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# --- Request (соответствует OpenAPI CreatePaymentRequest) ---


class CreatePaymentRequest(BaseModel):
    """bookingId может быть строкой (Django PK) или UUID."""
    booking_id: str = Field(..., alias="bookingId")
    amount: Decimal = Field(..., ge=0)
    currency: str = "RUB"
    description: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None

    model_config = {"populate_by_name": True}


# --- Response (соответствует OpenAPI PaymentResponse) ---


class PaymentResponse(BaseModel):
    id: UUID
    booking_id: str  # совпадает с форматом из CreatePaymentRequest
    status: str  # CREATED | PROCESSING | SUCCESS | FAILED
    amount: Decimal
    currency: str
    created_at: datetime
    updated_at: datetime
    failure_reason: Optional[str] = None

    model_config = {"from_attributes": True}


# --- List (соответствует OpenAPI PaymentListResponse) ---


class PaymentListResponse(BaseModel):
    items: list[PaymentResponse]
    total: int
    limit: int
    offset: int


# --- Error (соответствует OpenAPI Error) ---


class ErrorResponse(BaseModel):
    error: str
    code: Optional[str] = None
