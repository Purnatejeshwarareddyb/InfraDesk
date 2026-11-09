"""Make a consistent, timestamped backup of the SQLite database.

Uses SQLite's online backup API, so it is safe to run while the application is running.

Usage (from the backend folder):
    python scripts/backup_database.py [--db data/infradesk.db] [--out backups]
"""

import argparse
import os
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path

DEFAULT_URL = "sqlite:///./data/infradesk.db"


def database_path_from_url(url: str) -> Path:
    prefix = "sqlite:///"
    if not url.startswith(prefix):
        raise SystemExit("Only SQLite databases can be backed up with this script.")
    return Path(url[len(prefix):])


def backup(db_path: Path, out_dir: Path) -> Path:
    if not db_path.is_file():
        raise FileNotFoundError(f"Database file not found: {db_path}")
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    target = out_dir / f"infradesk-{stamp}.db"
    source = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        destination = sqlite3.connect(target)
        try:
            source.backup(destination)
        finally:
            destination.close()
    finally:
        source.close()
    check = sqlite3.connect(target)
    try:
        result = check.execute("PRAGMA integrity_check").fetchone()[0]
    finally:
        check.close()
    if result != "ok":
        target.unlink(missing_ok=True)
        raise RuntimeError(f"Backup failed the integrity check: {result}")
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description="Back up the InfraDesk SQLite database.")
    parser.add_argument("--db", type=Path, default=None, help="database file (default: from DATABASE_URL)")
    parser.add_argument("--out", type=Path, default=Path("backups"), help="backup folder (default: ./backups)")
    args = parser.parse_args()
    db_path = args.db or database_path_from_url(os.environ.get("DATABASE_URL", DEFAULT_URL))
    try:
        target = backup(db_path, args.out)
    except (FileNotFoundError, RuntimeError, sqlite3.Error) as exc:
        print(f"Backup failed: {exc}", file=sys.stderr)
        return 1
    print(f"Backup written to {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
