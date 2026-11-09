import csv
import io

import pytest
from sqlalchemy import select

from app.models.audit_event import AuditEvent
from app.models.ticket import Ticket
from app.services.ticket_service import TRANSITIONS
from app.tests.conftest import new_ticket


def move(client, ticket_id, status, **extra):
    return client.post(f"/api/v1/tickets/{ticket_id}/transition", json={"status": status, **extra})


# ----------------------------------------------------------------- creation


def test_ticket_creation_persists_and_gets_readable_number(worker_a_client, db):
    ticket = new_ticket(worker_a_client, priority="HIGH", category="NETWORK")
    assert ticket["ticket_number"] == f"HD-{ticket['id']:06d}"
    assert ticket["status"] == "OPEN"
    assert ticket["reporter"]["username"] == "worker_a"
    stored = db.get(Ticket, ticket["id"])
    assert stored is not None and stored.title == ticket["title"]
    events = db.scalars(select(AuditEvent).where(AuditEvent.ticket_id == ticket["id"])).all()
    assert [e.event_type.value for e in events] == ["TICKET_CREATED"]


def test_ticket_validation_errors_use_standard_shape(worker_a_client):
    response = worker_a_client.post("/api/v1/tickets", json={"title": "abc", "description": "short"})
    assert response.status_code == 422
    body = response.json()["error"]
    assert body["code"] == "validation_error"
    fields = {d["field"] for d in body["details"]}
    assert {"title", "description"} <= fields


def test_invalid_enum_value_is_rejected(worker_a_client):
    response = worker_a_client.post(
        "/api/v1/tickets",
        json={"title": "Valid title here", "description": "Valid description text.", "priority": "SUPER"},
    )
    assert response.status_code == 422


def test_whitespace_only_title_is_rejected(worker_a_client):
    response = worker_a_client.post(
        "/api/v1/tickets", json={"title": "          ", "description": "Valid description text."}
    )
    assert response.status_code == 422


def test_creating_ticket_notifies_administrators(admin_client, worker_a_client):
    ticket = new_ticket(worker_a_client)
    notes = admin_client.get("/api/v1/notifications").json()
    assert notes["unread_count"] == 1
    assert notes["items"][0]["type"] == "TICKET_CREATED"
    assert notes["items"][0]["ticket_id"] == ticket["id"]
    # the reporter does not notify themselves
    assert worker_a_client.get("/api/v1/notifications").json()["total"] == 0


def test_unknown_or_retired_asset_cannot_be_linked(admin_client, worker_a_client):
    missing = worker_a_client.post(
        "/api/v1/tickets",
        json={"title": "Asset does not exist", "description": "Linking an unknown asset.", "related_asset_id": 999},
    )
    assert missing.status_code == 422
    asset = admin_client.post("/api/v1/assets", json={"asset_tag": "OLD-1", "name": "Old PC"}).json()
    admin_client.post(f"/api/v1/assets/{asset['id']}/retire")
    retired = worker_a_client.post(
        "/api/v1/tickets",
        json={"title": "Asset is retired", "description": "Linking a retired asset.", "related_asset_id": asset["id"]},
    )
    assert retired.status_code == 422
    assert retired.json()["error"]["code"] == "asset_retired"


def test_ticket_can_reference_an_asset(admin_client, worker_a_client):
    asset = admin_client.post("/api/v1/assets", json={"asset_tag": "pc-7", "name": "Lab PC 7"}).json()
    ticket = new_ticket(worker_a_client, related_asset_id=asset["id"])
    assert ticket["related_asset"]["asset_tag"] == "PC-7"


# ---------------------------------------------------------------- workflow


def test_full_ticket_lifecycle(admin_client, worker_a_client, worker_a, worker_b_client):
    ticket = new_ticket(worker_b_client)
    tid = ticket["id"]

    assigned = admin_client.post(f"/api/v1/tickets/{tid}/assign", json={"assignee_id": worker_a.id}).json()
    assert assigned["status"] == "ASSIGNED"
    assert assigned["assignee"]["id"] == worker_a.id

    assert move(worker_a_client, tid, "IN_PROGRESS").status_code == 200
    assert move(worker_a_client, tid, "WAITING").status_code == 200
    assert move(worker_a_client, tid, "IN_PROGRESS").status_code == 200

    no_note = move(worker_a_client, tid, "RESOLVED")
    assert no_note.status_code == 422
    assert no_note.json()["error"]["code"] == "resolution_required"

    resolved = move(worker_a_client, tid, "RESOLVED", resolution_note="Replaced the lamp.").json()
    assert resolved["status"] == "RESOLVED"
    assert resolved["resolution_note"] == "Replaced the lamp."
    assert resolved["resolved_at"] is not None

    # only administrators close tickets
    assert move(worker_a_client, tid, "CLOSED").status_code == 422
    closed = move(admin_client, tid, "CLOSED").json()
    assert closed["status"] == "CLOSED" and closed["closed_at"] is not None

    history = admin_client.get(f"/api/v1/tickets/{tid}/history").json()
    kinds = [e["event_type"] for e in history]
    assert kinds[0] == "TICKET_CREATED"
    assert kinds.count("STATUS_CHANGED") == 6  # assign, 3 worker moves, resolve, close
    assert kinds.count("TICKET_ASSIGNED") == 1


