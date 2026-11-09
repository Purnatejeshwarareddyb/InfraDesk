from app.tests.conftest import new_ticket


def counts(items):
    return {i["key"]: i["count"] for i in items}


def test_empty_database_gives_zero_counts(admin_client):
    data = admin_client.get("/api/v1/reports/summary").json()
    assert data["scope"] == "all"
    assert data["total"] == data["open"] == data["in_progress"] == data["resolved"] == 0
    assert data["recent_activity"] == []
    assert set(counts(data["by_status"])) == {"OPEN", "ASSIGNED", "IN_PROGRESS", "WAITING", "RESOLVED", "CLOSED", "CANCELLED"}


def test_summary_reflects_actual_records(admin_client, worker_a_client, worker_a):
    t1 = new_ticket(worker_a_client, priority="URGENT")
    t2 = new_ticket(worker_a_client, priority="HIGH")
    t3 = new_ticket(worker_a_client, priority="LOW")
    new_ticket(worker_a_client, priority="MEDIUM")

    for t in (t1, t2, t3):
        admin_client.post(f"/api/v1/tickets/{t['id']}/assign", json={"assignee_id": worker_a.id})
    worker_a_client.post(f"/api/v1/tickets/{t2['id']}/transition", json={"status": "IN_PROGRESS"})
    worker_a_client.post(f"/api/v1/tickets/{t3['id']}/transition", json={"status": "IN_PROGRESS"})
    worker_a_client.post(
        f"/api/v1/tickets/{t3['id']}/transition", json={"status": "RESOLVED", "resolution_note": "Done."}
    )

    data = admin_client.get("/api/v1/reports/summary").json()
    assert data["total"] == 4
    assert data["open"] == 2  # t1 ASSIGNED + the unassigned one
    assert data["in_progress"] == 1
    assert data["resolved"] == 1
    assert data["high_priority_active"] == 2  # t1 URGENT + t2 HIGH are still active
    assert counts(data["by_priority"]) == {"LOW": 1, "MEDIUM": 1, "HIGH": 1, "URGENT": 1}
    assert len(data["recent_activity"]) == 10


def test_worker_summary_only_counts_own_tickets(admin_client, worker_a_client, worker_b_client):
    new_ticket(worker_a_client)
    new_ticket(worker_a_client)
    new_ticket(worker_b_client)
    data = worker_a_client.get("/api/v1/reports/summary").json()
    assert data["scope"] == "mine" and data["total"] == 2
    assert admin_client.get("/api/v1/reports/summary").json()["total"] == 3


def test_ticket_report_groups_by_category_and_assignee(admin_client, worker_a_client, worker_a):
    a = new_ticket(worker_a_client, category="NETWORK")
    new_ticket(worker_a_client, category="NETWORK")
    new_ticket(worker_a_client, category="PRINTER")
    admin_client.post(f"/api/v1/tickets/{a['id']}/assign", json={"assignee_id": worker_a.id})

    report = admin_client.get("/api/v1/reports/tickets").json()
    assert report["total"] == 3
    assert counts(report["by_category"])["NETWORK"] == 2
    assert counts(report["by_category"])["PRINTER"] == 1
    assert counts(report["by_category"])["HARDWARE"] == 0
    by_assignee = {i["label"]: i["count"] for i in report["by_assignee"]}
    assert by_assignee == {"Worker A": 1, "Unassigned": 2}


def test_ticket_report_date_range(admin_client, worker_a_client):
    new_ticket(worker_a_client)
    far_future = admin_client.get("/api/v1/reports/tickets", params={"date_from": "2100-01-01"}).json()
    assert far_future["total"] == 0
    inside = admin_client.get("/api/v1/reports/tickets", params={"date_from": "2000-01-01", "date_to": "2100-01-01"}).json()
    assert inside["total"] == 1
    bad = admin_client.get("/api/v1/reports/tickets", params={"date_from": "2100-01-01", "date_to": "2000-01-01"})
    assert bad.status_code == 422 and bad.json()["error"]["code"] == "invalid_date_range"
