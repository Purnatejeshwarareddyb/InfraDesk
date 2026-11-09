"""Alembic environment. Works without SECRET_KEY because it only needs the database URL."""

import os
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import create_engine, pool

import app.models  # noqa: F401  (registers all tables on Base.metadata)
from alembic import context
from app.db.base import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata

DEFAULT_URL = "sqlite:///./data/infradesk.db"


def get_url() -> str:
    return config.get_main_option("sqlalchemy.url") or os.getenv("DATABASE_URL") or DEFAULT_URL


def _prepare_sqlite_directory(url: str) -> None:
    prefix = "sqlite:///"
    if url.startswith(prefix) and ":memory:" not in url:
        Path(url[len(prefix):]).parent.mkdir(parents=True, exist_ok=True)


def run_migrations_offline() -> None:
    context.configure(
        url=get_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        render_as_batch=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    url = get_url()
    _prepare_sqlite_directory(url)
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    engine = create_engine(url, poolclass=pool.NullPool, connect_args=connect_args)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, render_as_batch=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
