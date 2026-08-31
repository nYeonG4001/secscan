import io
import zipfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, get_db
from app.core.deps import get_source_workspace, get_upload_locks, require_admin, require_csrf
from app.core.security import hash_password
from app.main import app
from app.models.analysis import Analysis
from app.models.project import Project
from app.models.user import User
from app.services.project_upload_lock import ProjectUploadLocks
from app.services.source_workspace import SourceWorkspace


def make_archive(entries, *, compression=zipfile.ZIP_DEFLATED) -> io.BytesIO:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=compression) as zf:
        for name, content in entries:
            if isinstance(content, str):
                content = content.encode()
            zf.writestr(name, content)
    buf.seek(0)
    return buf


def create_user(db_session: Session, *, email: str, role: str) -> User:
    user = User(email=email, password_hash=hash_password("correct-password"), role=role)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def login(client, email: str) -> str:
    response = client.post(
        "/auth/login", json={"email": email, "password": "correct-password"}
    )
    assert response.status_code == 200
    return client.cookies.get("secscan_csrf")


def auth_headers(token: str) -> dict:
    return {"X-CSRF-Token": token}


def create_project_via_api(client, token: str, name: str = "테스트 프로젝트") -> dict:
    resp = client.post("/projects/", json={"name": name}, headers=auth_headers(token))
    assert resp.status_code == 200
    return resp.json()


def upload_zip(client, project_id: int, archive: io.BytesIO, token: str):
    return client.put(
        f"/projects/{project_id}/source",
        files={"file": ("source.zip", archive, "application/zip")},
        headers=auth_headers(token),
    )


@pytest.fixture
def upload_workspace(tmp_path):
    return SourceWorkspace(tmp_path / "storage")


@pytest.fixture
def upload_locks():
    return ProjectUploadLocks()


@pytest.fixture
def upload_client(db_session, upload_workspace, upload_locks):
    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_source_workspace] = lambda: upload_workspace
    app.dependency_overrides[get_upload_locks] = lambda: upload_locks

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# ---------- ADMIN success ----------


def test_admin_uploads_valid_source_with_csrf(upload_client, db_session, upload_workspace):
    admin = create_user(db_session, email="admin@secscan.io", role="ADMIN")
    token = login(upload_client, admin.email)
    project = create_project_via_api(upload_client, token)

    archive = make_archive([("src/Main.java", "class Main {}")])
    response = upload_zip(upload_client, project["id"], archive, token)

    assert response.status_code == 200
    body = response.json()
    assert body["project_id"] == project["id"]
    assert body["source_status"] == "REGISTERED"
    assert body["target_languages"] == ["JAVA"]
    assert set(body.keys()) == {"project_id", "source_status", "target_languages"}


# ---------- Auth / CSRF rejection ----------


def test_unauthenticated_upload_returns_401(upload_client, db_session):
    admin = create_user(db_session, email="admin@secscan.io", role="ADMIN")
    token = login(upload_client, admin.email)
    project = create_project_via_api(upload_client, token)

    upload_client.cookies.clear()
    archive = make_archive([("app.py", "print('hello')")])
    response = upload_client.put(
        f"/projects/{project['id']}/source",
        files={"file": ("source.zip", archive, "application/zip")},
    )

    assert response.status_code == 401


def test_user_upload_returns_403(upload_client, db_session):
    admin = create_user(db_session, email="admin@secscan.io", role="ADMIN")
    user = create_user(db_session, email="user@secscan.io", role="USER")
    admin_token = login(upload_client, admin.email)
    project = create_project_via_api(upload_client, admin_token)

    upload_client.cookies.clear()
    user_token = login(upload_client, user.email)

    archive = make_archive([("app.py", "print('hello')")])
    response = upload_zip(upload_client, project["id"], archive, user_token)

    assert response.status_code == 403


def test_missing_csrf_returns_403(upload_client, db_session):
    admin = create_user(db_session, email="admin@secscan.io", role="ADMIN")
    login(upload_client, admin.email)
    token = upload_client.cookies.get("secscan_csrf")
    project = create_project_via_api(upload_client, token)

    archive = make_archive([("app.py", "print('hello')")])
    response = upload_client.put(
        f"/projects/{project['id']}/source",
        files={"file": ("source.zip", archive, "application/zip")},
    )

    assert response.status_code == 403