@pytest.mark.parametrize(
    "from_status,to_status",
    [
        ("OPEN", "RESOLVED"),
        ("OPEN", "CLOSED"),
        ("OPEN", "WAITING"),
        ("ASSIGNED", "RESOLVED"),
        ("IN_PROGRESS", "OPEN"),
        ("IN_PROGRESS", "CLOSED"),
        ("RESOLVED", "WAITING"),
        ("CANCELLED", "IN_PROGRESS"),
    ],
)
def test_illegal_transitions_are_rejected_even_for_admin(admin_client, admin, worker_a, db, from_status, to_status):
    ticket = new_ticket(admin_client)
    stored = db.get(Ticket, ticket["id"])
    stored.status = type(stored.status)(from_status)
    stored.assignee_id = worker_a.id
    db.commit()
    response = move(admin_client, ticket["id"], to_status, resolution_note="x")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_transition"
    db.refresh(stored)
    assert stored.status.value == from_status


def test_transition_table_matches_specification():
    names = {k.value: {v.value for v in vs} for k, vs in TRANSITIONS.items()}
    assert names["OPEN"] == {"ASSIGNED", "IN_PROGRESS", "CANCELLED"}
    assert names["ASSIGNED"] == {"IN_PROGRESS", "WAITING", "CANCELLED"}
    assert names["IN_PROGRESS"] == {"WAITING", "RESOLVED"}
    assert names["WAITING"] == {"IN_PROGRESS", "RESOLVED"}
    assert names["RESOLVED"] == {"CLOSED", "IN_PROGRESS"}
    assert names["CLOSED"] == {"IN_PROGRESS"}
    assert names["CANCELLED"] == set()


def test_assigned_status_can_only_be_set_through_assign(admin_client):
    ticket = new_ticket(admin_client)
    response = move(admin_client, ticket["id"], "ASSIGNED")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "use_assign"


def test_admin_starting_unassigned_ticket_takes_ownership(admin_client, admin):
    ticket = new_ticket(admin_client)
    started = move(admin_client, ticket["id"], "IN_PROGRESS").json()
    assert started["assignee"]["id"] == admin.id


def test_worker_cannot_start_open_unassigned_ticket(worker_a_client):
    ticket = new_ticket(worker_a_client)
    assert ticket["allowed_transitions"] == ["CANCELLED"]
    assert move(worker_a_client, ticket["id"], "IN_PROGRESS").status_code == 422


def test_reporter_may_cancel_only_while_open(admin_client, worker_a_client, worker_a):
    cancel_me = new_ticket(worker_a_client)
    cancelled = move(worker_a_client, cancel_me["id"], "CANCELLED")
    assert cancelled.status_code == 200 and cancelled.json()["status"] == "CANCELLED"

    assigned = new_ticket(worker_a_client)
    admin_client.post(f"/api/v1/tickets/{assigned['id']}/assign", json={"assignee_id": worker_a.id})
    assert move(worker_a_client, assigned["id"], "CANCELLED").status_code == 422
    assert move(admin_client, assigned["id"], "CANCELLED").status_code == 200


def test_cancelled_ticket_cannot_be_reassigned_or_reopened(admin_client, worker_a_client, worker_a):
    ticket = new_ticket(worker_a_client)
    move(worker_a_client, ticket["id"], "CANCELLED")
    assign = admin_client.post(f"/api/v1/tickets/{ticket['id']}/assign", json={"assignee_id": worker_a.id})
    assert assign.status_code == 422
    assert assign.json()["error"]["code"] == "not_assignable"
    assert move(admin_client, ticket["id"], "IN_PROGRESS").status_code == 422


