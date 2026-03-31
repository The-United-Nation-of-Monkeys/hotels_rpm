import uuid
from enum import Enum
from sqlalchemy import Column, String, Numeric, DateTime, Text, Integer
from sqlalchemy.sql import func

from app.database import Base


class PaymentStatus(str, Enum):
    CREATED = "CREATED"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class Payment(Base):
    """Модель платежа в БД."""

    __tablename__ = "payments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    # booking_id теперь числовой идентификатор (PK из Booking Service)
    booking_id = Column(Integer, nullable=False, index=True)
    status = Column(String(20), nullable=False, default=PaymentStatus.CREATED.value)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(10), nullable=False, default="RUB")
    description = Column(Text, nullable=True)
    metadata_ = Column("metadata", Text, nullable=True)  # JSON string для SQLite
    failure_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
