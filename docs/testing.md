# Как протестировать сервисы

## 1. Запуск через Docker Compose

```bash
# Из корня проекта (если образы уже собраны — без --build)
docker compose up --no-build

# Или с пересборкой (нужен доступ в интернет для python:3.12-slim)
docker compose up --build
```

Сервисы:
- **Booking (Django):** http://localhost:8000
- **Payment:** http://localhost:8082
- **Notification:** http://localhost:8083

## 2. Тестовые данные (Room и Guest)

Перед первым тестом API бронирований создайте номер и гостя:

```bash
docker compose exec booking python manage.py seed_test_data
```

В выводе будут указаны `roomId` и `guestId` (обычно 1 и 1).

## 3. Автоматическая проверка (скрипт)

Из корня проекта:

```bash
chmod +x scripts/test_services.sh
./scripts/test_services.sh
```

Скрипт:
1. Проверяет доступность Payment и Notification (health), Booking (главная страница).
2. Запрашивает список бронирований `GET /api/bookings`.
3. Создаёт бронирование `POST /api/bookings` (даты завтра — послезавтра).
4. Запрашивает созданное бронирование по ID.
5. Запрашивает список платежей и уведомлений.

При необходимости можно задать URL и ID:

```bash
BOOKING_URL=http://localhost:8000 PAYMENT_URL=http://localhost:8082 NOTIFICATION_URL=http://localhost:8083 \
ROOM_ID=1 GUEST_ID=1 \
./scripts/test_services.sh
```

## 4. Ручная проверка (curl)

**Health:**
```bash
curl http://localhost:8082/health
curl http://localhost:8083/health
```

**Создание бронирования** (подставьте свои `roomId` и `guestId` после `seed_test_data`):
```bash
curl -X POST http://localhost:8000/api/bookings/ \
  -H "Content-Type: application/json" \
  -d '{"roomId":1,"guestId":1,"checkInDate":"2026-03-01","checkOutDate":"2026-03-03","adultsCount":2}'
```

**Список бронирований:**
```bash
curl http://localhost:8000/api/bookings/
```

**Платежи и уведомления:**
```bash
curl http://localhost:8082/api/payments?limit=5
curl http://localhost:8083/api/notifications?limit=5
```

## 5. Полный поток (цепочка сервисов)

1. `POST /api/bookings` на Booking → создаётся бронирование в статусе PAYMENT_PENDING, Booking вызывает Payment.
2. Payment создаёт платёж и дергает Notification.
3. Notification дергает Booking (`confirm-payment` или `cancel`).

Для проверки цепочки достаточно создать бронирование (шаг 3 или 4); в логах контейнеров будут вызовы между сервисами. Просмотр логов:

```bash
docker compose logs -f booking payment notification
```
