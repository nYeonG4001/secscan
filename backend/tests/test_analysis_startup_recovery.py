from app.core.database import SessionLocal
from app.main import recover_interrupted_analyses_and_sweep_stale_workspaces
from app.models.analysis import Analysis
from app.models.project import Project
from app.models.user import User
from app.services.source_workspace import SourceWorkspace


def test_startup_marks_pending_and_running_analyses_as_interrupted(
    db_session, tmp_path, monkeypatch
):
    admin = User(email="recovery@secscan.io", password_hash="hash", role="ADMIN")
    db_session.add(admin)
    db_session.commit()
    project = Project(name="복구 프로젝트", created_by=admin.id)
    running_project = Project(name="실행 중 복구 프로젝트", created_by=admin.id)
    db_session.add_all([project, running_project])
    db_session.commit()
    db_session.add_all(
        [
            Analysis(project_id=project.id, executed_by=admin.id, status="PENDING"),
            Analysis(project_id=running_project.id, executed_by=admin.id, status="RUNNING"),
        ]
    )
    db_session.commit()
    workspace = SourceWorkspace(tmp_path / "storage")
    monkeypatch.setattr("app.main.get_source_workspace", lambda: workspace)

    recover_interrupted_analyses_and_sweep_stale_workspaces()

    verification_db = SessionLocal()
    try:
        recovered = verification_db.query(Analysis).order_by(Analysis.id).all()
        assert [analysis.status for analysis in recovered] == ["FAILED", "FAILED"]
        assert {analysis.error_code for analysis in recovered} == {"ANALYSIS_INTERRUPTED"}
        assert all(analysis.completed_at for analysis in recovered)
    finally:
        verification_db.close()
