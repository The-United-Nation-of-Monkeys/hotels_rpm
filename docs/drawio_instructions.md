# Инструкция по созданию ER-диаграммы в draw.io

## Способ 1: Использование готовой схемы dbdiagram.io

1. Откройте файл [`database_schema.dbml`](database_schema.dbml) в любом текстовом редакторе
2. Перейдите на https://dbdiagram.io
3. Нажмите "Import" и вставьте содержимое файла
4. Диаграмма будет автоматически сгенерирована
5. Вы можете экспортировать её в PNG/SVG для добавления в README

## Способ 2: Создание в draw.io

### Шаги:

1. Откройте https://app.diagrams.net/ (draw.io)
2. Создайте новую диаграмму
3. Используйте следующие сущности и связи:

### Сущности:

#### User (Пользователь)
- id (PK, Integer)
- username (String)
- email (String)
- first_name (String)
- last_name (String)
- password (String)
- date_joined (DateTime)

#### UserProfile (Профиль пользователя)
- id (PK, Integer)
- user_id (FK → User.id, OneToOne)
- user_type (String: 'user' или 'organization')
- phone (String)
- address (Text)
- organization_name (String)
- created_at (DateTime)
- updated_at (DateTime)

#### Hotel (Отель)
- hotel_id (PK, Integer)
- name (String)
- description (Text)
- address (Text)
- phone (String)
- email (String)
- owner_id (FK → User.id)
- created_at (DateTime)
- updated_at (DateTime)

#### Room (Номер)
- room_id (PK, Integer)
- hotel_id (FK → Hotel.hotel_id)
- number (String)
- name (String)
- description (Text)
- type_name (String)
- price_per_night (Decimal)
- created_at (DateTime)
- updated_at (DateTime)

#### Guest (Гость)
- guest_id (PK, Integer)
- first_name (String)
- last_name (String)
- middle_name (String, nullable)
- passport_number (String, Unique)
- email (String, nullable)
- phone (String)
- created_at (DateTime)
- updated_at (DateTime)

#### Booking (Бронирование)
- booking_id (PK, Integer)
- user_id (FK → User.id, nullable)
- guest_id (FK → Guest.guest_id)
- room_id (FK → Room.room_id)
- check_in_date (Date)
- check_out_date (Date)
- adults_count (Integer)
- children_count (Integer)
- total_price (Decimal)
- special_requests (Text, nullable)
- created_at (DateTime)
- updated_at (DateTime)

### Связи:

1. **User ↔ UserProfile**: One-to-One (1:1)
   - User.id → UserProfile.user_id

2. **User ↔ Hotel**: One-to-Many (1:N)
   - User.id → Hotel.owner_id

3. **User ↔ Booking**: One-to-Many (1:N)
   - User.id → Booking.user_id (nullable)

4. **Hotel ↔ Room**: One-to-Many (1:N)
   - Hotel.hotel_id → Room.hotel_id

5. **Room ↔ Booking**: One-to-Many (1:N)
   - Room.room_id → Booking.room_id

6. **Guest ↔ Booking**: One-to-Many (1:N)
   - Guest.guest_id → Booking.guest_id

### Визуализация в draw.io:

1. Используйте фигуру "Entity" из раздела "Entity Relation"
2. Добавьте все поля в каждую сущность
3. Используйте стрелки для обозначения связей:
   - **One-to-One**: стрелка с "1" на обоих концах
   - **One-to-Many**: стрелка с "1" на одной стороне и "N" на другой
4. Обозначьте Primary Keys (PK) жирным шрифтом
5. Обозначьте Foreign Keys (FK) курсивом
6. Добавьте пометки для уникальных полей (UK)

### Пример расположения:

```
    [User] ──1:1── [UserProfile]
      │
      ├──1:N── [Hotel] ──1:N── [Room] ──1:N── [Booking]
      │                                    ▲
      └──1:N───────────────────────────────┘
                                          │
                                    [Guest] ──1:N──┘
```

### Экспорт:

1. Файл → Экспортировать как → PNG (для README)
2. Или → Экспортировать как → SVG (для лучшего качества)
3. Сохраните файл в папку `docs/` с именем `database_er_diagram.png`

### Добавление в README:

После создания диаграммы, добавьте её в README.md:

```markdown
## 📊 ER-диаграмма базы данных

![ER-диаграмма базы данных](docs/database_er_diagram.png)
```