def test_invalid_csrf_returns_403(upload_client, db_session):
    admin = create_user(db_session, email="admin@secscan.io", role="ADMIN")
    login(upload_client, admin.email)
    token = upload_client.cookies.get("secscan_csrf")
    project = create_project_via_api(upload_client, token)

    archive = make_archive([("app.py", "print('hello')")])
    response = upload_client.put(
        f"/projects/{project['id']}/source",
        files={"file": ("source.zip", archive, "application/zip")},
        headers={"X-CSRF-Token": "wrong-csrf-token"},
    )

    assert response.status_code == 403


# ---------- Nonexistent project ----------


def test_nonexistent_project_returns_404(upload_client, db_session):
    admin = create_user(db_session, email="admin@secscan.io", role="ADMIN")
    token = login(upload_client, admin.email)

    archive = make_archive([("app.py", "print('hello')")])
    response = upload_zip(upload_client, 99999, archive, token)

    assert response.status_code == 404


# ---------- Active analysis ----------


def test_pending_analysis_returns_409_analysis_active(upload_client, db_session):
    admin = create_user(db_session, email="admin@secscan.io", role="ADMIN")
    token = login(upload_client, admin.email)
    project = create_project_via_api(upload_client, token)

    analysis = Analysis(
        project_id=project["id"], executed_by=admin.id, status="PENDING"
    )
    db_session.add(analysis)
    db_session.commit()

    archive = make_archive([("app.py", "print('hello')")])
    response = upload_zip(upload_client, project["id"], archive, token)

    assert response.status_code == 409
    assert response.json() == {"code": "ANALYSIS_ACTIVE"}


def test_running_analysis_returns_409_analysis_active(upload_client, db_session):
    admin = create_user(db_session, email="admin@secscan.io", role="ADMIN")
    token = login(upload_client, admin.email)
    project = create_project_via_api(upload_client, token)

    analysis = Analysis(
        project_id=project["id"], executed_by=admin.id, status="RUNNING"
    )
    db_session.add(analysis)
    db_session.commit()

    archive = make_archive([("app.py", "print('hello')")])
    response = upload_zip(upload_client, project["id"], archive, token)

    assert response.status_code == 409
    assert response.json() == {"code": "ANALYSIS_ACTIVE"}


# ---------- Concurrent upload ----------


def test_concurrent_upload_returns_409_upload_in_progress(
    upload_client, db_session, upload_locks
):
    admin = create_user(db_session, email="admin@secscan.io", role="ADMIN")
    token = login(upload_client, admin.email)
    project = create_project_via_api(upload_client, token)

    lock = upload_locks._lock_for(project["id"])
    lock.acquire()
    try:
        archive = make_archive([("app.py", "print('hello')")])
        response = upload_zip(upload_client, project["id"], archive, token)
        assert response.status_code == 409
        assert response.json() == {"code": "UPLOAD_IN_PROGRESS"}
    finally:
        lock.release()


# ---------- Language detection ----------


def test_java_detection(upload_client, db_session):
    admin = create_user(db_session, email="admin@secscan.io", role="ADMIN")
    token = login(upload_client, admin.email)
    project = create_project_via_api(upload_client, token)

    archive = make_archive([("App.java", "class App {}")])
    response = upload_zip(upload_client, project["id"], archive, token)

    assert response.status_code == 200
    assert response.json()["target_languages"] == ["JAVA"]

    fresh = SessionLocal()
    p = fresh.get(Project, project["id"])
    assert p.target_languages == ["JAVA"]
    assert p.source_type == "FILE_UPLOAD"
    assert p.source_location is not None
    fresh.close()


def test_javascript_detection(upload_client, db_session):
    admin = create_user(db_session, email="admin@secscan.io", role="ADMIN")
    token = login(upload_client, admin.email)
    project = create_project_via_api(upload_client, token)

    archive = make_archive([("app.js", "console.log('hi')")])
    response = upload_zip(upload_client, project["id"], archive, token)

    assert response.status_code == 200
    assert response.json()["target_languages"] == ["JAVASCRIPT"]

    fresh = SessionLocal()
    p = fresh.get(Project, project["id"])
    assert p.target_languages == ["JAVASCRIPT"]
    fresh.close()


def test_python_detection(upload_client, db_session):
    admin = create_user(db_session, email="admin@secscan.io", role="ADMIN")
    token = login(upload_client, admin.email)
    project = create_project_via_api(upload_client, token)

    archive = make_archive([("app.py", "print('hi')")])
    response = upload_zip(upload_client, project["id"], archive, token)

    assert response.status_code == 200
    assert response.json()["target_languages"] == ["PYTHON"]

    fresh = SessionLocal()
    p = fresh.get(Project, project["id"])
    assert p.target_languages == ["PYTHON"]
    fresh.close()


