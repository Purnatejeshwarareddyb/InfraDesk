"""Create the first administrator account.

Usage (from the backend folder):
    python scripts/create_admin.py --username admin --display-name "Lab Admin"
The password is asked for interactively, or read from the INFRADESK_ADMIN_PASSWORD
environment variable (useful for automation). It is never printed.
"""

import argparse
import getpass
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402

from app.core.security import hash_password  # noqa: E402
from app.db.init_db import run_migrations  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.models.enums import EventType, Role  # noqa: E402
from app.models.user import User  # noqa: E402
from app.schemas.user import normalize_username, validate_password_strength  # noqa: E402
from app.services import audit_service  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Create an InfraDesk administrator.")
    parser.add_argument("--username", required=True)
    parser.add_argument("--display-name", required=True)
    args = parser.parse_args()

    try:
        username = normalize_username(args.username)
        password = os.environ.get("INFRADESK_ADMIN_PASSWORD") or getpass.getpass("Password: ")
        if "INFRADESK_ADMIN_PASSWORD" not in os.environ:
            if getpass.getpass("Repeat password: ") != password:
                print("Passwords do not match.", file=sys.stderr)
                return 1
        validate_password_strength(password)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    run_migrations()
    with SessionLocal() as db:
        if db.scalar(select(User).where(User.username == username)):
            print(f"Error: user '{username}' already exists.", file=sys.stderr)
            return 1
        admin = User(
            username=username, display_name=args.display_name.strip(), password_hash=hash_password(password), role=Role.ADMIN
        )
        db.add(admin)
        db.flush()
        audit_service.record(db, event_type=EventType.USER_CREATED, actor_id=admin.id, detail=f"Created user '{username}' with role ADMIN (command line).")
        db.commit()
    print(f"Administrator '{username}' created.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
