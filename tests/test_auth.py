import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

# StaticPool: a plain in-memory sqlite engine hands each new connection a
# separate (empty) database, so the create_all() below wouldn't be visible to
# the sessions the app actually uses. StaticPool keeps everyone on the one
# connection, like a real on-disk database would behave.
_engine = create_engine(
    "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
)
_TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


def _override_get_db():
    db = _TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def _fresh_db():
    Base.metadata.create_all(bind=_engine)
    yield
    Base.metadata.drop_all(bind=_engine)


def _register(name="Test User", email="user@example.com", password="secret123"):
    return client.post("/auth/register", json={"name": name, "email": email, "password": password})


def _login(email="user@example.com", password="secret123"):
    return client.post("/auth/login", json={"email": email, "password": password})


def test_register_creates_a_user():
    response = _register()

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "user@example.com"
    assert body["name"] == "Test User"
    assert "id" in body and "hashed_password" not in body


def test_register_rejects_a_duplicate_email():
    _register()

    response = _register()

    assert response.status_code == 400


def test_login_returns_a_token_for_correct_credentials():
    _register()

    response = _login()

    assert response.status_code == 200
    assert response.json()["access_token"]


def test_login_rejects_an_unknown_email():
    response = _login(email="nobody@example.com")

    assert response.status_code == 401


def test_login_rejects_the_wrong_password():
    _register()

    response = _login(password="wrong-password")

    assert response.status_code == 401


def test_me_rejects_a_missing_token():
    response = client.get("/auth/me")

    assert response.status_code == 401  # HTTPBearer's own rejection when no Authorization header is sent


def test_me_rejects_a_garbage_token():
    response = client.get("/auth/me", headers={"Authorization": "Bearer not-a-real-token"})

    assert response.status_code == 401


def test_me_returns_the_current_user_for_a_valid_token():
    _register()
    token = _login().json()["access_token"]

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["email"] == "user@example.com"
