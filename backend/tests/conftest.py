import os

import pytest
from sqlalchemy.engine.url import make_url

test_database_url = os.environ.get("TEST_DATABASE_URL")
if not test_database_url:
    raise RuntimeError(
        "TEST_DATABASE_URL must be set to a dedicated PostgreSQL test database "
        "whose name ends with '_test'."
    )

try:
    parsed_test_database_url = make_url(test_database_url)
except Exception as exc:
    raise RuntimeError("TEST_DATABASE_URL must be a valid SQLAlchemy database URL.") from exc

if parsed_test_database_url.get_backend_name() != "postgresql":
    raise RuntimeError("TEST_DATABASE_URL must use a PostgreSQL URL.")

if not parsed_test_database_url.database or not parsed_test_database_url.database.endswith("_test"):
    raise RuntimeError("TEST_DATABASE_URL database name must end with '_test'.")

os.environ["DATABASE_URL"] = test_database_url
os.environ.setdefault("SECRET_KEY", "test-secret-key")

from app import models  # noqa: E402, F401
from app.core.database import Base, SessionLocal, engine  # noqa: E402


@pytest.fixture
def db_session():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
