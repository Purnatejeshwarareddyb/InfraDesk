"""Create or upgrade the database schema using Alembic migrations."""

from pathlib import Path

from alembic.config import Config

from alembic import command

BACKEND_DIR = Path(__file__).resolve().parents[2]


def run_migrations(database_url: str | None = None) -> None:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    if database_url:
        config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, "head")


if __name__ == "__main__":
    run_migrations()
    print("Database is up to date.")
