"""
REST API для микросервисной связки: Booking Service.
Эндпоинты: GET/POST /api/bookings, GET /api/bookings/<id>, POST confirm-payment, POST cancel.
"""
import json
import logging
from decimal import Decimal

import httpx
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import Booking, Room, Guest

logger = logging.getLogger(__name__)


def _booking_to_json(booking: Booking) -> dict:
    """Сериализация бронирования в формат API (totalPrice вычислен при создании)."""
    return {
        "id": str(booking.booking_id),
        "roomId": str(booking.room_id),
        "guestId": str(booking.guest_id),
        "status": booking.status,
        "checkInDate": booking.check_in_date.isoformat(),
        "checkOutDate": booking.check_out_date.isoformat(),
        "adultsCount": booking.adults_count,
        "childrenCount": booking.children_count,
        "totalPrice": float(booking.total_price),
        "createdAt": booking.created_at.isoformat() if booking.created_at else None,
    }


@csrf_exempt
@require_http_methods(["GET", "POST"])
async def api_bookings_list_or_create(request):
    """GET /api/bookings/ — список. POST /api/bookings/ — создание и вызов Payment Service."""
    if request.method == "GET":
        limit = int(request.GET.get("limit", 20))
        offset = int(request.GET.get("offset", 0))
        status = request.GET.get("status")
        qs = Booking.objects.select_related("room", "guest").order_by("-created_at")
        if status:
            qs = qs.filter(status=status)
        total = await qs.acount()
        items = [_booking_to_json(b) async for b in qs[offset : offset + limit]]
        return JsonResponse({
            "items": items,
            "total": total,
            "limit": limit,
            "offset": offset,
        })
    return await _api_create_booking(request)


async def _api_create_booking(request):
    """POST /api/bookings/ — создание бронирования, вызов Payment Service."""
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON", "code": "INVALID_JSON"}, status=400)

    room_id = body.get("roomId")
    guest_id = body.get("guestId")
    check_in = body.get("checkInDate")
    check_out = body.get("checkOutDate")
    adults_count = body.get("adultsCount", 1)
    children_count = body.get("childrenCount", 0)
    special_requests = body.get("specialRequests") or ""

    if not all([room_id, guest_id, check_in, check_out]):
        return JsonResponse(
            {"error": "roomId, guestId, checkInDate, checkOutDate required", "code": "VALIDATION"},
            status=400,
        )

    from datetime import datetime
    try:
        check_in_date = datetime.strptime(check_in, "%Y-%m-%d").date()
        check_out_date = datetime.strptime(check_out, "%Y-%m-%d").date()
    except ValueError:
        return JsonResponse({"error": "Dates must be YYYY-MM-DD", "code": "VALIDATION"}, status=400)

    try:
        room = await Room.objects.aget(pk=room_id)
    except Room.DoesNotExist:
        return JsonResponse({"error": "Room not found", "code": "NOT_FOUND"}, status=404)

    try:
        guest = await Guest.objects.aget(pk=guest_id)
    except Guest.DoesNotExist:
        return JsonResponse({"error": "Guest not found", "code": "NOT_FOUND"}, status=404)

    if check_in_date >= check_out_date:
        return JsonResponse({"error": "checkOutDate must be after checkInDate", "code": "VALIDATION"}, status=400)

    total_price = room.calculate_price(check_in_date, check_out_date)
    booking = Booking(
        room=room,
        guest=guest,
        check_in_date=check_in_date,
        check_out_date=check_out_date,
        adults_count=adults_count,
        children_count=children_count,
        total_price=total_price,
        special_requests=special_requests,
        status=Booking.STATUS_PAYMENT_PENDING,
    )
    await booking.asave()

    payment_url = getattr(settings, "PAYMENT_SERVICE_URL", "http://localhost:8082").rstrip("/")
    payload = {
        "bookingId": str(booking.booking_id),
        "amount": float(total_price),
        "currency": "RUB",
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(f"{payment_url}/api/payments", json=payload)
            if resp.status_code not in (200, 201):
                logger.warning("Payment service returned %s: %s", resp.status_code, resp.text)
                booking.status = Booking.STATUS_PAYMENT_FAILED
                await booking.asave(update_fields=["status"])
                return JsonResponse(
                    {"error": "Payment service error", "code": "PAYMENT_ERROR"},
                    status=503,
                )
    except httpx.RequestError as e:
        logger.exception("Payment service unreachable: %s", e)
        booking.status = Booking.STATUS_PAYMENT_FAILED
        await booking.asave(update_fields=["status"])
        return JsonResponse(
            {"error": "Payment service unreachable", "code": "PAYMENT_UNREACHABLE"},
            status=503,
        )

    return JsonResponse(_booking_to_json(booking), status=201)


@csrf_exempt
@require_http_methods(["GET"])
async def api_get_booking(request, booking_id):
    """GET /api/bookings/<id>/ — одно бронирование."""
    try:
        booking = await Booking.objects.aget(booking_id=booking_id)
    except Booking.DoesNotExist:
        return JsonResponse({"error": "Booking not found", "code": "NOT_FOUND"}, status=404)
    return JsonResponse(_booking_to_json(booking))


@csrf_exempt
@require_http_methods(["POST"])
async def api_confirm_payment(request, booking_id):
    """POST /api/bookings/<id>/confirm-payment/ — подтверждение оплаты."""
    try:
        booking = await Booking.objects.aget(booking_id=booking_id)
    except Booking.DoesNotExist:
        return JsonResponse({"error": "Booking not found", "code": "NOT_FOUND"}, status=404)
    if booking.status != Booking.STATUS_PAYMENT_PENDING:
        return JsonResponse(
            {"error": "Booking status is not PAYMENT_PENDING", "code": "INVALID_STATUS"},
            status=400,
        )
    booking.status = Booking.STATUS_PAID
    await booking.asave(update_fields=["status"])
    return JsonResponse({"ok": True})


@csrf_exempt
@require_http_methods(["POST"])
async def api_cancel_booking(request, booking_id):
    """POST /api/bookings/<id>/cancel/ — отмена бронирования."""
    try:
        booking = await Booking.objects.aget(booking_id=booking_id)
    except Booking.DoesNotExist:
        return JsonResponse({"error": "Booking not found", "code": "NOT_FOUND"}, status=404)
    booking.status = Booking.STATUS_CANCELLED
    await booking.asave(update_fields=["status"])
    return JsonResponse({"ok": True})
