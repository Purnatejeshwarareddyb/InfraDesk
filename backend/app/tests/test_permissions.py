import pytest

from app.tests.conftest import new_ticket

ADMIN_ONLY_GET = [
    "/api/v1/users",
    "/api/v1/users/1",
    "/api/v1/activity",
    "/api/v1/reports/tickets",
    "/api/v1/tickets/export.csv",
]


@pytest.mark.parametrize("path", ADMIN_ONLY_GET)
def test_worker_cannot_use_admin_get_routes(worker_a_client, admin, path):
    response = worker_a_client.get(path)
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "admin_required"


@pytest.mark.parametrize("path", ADMIN_ONLY_GET)
def test_anonymous_gets_401_on_protected_routes(anon, path):
    assert anon.get(path).status_code == 401


def test_worker_cannot_create_users_or_assets(worker_a_client):
    user = worker_a_client.post(
        "/api/v1/users", json={"username": "newbie", "display_name": "New Bie", "password": "Valid-Passw0rd-1"}
    )
    asset = worker_a_client.post("/api/v1/assets", json={"asset_tag": "PC-1", "name": "Desktop"})
    assert user.status_code == 403
    assert asset.status_code == 403


def test_worker_cannot_promote_themselves(worker_a_client, worker_a, db):
    response = worker_a_client.patch(f"/api/v1/users/{worker_a.id}", json={"role": "ADMIN"})
    assert response.status_code == 403
    db.refresh(worker_a)
    assert worker_a.role.value == "WORKER"


def test_extra_role_field_in_ticket_request_is_ignored(worker_a_client, worker_a, db):
    response = worker_a_client.post(
        "/api/v1/tickets",
        json={
            "title": "Role injection attempt",
            "description": "Trying to sneak extra fields into a normal request.",
            "role": "ADMIN",
            "assignee_id": worker_a.id,
            "status": "RESOLVED",
        },
    )
    assert response.status_code == 201
    ticket = response.json()
    assert ticket["status"] == "OPEN"
    assert ticket["assignee"] is None


def test_worker_cannot_assign_or_edit_tickets(worker_a_client, worker_a):
    ticket = new_ticket(worker_a_client)
    assign = worker_a_client.post(f"/api/v1/tickets/{ticket['id']}/assign", json={"assignee_id": worker_a.id})
    edit = worker_a_client.patch(f"/api/v1/tickets/{ticket['id']}", json={"priority": "URGENT"})
    assert assign.status_code == 403
    assert edit.status_code == 403


def test_worker_cannot_see_someone_elses_ticket(worker_a_client, worker_b_client):
    ticket = new_ticket(worker_a_client)
    assert worker_b_client.get(f"/api/v1/tickets/{ticket['id']}").status_code == 404
    assert worker_b_client.get(f"/api/v1/tickets/{ticket['id']}/history").status_code == 404
    listing = worker_b_client.get("/api/v1/tickets").json()
    assert listing["total"] == 0
    comment = worker_b_client.post(f"/api/v1/tickets/{ticket['id']}/comments", json={"body": "Sneaky comment"})
    assert comment.status_code == 404
    move = worker_b_client.post(f"/api/v1/tickets/{ticket['id']}/transition", json={"status": "CANCELLED"})
    assert move.status_code == 404


def test_worker_sees_own_and_assigned_tickets_only(admin_client, worker_a_client, worker_b_client, worker_a, worker_b):
    mine = new_ticket(worker_a_client, title="Reported by worker A")
    other = new_ticket(worker_b_client, title="Reported by worker B")
    admin_ticket = new_ticket(admin_client, title="Reported by admin for worker A")
    admin_client.post(f"/api/v1/tickets/{admin_ticket['id']}/assign", json={"assignee_id": worker_a.id})
    ids = {t["id"] for t in worker_a_client.get("/api/v1/tickets").json()["items"]}
    assert ids == {mine["id"], admin_ticket["id"]}
    assert other["id"] not in ids
    assert admin_client.get("/api/v1/tickets").json()["total"] == 3


def test_worker_can_read_assets_but_not_change_them(admin_client, worker_a_client):
    created = admin_client.post("/api/v1/assets", json={"asset_tag": "pc-001", "name": "Lab PC 1"}).json()
    assert worker_a_client.get("/api/v1/assets").json()["total"] == 1
    assert worker_a_client.patch(f"/api/v1/assets/{created['id']}", json={"name": "Hacked"}).status_code == 403
    assert worker_a_client.post(f"/api/v1/assets/{created['id']}/retire").status_code == 403


def test_worker_cannot_read_another_users_notifications(admin_client, worker_a_client, worker_b_client, worker_a):
    ticket = new_ticket(admin_client)
    admin_client.post(f"/api/v1/tickets/{ticket['id']}/assign", json={"assignee_id": worker_a.id})
    note = worker_a_client.get("/api/v1/notifications").json()["items"][0]
    assert worker_b_client.post(f"/api/v1/notifications/{note['id']}/read").status_code == 404
    assert worker_b_client.get("/api/v1/notifications").json()["total"] == 0


def test_error_responses_never_contain_stack_traces(anon, worker_a_client):
    # Authentication is checked first, so anonymous callers learn nothing about the route.
    assert anon.get("/api/v1/tickets/abc").status_code == 401
    response = worker_a_client.get("/api/v1/tickets/abc")
    assert response.status_code == 422
    assert "Traceback" not in response.text
    assert response.json()["error"]["code"] == "validation_error"
