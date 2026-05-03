import os

# Must be set before any module-level imports that read them (auth.py, graph.py)
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-testing-only")
os.environ.setdefault("GROQ_API", "gsk_test_placeholder_not_real")
os.environ.setdefault("NEWS_API", "test_placeholder")

import uuid
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from db.database import get_db
from api.main import app
from api.auth import create_token
from db.models import User

_engine = create_engine(os.getenv("DB_URL"))
_TestingSessionLocal = sessionmaker(autocommit=False, bind=_engine)


@pytest.fixture
def client():
    session = _TestingSessionLocal()

    def _override():
        yield session

    app.dependency_overrides[get_db] = _override
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    session.close()
    app.dependency_overrides.clear()


@pytest.fixture
def unique_email():
    return f"test_{uuid.uuid4().hex[:8]}@example.com"


@pytest.fixture
def auth_headers(client, unique_email):
    client.post("/api/register", json={"email": unique_email, "password": "testpass123"})
    lookup = _TestingSessionLocal()
    user = lookup.query(User).filter(User.email == unique_email).first()
    token = create_token(user.id)
    lookup.close()
    return {"Authorization": f"Bearer {token}"}
