"""Alembic upgrade/downgrade verification against the real test database.

Unlike the other tests in this suite, this module drives Alembic directly
instead of relying on ``Base.metadata.create_all()`` — the ORM's create_all
would silently mask a broken migration (e.g. a column the model expects but
the migration never adds).
"""

import os
from pathlib import Path

import pytest
from sqlalchemy import inspect, text

from alembic import command
from alembic.config import Config
from app.core.database import Base, engine

BACKEND_DIR = Path(__file__).resolve().parent.parent


def _alembic_config() -> Config:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    config.set_main_option("sqlalchemy.url", os.environ["DATABASE_URL"])
    return config


def _user_columns() -> set:
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return set()
    return {column["name"] for column in inspector.get_columns("users")}


def _reset_schema() -> None:
    # Base.metadata.drop_all() only knows about ORM-mapped tables — it leaves
    # Alembic's own alembic_version bookkeeping table behind. If that survives,
    # the next command.upgrade(..., "head") sees "already at head" and no-ops
    # even though the real tables were just dropped. Wipe both so each test
    # starts from a state Alembic and the DB agree is truly empty.
    Base.metadata.drop_all(bind=engine)
    with engine.begin() as connection:
        connection.execute(text("DROP TABLE IF EXISTS alembic_version"))


@pytest.fixture
def alembic_config():
    _reset_schema()
    config = _alembic_config()
    try:
        yield config
    finally:
        # Leave the DB in the same state every other test's db_session
        # fixture expects: full head schema, ready for its own drop_all/create_all.
        _reset_schema()
        command.upgrade(config, "head")


def test_upgrade_head_adds_user_account_state_columns(alembic_config):
    command.upgrade(alembic_config, "head")

    columns = _user_columns()
    assert {"active", "created_at", "updated_at"} <= columns


def test_downgrade_to_0001_removes_account_state_columns(alembic_config):
    command.upgrade(alembic_config, "head")
    command.downgrade(alembic_config, "0001")

    columns = _user_columns()
    assert columns == {"id", "email", "password_hash", "role"}


def test_upgrade_is_reapplicable_after_downgrade(alembic_config):
    command.upgrade(alembic_config, "head")
    command.downgrade(alembic_config, "0001")
    command.upgrade(alembic_config, "head")

    columns = _user_columns()
    assert {"active", "created_at", "updated_at"} <= columns


def test_downgrade_to_base_drops_all_tables(alembic_config):
    command.upgrade(alembic_config, "head")
    command.downgrade(alembic_config, "base")

    inspector = inspect(engine)
    # alembic_version is Alembic's own bookkeeping table, not app schema —
    # it stays behind (empty) even at the base revision.
    app_tables = set(inspector.get_table_names()) - {"alembic_version"}
    assert app_tables == set()
