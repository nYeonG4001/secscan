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


def _project_columns() -> set:
    inspector = inspect(engine)
    if "projects" not in inspector.get_table_names():
        return set()
    return {column["name"] for column in inspector.get_columns("projects")}


def _analysis_columns() -> set:
    inspector = inspect(engine)
    if "analyses" not in inspector.get_table_names():
        return set()
    return {column["name"] for column in inspector.get_columns("analyses")}


def _finding_columns() -> set:
    inspector = inspect(engine)
    if "findings" not in inspector.get_table_names():
        return set()
    return {column["name"] for column in inspector.get_columns("findings")}


def _kisa_catalog_columns() -> set:
    inspector = inspect(engine)
    if "kisa_catalog" not in inspector.get_table_names():
        return set()
    return {column["name"] for column in inspector.get_columns("kisa_catalog")}


def _project_access_columns() -> set:
    inspector = inspect(engine)
    if "project_accesses" not in inspector.get_table_names():
        return set()
    return {column["name"] for column in inspector.get_columns("project_accesses")}


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


def test_upgrade_head_adds_project_fields(alembic_config):
    command.upgrade(alembic_config, "head")

    columns = _project_columns()
    assert {
        "description",
        "source_type",
        "target_languages",
        "source_location",
        "updated_at",
    } <= columns


def test_downgrade_to_0002_removes_project_fields(alembic_config):
    command.upgrade(alembic_config, "head")
    command.downgrade(alembic_config, "0002")

    columns = _project_columns()
    assert columns == {"id", "name", "created_by", "created_at"}


def test_project_upgrade_is_reapplicable_after_downgrade(alembic_config):
    command.upgrade(alembic_config, "head")
    command.downgrade(alembic_config, "0002")
    command.upgrade(alembic_config, "head")

    columns = _project_columns()
    assert {
        "description",
        "source_type",
        "target_languages",
        "source_location",
        "updated_at",
    } <= columns


def test_upgrade_head_adds_analysis_execution_fields(alembic_config):
    command.upgrade(alembic_config, "head")

    columns = _analysis_columns()
    assert {
        "engine",
        "analyzed_languages",
        "source_location",
        "source_snapshot_location",
        "source_location",
        "error_code",
        "execution_log",
        "summary",
    } <= columns


def test_upgrade_head_creates_analysis_status_check_constraint(alembic_config):
    command.upgrade(alembic_config, "head")

    inspector = inspect(engine)
    constraint_names = {c["name"] for c in inspector.get_check_constraints("analyses")}
    assert "ck_analyses_status" in constraint_names


def test_upgrade_head_creates_active_analysis_partial_unique_index(alembic_config):
    command.upgrade(alembic_config, "head")

    inspector = inspect(engine)
    index_names = {ix["name"] for ix in inspector.get_indexes("analyses")}
    assert "uq_analyses_project_active" in index_names


def test_downgrade_to_0003_removes_analysis_execution_fields(alembic_config):
    command.upgrade(alembic_config, "head")
    command.downgrade(alembic_config, "0003")

    columns = _analysis_columns()
    assert columns == {
        "id",
        "project_id",
        "executed_by",
        "status",
        "created_at",
        "started_at",
        "completed_at",
        "error_message",
        "raw_result",
    }


def test_analysis_upgrade_is_reapplicable_after_downgrade(alembic_config):
    command.upgrade(alembic_config, "head")
    command.downgrade(alembic_config, "0003")
    command.upgrade(alembic_config, "head")

    columns = _analysis_columns()
    assert {
        "engine",
        "analyzed_languages",
        "source_snapshot_location",
        "source_location",
        "error_code",
        "summary",
    } <= columns


def test_upgrade_head_adds_finding_snapshot_fields(alembic_config):
    command.upgrade(alembic_config, "head")

    columns = _finding_columns()
    assert {"criterion_id", "evidence", "recommendation", "raw_result"} <= columns


