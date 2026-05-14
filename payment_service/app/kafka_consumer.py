"""Kafka consumer: читает события создания бронирований и создаёт платежи."""
import asyncio
import json
import logging
from decimal import Decimal

from aiokafka import AIOKafkaConsumer
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.models import Payment
from app.routers.payments import (
    _save_receipt_background,
    create_and_process_payment,
)

logger = logging.getLogger(__name__)

# Интервал между попытками подключения к Kafka при старте (секунды)
_RETRY_INTERVAL = 5


async def _handle_payment_event(data: dict) -> None:
    """Обрабатывает одно сообщение из топика payments.

    Ожидаемый формат от Booking Service:
        {"booking_id": <int>, "amount": <float>, "guest_id": <str>}
    Поле currency опционально; по умолчанию "RUB".
    """
    booking_id = data.get("booking_id")
    amount = data.get("amount")
    if booking_id is None or amount is None:
        logger.warning("Skipping malformed payment event (missing booking_id or amount): %s", data)
        return

    try:
        booking_id = int(booking_id)
    except (TypeError, ValueError):
        logger.warning("Skipping event with non-integer booking_id: %s", booking_id)
        return

    currency = data.get("currency", "RUB")
    description = f"Оплата бронирования #{booking_id}"

    db: Session = SessionLocal()
    try:
        # Идемпотентность: если платёж уже существует — пропускаем
        existing = db.query(Payment).filter(Payment.booking_id == booking_id).first()
        if existing:
            logger.info(
                "Payment for booking %s already exists (id=%s), skipping duplicate event",
                booking_id,
                existing.id,
            )
            return

        payment = await create_and_process_payment(
            booking_id=booking_id,
            amount=Decimal(str(amount)),
            currency=currency,
            description=description,
            metadata_str=None,
            db=db,
        )
        logger.info(
            "Payment %s created for booking %s via Kafka (status=%s)",
            payment.id,
            booking_id,
            payment.status,
        )

        # Генерация PDF-чека в фоне, не блокируя consumer
        asyncio.create_task(asyncio.to_thread(_save_receipt_background, payment.id))

    except Exception:
        logger.exception("Failed to process payment event for booking %s", booking_id)
    finally:
        db.close()


async def run_kafka_consumer() -> None:
    """Запускает бесконечный цикл чтения событий оплаты из Kafka.

    При недоступности Kafka повторяет попытку подключения каждые _RETRY_INTERVAL секунд.
    Корректно завершается при отмене asyncio-задачи (shutdown FastAPI).
    """
    if not settings.kafka_consumer_enabled:
        logger.info("Kafka consumer disabled (PAYMENT_KAFKA_CONSUMER_ENABLED=false)")
        return

    logger.info(
        "Starting Kafka consumer: topic=%s, group=%s, brokers=%s",
        settings.kafka_payment_topic,
        settings.kafka_consumer_group,
        settings.kafka_bootstrap_servers,
    )

    consumer = AIOKafkaConsumer(
        settings.kafka_payment_topic,
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id=settings.kafka_consumer_group,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        auto_offset_reset="earliest",
        enable_auto_commit=True,
    )

    # Retry-loop: ждём, пока Kafka не будет готова
    while True:
        try:
            await consumer.start()
            logger.info("Kafka consumer connected and listening")
            break
        except asyncio.CancelledError:
            return
        except Exception as exc:
            logger.warning("Kafka not available yet, retrying in %ds: %s", _RETRY_INTERVAL, exc)
            await asyncio.sleep(_RETRY_INTERVAL)

    try:
        async for msg in consumer:
            logger.debug("Kafka message received: partition=%s offset=%s", msg.partition, msg.offset)
            await _handle_payment_event(msg.value)
    except asyncio.CancelledError:
        logger.info("Kafka consumer received cancellation signal")
    except Exception:
        logger.exception("Unexpected error in Kafka consumer loop")
    finally:
        await consumer.stop()
        logger.info("Kafka consumer stopped")