def test_reopening_resolved_and_closed_tickets(admin_client, worker_a_client, worker_a):
    ticket = new_ticket(admin_client)
    tid = ticket["id"]
    admin_client.post(f"/api/v1/tickets/{tid}/assign", json={"assignee_id": worker_a.id})
    move(worker_a_client, tid, "IN_PROGRESS")
    move(worker_a_client, tid, "RESOLVED", resolution_note="Fixed.")
    reopened = move(worker_a_client, tid, "IN_PROGRESS").json()
    assert reopened["resolved_at"] is None

    move(worker_a_client, tid, "RESOLVED", resolution_note="Fixed for real.")
    move(admin_client, tid, "CLOSED")
    assert move(worker_a_client, tid, "IN_PROGRESS").status_code == 422  # closed: admin only
    again = move(admin_client, tid, "IN_PROGRESS").json()
    assert again["status"] == "IN_PROGRESS" and again["closed_at"] is None


def test_other_worker_who_is_not_assignee_cannot_progress_ticket(admin_client, worker_a_client, worker_b_client, worker_a, worker_b):
    ticket = new_ticket(admin_client)
    admin_client.post(f"/api/v1/tickets/{ticket['id']}/assign", json={"assignee_id": worker_a.id})
    # worker_b cannot even see it
    assert move(worker_b_client, ticket["id"], "IN_PROGRESS").status_code == 404


def test_allowed_transitions_reflect_role(admin_client, worker_a_client, worker_a):
    ticket = new_ticket(admin_client)
    admin_client.post(f"/api/v1/tickets/{ticket['id']}/assign", json={"assignee_id": worker_a.id})
    for_worker = worker_a_client.get(f"/api/v1/tickets/{ticket['id']}").json()["ticket"]["allowed_transitions"]
    for_admin = admin_client.get(f"/api/v1/tickets/{ticket['id']}").json()["ticket"]["allowed_transitions"]
    assert for_worker == ["IN_PROGRESS", "WAITING"]
    assert for_admin == ["IN_PROGRESS", "WAITING", "CANCELLED"]


# --------------------------------------------------------------- assignment


def test_assign_rules(admin_client, worker_a, make_user):
    inactive = make_user("inactive_w", active=False)
    ticket = new_ticket(admin_client)
    tid = ticket["id"]
    assert admin_client.post(f"/api/v1/tickets/{tid}/assign", json={"assignee_id": 9999}).status_code == 422
    assert admin_client.post(f"/api/v1/tickets/{tid}/assign", json={"assignee_id": inactive.id}).status_code == 422
    assert admin_client.post(f"/api/v1/tickets/{tid}/assign", json={"assignee_id": worker_a.id}).status_code == 200
    same = admin_client.post(f"/api/v1/tickets/{tid}/assign", json={"assignee_id": worker_a.id})
    assert same.status_code == 422 and same.json()["error"]["code"] == "same_assignee"


def test_reassign_keeps_status_and_records_history(admin_client, worker_a, worker_b):
    ticket = new_ticket(admin_client)
    tid = ticket["id"]
    admin_client.post(f"/api/v1/tickets/{tid}/assign", json={"assignee_id": worker_a.id})
    move(admin_client, tid, "IN_PROGRESS")
    result = admin_client.post(f"/api/v1/tickets/{tid}/assign", json={"assignee_id": worker_b.id}).json()
    assert result["status"] == "IN_PROGRESS"
    assigned_events = [e for e in admin_client.get(f"/api/v1/tickets/{tid}/history").json() if e["event_type"] == "TICKET_ASSIGNED"]
    assert assigned_events[-1]["old_value"] == "Worker A"
    assert assigned_events[-1]["new_value"] == "Worker B"


# ------------------------------------------------------------ edit, comment


def test_admin_edit_records_history_and_ignores_no_ops(admin_client):
    ticket = new_ticket(admin_client, priority="LOW")
    tid = ticket["id"]
    same = admin_client.patch(f"/api/v1/tickets/{tid}", json={"priority": "LOW"})
    assert same.status_code == 200
    changed = admin_client.patch(f"/api/v1/tickets/{tid}", json={"priority": "URGENT", "category": "NETWORK"}).json()
    assert changed["priority"] == "URGENT" and changed["category"] == "NETWORK"
    updates = [e for e in admin_client.get(f"/api/v1/tickets/{tid}/history").json() if e["event_type"] == "TICKET_UPDATED"]
    assert len(updates) == 2
    assert {(u["old_value"], u["new_value"]) for u in updates} == {("LOW", "URGENT"), ("HARDWARE", "NETWORK")}