def test_upgrade_head_adds_kisa_catalog_snapshot_source_fields(alembic_config):
    command.upgrade(alembic_config, "head")

    columns = _kisa_catalog_columns()
    assert {"criterion_id", "recommendation"} <= columns


def test_downgrade_to_0004_removes_finding_snapshot_fields(alembic_config):
    command.upgrade(alembic_config, "head")
    command.downgrade(alembic_config, "0004")

    finding_columns = _finding_columns()
    assert finding_columns == {
        "id",
        "analysis_id",
        "kisa_code",
        "rule_name",
        "severity",
        "confidence",
        "language",
        "file_path",
        "line",
        "message",
        "code_snippet",
    }

    catalog_columns = _kisa_catalog_columns()
    assert catalog_columns == {
        "kisa_code",
        "category",
        "name",
        "description",
        "default_severity",
        "implementation_status",
        "semgrep_rule_id",
    }


def test_finding_upgrade_is_reapplicable_after_downgrade(alembic_config):
    command.upgrade(alembic_config, "head")
    command.downgrade(alembic_config, "0004")
    command.upgrade(alembic_config, "head")

    columns = _finding_columns()
    assert {"criterion_id", "evidence", "recommendation", "raw_result"} <= columns


def test_upgrade_head_adds_kisa_catalog_full_fields(alembic_config):
    command.upgrade(alembic_config, "head")

    columns = _kisa_catalog_columns()
    assert {"item_number", "reference_info", "active"} <= columns


def test_upgrade_head_creates_kisa_catalog_implementation_status_check_constraint(
    alembic_config,
):
    command.upgrade(alembic_config, "head")

    inspector = inspect(engine)
    constraint_names = {c["name"] for c in inspector.get_check_constraints("kisa_catalog")}
    assert "ck_kisa_catalog_implementation_status" in constraint_names


def test_downgrade_to_0005_removes_kisa_catalog_full_fields(alembic_config):
    command.upgrade(alembic_config, "head")
    command.downgrade(alembic_config, "0005")

    columns = _kisa_catalog_columns()
    assert columns == {
        "kisa_code",
        "criterion_id",
        "category",
        "name",
        "description",
        "default_severity",
        "implementation_status",
        "semgrep_rule_id",
        "recommendation",
    }


def test_kisa_catalog_upgrade_is_reapplicable_after_downgrade(alembic_config):
    command.upgrade(alembic_config, "head")
    command.downgrade(alembic_config, "0005")
    command.upgrade(alembic_config, "head")

    columns = _kisa_catalog_columns()
    assert {"item_number", "reference_info", "active"} <= columns


# --- E1-08 comprehensive audit ---
#
# E1-01~E1-06 each already verified their own slice of the head schema above
# (mostly with `<=`, i.e. "at least these columns exist"). This section is
# the one-time full audit against docs/erd.md that no individual E1-0X task
# owned: exact column sets (`==`, catching columns ERD does NOT list too),
# every ERD-declared foreign key, and every uniqueness/check constraint in
# one place. Audited 2026-08-27: head schema matched erd.md exactly on all
# six tables and all FKs/constraints existed — no migration fixes required.

ERD_COLUMNS = {
    "users": {"id", "email", "password_hash", "role", "active", "created_at", "updated_at"},
    "projects": {
        "id",
        "name",
        "description",
        "source_type",
        "target_languages",
        "source_location",
        "created_by",
        "created_at",
        "updated_at",
    },
    "project_accesses": {"id", "project_id", "user_id", "granted_at", "granted_by"},
    "analyses": {
        "id",
        "project_id",
        "executed_by",
        "engine",
        "analyzed_languages",
        "source_snapshot_location",
        "source_location",
        "status",
        "created_at",
        "started_at",
        "completed_at",
        "error_code",
        "error_message",
        "execution_log",
        "summary",
        "raw_result",
    },
    "findings": {
        "id",
        "analysis_id",
        "kisa_code",
        "criterion_id",
        "rule_name",
        "severity",
        "confidence",
        "language",
        "file_path",
        "line",
        "message",
        "evidence",
        "recommendation",
        "raw_result",
        "code_snippet",
    },
    "kisa_catalog": {
        "kisa_code",
        "criterion_id",
        "item_number",
        "category",
        "name",
        "description",
        "reference_info",
        "default_severity",
        "active",
        "implementation_status",
        "semgrep_rule_id",
        "recommendation",
    },
}


