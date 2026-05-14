from django.urls import path
from . import views_api

urlpatterns = [
    path("health/", views_api.api_health),
    path("metrics/", views_api.api_metrics),
    path("bookings/", views_api.api_bookings_list_or_create),
    path("bookings/<int:booking_id>/", views_api.api_get_booking),
    path("bookings/<int:booking_id>/confirm-payment/", views_api.api_confirm_payment),
    path("bookings/<int:booking_id>/cancel/", views_api.api_cancel_booking),
]
