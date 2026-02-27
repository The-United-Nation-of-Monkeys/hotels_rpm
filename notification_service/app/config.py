from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Конфигурация сервиса уведомлений."""

    app_name: str = "Notification Service"
    debug: bool = False

    database_url: str = "sqlite:///./notification_service.db"
    host: str = "0.0.0.0"
    port: int = 8083

    # URL Booking Service (для вызова confirm-payment / cancel)
    booking_service_url: str = "http://localhost:8000"

    class Config:
        env_prefix = "NOTIFICATION_"
        env_file = ".env"


settings = Settings()
