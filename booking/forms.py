from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Room, Guest, Booking


class BookingForm(forms.ModelForm):
    """Форма для создания бронирования"""
    
    class Meta:
        model = Booking
        fields = ['room', 'check_in_date', 'check_out_date', 'adults_count', 
                  'children_count', 'total_price', 'special_requests']
        widgets = {
            'check_in_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'check_out_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'room': forms.Select(attrs={'class': 'form-control'}),
            'adults_count': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'children_count': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'total_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'special_requests': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
        labels = {
            'room': 'Номер',
            'check_in_date': 'Дата заезда',
            'check_out_date': 'Дата выезда',
            'adults_count': 'Количество взрослых',
            'children_count': 'Количество детей',
            'total_price': 'Стоимость проживания',
            'special_requests': 'Пожелания',
        }

    def clean(self):
        cleaned_data = super().clean()
        check_in_date = cleaned_data.get('check_in_date')
        check_out_date = cleaned_data.get('check_out_date')
        
        if check_in_date and check_out_date:
            if check_in_date >= check_out_date:
                raise ValidationError("Дата заезда должна быть раньше даты выезда")
            if check_in_date < timezone.now().date():
                raise ValidationError("Дата заезда не может быть в прошлом")
        
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
