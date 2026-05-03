import uuid


def _email():
    return f"test_{uuid.uuid4().hex[:8]}@example.com"


def test_register_new_user(client):
    resp = client.post("/api/register", json={"email": _email(), "password": "password123"})
    assert resp.status_code == 201


def test_register_duplicate_user_returns_409(client):
    email = _email()
    client.post("/api/register", json={"email": email, "password": "password123"})
    resp = client.post("/api/register", json={"email": email, "password": "password123"})
    assert resp.status_code == 409


def test_login_success_returns_token(client):
    email = _email()
    client.post("/api/register", json={"email": email, "password": "password123"})
    resp = client.post("/api/login", json={"email": email, "password": "password123"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()
    assert resp.json()["token_type"] == "bearer"


def test_login_wrong_password_returns_401(client):
    email = _email()
    client.post("/api/register", json={"email": email, "password": "correctpassword"})
    resp = client.post("/api/login", json={"email": email, "password": "wrongpassword"})
    assert resp.status_code == 401


def test_login_nonexistent_user_returns_401(client):
    resp = client.post("/api/login", json={"email": "nobody@nowhere.com", "password": "anything"})
    assert resp.status_code == 401


def test_protected_route_without_token_returns_401(client):
    resp = client.get("/api/portfolio")
    assert resp.status_code == 401
