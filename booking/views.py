from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, TemplateView
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Q
from django.utils import timezone
from .models import Room, Guest, Booking
from .forms import BookingForm, GuestForm


class HomeView(TemplateView):
    """Главная страница"""
    template_name = 'booking/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['rooms_count'] = Room.objects.count()
        context['guests_count'] = Guest.objects.count()
        context['bookings_count'] = Booking.objects.count()
        context['available_rooms'] = Room.objects.all()[:3]
        return context


class RoomListView(ListView):
    """Список номеров"""
    model = Room
    template_name = 'booking/rooms.html'
    context_object_name = 'rooms'
    paginate_by = 9
    
    def get_queryset(self):
        queryset = Room.objects.all()
        room_type = self.request.GET.get('type')
        if room_type:
            queryset = queryset.filter(type_name__icontains=room_type)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['room_types'] = Room.objects.values_list('type_name', flat=True).distinct()
        return context


class RoomDetailView(DetailView):
    """Детальная информация о номере"""
    model = Room
    template_name = 'booking/room_detail.html'
    context_object_name = 'room'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Проверяем доступность номера
        check_in = self.request.GET.get('check_in')
        check_out = self.request.GET.get('check_out')
        context['is_available'] = True
        
        if check_in and check_out:
            try:
                from datetime import datetime
                check_in_date = datetime.strptime(check_in, '%Y-%m-%d').date()
                check_out_date = datetime.strptime(check_out, '%Y-%m-%d').date()
                
                # Проверяем пересечения с существующими бронированиями
                conflicting_bookings = Booking.objects.filter(
                    room=self.object,
                    check_in_date__lt=check_out_date,
                    check_out_date__gt=check_in_date
                )
                context['is_available'] = not conflicting_bookings.exists()
                context['check_in'] = check_in
                context['check_out'] = check_out
            except ValueError:
                pass
        
        return context


class GuestListView(ListView):
    """Список гостей"""
    model = Guest
    template_name = 'booking/guests.html'
    context_object_name = 'guests'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Guest.objects.all()
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(phone__icontains=search) |
                Q(email__icontains=search)
            )
        return queryset


class GuestDetailView(DetailView):
    """Детальная информация о госте"""
    model = Guest
    template_name = 'booking/guest_detail.html'
    context_object_name = 'guest'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['bookings'] = self.object.bookings.all().order_by('-check_in_date')
        return context


class GuestCreateView(CreateView):
    """Создание нового гостя"""
    model = Guest
    form_class = GuestForm
    template_name = 'booking/guest_form.html'
    success_url = reverse_lazy('guests')
    
    def form_valid(self, form):
        messages.success(self.request, 'Гость успешно добавлен!')
        return super().form_valid(form)


class BookingListView(ListView):
    """Список бронирований"""
    model = Booking
    template_name = 'booking/bookings.html'
    context_object_name = 'bookings'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Booking.objects.select_related('guest', 'room').all()
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(guest__first_name__icontains=search) |
                Q(guest__last_name__icontains=search) |
                Q(room__number__icontains=search) |
                Q(room__name__icontains=search)
            )
        return queryset.order_by('-check_in_date')


class BookingDetailView(DetailView):
    """Детальная информация о бронировании"""
    model = Booking
    template_name = 'booking/booking_detail.html'
    context_object_name = 'booking'


class BookingCreateView(CreateView):
    """Создание нового бронирования"""
    model = Booking
    form_class = BookingForm
    template_name = 'booking/booking_form.html'
    success_url = reverse_lazy('bookings')
    
    def get_initial(self):
        initial = super().get_initial()
        room_id = self.request.GET.get('room')
        if room_id:
            initial['room'] = room_id
        return initial
    
    def form_valid(self, form):
        # Получаем или создаем гостя
        guest_id = self.request.POST.get('guest_id')
        guest = None
        
        if guest_id:
            try:
                guest = Guest.objects.get(pk=guest_id)
            except Guest.DoesNotExist:
                messages.error(self.request, 'Выбранный гость не найден')
                return self.form_invalid(form)
        else:
            # Создаем нового гостя из формы
            guest_form = GuestForm(self.request.POST)
            if guest_form.is_valid():
                guest = guest_form.save()
            else:
                messages.error(self.request, 'Ошибка при создании гостя. Проверьте заполнение полей.')
                # Добавляем ошибки формы гостя в контекст
                context = self.get_context_data(form=form)
                context['guest_form'] = guest_form
                return self.render_to_response(context)
        
        if not guest:
            messages.error(self.request, 'Необходимо выбрать или создать гостя')
            return self.form_invalid(form)
        
        booking = form.save(commit=False)
        booking.guest = guest
        booking.save()
        messages.success(self.request, 'Бронирование успешно создано!')
        return redirect(self.success_url)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['guest_form'] = GuestForm()
        context['guests'] = Guest.objects.all()[:10]  # Последние 10 гостей
        return context


class ContactView(TemplateView):
    """Страница контактов"""
    template_name = 'booking/contact.html'
