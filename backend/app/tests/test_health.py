def test_health_ok(anon):
    response = anon.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["version"]


def test_ready_ok(anon):
    response = anon.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_ready_reports_unavailable_database_without_leaking_details(anon, monkeypatch):
    class BrokenSession:
        def __enter__(self):
            raise RuntimeError("secret path /var/lib/infradesk/infradesk.db is locked")

        def __exit__(self, *args):
            return False

    monkeypatch.setattr("app.api.v1.health.SessionLocal", lambda: BrokenSession())
    response = anon.get("/ready")
    assert response.status_code == 503
    assert response.json() == {"status": "not_ready"}
    assert "secret" not in response.text and ".db" not in response.text


def test_unknown_route_uses_standard_error_shape(anon):
    response = anon.get("/api/v1/does-not-exist")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_api_docs_are_served_locally_without_cdn(anon):
    page = anon.get("/docs")
    assert page.status_code == 200
    assert "cdn.jsdelivr" not in page.text and "fastapi.tiangolo.com" not in page.text
    assert "/docs-assets/swagger-ui-bundle.js" in page.text
    assert anon.get("/docs-assets/swagger-ui-bundle.js").status_code == 200
    assert anon.get("/docs-assets/swagger-ui.css").status_code == 200
    assert anon.get("/openapi.json").status_code == 200
