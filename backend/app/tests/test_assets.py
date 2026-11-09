def make_asset(client, **overrides):
    payload = {"asset_tag": "lab-pc-001", "name": "Lab PC 1", "asset_type": "COMPUTER", "location": "Lab 2"}
    payload.update(overrides)
    return client.post("/api/v1/assets", json=payload)


def test_create_list_get_asset(admin_client, worker_a_client):
    created = make_asset(admin_client, serial_number="SN-123", notes="Bought in 2024")
    assert created.status_code == 201
    asset = created.json()
    assert asset["asset_tag"] == "LAB-PC-001"  # tags are upper-cased
    assert asset["status"] == "ACTIVE"
    assert asset["serial_number"] == "SN-123"

    listing = admin_client.get("/api/v1/assets").json()
    assert listing["total"] == 1
    assert worker_a_client.get(f"/api/v1/assets/{asset['id']}").json()["name"] == "Lab PC 1"


def test_duplicate_asset_tag_is_a_conflict(admin_client):
    assert make_asset(admin_client).status_code == 201
    duplicate = make_asset(admin_client, name="Another")
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "asset_tag_taken"


def test_update_asset(admin_client):
    asset = make_asset(admin_client).json()
    updated = admin_client.patch(
        f"/api/v1/assets/{asset['id']}", json={"location": "Lab 3", "status": "IN_REPAIR", "serial_number": ""}
    )
    assert updated.status_code == 200
    body = updated.json()
    assert body["location"] == "Lab 3" and body["status"] == "IN_REPAIR" and body["serial_number"] is None


def test_update_to_existing_tag_is_a_conflict(admin_client):
    make_asset(admin_client, asset_tag="A-1", name="First")
    second = make_asset(admin_client, asset_tag="A-2", name="Second").json()
    response = admin_client.patch(f"/api/v1/assets/{second['id']}", json={"asset_tag": "a-1"})
    assert response.status_code == 409


def test_retire_asset_keeps_the_record(admin_client):
    asset = make_asset(admin_client).json()
    retired = admin_client.post(f"/api/v1/assets/{asset['id']}/retire")
    assert retired.status_code == 200 and retired.json()["status"] == "RETIRED"
    assert admin_client.get(f"/api/v1/assets/{asset['id']}").status_code == 200
    assert admin_client.get("/api/v1/assets", params={"include_retired": False}).json()["total"] == 0
    assert admin_client.get("/api/v1/assets").json()["total"] == 1


def test_asset_search_and_filter(admin_client):
    make_asset(admin_client, asset_tag="PRN-1", name="Office printer", asset_type="PRINTER", location="Admin office")
    make_asset(admin_client, asset_tag="PC-1", name="Desktop", asset_type="COMPUTER", location="Lab 1")
    assert admin_client.get("/api/v1/assets", params={"q": "printer"}).json()["total"] == 1
    assert admin_client.get("/api/v1/assets", params={"q": "lab 1"}).json()["total"] == 1
    assert admin_client.get("/api/v1/assets", params={"asset_type": "PRINTER"}).json()["total"] == 1


def test_asset_validation(admin_client):
    assert make_asset(admin_client, asset_tag="x").status_code == 422
    assert make_asset(admin_client, asset_type="TOASTER").status_code == 422
    assert admin_client.get("/api/v1/assets/9999").status_code == 404


def test_asset_changes_appear_in_activity_log(admin_client):
    asset = make_asset(admin_client).json()
    admin_client.post(f"/api/v1/assets/{asset['id']}/retire")
    events = [e["event_type"] for e in admin_client.get("/api/v1/activity").json()["items"]]
    assert "ASSET_CREATED" in events and "ASSET_RETIRED" in events