def test_multi_language_detection(upload_client, db_session):
    admin = create_user(db_session, email="admin@secscan.io", role="ADMIN")
    token = login(upload_client, admin.email)
    project = create_project_via_api(upload_client, token)

    archive = make_archive([
        ("Main.java", "class Main {}"),
        ("app.js", "console.log('hi')"),
        ("script.py", "print('hi')"),
        ("README.md", "docs"),
    ])
    response = upload_zip(upload_client, project["id"], archive, token)

    assert response.status_code == 200
    assert response.json()["target_languages"] == ["JAVA", "JAVASCRIPT", "PYTHON"]

    fresh = SessionLocal()
    p = fresh.get(Project, project["id"])
    assert p.target_languages == ["JAVA", "JAVASCRIPT", "PYTHON"]
    fresh.close()


# ---------- Unsupported source ----------


def test_unsupported_files_only_returns_no_supported_source(upload_client, db_session):
    admin = create_user(db_session, email="admin@secscan.io", role="ADMIN")
    token = login(upload_client, admin.email)
    project = create_project_via_api(upload_client, token)

    archive = make_archive([
        ("README.md", "docs"),
        ("data.csv", "a,b,c"),
        ("config.yaml", "key: value"),
    ])
    response = upload_zip(upload_client, project["id"], archive, token)

    assert response.status_code == 422
    assert response.json() == {"code": "NO_SUPPORTED_SOURCE"}


# ---------- Unsafe archive ----------


def test_path_traversal_returns_unsafe_archive(upload_client, db_session):
    admin = create_user(db_session, email="admin@secscan.io", role="ADMIN")
    token = login(upload_client, admin.email)
    project = create_project_via_api(upload_client, token)

    archive = make_archive([("../escape.py", "print('evil')"), ("safe.py", "print(1)")])
    response = upload_zip(upload_client, project["id"], archive, token)

    assert response.status_code == 422
    assert response.json() == {"code": "UNSAFE_ARCHIVE"}


# ---------- DB commit failure ----------


def test_db_commit_failure_cleans_promoted_and_preserves_location(
    db_session, upload_workspace, upload_locks
):
    admin = create_user(db_session, email="admin@secscan.io", role="ADMIN")

    project = Project(name="DB실패", created_by=admin.id)
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    old_source_id = "a" * 32
    old_location = f"projects/{project.id}/sources/{old_source_id}"
    old_source_dir = (
        upload_workspace.storage_root
        / "projects"
        / str(project.id)
        / "sources"
        / old_source_id
    )
    old_source_dir.mkdir(parents=True)
    (old_source_dir / "old.py").write_text("old source")

    project.source_location = old_location
    db_session.commit()

    def override_get_db():
        db = SessionLocal()

        def failing_commit():
            raise RuntimeError("simulated DB failure")

        db.commit = failing_commit
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_source_workspace] = lambda: upload_workspace
    app.dependency_overrides[get_upload_locks] = lambda: upload_locks
    app.dependency_overrides[require_admin] = lambda: admin
    app.dependency_overrides[require_csrf] = lambda: None

    try:
        archive = make_archive([("Main.java", "class Main {}")])
        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.put(
                f"/projects/{project.id}/source",
                files={"file": ("source.zip", archive, "application/zip")},
            )

        assert response.status_code == 500

        db_session.expire(project)
        db_session.refresh(project)
        assert project.source_location == old_location

        sources_dir = (
            upload_workspace.storage_root / "projects" / str(project.id) / "sources"
        )
        remaining = sorted(d.name for d in sources_dir.iterdir() if d.is_dir())
        assert remaining == [old_source_id]
    finally:
        app.dependency_overrides.clear()


