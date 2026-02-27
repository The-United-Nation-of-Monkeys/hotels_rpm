# Payment Service

Сервис оплаты (микросервис). REST API соответствует спецификации [docs/openapi-payment-service.yaml](../docs/openapi-payment-service.yaml).

## Стек

- **FastAPI** — веб-фреймворк
- **SQLAlchemy** — ORM, работа с БД
- **SQLite** — БД по умолчанию (можно заменить на PostgreSQL через `PAYMENT_DATABASE_URL`)

## Установка и запуск

```bash
cd payment_service
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8082 --reload
```

- API: http://localhost:8082
- Документация: http://localhost:8082/docs
- Health: http://localhost:8082/health

## Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `PAYMENT_DATABASE_URL` | URL БД | `sqlite:///./payment_service.db` |
| `PAYMENT_DEBUG` | Логирование SQL | `false` |

## Эндпоинты (4 ручки)

- `GET /api/payments` — список платежей (limit, offset, status, bookingId)
- `POST /api/payments` — создание платежа (bookingId, amount, currency)
- `GET /api/payments/by-booking/{bookingId}` — платежи по бронированию
- `GET /api/payments/{id}` — получение статуса платежа по ID

Статусы платежа: `CREATED` → `PROCESSING` → `SUCCESS` / `FAILED`.
