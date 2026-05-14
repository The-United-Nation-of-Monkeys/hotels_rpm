from django.test import TestCase

class BookingServiceInfraTests(TestCase):
    def test_health_and_metrics_endpoints(self):
        health = self.client.get("/api/health/")
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.json()["service"], "booking-service")

        metrics = self.client.get("/api/metrics/")
        self.assertEqual(metrics.status_code, 200)
        self.assertIn("booking_http_requests_total", metrics.content.decode("utf-8"))
