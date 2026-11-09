"""Test setup: a throw-away SQLite file and helpers to create users and sign in."""

import os
import tempfile
from pathlib import Path

_TMP_DIR = tempfile.mkdtemp(prefix="infradesk-tests-")
os.environ["SECRET_KEY"] = "test-secret-key-for-automated-tests-only-0123456789"
os.environ["DATABASE_URL"] = f"sqlite:///{Path(_TMP_DIR) / 'test.db'}"
os.environ["ENVIRONMENT"] = "test"
os.environ["CORS_ORIGINS"] = "http://localhost:5173"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import app.models  # noqa: E402,F401
from app.core.security import hash_password  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402
from app.main import app as fastapi_app  # noqa: E402
from app.models.enums import Role  # noqa: E402
from app.models.user import User  # noqa: E402

PASSWORD = "Test-Passw0rd-1"


@pytest.fixture(autouse=True)
def fresh_database():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def make_user(db):
    def _make(username: str, role: Role = Role.WORKER, *, active: bool = True, display_name: str | None = None) -> User:
        user = User(
            username=username,
            display_name=display_name or username.replace("_", " ").title(),
            password_hash=hash_password(PASSWORD),
            role=role,
            is_active=active,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    return _make


@pytest.fixture
def anon():
    with TestClient(fastapi_app) as client:
        yield client


@pytest.fixture
def login():
    """Return a function that signs in and gives back a client holding the session cookie."""
    clients: list[TestClient] = []

    def _login(username: str, password: str = PASSWORD) -> TestClient:
        client = TestClient(fastapi_app)
        clients.append(client)
        response = client.post("/api/v1/auth/login", json={"username": username, "password": password})
        assert response.status_code == 200, response.text
        return client

    yield _login
    for c in clients:
        c.close()


@pytest.fixture
def admin(make_user):
    return make_user("admin_one", Role.ADMIN, display_name="Admin One")


@pytest.fixture
def worker_a(make_user):
    return make_user("worker_a", Role.WORKER, display_name="Worker A")


@pytest.fixture
def worker_b(make_user):
    return make_user("worker_b", Role.WORKER, display_name="Worker B")


@pytest.fixture
def admin_client(admin, login):
    return login(admin.username)


@pytest.fixture
def worker_a_client(worker_a, login):
    return login(worker_a.username)


@pytest.fixture
def worker_b_client(worker_b, login):
    return login(worker_b.username)


def new_ticket(client: TestClient, **overrides) -> dict:
    payload = {
        "title": "Projector in Lab 2 does not turn on",
        "description": "The projector shows no light and the remote has no effect.",
        "category": "HARDWARE",
        "priority": "MEDIUM",
    }
    payload.update(overrides)
    response = client.post("/api/v1/tickets", json=payload)
    assert response.status_code == 201, response.text
    return response.json()
