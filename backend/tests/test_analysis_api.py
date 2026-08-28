import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, get_db
from app.core.deps import get_analysis_executor, get_source_workspace, get_upload_locks
from app.core.security import hash_password
from app.main import app
from app.models.analysis import Analysis
from app.models.project import Project, ProjectAccess
from app.models.user import User
from app.services.project_upload_lock import ProjectUploadLocks
from app.services.source_workspace import SourceWorkspace


class RecordingExecutor:
    def __init__(self):
        self.submitted: list[int] = []

    def submit(self, analysis_id: int) -> None:
        self.submitted.append(analysis_id)


@pytest.fixture
def api_context(db_session: Session, tmp_path):
    workspace = SourceWorkspace(tmp_path / "storage")
    executor = RecordingExecutor()
    locks = ProjectUploadLocks()

    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_source_workspace] = lambda: workspace
    app.dependency_overrides[get_upload_locks] = lambda: locks
    app.dependency_overrides[get_analysis_executor] = lambda: executor
    with TestClient(app) as client:
        yield client, workspace, executor, locks
    app.dependency_overrides.clear()


def _user(db_session, email: str, role: str) -> User:
    user = User(email=email, password_hash=hash_password("correct-password"), role=role)
    db_session.add(user)
    db_session.commit()
    return user


def _login(client, email: str) -> dict[str, str]:
    response = client.post("/auth/login", json={"email": email, "password": "correct-password"})
    assert response.status_code == 200
    return {"X-CSRF-Token": client.cookies.get("secscan_csrf")}


def _registered_project(db_session, workspace, admin: User) -> Project:
    project = Project(name="E4 API 프로젝트", created_by=admin.id, target_languages=["PYTHON"])
    db_session.add(project)
    db_session.commit()
    staging = workspace.create_staging_directory()
    (staging / "app.py").write_text("print('safe')")
    project.source_location = workspace.promote_staging_directory(project.id, staging)
    db_session.commit()
    return project


def test_admin_creates_pending_analysis_and_captures_source(api_context, db_session):
    client, workspace, executor, _ = api_context
    admin = _user(db_session, "analysis-admin@secscan.io", "ADMIN")
    project = _registered_project(db_session, workspace, admin)

    response = client.post(
        "/analyses/", json={"project_id": project.id}, headers=_login(client, admin.email)
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "PENDING"
    assert "source_location" not in body
    assert "source_snapshot_location" not in body
    assert executor.submitted == [body["id"]]
    analysis = db_session.get(Analysis, body["id"])
    assert analysis.source_location == project.source_location
    assert analysis.source_snapshot_location == f"analyses/{analysis.id}/source"


def test_analysis_api_enforces_auth_access_and_active_conflicts(api_context, db_session):
    client, workspace, _, locks = api_context
    admin = _user(db_session, "analysis-auth-admin@secscan.io", "ADMIN")
    member = _user(db_session, "analysis-member@secscan.io", "USER")
    project = _registered_project(db_session, workspace, admin)

    assert client.post("/analyses/", json={"project_id": project.id}).status_code == 401
    assert (
        client.post(
            "/analyses/", json={"project_id": project.id}, headers=_login(client, member.email)
        ).status_code
        == 403
    )
    admin_headers = _login(client, admin.email)
    first = client.post("/analyses/", json={"project_id": project.id}, headers=admin_headers)
    assert first.status_code == 201
    duplicate = client.post("/analyses/", json={"project_id": project.id}, headers=admin_headers)
    assert duplicate.status_code == 409
    assert duplicate.json() == {
        "code": "ANALYSIS_ACTIVE",
        "analysis_id": first.json()["id"],
        "status": "PENDING",
    }
    missing = client.post("/analyses/", json={"project_id": 9999}, headers=admin_headers)
    assert missing.status_code == 404

    terminal = db_session.get(Analysis, first.json()["id"])
    terminal.status = "FAILED"
    db_session.commit()
    with locks.acquire(project.id):
        uploading = client.post(
            "/analyses/", json={"project_id": project.id}, headers=admin_headers
        )
    assert uploading.status_code == 409
    assert uploading.json() == {"code": "SOURCE_UPLOAD_IN_PROGRESS"}


def test_user_never_receives_admin_execution_fields(api_context, db_session):
    client, workspace, _, _ = api_context
    admin = _user(db_session, "analysis-fields-admin@secscan.io", "ADMIN")
    member = _user(db_session, "analysis-fields-member@secscan.io", "USER")
    project = _registered_project(db_session, workspace, admin)
    db_session.add(ProjectAccess(project_id=project.id, user_id=member.id, granted_by=admin.id))
    analysis = Analysis(
        project_id=project.id,
        executed_by=admin.id,
        status="FAILED",
        error_code="ENGINE_EXECUTION_FAILED",
        error_message="private detail",
        execution_log="private log",
        raw_result={"internal": "metadata"},
    )
    db_session.add(analysis)
    db_session.commit()

    user_response = client.get(f"/analyses/{analysis.id}", headers=_login(client, member.email))

    assert user_response.status_code == 200
    assert {"error_code", "error_message", "execution_log", "raw_result"}.isdisjoint(
        user_response.json()
    )