def test_db_commit_failure_preserves_none_location(
    db_session, upload_workspace, upload_locks
):
    admin = create_user(db_session, email="admin@secscan.io", role="ADMIN")

    project = Project(name="DB실패없음", created_by=admin.id)
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    assert project.source_location is None

    def override_get_db():
        db = SessionLocal()

        def failing_commit():
            raise RuntimeError("simulated DB failure")

        db.commit = failing_commit
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_source_workspace] = lambda: upload_workspace
    app.dependency_overrides[get_upload_locks] = lambda: upload_locks
    app.dependency_overrides[require_admin] = lambda: admin
    app.dependency_overrides[require_csrf] = lambda: None

    try:
        archive = make_archive([("Main.java", "class Main {}")])
        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.put(
                f"/projects/{project.id}/source",
                files={"file": ("source.zip", archive, "application/zip")},
            )

        assert response.status_code == 500

        db_session.expire(project)
        db_session.refresh(project)
        assert project.source_location is None
    finally:
        app.dependency_overrides.clear()


# ---------- Response body safety ----------


def test_success_response_contains_no_filesystem_paths(upload_client, db_session):
    admin = create_user(db_session, email="admin@secscan.io", role="ADMIN")
    token = login(upload_client, admin.email)
    project = create_project_via_api(upload_client, token)

    archive = make_archive([("src/Main.java", "class Main {}")])
    response = upload_zip(upload_client, project["id"], archive, token)

    assert response.status_code == 200
    body_text = response.text
    assert "source.zip" not in body_text
    assert "Main.java" not in body_text
    assert "storage" not in body_text
    assert "staging" not in body_text
    assert "projects/" not in body_text


def test_error_response_contains_no_filesystem_paths(upload_client, db_session):
    admin = create_user(db_session, email="admin@secscan.io", role="ADMIN")
    token = login(upload_client, admin.email)
    project = create_project_via_api(upload_client, token)

    archive = make_archive([("../escape.py", "print('evil')"), ("ok.py", "1")])
    response = upload_client.put(
        f"/projects/{project['id']}/source",
        files={"file": ("malicious.zip", archive, "application/zip")},
        headers=auth_headers(token),
    )

    body_text = response.text
    assert "malicious.zip" not in body_text
    assert "escape.py" not in body_text
    assert "storage" not in body_text
    assert "staging" not in body_text


# ---------- No Analysis side-effect ----------


def test_successful_upload_does_not_create_analysis(upload_client, db_session):
    admin = create_user(db_session, email="admin@secscan.io", role="ADMIN")
    token = login(upload_client, admin.email)
    project = create_project_via_api(upload_client, token)

    archive = make_archive([("Main.java", "class Main {}")])
    response = upload_zip(upload_client, project["id"], archive, token)

    assert response.status_code == 200

    fresh = SessionLocal()
    count = (
        fresh.query(Analysis).filter(Analysis.project_id == project["id"]).count()
    )
    assert count == 0
    fresh.close()


# ---------- Startup sweep ----------


def test_startup_sweep_removes_stale_keeps_referenced_and_ignores_legacy_locations(
    tmp_path,
):
    import os
    import time
    from unittest.mock import MagicMock, patch

    workspace = SourceWorkspace(tmp_path / "storage")

    project_id = 42
    referenced_id = "a" * 32
    referenced_dir = (
        workspace.storage_root / "projects" / str(project_id) / "sources" / referenced_id
    )
    referenced_dir.mkdir(parents=True)
    (referenced_dir / "keep.py").write_text("keep")
    source_location = f"projects/{project_id}/sources/{referenced_id}"

    stale_staging = workspace.create_staging_directory()
    (stale_staging / "stale.txt").write_text("stale")

    unreferenced_id = "b" * 32
    unreferenced_dir = (
        workspace.storage_root / "projects" / str(project_id) / "sources" / unreferenced_id
    )
    unreferenced_dir.mkdir(parents=True)
    (unreferenced_dir / "old.py").write_text("old")

    past = time.time() - 90000
    os.utime(stale_staging, (past, past))
    os.utime(unreferenced_dir, (past, past))

    fresh_staging = workspace.create_staging_directory()
    (fresh_staging / "fresh.txt").write_text("fresh")

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.all.return_value = [
        (source_location,),
        ("/legacy/current-source",),
    ]

    with (
        patch("app.main.get_source_workspace", return_value=workspace),
        patch("app.main.SessionLocal", return_value=mock_db),
        patch("app.main.logger.warning") as warning,
    ):
        from app.main import recover_interrupted_analyses_and_sweep_stale_workspaces

        recover_interrupted_analyses_and_sweep_stale_workspaces()

    assert not stale_staging.exists()
    assert not unreferenced_dir.exists()
    assert referenced_dir.exists()
    assert fresh_staging.exists()
    warning.assert_any_call(
        "Startup sweep ignored %d unmanaged project source location(s)",
        1,
    )
