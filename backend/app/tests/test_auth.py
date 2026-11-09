from datetime import UTC, datetime, timedelta

import jwt

from app.core.config import get_settings
from app.core.security import ALGORITHM
from app.tests.conftest import PASSWORD


def test_valid_login_sets_http_only_cookie_and_hides_hash(anon, worker_a):
    response = anon.post("/api/v1/auth/login", json={"username": "worker_a", "password": PASSWORD})
    assert response.status_code == 200
    body = response.json()
    assert body["user"]["username"] == "worker_a"
    assert body["user"]["role"] == "WORKER"
    assert "password" not in response.text.lower()
    cookie = response.headers["set-cookie"].lower()
    assert "httponly" in cookie
    assert "samesite=lax" in cookie
    assert anon.get("/api/v1/auth/me").json()["username"] == "worker_a"


def test_username_is_case_insensitive_and_trimmed(anon, worker_a):
    response = anon.post("/api/v1/auth/login", json={"username": "  WORKER_A ", "password": PASSWORD})
    assert response.status_code == 200


def test_invalid_login_does_not_reveal_which_part_was_wrong(anon, worker_a):
    wrong_password = anon.post("/api/v1/auth/login", json={"username": "worker_a", "password": "nope-nope-1A"})
    unknown_user = anon.post("/api/v1/auth/login", json={"username": "ghost", "password": PASSWORD})
    assert wrong_password.status_code == unknown_user.status_code == 401
    assert wrong_password.json() == unknown_user.json()
    assert wrong_password.json()["error"]["message"] == "Invalid username or password."


def test_inactive_user_cannot_log_in(anon, make_user):
    make_user("sleepy", active=False)
    response = anon.post("/api/v1/auth/login", json={"username": "sleepy", "password": PASSWORD})
    assert response.status_code == 401
    assert response.json()["error"]["message"] == "Invalid username or password."


def test_me_requires_authentication(anon):
    response = anon.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "not_authenticated"


def test_logout_ends_session(worker_a_client):
    assert worker_a_client.get("/api/v1/auth/me").status_code == 200
    assert worker_a_client.post("/api/v1/auth/logout").status_code == 200
    assert worker_a_client.get("/api/v1/auth/me").status_code == 401


def test_expired_token_is_rejected(anon, worker_a):
    settings = get_settings()
    past = datetime.now(UTC) - timedelta(minutes=5)
    token = jwt.encode(
        {"sub": str(worker_a.id), "iat": past - timedelta(hours=1), "exp": past}, settings.secret_key, algorithm=ALGORITHM
    )
    anon.cookies.set(settings.cookie_name, token)
    response = anon.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "session_expired"


def test_token_with_wrong_signature_is_rejected(anon, worker_a):
    settings = get_settings()
    now = datetime.now(UTC)
    token = jwt.encode(
        {"sub": str(worker_a.id), "iat": now, "exp": now + timedelta(minutes=5)},
        "some-other-secret-key-which-is-long-enough-123",
        algorithm=ALGORITHM,
    )
    anon.cookies.set(settings.cookie_name, token)
    assert anon.get("/api/v1/auth/me").status_code == 401


def test_deactivated_user_loses_access_immediately(admin_client, worker_a, worker_a_client):
    assert worker_a_client.get("/api/v1/auth/me").status_code == 200
    assert admin_client.post(f"/api/v1/users/{worker_a.id}/deactivate").status_code == 200
    assert worker_a_client.get("/api/v1/auth/me").status_code == 401


def test_change_password_requires_current_password(worker_a_client, anon):
    bad = worker_a_client.post(
        "/api/v1/auth/change-password", json={"current_password": "wrong-Password-1", "new_password": "Brand-New-Pass-9"}
    )
    assert bad.status_code == 401
    ok = worker_a_client.post(
        "/api/v1/auth/change-password", json={"current_password": PASSWORD, "new_password": "Brand-New-Pass-9"}
    )
    assert ok.status_code == 200
    assert anon.post("/api/v1/auth/login", json={"username": "worker_a", "password": PASSWORD}).status_code == 401
    assert anon.post("/api/v1/auth/login", json={"username": "worker_a", "password": "Brand-New-Pass-9"}).status_code == 200


def test_weak_new_password_is_rejected(worker_a_client):
    response = worker_a_client.post(
        "/api/v1/auth/change-password", json={"current_password": PASSWORD, "new_password": "short"}
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_cross_site_write_request_is_blocked(worker_a_client):
    payload = {
        "title": "Forged request from another site",
        "description": "This should be rejected by the origin check.",
    }
    forged = worker_a_client.post("/api/v1/tickets", json=payload, headers={"Origin": "https://evil.example"})
    assert forged.status_code == 403
    assert forged.json()["error"]["code"] == "csrf_check_failed"
    allowed = worker_a_client.post("/api/v1/tickets", json=payload, headers={"Origin": "http://localhost:5173"})
    assert allowed.status_code == 201
    same_origin = worker_a_client.post("/api/v1/tickets", json=payload, headers={"Origin": "http://testserver"})
    assert same_origin.status_code == 201


def test_password_is_stored_hashed(db, worker_a):
    assert worker_a.password_hash != PASSWORD
    assert worker_a.password_hash.startswith("$argon2")
