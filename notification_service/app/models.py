import uuid
from sqlalchemy import Column, String, DateTime, Text, Boolean
from sqlalchemy.sql import func

from app.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    type = Column(String(20), nullable=False, index=True)  # PAYMENT, BOOKING
    payload = Column(Text, nullable=True)  # JSON
    processed = Column(Boolean, default=False, nullable=False)
    read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
