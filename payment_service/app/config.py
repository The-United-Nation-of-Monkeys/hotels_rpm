from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Конфигурация сервиса оплаты."""

    app_name: str = "Payment Service"
    debug: bool = False

    # База данных (SQLite по умолчанию)
    database_url: str = "sqlite:///./payment_service.db"

    # Порт сервера (по OpenAPI — 8082)
    host: str = "0.0.0.0"
    port: int = 8082

    # URL Notification Service (вызов после SUCCESS/FAILED)
    notification_service_url: str = "http://localhost:8083"

    # Папка для сохранения чеков (PDF); в Docker — монтируется volume
    receipts_dir: str = "./receipts"

    # Реквизиты организации для чека
    receipt_company_name: str = "ООО «Гостиница»"
    receipt_inn: str = "7707123456"
    receipt_address: str = "г. Москва, ул. Примерная, д. 1"

    # Kafka consumer
    kafka_bootstrap_servers: str = "kafka:9092"
    kafka_payment_topic: str = "payments"
    kafka_consumer_group: str = "payment-service"
    kafka_consumer_enabled: bool = True

    class Config:
        env_prefix = "PAYMENT_"
        env_file = ".env"


settings = Settings()
