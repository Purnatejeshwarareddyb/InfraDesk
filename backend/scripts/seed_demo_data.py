"""Load clearly fictional DEMO data (users, assets and tickets).

This is an explicit, opt-in command. It refuses to run unless --yes is given and it
refuses to run when ENVIRONMENT=production unless --force-production is also given.
All names below are invented. The demo password is shown on screen so that the demo
can be explained; change it (or set DEMO_PASSWORD) if the machine is shared.

Usage (from the backend folder):
    python scripts/seed_demo_data.py --yes
"""

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import func, select  # noqa: E402

from app.core.security import hash_password  # noqa: E402
from app.db.init_db import run_migrations  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.models.asset import Asset  # noqa: E402
from app.models.enums import AssetStatus, AssetType, Category, Priority, Role, TicketStatus  # noqa: E402
from app.models.user import User  # noqa: E402
from app.schemas.ticket import TicketCreate  # noqa: E402
from app.services import ticket_service  # noqa: E402

DEFAULT_DEMO_PASSWORD = "Demo-Passw0rd!"

USERS = [
    ("demo_admin", "Demo Administrator", Role.ADMIN),
    ("worker_asha", "Asha Verma (demo)", Role.WORKER),
    ("worker_ravi", "Ravi Kumar (demo)", Role.WORKER),
]

ASSETS = [
    ("LAB1-PC-001", "Lab 1 Desktop 01", AssetType.COMPUTER, "Computer Lab 1", "DEMO-SN-1001"),
    ("LAB1-PC-002", "Lab 1 Desktop 02", AssetType.COMPUTER, "Computer Lab 1", "DEMO-SN-1002"),
    ("LAB2-PRN-001", "Lab 2 Laser Printer", AssetType.PRINTER, "Computer Lab 2", "DEMO-SN-2001"),
    ("NET-SW-001", "Core Network Switch", AssetType.NETWORK, "Server Room", "DEMO-SN-3001"),
    ("LAP-017", "Staff Laptop 17", AssetType.LAPTOP, "Staff Room", "DEMO-SN-4017"),
]

TICKETS = [
    ("Printer in Lab 2 prints blank pages", "Every job comes out blank. Toner was replaced last week.", Category.PRINTER, Priority.MEDIUM, "LAB2-PRN-001"),
    ("Desktop 02 in Lab 1 will not boot", "Shows a black screen after the BIOS logo. Fan is running.", Category.HARDWARE, Priority.HIGH, "LAB1-PC-002"),
    ("WiFi drops every hour in Staff Room", "Connection is lost for about two minutes at the start of every hour.", Category.NETWORK, Priority.URGENT, None),
    ("Cannot log in to the lab portal", "The password is rejected after the weekend reset.", Category.ACCOUNT_ACCESS, Priority.LOW, None),
    ("Install Python 3.12 on Lab 1 desktops", "Needed for the programming course starting next week.", Category.SOFTWARE, Priority.MEDIUM, "LAB1-PC-001"),
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Load fictional demo data into InfraDesk.")
    parser.add_argument("--yes", action="store_true", help="confirm that demo data should be created")
    parser.add_argument("--force-production", action="store_true")
    args = parser.parse_args()

    if not args.yes:
        print("This command creates fictional demo users, assets and tickets. Run it again with --yes to continue.")
        return 1
    if os.environ.get("ENVIRONMENT", "development").lower() == "production" and not args.force_production:
        print("Refusing to create demo data while ENVIRONMENT=production.", file=sys.stderr)
        return 1

    password = os.environ.get("DEMO_PASSWORD", DEFAULT_DEMO_PASSWORD)
    run_migrations()

    with SessionLocal() as db:
        if db.scalar(select(func.count(User.id)).where(User.username == "demo_admin")):
            print("Demo data is already present; nothing to do.")
            return 0

        users = {}
        for username, display_name, role in USERS:
            user = User(username=username, display_name=display_name, password_hash=hash_password(password), role=role)
            db.add(user)
            users[username] = user
        assets = {}
        for tag, name, kind, location, serial in ASSETS:
            asset = Asset(asset_tag=tag, name=name, asset_type=kind, location=location, serial_number=serial, status=AssetStatus.ACTIVE)
            db.add(asset)
            assets[tag] = asset
        db.commit()

        admin, asha, ravi = users["demo_admin"], users["worker_asha"], users["worker_ravi"]
        created = []
        for index, (title, description, category, priority, asset_tag) in enumerate(TICKETS):
            reporter = asha if index % 2 == 0 else ravi
            data = TicketCreate(
                title=title,
                description=description,
                category=category,
                priority=priority,
                related_asset_id=assets[asset_tag].id if asset_tag else None,
            )
            created.append(ticket_service.create_ticket(db, reporter, data))

        # Move a few tickets through the real workflow so that dashboards have variety.
        ticket_service.assign_ticket(db, admin, created[0], asha.id)
        ticket_service.assign_ticket(db, admin, created[1], ravi.id)
        ticket_service.transition_ticket(db, ravi, created[1], TicketStatus.IN_PROGRESS)
        ticket_service.assign_ticket(db, admin, created[2], asha.id)
        ticket_service.transition_ticket(db, asha, created[2], TicketStatus.IN_PROGRESS)
        ticket_service.transition_ticket(db, asha, created[2], TicketStatus.RESOLVED, "Replaced the access point firmware.")
        ticket_service.add_comment(db, admin, created[1], "Please check the RAM modules first.")

    print("Demo data created.")
    print("Demo accounts (LOCAL DEMO ONLY, change the password before sharing this machine):")
    for username, _name, role in USERS:
        print(f"  {username:<12} role={role.value:<7} password={password}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
