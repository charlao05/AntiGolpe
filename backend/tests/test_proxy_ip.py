from backend.app.main import client_ip


def test_client_ip_uses_render_forwarded_ip():
    headers = {"x-forwarded-for": "203.0.113.10, 10.0.0.5"}
    assert client_ip("10.0.0.5", headers) == "203.0.113.10"


def test_client_ip_falls_back_to_connection_ip():
    assert client_ip("10.0.0.5", {}) == "10.0.0.5"


def test_client_ip_ignores_empty_forwarded_header():
    headers = {"x-forwarded-for": "   "}
    assert client_ip("10.0.0.5", headers) == "10.0.0.5"