def test_comment_is_stored_in_history_and_notifies_other_party(admin_client, worker_a_client, worker_a):
    ticket = new_ticket(worker_a_client)
    tid = ticket["id"]
    created = admin_client.post(f"/api/v1/tickets/{tid}/comments", json={"body": "Please send a photo."})
    assert created.status_code == 201
    detail = worker_a_client.get(f"/api/v1/tickets/{tid}").json()
    assert [c["body"] for c in detail["comments"]] == ["Please send a photo."]
    assert "COMMENT_ADDED" in [e["event_type"] for e in detail["history"]]
    notes = worker_a_client.get("/api/v1/notifications").json()
    assert notes["items"][0]["type"] == "TICKET_COMMENT"


def test_empty_comment_is_rejected(worker_a_client):
    ticket = new_ticket(worker_a_client)
    assert worker_a_client.post(f"/api/v1/tickets/{ticket['id']}/comments", json={"body": "   "}).status_code == 422


# ---------------------------------------------------------- list and search


def test_filters_search_sort_and_pagination(admin_client, worker_a_client, worker_a):
    first = new_ticket(worker_a_client, title="Printer jam in office", category="PRINTER", priority="LOW")
    new_ticket(worker_a_client, title="WiFi drops every hour", category="NETWORK", priority="URGENT")
    new_ticket(admin_client, title="Reset account password", category="ACCOUNT_ACCESS", priority="HIGH")
    admin_client.post(f"/api/v1/tickets/{first['id']}/assign", json={"assignee_id": worker_a.id})

    def ids(**params):
        return [t["title"] for t in admin_client.get("/api/v1/tickets", params=params).json()["items"]]

    assert ids(category="NETWORK") == ["WiFi drops every hour"]
    assert ids(priority="HIGH") == ["Reset account password"]
    assert ids(status="ASSIGNED") == ["Printer jam in office"]
    assert ids(assignee_id=worker_a.id) == ["Printer jam in office"]
    assert ids(q="wifi") == ["WiFi drops every hour"]
    assert ids(q=first["ticket_number"].lower()) == ["Printer jam in office"]
    assert ids(q=str(first["id"])) == ["Printer jam in office"]
    assert set(ids(q="worker a")) == {"Printer jam in office", "WiFi drops every hour"}
    assert ids(sort="priority")[0] == "WiFi drops every hour"
    assert ids(sort="oldest")[0] == "Printer jam in office"

    page = admin_client.get("/api/v1/tickets", params={"page_size": 2, "page": 2}).json()
    assert page["total"] == 3 and page["pages"] == 2 and len(page["items"]) == 1


def test_page_size_is_limited(admin_client):
    assert admin_client.get("/api/v1/tickets", params={"page_size": 1000}).status_code == 422


def test_mine_filter_for_admin(admin_client, worker_a_client):
    new_ticket(worker_a_client)
    new_ticket(admin_client)
    assert admin_client.get("/api/v1/tickets", params={"mine": True}).json()["total"] == 1


def test_date_range_filter(admin_client, worker_a_client):
    new_ticket(worker_a_client)
    today = "2100-01-01"
    assert admin_client.get("/api/v1/tickets", params={"created_from": today}).json()["total"] == 0
    assert admin_client.get("/api/v1/tickets", params={"created_to": "2000-01-01"}).json()["total"] == 0
    assert admin_client.get("/api/v1/tickets", params={"created_from": "2000-01-01", "created_to": today}).json()["total"] == 1


# ---------------------------------------------------------------------- CSV


def test_csv_export_headers_and_escaping(admin_client, worker_a_client):
    new_ticket(worker_a_client, title='Printer "HP-1", second floor', description="Line one\nLine two, with comma")
    new_ticket(worker_a_client, title="=HYPERLINK(\"http://evil.example\")", description="Formula injection attempt.")
    response = admin_client.get("/api/v1/tickets/export.csv")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "attachment" in response.headers["content-disposition"]
    rows = list(csv.reader(io.StringIO(response.text)))
    assert rows[0][:5] == ["ticket_number", "title", "category", "priority", "status"]
    titles = {r[1] for r in rows[1:]}
    assert 'Printer "HP-1", second floor' in titles  # quotes and commas round-trip correctly
    assert "'=HYPERLINK(\"http://evil.example\")" in titles  # leading = is neutralised
    assert len(rows) == 3


def test_csv_export_respects_filters(admin_client, worker_a_client):
    new_ticket(worker_a_client, category="NETWORK")
    new_ticket(worker_a_client, category="PRINTER")
    rows = list(csv.reader(io.StringIO(admin_client.get("/api/v1/tickets/export.csv", params={"category": "NETWORK"}).text)))
    assert len(rows) == 2
