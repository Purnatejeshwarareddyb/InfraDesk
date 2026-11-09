from app.tests.conftest import new_ticket


def test_assignment_creates_notification_for_assignee(admin_client, worker_a_client, worker_a):
    ticket = new_ticket(admin_client, title="Replace broken keyboard")
    admin_client.post(f"/api/v1/tickets/{ticket['id']}/assign", json={"assignee_id": worker_a.id})
    data = worker_a_client.get("/api/v1/notifications").json()
    assert data["total"] == 1 and data["unread_count"] == 1
    note = data["items"][0]
    assert note["type"] == "TICKET_ASSIGNED"
    assert note["ticket_id"] == ticket["id"]
    assert "Replace broken keyboard" in note["message"]
    assert note["read_at"] is None


def test_read_state_persists(admin_client, worker_a_client, worker_a, login):
    ticket = new_ticket(admin_client)
    admin_client.post(f"/api/v1/tickets/{ticket['id']}/assign", json={"assignee_id": worker_a.id})
    note = worker_a_client.get("/api/v1/notifications").json()["items"][0]

    read = worker_a_client.post(f"/api/v1/notifications/{note['id']}/read")
    assert read.status_code == 200 and read.json()["read_at"] is not None

    fresh_session = login(worker_a.username)  # a brand new login sees the stored state
    data = fresh_session.get("/api/v1/notifications").json()
    assert data["unread_count"] == 0
    assert data["items"][0]["read_at"] is not None
    assert fresh_session.get("/api/v1/notifications", params={"unread_only": True}).json()["total"] == 0


def test_read_all(admin_client, worker_a_client, worker_a):
    for title in ("First broken thing here", "Second broken thing here", "Third broken thing here"):
        t = new_ticket(admin_client, title=title)
        admin_client.post(f"/api/v1/tickets/{t['id']}/assign", json={"assignee_id": worker_a.id})
    assert worker_a_client.get("/api/v1/notifications").json()["unread_count"] == 3
    response = worker_a_client.post("/api/v1/notifications/read-all")
    assert response.status_code == 200
    assert worker_a_client.get("/api/v1/notifications").json()["unread_count"] == 0


def test_unknown_notification_is_404(worker_a_client):
    assert worker_a_client.post("/api/v1/notifications/12345/read").status_code == 404


def test_status_change_notifies_reporter_and_admin_on_resolve(admin_client, worker_a_client, worker_b_client, worker_a):
    ticket = new_ticket(worker_b_client)
    tid = ticket["id"]
    admin_client.post(f"/api/v1/tickets/{tid}/assign", json={"assignee_id": worker_a.id})
    worker_a_client.post(f"/api/v1/tickets/{tid}/transition", json={"status": "IN_PROGRESS"})
    worker_a_client.post(
        f"/api/v1/tickets/{tid}/transition", json={"status": "RESOLVED", "resolution_note": "Cable replaced."}
    )
    reporter_types = [n["type"] for n in worker_b_client.get("/api/v1/notifications").json()["items"]]
    assert reporter_types.count("TICKET_STATUS") == 2
    admin_types = [n["type"] for n in admin_client.get("/api/v1/notifications").json()["items"]]
    assert "TICKET_STATUS" in admin_types  # administrators hear about resolutions


def test_actor_is_not_notified_about_own_action(admin_client, admin, worker_a):
    ticket = new_ticket(admin_client)
    admin_client.post(f"/api/v1/tickets/{ticket['id']}/assign", json={"assignee_id": admin.id})
    assert admin_client.get("/api/v1/notifications").json()["total"] == 0


def test_status_notification_uses_readable_status_names(admin_client, worker_a_client, worker_b_client, worker_a):
    ticket = new_ticket(worker_b_client)
    admin_client.post(f"/api/v1/tickets/{ticket['id']}/assign", json={"assignee_id": worker_a.id})
    worker_a_client.post(f"/api/v1/tickets/{ticket['id']}/transition", json={"status": "IN_PROGRESS"})
    messages = [n["message"] for n in worker_b_client.get("/api/v1/notifications").json()["items"]]
    assert any("from Assigned to In progress" in m for m in messages)
    assert not any("IN_PROGRESS" in m for m in messages)
