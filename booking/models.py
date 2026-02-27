from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    """Профиль пользователя"""
    USER_TYPE_CHOICES = [
        ('user', 'Пользователь'),
        ('organization', 'Организация'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name="Пользователь")
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='user', verbose_name="Тип пользователя")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон")
    address = models.TextField(blank=True, verbose_name="Адрес")
    organization_name = models.CharField(max_length=200, blank=True, verbose_name="Название организации")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    
    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"
    
    def __str__(self):
        if self.user_type == 'organization':
            return f"{self.organization_name} ({self.user.username})"
        return f"{self.user.get_full_name() or self.user.username}"
    
    @property
    def is_organization(self):
        return self.user_type == 'organization'
    
    @property
    def is_regular_user(self):
        return self.user_type == 'user'


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Создание профиля при создании пользователя"""
    if created:
        UserProfile.objects.get_or_create(user=instance)


class Hotel(models.Model):
    """Модель отеля"""
    hotel_id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=200, verbose_name="Название отеля")
    description = models.TextField(verbose_name="Описание")
    address = models.TextField(verbose_name="Адрес")
    phone = models.CharField(max_length=20, verbose_name="Телефон")
    email = models.EmailField(verbose_name="Email")
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hotels', verbose_name="Владелец")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    
    class Meta:
        verbose_name = "Отель"
        verbose_name_plural = "Отели"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Room(models.Model):
    """Модель номера отеля"""
    room_id = models.BigAutoField(primary_key=True)
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='rooms', null=True, blank=True, verbose_name="Отель")
    number = models.CharField(max_length=50, verbose_name="Номер комнаты")
    name = models.CharField(max_length=200, verbose_name="Название номера")
    description = models.TextField(verbose_name="Описание")
    type_name = models.CharField(max_length=100, verbose_name="Тип комнаты")
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], default=0, verbose_name="Цена за ночь")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Номер"
        verbose_name_plural = "Номера"
        ordering = ['hotel', 'number']
        unique_together = [['hotel', 'number']]

    def __str__(self):
        return f"{self.hotel.name} - {self.number} - {self.name}"
    
    def calculate_price(self, check_in_date, check_out_date):
        """Вычисляет стоимость проживания за период"""
        from datetime import timedelta
        nights = (check_out_date - check_in_date).days
        return self.price_per_night * nights


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
    STATUS_CREATED = 'CREATED'
    STATUS_PAYMENT_PENDING = 'PAYMENT_PENDING'
    STATUS_PAID = 'PAID'
    STATUS_CANCELLED = 'CANCELLED'
    STATUS_PAYMENT_FAILED = 'PAYMENT_FAILED'
    STATUS_CHOICES = [
        (STATUS_CREATED, 'Создано'),
        (STATUS_PAYMENT_PENDING, 'Ожидает оплаты'),
        (STATUS_PAID, 'Оплачено'),
        (STATUS_CANCELLED, 'Отменено'),
        (STATUS_PAYMENT_FAILED, 'Ошибка оплаты'),
    ]

    booking_id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings', null=True, blank=True, verbose_name="Пользователь")
    guest = models.ForeignKey(Guest, on_delete=models.CASCADE, related_name='bookings', verbose_name="Гость")
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='bookings', verbose_name="Номер")
    check_in_date = models.DateField(verbose_name="Дата заезда")
    check_out_date = models.DateField(verbose_name="Дата выезда")
    adults_count = models.IntegerField(validators=[MinValueValidator(1)], verbose_name="Количество взрослых")
    children_count = models.IntegerField(default=0, validators=[MinValueValidator(0)], verbose_name="Количество детей")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Стоимость проживания")
    special_requests = models.TextField(null=True, blank=True, verbose_name="Пожелания")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PAYMENT_PENDING,
        verbose_name="Статус бронирования",
    )
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
    
    def save(self, *args, **kwargs):
        """Автоматический расчет стоимости при сохранении"""
        if self.room and self.check_in_date and self.check_out_date:
            self.total_price = self.room.calculate_price(self.check_in_date, self.check_out_date)
        super().save(*args, **kwargs)
