from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.responses import Response

REQUEST_COUNT = Counter(
    "notification_http_requests_total",
    "Total HTTP requests for notification service",
    ["method", "path", "status"],
)

REQUEST_LATENCY = Histogram(
    "notification_http_request_duration_seconds",
    "HTTP request latency for notification service",
    ["method", "path"],
)


def render_metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
