from app.tests.conftest import PASSWORD

NEW_USER = {"username": "Worker_C", "display_name": "Worker C", "password": "Valid-Passw0rd-1", "role": "WORKER"}


def test_admin_creates_worker_who_can_log_in(admin_client, anon):
    created = admin_client.post("/api/v1/users", json=NEW_USER)
    assert created.status_code == 201
    body = created.json()
    assert body["username"] == "worker_c"  # normalised
    assert body["role"] == "WORKER" and body["is_active"] is True
    assert "password" not in created.text.lower().replace("passwords", "")
    assert anon.post("/api/v1/auth/login", json={"username": "worker_c", "password": "Valid-Passw0rd-1"}).status_code == 200


def test_duplicate_username_is_a_conflict(admin_client):
    admin_client.post("/api/v1/users", json=NEW_USER)
    again = admin_client.post("/api/v1/users", json=NEW_USER)
    assert again.status_code == 409 and again.json()["error"]["code"] == "username_taken"


def test_user_validation(admin_client):
    assert admin_client.post("/api/v1/users", json={**NEW_USER, "username": "a b"}).status_code == 422
    assert admin_client.post("/api/v1/users", json={**NEW_USER, "password": "alllowercase1"}).status_code == 422
    assert admin_client.post("/api/v1/users", json={**NEW_USER, "password": "Short1"}).status_code == 422
    assert admin_client.post("/api/v1/users", json={**NEW_USER, "role": "ROOT"}).status_code == 422


def test_list_users_search_and_filters(admin_client, worker_a, worker_b):
    assert admin_client.get("/api/v1/users").json()["total"] == 3
    assert admin_client.get("/api/v1/users", params={"q": "worker"}).json()["total"] == 2
    assert admin_client.get("/api/v1/users", params={"role": "ADMIN"}).json()["total"] == 1
    admin_client.post(f"/api/v1/users/{worker_b.id}/deactivate")
    assert admin_client.get("/api/v1/users", params={"active": False}).json()["total"] == 1


def test_list_never_exposes_password_hashes(admin_client, worker_a):
    text = admin_client.get("/api/v1/users").text
    assert "argon2" not in text and "password_hash" not in text


def test_deactivate_and_activate(admin_client, worker_a, anon):
    assert admin_client.post(f"/api/v1/users/{worker_a.id}/deactivate").json()["is_active"] is False
    assert anon.post("/api/v1/auth/login", json={"username": "worker_a", "password": PASSWORD}).status_code == 401
    assert admin_client.post(f"/api/v1/users/{worker_a.id}/activate").json()["is_active"] is True
    assert anon.post("/api/v1/auth/login", json={"username": "worker_a", "password": PASSWORD}).status_code == 200


def test_admin_cannot_deactivate_self(admin_client, admin):
    response = admin_client.post(f"/api/v1/users/{admin.id}/deactivate")
    assert response.status_code == 422 and response.json()["error"]["code"] == "self_deactivate"


def test_last_active_admin_is_protected(admin_client, admin, make_user, login):
    second = make_user("admin_two", role=admin.role)
    second_client = login(second.username)
    assert second_client.post(f"/api/v1/users/{admin.id}/deactivate").status_code == 200
    # admin_two is now the only active admin and cannot be demoted
    demote = second_client.patch(f"/api/v1/users/{second.id}", json={"role": "WORKER"})
    assert demote.status_code == 422 and demote.json()["error"]["code"] == "last_admin"


def test_admin_can_change_role_and_reset_password(admin_client, worker_a, anon):
    updated = admin_client.patch(
        f"/api/v1/users/{worker_a.id}", json={"role": "ADMIN", "display_name": "Worker Alpha", "password": "Reset-Passw0rd-7"}
    )
    assert updated.status_code == 200
    assert updated.json()["role"] == "ADMIN" and updated.json()["display_name"] == "Worker Alpha"
    assert anon.post("/api/v1/auth/login", json={"username": "worker_a", "password": "Reset-Passw0rd-7"}).status_code == 200


def test_unknown_user_is_404(admin_client):
    assert admin_client.get("/api/v1/users/9999").status_code == 404


def test_user_changes_appear_in_activity_log(admin_client, worker_a):
    admin_client.post("/api/v1/users", json=NEW_USER)
    admin_client.post(f"/api/v1/users/{worker_a.id}/deactivate")
    events = [e["event_type"] for e in admin_client.get("/api/v1/activity").json()["items"]]
    assert "USER_CREATED" in events and "USER_DEACTIVATED" in events
