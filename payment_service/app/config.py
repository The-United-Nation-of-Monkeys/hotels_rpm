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

    class Config:
        env_prefix = "PAYMENT_"
        env_file = ".env"


settings = Settings()
