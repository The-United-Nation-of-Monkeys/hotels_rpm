from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone


class Room(models.Model):
    """Модель номера отеля"""
    room_id = models.BigAutoField(primary_key=True)
    number = models.CharField(max_length=50, unique=True, verbose_name="Номер комнаты")
    name = models.CharField(max_length=200, verbose_name="Название номера")
    description = models.TextField(verbose_name="Описание")
    type_name = models.CharField(max_length=100, verbose_name="Тип комнаты")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Номер"
        verbose_name_plural = "Номера"
        ordering = ['number']

    def __str__(self):
        return f"{self.number} - {self.name}"


class Guest(models.Model):
    """Модель гостя"""
    guest_id = models.BigAutoField(primary_key=True)
    first_name = models.CharField(max_length=100, verbose_name="Имя")
    last_name = models.CharField(max_length=100, verbose_name="Фамилия")
    middle_name = models.CharField(max_length=100, null=True, blank=True, verbose_name="Отчество")
    passport_number = models.CharField(max_length=50, unique=True, verbose_name="Номер паспорта")
    email = models.EmailField(null=True, blank=True, verbose_name="Электронная почта")
    phone = models.CharField(max_length=20, verbose_name="Телефон")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Гость"
        verbose_name_plural = "Гости"
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.last_name} {self.first_name}"

    @property
    def full_name(self):
        """Полное имя гостя"""
        parts = [self.last_name, self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        return " ".join(parts)


class Booking(models.Model):
    """Модель бронирования"""
    booking_id = models.BigAutoField(primary_key=True)
    guest = models.ForeignKey(Guest, on_delete=models.CASCADE, related_name='bookings', verbose_name="Гость")
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='bookings', verbose_name="Номер")
    check_in_date = models.DateField(verbose_name="Дата заезда")
    check_out_date = models.DateField(verbose_name="Дата выезда")
    adults_count = models.IntegerField(validators=[MinValueValidator(1)], verbose_name="Количество взрослых")
    children_count = models.IntegerField(default=0, validators=[MinValueValidator(0)], verbose_name="Количество детей")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Стоимость проживания")
    special_requests = models.TextField(null=True, blank=True, verbose_name="Пожелания")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Бронирование"
        verbose_name_plural = "Бронирования"
        ordering = ['-check_in_date']

    def __str__(self):
        return f"Бронирование #{self.booking_id} - {self.guest} в {self.room}"

    def clean(self):
        """Валидация дат"""
        from django.core.exceptions import ValidationError
        if self.check_in_date and self.check_out_date:
            if self.check_in_date >= self.check_out_date:
                raise ValidationError({
                    'check_out_date': "Дата заезда должна быть раньше даты выезда"
                })
            if self.check_in_date < timezone.now().date():
                raise ValidationError({
                    'check_in_date': "Дата заезда не может быть в прошлом"
                })
