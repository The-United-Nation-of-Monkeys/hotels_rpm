"""
Создаёт минимальные тестовые данные: один номер (Room) и один гостя (Guest).
Запуск: python manage.py seed_test_data
"""
from django.core.management.base import BaseCommand
from booking.models import Room, Guest


class Command(BaseCommand):
    help = "Создаёт тестовые Room и Guest для проверки API бронирований"

    def handle(self, *args, **options):
        guest, created = Guest.objects.get_or_create(
            passport_number="TEST-PASSPORT-001",
            defaults={
                "first_name": "Иван",
                "last_name": "Тестов",
                "phone": "+79001234567",
                "email": "test@example.com",
            },
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"Создан гость id={guest.guest_id}"))
        else:
            self.stdout.write(f"Гость уже есть id={guest.guest_id}")

        room, created = Room.objects.get_or_create(
            number="101",
            defaults={
                "name": "Тестовый номер",
                "description": "Номер для тестов API",
                "type_name": "Стандарт",
                "price_per_night": 5000,
            },
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"Создан номер id={room.room_id}"))
        else:
            self.stdout.write(f"Номер уже есть id={room.room_id}")

        self.stdout.write(
            self.style.SUCCESS(
                f"\nДля теста API используйте: roomId={room.room_id}, guestId={guest.guest_id}"
            )
        )
