# Generated manually for Booking.status (microservice API)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0002_alter_room_options_booking_user_room_price_per_night_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='status',
            field=models.CharField(
                choices=[
                    ('CREATED', 'Создано'),
                    ('PAYMENT_PENDING', 'Ожидает оплаты'),
                    ('PAID', 'Оплачено'),
                    ('CANCELLED', 'Отменено'),
                    ('PAYMENT_FAILED', 'Ошибка оплаты'),
                ],
                default='PAYMENT_PENDING',
                max_length=20,
                verbose_name='Статус бронирования',
            ),
        ),
    ]
