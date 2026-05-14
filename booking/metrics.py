from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from django.http import HttpResponse

REQUEST_COUNT = Counter(
    "booking_http_requests_total",
    "Total HTTP requests for booking service",
    ["method", "path", "status"],
)

REQUEST_LATENCY = Histogram(
    "booking_http_request_duration_seconds",
    "HTTP request latency for booking service",
    ["method", "path"],
)


def metrics_response() -> HttpResponse:
    return HttpResponse(generate_latest(), content_type=CONTENT_TYPE_LATEST)
