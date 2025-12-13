# API Документация

Система бронирования отелей предоставляет REST API для проверки доступности номеров.

## Базовый URL

```
http://127.0.0.1:8000
```

## Эндпоинты

### 1. Проверка доступности номера

Проверяет доступность номера на указанные даты и рассчитывает стоимость.

**Endpoint:** `GET /rooms/{room_id}/check-availability/`

**Параметры запроса (Query Parameters):**

| Параметр | Тип | Обязательный | Описание |
|----------|-----|---------------|----------|
| `check_in` | string (YYYY-MM-DD) | Да | Дата заезда |
| `check_out` | string (YYYY-MM-DD) | Да | Дата выезда |

**Пример запроса:**

```http
GET /rooms/1/check-availability/?check_in=2025-12-10&check_out=2025-12-15
```

**Успешный ответ (200 OK):**

Если номер доступен:
```json
{
  "available": true,
  "nights": 5,
  "total_price": 25000.00,
  "price_per_night": 5000.00
}
```

Если номер занят:
```json
{
  "available": false,
  "nights": 5,
  "total_price": 25000.00,
  "price_per_night": 5000.00,
  "booking_dates": [
    {
      "check_in": "10.12.2025",
      "check_out": "15.12.2025"
    },
    {
      "check_in": "20.12.2025",
      "check_out": "25.12.2025"
    }
  ]
}
```

**Ошибки:**

**400 Bad Request** - Не указаны даты:
```json
{
  "error": "Не указаны даты"
}
```

**400 Bad Request** - Неверный формат даты:
```json
{
  "error": "Дата выезда должна быть позже даты заезда"
}
```

**400 Bad Request** - Дата в прошлом:
```json
{
  "error": "Дата заезда не может быть в прошлом"
}
```

**404 Not Found** - Номер не найден:
```json
{
  "error": "Номер не найден"
}
```

**500 Internal Server Error** - Ошибка сервера:
```json
{
  "error": "Ошибка при проверке доступности: <описание ошибки>"
}
```

## Формат данных

### Поля ответа

| Поле | Тип | Описание |
|------|-----|----------|
| `available` | boolean | Доступен ли номер на указанные даты |
| `nights` | integer | Количество ночей |
| `total_price` | float | Общая стоимость проживания |
| `price_per_night` | float | Цена за одну ночь |
| `booking_dates` | array | Массив объектов с датами занятости (только если `available: false`) |

### Объект booking_dates

| Поле | Тип | Описание |
|------|-----|----------|
| `check_in` | string | Дата заезда в формате DD.MM.YYYY |
| `check_out` | string | Дата выезда в формате DD.MM.YYYY |

## Примеры использования

### JavaScript (Fetch API)

```javascript
const roomId = 1;
const checkIn = '2025-12-10';
const checkOut = '2025-12-15';

fetch(`/rooms/${roomId}/check-availability/?check_in=${checkIn}&check_out=${checkOut}`, {
  method: 'GET',
  headers: {
    'X-Requested-With': 'XMLHttpRequest',
    'Accept': 'application/json',
  },
  credentials: 'same-origin'
})
  .then(response => response.json())
  .then(data => {
    if (data.available) {
      console.log(`Номер доступен! Стоимость: ${data.total_price} ₽`);
    } else {
      console.log('Номер занят на даты:', data.booking_dates);
    }
  })
  .catch(error => console.error('Ошибка:', error));
```

### cURL

```bash
curl -X GET "http://127.0.0.1:8000/rooms/1/check-availability/?check_in=2025-12-10&check_out=2025-12-15" \
  -H "Accept: application/json" \
  -H "X-Requested-With: XMLHttpRequest"
```

### Python (requests)

```python
import requests

url = "http://127.0.0.1:8000/rooms/1/check-availability/"
params = {
    "check_in": "2025-12-10",
    "check_out": "2025-12-15"
}

response = requests.get(url, params=params, headers={
    "Accept": "application/json",
    "X-Requested-With": "XMLHttpRequest"
})

data = response.json()
if data['available']:
    print(f"Номер доступен! Стоимость: {data['total_price']} ₽")
else:
    print(f"Номер занят на даты: {data['booking_dates']}")
```

## Заметки

- Все даты должны быть в формате `YYYY-MM-DD`
- API не требует аутентификации для проверки доступности
- Валидация дат выполняется на сервере
- Проверка пересечений бронирований использует логику: `check_in_date < check_out AND check_out_date > check_in`
