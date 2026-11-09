"""Restore the SQLite database from a backup file. DESTRUCTIVE: it replaces the current data.

Safety measures:
  * the backup is checked with PRAGMA integrity_check before anything is replaced
  * the current database is first copied to a timestamped *.before-restore file
  * the command asks for confirmation unless --yes is given

Stop the application before restoring so that nothing writes to the file during the copy.

Usage (from the backend folder):
    python scripts/restore_database.py backups/infradesk-YYYYMMDDTHHMMSS...db [--db data/infradesk.db]
"""

import argparse
import os
import shutil
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path

DEFAULT_URL = "sqlite:///./data/infradesk.db"


def database_path_from_url(url: str) -> Path:
    prefix = "sqlite:///"
    if not url.startswith(prefix):
        raise SystemExit("Only SQLite databases can be restored with this script.")
    return Path(url[len(prefix):])


def verify(backup_file: Path) -> None:
    if not backup_file.is_file():
        raise FileNotFoundError(f"Backup file not found: {backup_file}")
    connection = sqlite3.connect(f"file:{backup_file}?mode=ro", uri=True)
    try:
        result = connection.execute("PRAGMA integrity_check").fetchone()[0]
        tables = {r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    except sqlite3.DatabaseError as exc:
        raise RuntimeError(f"Not a valid SQLite database: {exc}") from exc
    finally:
        connection.close()
    if result != "ok":
        raise RuntimeError(f"Backup failed the integrity check: {result}")
    if not {"users", "tickets"} <= tables:
        raise RuntimeError("The file does not look like an InfraDesk database (users/tickets tables missing).")


def restore(backup_file: Path, db_path: Path) -> Path | None:
    """Replace db_path with backup_file. Returns the safety copy of the old database, if any."""
    verify(backup_file)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    safety_copy = None
    if db_path.exists():
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
        safety_copy = db_path.with_name(f"{db_path.name}.before-restore-{stamp}")
        shutil.copy2(db_path, safety_copy)
    for suffix in ("-wal", "-shm"):  # leftovers of the old database must not be replayed
        Path(str(db_path) + suffix).unlink(missing_ok=True)
    shutil.copy2(backup_file, db_path)
    return safety_copy


def main() -> int:
    parser = argparse.ArgumentParser(description="Restore the InfraDesk SQLite database from a backup.")
    parser.add_argument("backup", type=Path)
    parser.add_argument("--db", type=Path, default=None, help="database file (default: from DATABASE_URL)")
    parser.add_argument("--yes", action="store_true", help="do not ask for confirmation")
    args = parser.parse_args()
    db_path = args.db or database_path_from_url(os.environ.get("DATABASE_URL", DEFAULT_URL))

    try:
        verify(args.backup)
    except (FileNotFoundError, RuntimeError) as exc:
        print(f"Restore aborted: {exc}", file=sys.stderr)
        return 1

    if not args.yes:
        print(f"This will REPLACE the database at {db_path} with {args.backup}.")
        print("Make sure the application is stopped. The current database is saved first.")
        if input("Type 'restore' to continue: ").strip().lower() != "restore":
            print("Cancelled. Nothing was changed.")
            return 1
    safety_copy = restore(args.backup, db_path)
    if safety_copy:
        print(f"Previous database saved as {safety_copy}")
    print(f"Database restored from {args.backup}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
