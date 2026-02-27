#!/usr/bin/env bash
# Проверка всех трёх сервисов (Booking, Payment, Notification).
# Запуск: из корня проекта, при поднятом docker-compose:
#   ./scripts/test_services.sh
# Либо указать базовые URL:
#   BOOKING_URL=http://localhost:8000 PAYMENT_URL=http://localhost:8082 NOTIFICATION_URL=http://localhost:8083 ./scripts/test_services.sh
#
# Перед первым запуском создайте тестовые данные в контейнере booking:
#   docker compose exec booking python manage.py seed_test_data

set -e

BOOKING_URL="${BOOKING_URL:-http://localhost:8000}"
PAYMENT_URL="${PAYMENT_URL:-http://localhost:8082}"
NOTIFICATION_URL="${NOTIFICATION_URL:-http://localhost:8083}"

# ID номера и гостя (после seed_test_data обычно 1 и 1)
ROOM_ID="${ROOM_ID:-1}"
GUEST_ID="${GUEST_ID:-1}"

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

ok() { echo -e "${GREEN}OK${NC} $*"; }
fail() { echo -e "${RED}FAIL${NC} $*"; exit 1; }

echo "=== 1. Health-check сервисов ==="
curl -sf "${PAYMENT_URL}/health" > /dev/null && ok "Payment (${PAYMENT_URL})" || fail "Payment (${PAYMENT_URL})"
curl -sf "${NOTIFICATION_URL}/health" > /dev/null && ok "Notification (${NOTIFICATION_URL})" || fail "Notification (${NOTIFICATION_URL})"
# Booking (Django) не имеет /health — проверяем главную
curl -sf -o /dev/null "${BOOKING_URL}/" && ok "Booking (${BOOKING_URL})" || fail "Booking (${BOOKING_URL})"

echo ""
echo "=== 2. GET /api/bookings ==="
LIST=$(curl -sf "${BOOKING_URL}/api/bookings/?limit=2")
echo "$LIST" | python3 -m json.tool 2>/dev/null || echo "$LIST"

echo ""
echo "=== 3. POST /api/bookings (создание бронирования) ==="
if date -v+1d +%Y-%m-%d >/dev/null 2>&1; then
  CHECK_IN=$(date -v+1d +%Y-%m-%d)
  CHECK_OUT=$(date -v+3d +%Y-%m-%d)
else
  CHECK_IN=$(date -d "+1 day" +%Y-%m-%d)
  CHECK_OUT=$(date -d "+3 days" +%Y-%m-%d)
fi
BODY="{\"roomId\": ${ROOM_ID}, \"guestId\": ${GUEST_ID}, \"checkInDate\": \"${CHECK_IN}\", \"checkOutDate\": \"${CHECK_OUT}\", \"adultsCount\": 2}"
CREATE=$(curl -s -w "\n%{http_code}" -X POST "${BOOKING_URL}/api/bookings/" -H "Content-Type: application/json" -d "$BODY")
HTTP_CODE=$(echo "$CREATE" | tail -n1)
CREATE_BODY=$(echo "$CREATE" | sed '$d')
echo "$CREATE_BODY" | python3 -m json.tool 2>/dev/null || echo "$CREATE_BODY"
BOOKING_ID=$(echo "$CREATE_BODY" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('id',''))" 2>/dev/null)
if [ -n "$BOOKING_ID" ] && [ "$HTTP_CODE" = "201" ]; then
  ok "Бронирование создано (id=$BOOKING_ID)"
else
  echo "Код ответа: $HTTP_CODE. Если 404 — выполните: docker compose exec booking python manage.py seed_test_data"
fi

if [ -n "$BOOKING_ID" ]; then
  echo ""
  echo "=== 4. GET /api/bookings/${BOOKING_ID} ==="
  curl -sf "${BOOKING_URL}/api/bookings/${BOOKING_ID}/" | python3 -m json.tool
fi

echo ""
echo "=== 5. GET /api/payments ==="
curl -sf "${PAYMENT_URL}/api/payments?limit=3" | python3 -m json.tool 2>/dev/null || curl -sf "${PAYMENT_URL}/api/payments?limit=3"

echo ""
echo "=== 6. GET /api/notifications ==="
curl -sf "${NOTIFICATION_URL}/api/notifications?limit=3" | python3 -m json.tool 2>/dev/null || curl -sf "${NOTIFICATION_URL}/api/notifications?limit=3"

echo ""
echo -e "${GREEN}Проверка завершена.${NC}"
