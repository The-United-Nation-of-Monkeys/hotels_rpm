# API микросервисов (Booking, Payment, Notification)

Минимум **по 4 ручки** на каждый сервис. Спецификации OpenAPI 3.0:  
[Booking](openapi-booking-service.yaml) · [Payment](openapi-payment-service.yaml) · [Notification](openapi-notification-service.yaml)

**Базовые URL:** Booking (Django) `http://localhost:8000` · Payment `http://localhost:8082` · Notification `http://localhost:8083`

**Реализации:** Booking — Django-приложение (корень проекта); Payment — [payment_service/](../payment_service/); Notification — [notification_service/](../notification_service/).

---

## 1. Booking Service (Django, порт 8000)

| Метод | Путь | Описание |
|-------|------|----------|
| **GET** | `/api/bookings` | Список бронирований (query: `limit`, `offset`, `status`) |
| **POST** | `/api/bookings` | Создание бронирования → статус PAYMENT_PENDING, вызов Payment Service |
| **GET** | `/api/bookings/{id}` | Получить бронирование по ID |
| **POST** | `/api/bookings/{id}/confirm-payment` | Подтверждение оплаты (вызывает Notification Service) → статус PAID |
| **POST** | `/api/bookings/{id}/cancel` | Отмена бронирования |

**Статусы бронирования:** `CREATED` → `PAYMENT_PENDING` → `PAID` | `CANCELLED` | `PAYMENT_FAILED`

**Цена бронирования:** поле `totalPrice` в ответах вычисляется при создании как **(check_out − check_in) × room.price_per_night** (число ночей × цена за ночь).

---

## 2. Payment Service (порт 8082)

| Метод | Путь | Описание |
|-------|------|----------|
| **GET** | `/api/payments` | Список платежей (query: `limit`, `offset`, `status`, `bookingId`) |
| **POST** | `/api/payments` | Создание платежа (вызывает Booking Service); CREATED → PROCESSING → SUCCESS/FAILED |
| **GET** | `/api/payments/by-booking/{bookingId}` | Платежи по бронированию |
| **GET** | `/api/payments/{id}` | Получить платёж по ID |

**Статусы платежа:** `CREATED` → `PROCESSING` → `SUCCESS` | `FAILED`

---

## 3. Notification Service (порт 8083)

| Метод | Путь | Описание |
|-------|------|----------|
| **GET** | `/api/notifications` | Список уведомлений (query: `limit`, `offset`, `type`) |
| **POST** | `/api/notifications/payment` | Приём события об оплате от Payment Service → вызов Booking confirm/cancel |
| **GET** | `/api/notifications/{id}` | Получить уведомление по ID |
| **PATCH** | `/api/notifications/{id}/read` | Отметить уведомление как прочитанное |

---

## Поток выполнения

1. Клиент → **Booking Service**: `POST /api/bookings`
2. Booking → **Payment Service**: `POST /api/payments`
3. Payment → **Notification Service**: `POST /api/notifications/payment`
4. Notification → **Booking Service**: `POST /api/bookings/{id}/confirm-payment` или отмена

---

## Запуск и связка

**Порядок запуска:** 1) Booking (Django), 2) Payment Service, 3) Notification Service.

**Переменные окружения для связки:**

| Сервис | Переменная | Значение по умолчанию | Описание |
|--------|------------|------------------------|----------|
| Django (Booking) | `PAYMENT_SERVICE_URL` | `http://localhost:8082` | URL Payment Service для создания платежа при бронировании |
| Payment Service | `PAYMENT_NOTIFICATION_SERVICE_URL` | `http://localhost:8083` | URL Notification Service для отправки события об оплате |
| Notification Service | `NOTIFICATION_BOOKING_SERVICE_URL` | `http://localhost:8000` | URL Django (Booking) для confirm-payment и cancel |

**Пример запуска (три терминала):**

```bash
# 1. Booking (Django)
export PAYMENT_SERVICE_URL=http://localhost:8082
python manage.py migrate
python manage.py runserver 8000

# 2. Payment Service
cd payment_service && pip install -r requirements.txt
export PAYMENT_NOTIFICATION_SERVICE_URL=http://localhost:8083
uvicorn app.main:app --host 0.0.0.0 --port 8082

# 3. Notification Service
cd notification_service && pip install -r requirements.txt
export NOTIFICATION_BOOKING_SERVICE_URL=http://localhost:8000
uvicorn app.main:app --host 0.0.0.0 --port 8083
```

Итоговый готовый вариант: после запуска всех трёх сервисов с указанными URL цепочка (клиент → Booking → Payment → Notification → Booking) работает без дополнительной настройки.

**Docker Compose:** в корне проекта есть `docker-compose.yml`. Запуск одной командой: `docker-compose up --build`. Сервисы видят друг друга по именам контейнеров (booking, payment, notification).
