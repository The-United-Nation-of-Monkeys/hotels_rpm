from django.urls import path
from . import views

app_name = 'booking'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    
    # Аутентификация
    path('register/', views.RegistrationTypeView.as_view(), name='register_type'),
    path('register/user/', views.UserRegistrationView.as_view(), name='register_user'),
    path('register/organization/', views.OrganizationRegistrationView.as_view(), name='register_organization'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Личный кабинет
    path('profile/', views.ProfileView.as_view(), name='profile'),
    
    # Панель организации
    path('organization/', views.OrganizationPanelView.as_view(), name='organization_panel'),
    path('organization/hotels/create/', views.HotelCreateView.as_view(), name='hotel_create'),
    path('organization/hotels/<int:pk>/edit/', views.HotelUpdateView.as_view(), name='hotel_edit'),
    path('organization/rooms/create/', views.RoomCreateView.as_view(), name='room_create'),
    path('organization/rooms/<int:pk>/edit/', views.RoomUpdateView.as_view(), name='room_edit'),
    
    # Номера
    path('rooms/', views.RoomListView.as_view(), name='rooms'),
    path('rooms/<int:pk>/', views.RoomDetailView.as_view(), name='room_detail'),
    path('rooms/<int:room_id>/check-availability/', views.check_room_availability, name='check_room_availability'),
    
    # Гости
    path('guests/', views.GuestListView.as_view(), name='guests'),
    path('guests/create/', views.GuestCreateView.as_view(), name='guest_create'),
    path('guests/<int:pk>/', views.GuestDetailView.as_view(), name='guest_detail'),
    
    # Бронирования
    path('bookings/', views.BookingListView.as_view(), name='bookings'),
    path('bookings/create/', views.BookingCreateView.as_view(), name='booking_create'),
    path('bookings/<int:pk>/', views.BookingDetailView.as_view(), name='booking_detail'),
    
    # Контакты
    path('contact/', views.ContactView.as_view(), name='contact'),
]
