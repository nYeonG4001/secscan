import pytest
from sqlalchemy.exc import IntegrityError

from app.core.security import hash_password
from app.models.project import Project, ProjectAccess
from app.models.user import User


def create_user(db_session, *, email: str, role: str = "USER") -> User:
    user = User(email=email, password_hash=hash_password("password"), role=role)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def create_project(db_session, *, name: str, created_by: int) -> Project:
    project = Project(name=name, created_by=created_by)
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


def test_project_access_is_stored_in_its_own_table(db_session):
    admin = create_user(db_session, email="admin@secscan.io", role="ADMIN")
    member = create_user(db_session, email="member@secscan.io", role="USER")
    project = create_project(db_session, name="접근권한 테스트 프로젝트", created_by=admin.id)

    access = ProjectAccess(project_id=project.id, user_id=member.id, granted_by=admin.id)
    db_session.add(access)
    db_session.commit()
    db_session.refresh(access)

    assert ProjectAccess.__tablename__ == "project_accesses"
    assert access.id is not None
    assert access.granted_at is not None


def test_project_access_relationships_load_project_user_and_grantor(db_session):
    admin = create_user(db_session, email="admin@secscan.io", role="ADMIN")
    member = create_user(db_session, email="member@secscan.io", role="USER")
    project = create_project(db_session, name="관계 로드 테스트", created_by=admin.id)

    access = ProjectAccess(project_id=project.id, user_id=member.id, granted_by=admin.id)
    db_session.add(access)
    db_session.commit()
    db_session.refresh(access)

    assert access.project.id == project.id
    assert access.project.name == "관계 로드 테스트"
    assert access.user.id == member.id
    assert access.user.email == "member@secscan.io"
    assert access.grantor.id == admin.id
    assert access.grantor.role == "ADMIN"
    assert access in project.accesses
    assert access in member.project_accesses


def test_duplicate_project_user_access_is_rejected(db_session):
    admin = create_user(db_session, email="admin@secscan.io", role="ADMIN")
    member = create_user(db_session, email="member@secscan.io", role="USER")
    project = create_project(db_session, name="중복 권한 테스트", created_by=admin.id)

    first = ProjectAccess(project_id=project.id, user_id=member.id, granted_by=admin.id)
    db_session.add(first)
    db_session.commit()

    duplicate = ProjectAccess(project_id=project.id, user_id=member.id, granted_by=admin.id)
    db_session.add(duplicate)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_same_user_can_access_multiple_distinct_projects(db_session):
    admin = create_user(db_session, email="admin@secscan.io", role="ADMIN")
    member = create_user(db_session, email="member@secscan.io", role="USER")
    project_a = create_project(db_session, name="프로젝트 A", created_by=admin.id)
    project_b = create_project(db_session, name="프로젝트 B", created_by=admin.id)

    db_session.add_all(
        [
            ProjectAccess(project_id=project_a.id, user_id=member.id, granted_by=admin.id),
            ProjectAccess(project_id=project_b.id, user_id=member.id, granted_by=admin.id),
        ]
    )
    db_session.commit()

    assert len(member.project_accesses) == 2


def test_same_project_can_grant_multiple_distinct_users(db_session):
    admin = create_user(db_session, email="admin@secscan.io", role="ADMIN")
    member_a = create_user(db_session, email="member-a@secscan.io", role="USER")
    member_b = create_user(db_session, email="member-b@secscan.io", role="USER")
    project = create_project(db_session, name="다중 사용자 프로젝트", created_by=admin.id)

    db_session.add_all(
        [
            ProjectAccess(project_id=project.id, user_id=member_a.id, granted_by=admin.id),
            ProjectAccess(project_id=project.id, user_id=member_b.id, granted_by=admin.id),
        ]
    )
    db_session.commit()

    assert len(project.accesses) == 2
