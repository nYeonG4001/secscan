import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, get_db
from app.core.security import hash_password
from app.main import app
from app.models.kisa_catalog import KisaCatalog
from app.models.user import User
from app.services.kisa_catalog_seed import KISA_CATALOG_SEED_ROWS, seed_kisa_catalog


@pytest.fixture
def client(db_session: Session):
    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def create_user(db_session, *, email: str, role: str) -> User:
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
    return response.json()["access_token"]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_seed_data_has_exactly_49_items():
    assert len(KISA_CATALOG_SEED_ROWS) == 49
    assert len({row["kisa_code"] for row in KISA_CATALOG_SEED_ROWS}) == 49


def test_seed_inserts_exactly_49_catalog_rows(db_session):
    inserted = seed_kisa_catalog(db_session)

    assert inserted == 49
    assert db_session.query(KisaCatalog).count() == 49


def test_seed_is_idempotent(db_session):
    seed_kisa_catalog(db_session)
    second_run_inserted = seed_kisa_catalog(db_session)

    assert second_run_inserted == 0
    assert db_session.query(KisaCatalog).count() == 49


def test_implementation_status_constraint_rejects_invalid_value(db_session):
    item = KisaCatalog(
        kisa_code="TEST-001",
        category="입력데이터 검증 및 표현",
        name="테스트 항목",
        default_severity="HIGH",
        implementation_status="검토중",
    )
    db_session.add(item)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


@pytest.mark.parametrize("status", ["지원", "부분 지원", "미지원"])
def test_implementation_status_constraint_accepts_three_tier_values(db_session, status):
    item = KisaCatalog(
        kisa_code=f"TEST-{status}",
        category="입력데이터 검증 및 표현",
        name="테스트 항목",
        default_severity="HIGH",
        implementation_status=status,
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)

    assert item.implementation_status == status


def test_admin_can_register_new_catalog_item(client, db_session):
    admin = create_user(db_session, email="admin@secscan.io", role="ADMIN")
    token = login(client, admin.email)

    response = client.post(
        "/catalog/",
        json={
            "kisa_code": "KISA-050",
            "name": "신규 진단 항목",
            "description": "테스트용 신규 항목",
            "criterion_id": "4.1.99",
            "category": "입력데이터 검증 및 표현",
            "item_number": 50,
            "reference_info": "테스트 참조",
            "active": True,
            "default_severity": "MEDIUM",
            "implementation_status": "미지원",
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["kisa_code"] == "KISA-050"
    assert body["implementation_status"] == "미지원"


def test_duplicate_kisa_code_registration_returns_409(client, db_session):
    admin = create_user(db_session, email="admin@secscan.io", role="ADMIN")
    token = login(client, admin.email)
    payload = {
        "kisa_code": "KISA-051",
        "name": "중복 등록 테스트",
        "category": "보안기능",
        "default_severity": "LOW",
    }
    first = client.post("/catalog/", json=payload, headers=auth_headers(token))
    assert first.status_code == 201

    second = client.post("/catalog/", json=payload, headers=auth_headers(token))

    assert second.status_code == 409


def test_non_admin_cannot_register_catalog_item(client, db_session):
    create_user(db_session, email="admin@secscan.io", role="ADMIN")
    user = create_user(db_session, email="user@secscan.io", role="USER")
    token = login(client, user.email)

    response = client.post(
        "/catalog/",
        json={
            "kisa_code": "KISA-052",
            "name": "권한 없는 등록 시도",
            "category": "보안기능",
            "default_severity": "LOW",
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 403


def test_admin_can_update_catalog_item_fields(client, db_session):
    admin = create_user(db_session, email="admin@secscan.io", role="ADMIN")
    token = login(client, admin.email)
    client.post(
        "/catalog/",
        json={
            "kisa_code": "KISA-053",
            "name": "수정 대상 항목",
            "category": "코드오류",
            "default_severity": "LOW",
            "implementation_status": "미지원",
        },
        headers=auth_headers(token),
    )

    response = client.patch(
        "/catalog/KISA-053",
        json={
            "description": "수정된 설명",
            "implementation_status": "지원",
            "active": False,
            "recommendation": "수정된 조치 권고",
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["description"] == "수정된 설명"
    assert body["implementation_status"] == "지원"
    assert body["active"] is False
    assert body["recommendation"] == "수정된 조치 권고"


def test_update_missing_catalog_item_returns_404(client, db_session):
    admin = create_user(db_session, email="admin@secscan.io", role="ADMIN")
    token = login(client, admin.email)

    response = client.patch(
        "/catalog/NO-SUCH-CODE",
        json={"description": "존재하지 않음"},
        headers=auth_headers(token),
    )

    assert response.status_code == 404
