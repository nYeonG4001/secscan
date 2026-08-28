import pytest
from sqlalchemy.exc import IntegrityError

from app.core.security import hash_password
from app.models.analysis import Analysis
from app.models.project import Project
from app.models.user import User
from app.schemas.analysis import AnalysisAdminOut, AnalysisUserOut


def create_user(db_session, *, email: str, role: str = "ADMIN") -> User:
    user = User(email=email, password_hash=hash_password("password"), role=role)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def create_project(db_session, *, name: str, created_by: int, target_languages=None) -> Project:
    project = Project(name=name, created_by=created_by, target_languages=target_languages)
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


def test_analysis_can_be_created_with_all_new_fields(db_session):
    admin = create_user(db_session, email="admin@secscan.io")
    project = create_project(db_session, name="분석 필드 테스트", created_by=admin.id)

    analysis = Analysis(
        project_id=project.id,
        executed_by=admin.id,
        engine="semgrep",
        analyzed_languages=["JAVA", "PYTHON"],
        source_snapshot_location="/var/secscan/snapshots/1",
        status="FAILED",
        error_code="ENGINE_ERROR",
        error_message="semgrep exited with code 1",
        execution_log="engine diagnostic",
        summary={"total_findings": 3},
    )
    db_session.add(analysis)
    db_session.commit()
    db_session.refresh(analysis)

    assert analysis.engine == "semgrep"
    assert analysis.analyzed_languages == ["JAVA", "PYTHON"]
    assert analysis.source_snapshot_location == "/var/secscan/snapshots/1"
    assert analysis.error_code == "ENGINE_ERROR"
    assert analysis.error_message == "semgrep exited with code 1"
    assert analysis.execution_log == "engine diagnostic"
    assert analysis.summary == {"total_findings": 3}


def test_analysis_status_constraint_rejects_invalid_value(db_session):
    admin = create_user(db_session, email="admin@secscan.io")
    project = create_project(db_session, name="상태 제약 테스트", created_by=admin.id)

    analysis = Analysis(project_id=project.id, executed_by=admin.id, status="CANCELLED")
    db_session.add(analysis)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


@pytest.mark.parametrize("status", ["PENDING", "RUNNING", "COMPLETED", "FAILED"])
def test_analysis_status_constraint_accepts_all_allowed_values(db_session, status):
    admin = create_user(db_session, email="admin@secscan.io")
    project = create_project(db_session, name=f"허용 상태 {status}", created_by=admin.id)

    analysis = Analysis(project_id=project.id, executed_by=admin.id, status=status)
    db_session.add(analysis)
    db_session.commit()
    db_session.refresh(analysis)

    assert analysis.status == status


@pytest.mark.parametrize(("first", "second"), [("PENDING", "RUNNING"), ("PENDING", "PENDING")])
def test_only_one_active_analysis_per_project_is_allowed(db_session, first, second):
    admin = create_user(db_session, email="admin@secscan.io")
    project = create_project(db_session, name="동시 실행 제한 테스트", created_by=admin.id)

    db_session.add(Analysis(project_id=project.id, executed_by=admin.id, status=first))
    db_session.commit()

    db_session.add(Analysis(project_id=project.id, executed_by=admin.id, status=second))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_completed_and_failed_analyses_do_not_block_new_active_analysis(db_session):
    admin = create_user(db_session, email="admin@secscan.io")
    project = create_project(db_session, name="종료 상태 허용 테스트", created_by=admin.id)

    db_session.add_all(
        [
            Analysis(project_id=project.id, executed_by=admin.id, status="COMPLETED"),
            Analysis(project_id=project.id, executed_by=admin.id, status="FAILED"),
        ]
    )
    db_session.commit()

    db_session.add(Analysis(project_id=project.id, executed_by=admin.id, status="PENDING"))
    db_session.commit()

    analyses = db_session.query(Analysis).filter(Analysis.project_id == project.id).all()
    assert len(analyses) == 3


def test_different_projects_can_each_have_an_active_analysis(db_session):
    admin = create_user(db_session, email="admin@secscan.io")
    project_a = create_project(db_session, name="프로젝트 A", created_by=admin.id)
    project_b = create_project(db_session, name="프로젝트 B", created_by=admin.id)

    db_session.add_all(
        [
            Analysis(project_id=project_a.id, executed_by=admin.id, status="PENDING"),
            Analysis(project_id=project_b.id, executed_by=admin.id, status="RUNNING"),
        ]
    )
    db_session.commit()

    assert db_session.query(Analysis).count() == 2


def test_analyzed_languages_snapshot_is_independent_of_project_target_languages(db_session):
    admin = create_user(db_session, email="admin@secscan.io")
    project = create_project(
        db_session, name="언어 스냅샷 테스트", created_by=admin.id, target_languages=["JAVA"]
    )

    analysis = Analysis(
        project_id=project.id,
        executed_by=admin.id,
        status="COMPLETED",
        analyzed_languages=["JAVA"],
    )
    db_session.add(analysis)
    db_session.commit()
    db_session.refresh(analysis)

    project.target_languages = ["PYTHON", "JAVASCRIPT"]
    db_session.commit()
    db_session.refresh(analysis)

    assert analysis.analyzed_languages == ["JAVA"]


def test_analysis_out_schemas_never_expose_source_snapshot_location():
    assert "source_snapshot_location" not in AnalysisUserOut.model_fields
    assert "source_snapshot_location" not in AnalysisAdminOut.model_fields


def test_analysis_admin_out_schema_includes_new_execution_fields():
    fields = AnalysisAdminOut.model_fields
    assert {"engine", "analyzed_languages", "error_code", "execution_log", "summary"} <= set(fields)
