from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, TemplateView, UpdateView
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Q
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from .models import Room, Guest, Booking, Hotel, UserProfile
from .forms import BookingForm, GuestForm, UserRegistrationForm, OrganizationRegistrationForm, UserProfileForm, HotelForm, RoomForm


class HomeView(TemplateView):
    """Главная страница"""
    template_name = 'booking/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['rooms_count'] = Room.objects.count()
        context['guests_count'] = Guest.objects.count()
        context['bookings_count'] = Booking.objects.count()
        context['available_rooms'] = Room.objects.select_related('hotel').all()[:3]
        return context


class RegistrationTypeView(TemplateView):
    """Выбор типа регистрации"""
    template_name = 'booking/registration_type.html'


class UserRegistrationView(CreateView):
    """Регистрация пользователя"""
    form_class = UserRegistrationForm
    template_name = 'booking/register_user.html'
    success_url = reverse_lazy('booking:home')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(self.request, 'Регистрация успешна! Добро пожаловать!')
        return response


class OrganizationRegistrationView(CreateView):
    """Регистрация организации"""
    form_class = OrganizationRegistrationForm
    template_name = 'booking/register_organization.html'
    success_url = reverse_lazy('booking:organization_panel')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(self.request, 'Организация успешно зарегистрирована!')
        return response


@require_http_methods(["GET", "POST"])
def login_view(request):
    """Вход в систему"""
    if request.method == 'POST':
        from django.contrib.auth import authenticate
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.username}!')
            if hasattr(user, 'profile') and user.profile.is_organization:
                return redirect('booking:organization_panel')
            return redirect('booking:home')
        else:
            messages.error(request, 'Неверное имя пользователя или пароль')
    return render(request, 'booking/login.html')


@login_required
def logout_view(request):
    """Выход из системы"""
    logout(request)
    messages.success(request, 'Вы успешно вышли из системы')
    return redirect('booking:home')


class ProfileView(LoginRequiredMixin, UpdateView):
    """Личный кабинет пользователя"""
    model = UserProfile
    form_class = UserProfileForm
    template_name = 'booking/profile.html'
    success_url = reverse_lazy('booking:profile')
    
    def get_object(self):
        return self.request.user.profile
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_bookings'] = Booking.objects.filter(user=self.request.user).order_by('-check_in_date')[:10]
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Профиль успешно обновлен!')
        return super().form_valid(form)


class OrganizationPanelView(LoginRequiredMixin, TemplateView):
    """Панель организации"""
    template_name = 'booking/organization_panel.html'
    
    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, 'profile') or not request.user.profile.is_organization:
            messages.error(request, 'Доступ запрещен. Только для организаций.')
            return redirect('booking:home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['hotels'] = Hotel.objects.filter(owner=self.request.user)
        context['rooms'] = Room.objects.filter(hotel__owner=self.request.user)
        context['bookings'] = Booking.objects.filter(room__hotel__owner=self.request.user).order_by('-check_in_date')[:10]
        return context


class HotelCreateView(LoginRequiredMixin, CreateView):
    """Создание отеля"""
    model = Hotel
    form_class = HotelForm
    template_name = 'booking/hotel_form.html'
    success_url = reverse_lazy('booking:organization_panel')
    
    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, 'profile') or not request.user.profile.is_organization:
            messages.error(request, 'Доступ запрещен. Только для организаций.')
            return redirect('booking:home')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        hotel = form.save(commit=False)
        hotel.owner = self.request.user
        hotel.save()
        messages.success(self.request, 'Отель успешно создан!')
        return redirect(self.success_url)


class HotelUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование отеля"""
    model = Hotel
    form_class = HotelForm
    template_name = 'booking/hotel_form.html'
    success_url = reverse_lazy('booking:organization_panel')
    
    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, 'profile') or not request.user.profile.is_organization:
            messages.error(request, 'Доступ запрещен.')
            return redirect('booking:home')
        hotel = self.get_object()
        if hotel.owner != request.user:
            messages.error(request, 'У вас нет прав для редактирования этого отеля.')
            return redirect('booking:organization_panel')
        return super().dispatch(request, *args, **kwargs)


class RoomCreateView(LoginRequiredMixin, CreateView):
    """Создание номера"""
    model = Room
    form_class = RoomForm
    template_name = 'booking/room_form.html'
    success_url = reverse_lazy('booking:organization_panel')
    
    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, 'profile') or not request.user.profile.is_organization:
            messages.error(request, 'Доступ запрещен. Только для организаций.')
            return redirect('booking:home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['initial'] = kwargs.get('initial', {})
        hotel_id = self.request.GET.get('hotel')
        if hotel_id:
            try:
                hotel = Hotel.objects.get(pk=hotel_id, owner=self.request.user)
                kwargs['initial']['hotel'] = hotel
            except Hotel.DoesNotExist:
                pass
        return kwargs
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['hotel'].queryset = Hotel.objects.filter(owner=self.request.user)
        return form
    
    def form_valid(self, form):
        messages.success(self.request, 'Номер успешно создан!')
        return super().form_valid(form)


class RoomUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование номера"""
    model = Room
    form_class = RoomForm
    template_name = 'booking/room_form.html'
    success_url = reverse_lazy('booking:organization_panel')
    
    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, 'profile') or not request.user.profile.is_organization:
            messages.error(request, 'Доступ запрещен.')
            return redirect('booking:home')
        room = self.get_object()
        if room.hotel.owner != request.user:
            messages.error(request, 'У вас нет прав для редактирования этого номера.')
            return redirect('booking:organization_panel')
        return super().dispatch(request, *args, **kwargs)
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['hotel'].queryset = Hotel.objects.filter(owner=self.request.user)
        return form


class RoomListView(ListView):
    """Список номеров"""
    model = Room
    template_name = 'booking/rooms.html'
    context_object_name = 'rooms'
    paginate_by = 9
    
    def get_queryset(self):
        queryset = Room.objects.select_related('hotel').all()
        room_type = self.request.GET.get('type')
        hotel_id = self.request.GET.get('hotel')
        if room_type:
            queryset = queryset.filter(type_name__icontains=room_type)
        if hotel_id:
            queryset = queryset.filter(hotel_id=hotel_id)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['room_types'] = Room.objects.values_list('type_name', flat=True).distinct()
        context['hotels'] = Hotel.objects.all()
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
        context['is_available'] = None
        
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


class BookingListView(LoginRequiredMixin, ListView):
    """Список бронирований"""
    model = Booking
    template_name = 'booking/bookings.html'
    context_object_name = 'bookings'
    paginate_by = 20
    
    def get_queryset(self):
        if hasattr(self.request.user, 'profile') and self.request.user.profile.is_organization:
            # Организации видят бронирования своих отелей
            queryset = Booking.objects.select_related('guest', 'room', 'room__hotel').filter(
                room__hotel__owner=self.request.user
            )
        else:
            # Пользователи видят только свои бронирования
            queryset = Booking.objects.select_related('guest', 'room', 'room__hotel').filter(
                user=self.request.user
            )
        
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


