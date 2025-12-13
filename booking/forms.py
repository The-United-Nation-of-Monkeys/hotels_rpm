from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Room, Guest, Booking, Hotel, UserProfile


class BookingForm(forms.ModelForm):
    """Форма для создания бронирования"""
    
    class Meta:
        model = Booking
        fields = ['room', 'check_in_date', 'check_out_date', 'adults_count', 
                  'children_count', 'special_requests']
        widgets = {
            'check_in_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'check_out_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'room': forms.Select(attrs={'class': 'form-control'}),
            'adults_count': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'children_count': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'special_requests': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
        labels = {
            'room': 'Номер',
            'check_in_date': 'Дата заезда',
            'check_out_date': 'Дата выезда',
            'adults_count': 'Количество взрослых',
            'children_count': 'Количество детей',
            'special_requests': 'Пожелания',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Показываем номера с информацией об отеле
        self.fields['room'].queryset = Room.objects.select_related('hotel').filter(hotel__isnull=False)
        
        def room_label(obj):
            hotel_name = obj.hotel.name if obj.hotel else "Без отеля"
            return f"{hotel_name} - {obj.name} ({obj.number}) - {obj.price_per_night} ₽/ночь"
        
        self.fields['room'].label_from_instance = room_label

    def clean(self):
        cleaned_data = super().clean()
        check_in_date = cleaned_data.get('check_in_date')
        check_out_date = cleaned_data.get('check_out_date')
        room = cleaned_data.get('room')
        
        if check_in_date and check_out_date:
            if check_in_date >= check_out_date:
                raise ValidationError("Дата заезда должна быть раньше даты выезда")
            if check_in_date < timezone.now().date():
                raise ValidationError("Дата заезда не может быть в прошлом")
            
            # Проверяем, не занят ли номер в эти даты
            if room:
                conflicting_bookings = Booking.objects.filter(
                    room=room,
                    check_in_date__lt=check_out_date,
                    check_out_date__gt=check_in_date
                ).order_by('check_in_date')
                
                if conflicting_bookings.exists():
                    # Формируем список дат занятости - все даты в одном сообщении
                    booking_dates = []
                    for booking in conflicting_bookings:
                        booking_dates.append(
                            f"{booking.check_in_date.strftime('%d.%m.%Y')} - {booking.check_out_date.strftime('%d.%m.%Y')}"
                        )
                    dates_str = ', '.join(booking_dates)
                    raise ValidationError(
                        f"НОМЕР УЖЕ ЗАНЯТ в это время. Забронирован: {dates_str}. Пожалуйста, выберите другие даты."
                    )
        
        return cleaned_data


class GuestForm(forms.ModelForm):
    """Форма для создания/редактирования гостя"""
    
    class Meta:
        model = Guest
        fields = ['first_name', 'last_name', 'middle_name', 'passport_number', 
                  'email', 'phone']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'middle_name': forms.TextInput(attrs={'class': 'form-control'}),
            'passport_number': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'middle_name': 'Отчество',
            'passport_number': 'Номер паспорта',
            'email': 'Электронная почта',
            'phone': 'Телефон',
        }


class UserRegistrationForm(UserCreationForm):
    """Форма регистрации пользователя"""
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    phone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            profile = user.profile
            profile.phone = self.cleaned_data.get('phone', '')
            profile.user_type = 'user'
            profile.save()
        return user


class OrganizationRegistrationForm(UserCreationForm):
    """Форма регистрации организации"""
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    organization_name = forms.CharField(max_length=200, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    phone = forms.CharField(max_length=20, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    address = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}))
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            profile = user.profile
            profile.user_type = 'organization'
            profile.organization_name = self.cleaned_data['organization_name']
            profile.phone = self.cleaned_data['phone']
            profile.address = self.cleaned_data.get('address', '')
            profile.save()
        return user


class UserProfileForm(forms.ModelForm):
    """Форма редактирования профиля пользователя"""
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = UserProfile
        fields = ['phone', 'address']
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name
            self.fields['email'].initial = self.user.email
    
    def save(self, commit=True):
        profile = super().save(commit=False)
        if self.user:
            self.user.first_name = self.cleaned_data['first_name']
            self.user.last_name = self.cleaned_data['last_name']
            self.user.email = self.cleaned_data['email']
            if commit:
                self.user.save()
                profile.save()
        return profile


class HotelForm(forms.ModelForm):
    """Форма создания/редактирования отеля"""
    
    class Meta:
        model = Hotel
        fields = ['name', 'description', 'address', 'phone', 'email']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }


class RoomForm(forms.ModelForm):
    """Форма создания/редактирования номера"""
    
    class Meta:
        model = Room
        fields = ['hotel', 'number', 'name', 'description', 'type_name', 'price_per_night']
        widgets = {
            'hotel': forms.Select(attrs={'class': 'form-control'}),
            'number': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'type_name': forms.TextInput(attrs={'class': 'form-control'}),
            'price_per_night': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0}),
        }
