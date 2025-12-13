# Архитектурная схема системы

## Общая архитектура

Система бронирования отелей построена на основе Django и следует классической архитектуре MVC (Model-View-Controller).

## Компоненты системы

```
┌─────────────┐
│   Браузер   │
│  (Frontend) │
└──────┬──────┘
       │
       │ HTTP/HTTPS
       │ AJAX (JSON)
       │
       ▼
┌─────────────────────────────────────┐
│      Django Backend (WSGI)          │
│  ┌───────────────────────────────┐  │
│  │   URL Router (urls.py)       │  │
│  └───────────┬──────────────────┘  │
│              │                      │
│  ┌───────────▼──────────────────┐  │
│  │   Views (views.py)            │  │
│  │   - Class-based Views         │  │
│  │   - Function-based Views      │  │
│  │   - AJAX endpoints            │  │
│  └───────────┬──────────────────┘  │
│              │                      │
│  ┌───────────▼──────────────────┐  │
│  │   Forms (forms.py)            │  │
│  │   - Validation                │  │
│  │   - Data processing           │  │
│  └───────────┬──────────────────┘  │
│              │                      │
│  ┌───────────▼──────────────────┐  │
│  │   Models (models.py)         │  │
│  │   - Business logic            │  │
│  │   - Data validation           │  │
│  └───────────┬──────────────────┘  │
└──────────────┼──────────────────────┘
               │
               │ Django ORM
               │
       ┌───────▼────────┐
       │   SQLite DB    │
       │   (Database)   │
       └───────────────┘
```

## Детальная схема взаимодействия

### 1. Просмотр номеров

```
Браузер → Django Views → Models → SQLite
         ← HTML Template ← QuerySet ←
```

### 2. Проверка доступности (AJAX)

```
Браузер → AJAX Request → check_room_availability()
         ← JSON Response ← QuerySet ← SQLite
```

### 3. Создание бронирования

```
Браузер → POST Request → BookingCreateView
                         → Forms Validation
                         → Transaction.atomic()
                         → Models.save()
                         → SQLite (with lock)
         ← Redirect/Success ←
```

### 4. Регистрация пользователя

```
Браузер → POST Request → UserRegistrationView
                         → User.objects.create()
                         → Signal (post_save)
                         → UserProfile.objects.create()
                         → SQLite
         ← Redirect ←
```

## Потоки данных

### Основной поток (HTTP Request)

1. **Браузер** отправляет HTTP запрос
2. **URL Router** определяет соответствующий view
3. **View** обрабатывает запрос:
   - Получает данные из **Models** через ORM
   - Использует **Forms** для валидации
   - Рендерит **Templates**
4. **Database** возвращает данные через ORM
5. **View** возвращает HTML/JSON ответ
6. **Браузер** отображает результат

### AJAX поток

1. **JavaScript** отправляет AJAX запрос
2. **URL Router** направляет на AJAX endpoint
3. **Function-based View** обрабатывает запрос
4. **Models** выполняют запросы к БД
5. **View** возвращает JSON ответ
6. **JavaScript** обновляет DOM

## Технологический стек

| Компонент | Технология | Назначение |
|-----------|------------|------------|
| Frontend | HTML5, CSS3, JavaScript | Пользовательский интерфейс |
| UI Framework | Bootstrap 5 | Стилизация и компоненты |
| Icons | Bootstrap Icons | Иконки |
| Backend | Django 5.2.8 | Веб-фреймворк |
| ORM | Django ORM | Работа с БД |
| Database | SQLite | Хранение данных |
| Templates | Django Templates | Рендеринг HTML |
| Static Files | Django Static Files | CSS, JS, изображения |

## Безопасность

- **CSRF Protection** - Django автоматически защищает от CSRF атак
- **SQL Injection Protection** - Django ORM защищает от SQL инъекций
- **XSS Protection** - Django Templates автоматически экранируют HTML
- **Authentication** - Django Auth система для управления пользователями
- **Authorization** - LoginRequiredMixin для защиты представлений
- **Transaction Safety** - Использование atomic транзакций для предотвращения race conditions

## Масштабируемость

Текущая архитектура поддерживает:
- Легкую замену SQLite на PostgreSQL/MySQL
- Добавление кэширования (Redis/Memcached)
- Разделение на микросервисы (API отдельно от фронтенда)
- Использование Celery для фоновых задач
- CDN для статических файлов