def test_e1_08_audit_head_schema_matches_erd_exactly(alembic_config):
    """E1-08 완료조건 1: head 스키마 6개 테이블이 docs/erd.md와 정확히 일치한다
    (부분집합이 아니라 초과·누락 컬럼이 없는 완전 일치)."""
    command.upgrade(alembic_config, "head")

    actual = {
        "users": _user_columns(),
        "projects": _project_columns(),
        "project_accesses": _project_access_columns(),
        "analyses": _analysis_columns(),
        "findings": _finding_columns(),
        "kisa_catalog": _kisa_catalog_columns(),
    }

    for table, expected_columns in ERD_COLUMNS.items():
        assert actual[table] == expected_columns, f"{table} columns diverge from docs/erd.md"


def test_e1_08_audit_all_foreign_keys_exist(alembic_config):
    """E1-08 완료조건 2: ERD가 정의한 외래키가 head 스키마에 전부 존재한다."""
    command.upgrade(alembic_config, "head")
    inspector = inspect(engine)

    def _fk_pairs(table: str) -> set:
        return {
            (
                tuple(fk["constrained_columns"]),
                fk["referred_table"],
                tuple(fk["referred_columns"]),
            )
            for fk in inspector.get_foreign_keys(table)
        }

    assert (("created_by",), "users", ("id",)) in _fk_pairs("projects")

    project_access_fks = _fk_pairs("project_accesses")
    assert (("project_id",), "projects", ("id",)) in project_access_fks
    assert (("user_id",), "users", ("id",)) in project_access_fks
    assert (("granted_by",), "users", ("id",)) in project_access_fks

    analysis_fks = _fk_pairs("analyses")
    assert (("project_id",), "projects", ("id",)) in analysis_fks
    assert (("executed_by",), "users", ("id",)) in analysis_fks

    finding_fks = _fk_pairs("findings")
    assert (("analysis_id",), "analyses", ("id",)) in finding_fks
    assert (("kisa_code",), "kisa_catalog", ("kisa_code",)) in finding_fks


def test_e1_08_audit_all_uniqueness_and_check_constraints_exist(alembic_config):
    """E1-08 완료조건 3: 중복 방지·체크 제약이 head 스키마에 전부 존재한다."""
    command.upgrade(alembic_config, "head")
    inspector = inspect(engine)

    user_indexes = {ix["name"]: ix for ix in inspector.get_indexes("users")}
    assert user_indexes["ix_users_email"]["unique"] is True

    project_constraints = {c["name"] for c in inspector.get_unique_constraints("projects")}
    assert "uq_projects_name" in project_constraints

    project_access_constraints = {
        c["name"] for c in inspector.get_unique_constraints("project_accesses")
    }
    assert "uq_project_user" in project_access_constraints

    user_checks = {c["name"] for c in inspector.get_check_constraints("users")}
    assert "ck_users_role" in user_checks

    analysis_checks = {c["name"] for c in inspector.get_check_constraints("analyses")}
    assert "ck_analyses_status" in analysis_checks

    analysis_indexes = {ix["name"] for ix in inspector.get_indexes("analyses")}
    assert "uq_analyses_project_active" in analysis_indexes

    catalog_checks = {c["name"] for c in inspector.get_check_constraints("kisa_catalog")}
    assert "ck_kisa_catalog_implementation_status" in catalog_checks
