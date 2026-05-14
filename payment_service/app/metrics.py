from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.responses import Response

REQUEST_COUNT = Counter(
    "payment_http_requests_total",
    "Total HTTP requests for payment service",
    ["method", "path", "status"],
)

REQUEST_LATENCY = Histogram(
    "payment_http_request_duration_seconds",
    "HTTP request latency for payment service",
    ["method", "path"],
)


def render_metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
