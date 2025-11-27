from django.contrib import admin
from .models import Room, Guest, Booking


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('number', 'name', 'type_name', 'created_at')
    list_filter = ('type_name', 'created_at')
    search_fields = ('number', 'name', 'type_name')
    readonly_fields = ('room_id', 'created_at', 'updated_at')
    fieldsets = (
        ('Основная информация', {
            'fields': ('room_id', 'number', 'name', 'type_name', 'description')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(Guest)
class GuestAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'middle_name', 'phone', 'email', 'passport_number')
    list_filter = ('created_at',)
    search_fields = ('last_name', 'first_name', 'middle_name', 'passport_number', 'phone', 'email')
    readonly_fields = ('guest_id', 'created_at', 'updated_at')
    fieldsets = (
        ('Основная информация', {
            'fields': ('guest_id', 'last_name', 'first_name', 'middle_name')
        }),
        ('Контактные данные', {
            'fields': ('passport_number', 'phone', 'email')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('booking_id', 'guest', 'room', 'check_in_date', 'check_out_date', 'total_price', 'created_at')
    list_filter = ('check_in_date', 'check_out_date', 'created_at', 'room__type_name')
    search_fields = ('guest__last_name', 'guest__first_name', 'room__number', 'room__name')
    readonly_fields = ('booking_id', 'created_at', 'updated_at')
    date_hierarchy = 'check_in_date'
    fieldsets = (
        ('Основная информация', {
            'fields': ('booking_id', 'guest', 'room')
        }),
        ('Даты проживания', {
            'fields': ('check_in_date', 'check_out_date')
        }),
        ('Детали бронирования', {
            'fields': ('adults_count', 'children_count', 'total_price', 'special_requests')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at')
        }),
    )
