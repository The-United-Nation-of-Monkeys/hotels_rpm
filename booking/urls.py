from django.urls import path
from . import views

app_name = 'booking'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('rooms/', views.RoomListView.as_view(), name='rooms'),
    path('rooms/<int:pk>/', views.RoomDetailView.as_view(), name='room_detail'),
    path('guests/', views.GuestListView.as_view(), name='guests'),
    path('guests/create/', views.GuestCreateView.as_view(), name='guest_create'),
    path('guests/<int:pk>/', views.GuestDetailView.as_view(), name='guest_detail'),
    path('bookings/', views.BookingListView.as_view(), name='bookings'),
    path('bookings/create/', views.BookingCreateView.as_view(), name='booking_create'),
    path('bookings/<int:pk>/', views.BookingDetailView.as_view(), name='booking_detail'),
    path('contact/', views.ContactView.as_view(), name='contact'),
]