class BookingCreateView(LoginRequiredMixin, CreateView):
    """Создание нового бронирования"""
    model = Booking
    form_class = BookingForm
    template_name = 'booking/booking_form.html'
    success_url = reverse_lazy('booking:bookings')
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Для бронирования необходимо войти в систему.')
            return redirect('booking:login')
        if hasattr(request.user, 'profile') and request.user.profile.is_organization:
            messages.error(request, 'Организации не могут создавать бронирования.')
            return redirect('booking:organization_panel')
        return super().dispatch(request, *args, **kwargs)
    
    def get_initial(self):
        initial = super().get_initial()
        room_id = self.request.GET.get('room')
        if room_id:
            initial['room'] = room_id
        return initial
    
    def form_invalid(self, form):
        """Обработка невалидной формы"""
        # Сохраняем выбранного гостя если был
        guest_id = self.request.POST.get('guest_id', '').strip()
        context = self.get_context_data(form=form)
        if guest_id:
            context['selected_guest_id'] = int(guest_id) if guest_id.isdigit() else None
        
        # Проверяем, есть ли ошибка о занятости номера из валидации формы
        # Если есть ошибка валидации формы, она уже будет показана через form.non_field_errors
        # Не нужно дублировать через booking_conflict
        
        return self.render_to_response(context)
    
    def form_valid(self, form):
        # Получаем или создаем гостя
        guest_id = self.request.POST.get('guest_id', '').strip()
        guest = None
        
        if guest_id:
            try:
                guest = Guest.objects.get(pk=guest_id)
                # Если гость выбран, не проверяем поля создания гостя
            except (Guest.DoesNotExist, ValueError) as e:
                messages.error(self.request, f'Выбранный гость не найден: {str(e)}')
                return self.form_invalid(form)
        else:
            # Создаем нового гостя из формы
            guest_form = GuestForm(self.request.POST)
            if guest_form.is_valid():
                try:
                    guest = guest_form.save()
                except Exception as e:
                    messages.error(self.request, f'Ошибка при сохранении гостя: {str(e)}')
                    context = self.get_context_data(form=form)
                    context['guest_form'] = guest_form
                    return self.render_to_response(context)
            else:
                # Форма гостя не валидна - показываем только общую ошибку
                # Детальные ошибки будут показаны в шаблоне рядом с полями
                has_errors = any(guest_form.errors.values())
                if has_errors:
                    # Проверяем, есть ли ошибка уникальности паспорта
                    if 'passport_number' in guest_form.errors:
                        for error in guest_form.errors['passport_number']:
                            if 'уже существует' in str(error) or 'already exists' in str(error).lower():
                                messages.error(self.request, 'Гость с таким номером паспорта уже существует. Пожалуйста, выберите его из списка выше.')
                            else:
                                messages.error(self.request, 'Пожалуйста, заполните все обязательные поля гостя.')
                    else:
                        messages.error(self.request, 'Пожалуйста, заполните все обязательные поля гостя.')
                else:
                    messages.error(self.request, 'Ошибка при создании гостя. Проверьте заполнение полей.')
                
                # Добавляем ошибки формы гостя в контекст
                context = self.get_context_data(form=form)
                context['guest_form'] = guest_form
                # Сохраняем значения формы бронирования
                context['form'] = form
                # Сохраняем выбранного гостя если был
                if guest_id:
                    context['selected_guest_id'] = guest_id
                return self.render_to_response(context)
        
        if not guest:
            messages.error(self.request, 'Необходимо выбрать или создать гостя')
            return self.form_invalid(form)
        
        # Дополнительная проверка доступности номера
        check_in_date = form.cleaned_data.get('check_in_date')
        check_out_date = form.cleaned_data.get('check_out_date')
        room = form.cleaned_data.get('room')
        
        # Проверка доступности номера уже выполняется в форме через clean()
        # Дополнительная проверка здесь не нужна, так как форма уже проверит это
        
        booking = form.save(commit=False)
        booking.guest = guest
        booking.user = self.request.user
        booking.save()
        messages.success(self.request, 'Бронирование успешно создано!')
        return redirect(self.success_url)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Если форма гостя уже была отправлена, используем её, иначе создаем новую
        if 'guest_form' not in context:
            if self.request.method == 'POST' and not self.request.POST.get('guest_id'):
                # Если была попытка создать гостя, используем данные из POST
                context['guest_form'] = GuestForm(self.request.POST)
            else:
                context['guest_form'] = GuestForm()
        context['guests'] = Guest.objects.all()[:10]  # Последние 10 гостей
        # Добавляем информацию о ценах для JavaScript
        import json
        context['room_prices_json'] = json.dumps({str(room.pk): float(room.price_per_night) for room in Room.objects.filter(hotel__isnull=False)})
        return context


class ContactView(TemplateView):
    """Страница контактов"""
    template_name = 'booking/contact.html'


from django.http import JsonResponse

def check_room_availability(request, room_id):
    """Проверка доступности номера через AJAX"""
    from datetime import datetime
    
    check_in = request.GET.get('check_in')
    check_out = request.GET.get('check_out')
    
    if not check_in or not check_out:
        return JsonResponse({'error': 'Не указаны даты'}, status=400)
    
    try:
        room = Room.objects.get(pk=room_id)
        check_in_date = datetime.strptime(check_in, '%Y-%m-%d').date()
        check_out_date = datetime.strptime(check_out, '%Y-%m-%d').date()
        
        if check_out_date <= check_in_date:
            return JsonResponse({'error': 'Дата выезда должна быть позже даты заезда'}, status=400)
        
        # Проверяем пересечения с существующими бронированиями
        conflicting_bookings = Booking.objects.filter(
            room=room,
            check_in_date__lt=check_out_date,
            check_out_date__gt=check_in_date
        ).order_by('check_in_date')
        
        is_available = not conflicting_bookings.exists()
        nights = (check_out_date - check_in_date).days
        total_price = float(room.price_per_night) * nights
        
        # Формируем список дат занятости
        booking_dates = []
        if not is_available:
            for booking in conflicting_bookings:
                booking_dates.append({
                    'check_in': booking.check_in_date.strftime('%d.%m.%Y'),
                    'check_out': booking.check_out_date.strftime('%d.%m.%Y')
                })
        
        response_data = {
            'available': is_available,
            'nights': nights,
            'total_price': total_price,
            'price_per_night': float(room.price_per_night)
        }
        
        if not is_available:
            response_data['booking_dates'] = booking_dates
        
        return JsonResponse(response_data)
    except Room.DoesNotExist:
        return JsonResponse({'error': 'Номер не найден'}, status=404)
    except ValueError:
        return JsonResponse({'error': 'Неверный формат даты'}, status=400)
