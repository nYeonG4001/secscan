import pytest
from sqlalchemy.exc import IntegrityError

from app.core.security import hash_password
from app.models.user import User


def test_user_defaults_include_active_and_timestamps(db_session):
    user = User(email="user@secscan.io", password_hash=hash_password("password"))
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert user.active is True
    assert user.role == "USER"
    assert user.created_at is not None
    assert user.updated_at is not None


def test_user_role_constraint_accepts_only_admin_and_user(db_session):
    admin = User(
        email="admin@secscan.io",
        password_hash=hash_password("password"),
        role="ADMIN",
    )
    user = User(
        email="user@secscan.io",
        password_hash=hash_password("password"),
        role="USER",
    )
    db_session.add_all([admin, user])
    db_session.commit()

    invalid_user = User(
        email="invalid-role@secscan.io",
        password_hash=hash_password("password"),
        role="OPERATOR",
    )
    db_session.add(invalid_user)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_user_model_has_no_plaintext_password_column():
    column_names = {column.name for column in User.__table__.columns}

    assert "password" not in column_names
    assert "password_hash" in column_names
