"""Migrations, seed/admin scripts and backup/restore, all against disposable databases."""

import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from app.db.base import Base
from app.db.init_db import BACKEND_DIR, run_migrations

SCRIPTS = BACKEND_DIR / "scripts"
sys.path.insert(0, str(SCRIPTS))

import backup_database  # noqa: E402
import restore_database  # noqa: E402


def run_script(name: str, db_file: Path, *args: str, **extra_env: str) -> subprocess.CompletedProcess:
    env = {
        **os.environ,
        "DATABASE_URL": f"sqlite:///{db_file}",
        "SECRET_KEY": "script-test-secret-key-0123456789abcdefghij",
        "ENVIRONMENT": "development",
        **extra_env,
    }
    return subprocess.run(
        [sys.executable, str(SCRIPTS / name), *args], cwd=BACKEND_DIR, env=env, capture_output=True, text=True, timeout=120
    )


def table_names(db_file: Path) -> set[str]:
    connection = sqlite3.connect(db_file)
    try:
        return {r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    finally:
        connection.close()


def count(db_file: Path, table: str) -> int:
    connection = sqlite3.connect(db_file)
    try:
        return connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]  # noqa: S608 - fixed names in tests
    finally:
        connection.close()


# -------------------------------------------------------------- migrations


def test_migrations_create_every_model_table(tmp_path):
    db_file = tmp_path / "migrated.db"
    run_migrations(f"sqlite:///{db_file}")
    expected = set(Base.metadata.tables) | {"alembic_version"}
    assert table_names(db_file) == expected


def test_migrations_can_run_twice(tmp_path):
    db_file = tmp_path / "twice.db"
    run_migrations(f"sqlite:///{db_file}")
    run_migrations(f"sqlite:///{db_file}")
    assert "tickets" in table_names(db_file)


# ----------------------------------------------------------------- scripts


def test_seed_requires_confirmation(tmp_path):
    result = run_script("seed_demo_data.py", tmp_path / "seed.db")
    assert result.returncode == 1
    assert not (tmp_path / "seed.db").exists()


def test_seed_refuses_in_production(tmp_path):
    result = run_script("seed_demo_data.py", tmp_path / "prod.db", "--yes", ENVIRONMENT="production")
    assert result.returncode == 1
    assert "production" in result.stderr.lower()


def test_seed_creates_demo_data_once(tmp_path):
    db_file = tmp_path / "seed.db"
    first = run_script("seed_demo_data.py", db_file, "--yes")
    assert first.returncode == 0, first.stderr
    assert count(db_file, "users") == 3
    assert count(db_file, "assets") == 5
    assert count(db_file, "tickets") == 5
    assert count(db_file, "notifications") > 0
    second = run_script("seed_demo_data.py", db_file, "--yes")
    assert second.returncode == 0 and "already present" in second.stdout
    assert count(db_file, "tickets") == 5


def test_seed_password_can_be_overridden(tmp_path):
    db_file = tmp_path / "seed.db"
    result = run_script("seed_demo_data.py", db_file, "--yes", DEMO_PASSWORD="Another-Passw0rd-5")
    assert result.returncode == 0 and "Another-Passw0rd-5" in result.stdout


def test_create_admin_script(tmp_path):
    db_file = tmp_path / "admin.db"
    ok = run_script("create_admin.py", db_file, "--username", "Root_Admin", "--display-name", "Root", INFRADESK_ADMIN_PASSWORD="Strong-Passw0rd-3")
    assert ok.returncode == 0, ok.stderr
    connection = sqlite3.connect(db_file)
    role, password_hash = connection.execute("SELECT role, password_hash FROM users WHERE username='root_admin'").fetchone()
    connection.close()
    assert role == "ADMIN" and password_hash.startswith("$argon2")
    duplicate = run_script("create_admin.py", db_file, "--username", "root_admin", "--display-name", "Again", INFRADESK_ADMIN_PASSWORD="Strong-Passw0rd-3")
    assert duplicate.returncode == 1
    weak = run_script("create_admin.py", db_file, "--username", "other", "--display-name", "Other", INFRADESK_ADMIN_PASSWORD="weak")
    assert weak.returncode == 1


# ---------------------------------------------------------- backup/restore


@pytest.fixture
def demo_db(tmp_path):
    db_file = tmp_path / "live.db"
    assert run_script("seed_demo_data.py", db_file, "--yes").returncode == 0
    return db_file


def test_backup_creates_valid_copy(demo_db, tmp_path):
    target = backup_database.backup(demo_db, tmp_path / "backups")
    assert target.is_file() and target.name.startswith("infradesk-")
    assert count(target, "tickets") == 5


def test_backup_of_missing_database_fails_cleanly(tmp_path):
    with pytest.raises(FileNotFoundError):
        backup_database.backup(tmp_path / "nope.db", tmp_path / "out")


def test_restore_replaces_data_and_keeps_safety_copy(demo_db, tmp_path):
    snapshot = backup_database.backup(demo_db, tmp_path / "backups")
    connection = sqlite3.connect(demo_db)
    connection.execute("DELETE FROM notifications")
    connection.execute("DELETE FROM audit_events")
    connection.execute("DELETE FROM ticket_comments")
    connection.execute("DELETE FROM tickets")
    connection.commit()
    connection.close()
    assert count(demo_db, "tickets") == 0

    safety_copy = restore_database.restore(snapshot, demo_db)
    assert count(demo_db, "tickets") == 5
    assert safety_copy is not None and count(safety_copy, "tickets") == 0


def test_restore_rejects_garbage_files(tmp_path):
    bad = tmp_path / "bad.db"
    bad.write_text("this is not a database")
    with pytest.raises(RuntimeError):
        restore_database.verify(bad)
    unrelated = tmp_path / "other.db"
    connection = sqlite3.connect(unrelated)
    connection.execute("CREATE TABLE something (id INTEGER)")
    connection.commit()
    connection.close()
    with pytest.raises(RuntimeError):
        restore_database.verify(unrelated)


def test_restore_command_asks_for_confirmation(demo_db, tmp_path):
    snapshot = backup_database.backup(demo_db, tmp_path / "backups")
    env = {**os.environ, "DATABASE_URL": f"sqlite:///{demo_db}"}
    refused = subprocess.run(
        [sys.executable, str(SCRIPTS / "restore_database.py"), str(snapshot)],
        cwd=BACKEND_DIR, env=env, input="no\n", capture_output=True, text=True,
    )
    assert refused.returncode == 1 and "Cancelled" in refused.stdout
    confirmed = subprocess.run(
        [sys.executable, str(SCRIPTS / "restore_database.py"), str(snapshot)],
        cwd=BACKEND_DIR, env=env, input="restore\n", capture_output=True, text=True,
    )
    assert confirmed.returncode == 0, confirmed.stderr
    assert "restored" in confirmed.stdout.lower()
