import uuid


def _name():
    return f"portfolio_{uuid.uuid4().hex[:8]}"


def test_create_portfolio(client, auth_headers):
    name = _name()
    resp = client.post("/api/portfolio", json={"name": name}, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "id" in data
    assert data["name"] == name


def test_create_duplicate_portfolio_name_returns_409(client, auth_headers):
    name = _name()
    client.post("/api/portfolio", json={"name": name}, headers=auth_headers)
    resp = client.post("/api/portfolio", json={"name": name}, headers=auth_headers)
    assert resp.status_code == 409


def test_get_portfolios_returns_list(client, auth_headers):
    name = _name()
    client.post("/api/portfolio", json={"name": name}, headers=auth_headers)
    resp = client.get("/api/portfolio", headers=auth_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    assert any(p["name"] == name for p in resp.json())


def test_delete_portfolio(client, auth_headers):
    portfolio_id = client.post("/api/portfolio", json={"name": _name()}, headers=auth_headers).json()["id"]
    resp = client.delete(f"/api/portfolio/{portfolio_id}", headers=auth_headers)
    assert resp.status_code == 200


def test_delete_nonexistent_portfolio_returns_404(client, auth_headers):
    resp = client.delete("/api/portfolio/99999", headers=auth_headers)
    assert resp.status_code == 404


def test_portfolio_endpoint_requires_auth(client):
    resp = client.get("/api/portfolio")
    assert resp.status_code == 401


def test_add_holding(client, auth_headers):
    portfolio_id = client.post("/api/portfolio", json={"name": _name()}, headers=auth_headers).json()["id"]
    resp = client.post(f"/api/holdings/{portfolio_id}", json={"ticker": "AAPL", "shares": 10.0}, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["ticker"] == "AAPL"
    assert data["shares"] == 10.0


def test_get_holdings(client, auth_headers):
    portfolio_id = client.post("/api/portfolio", json={"name": _name()}, headers=auth_headers).json()["id"]
    client.post(f"/api/holdings/{portfolio_id}", json={"ticker": "MSFT", "shares": 5.0}, headers=auth_headers)
    resp = client.get(f"/api/holdings/{portfolio_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert any(h["ticker"] == "MSFT" for h in resp.json())


def test_delete_holding(client, auth_headers):
    portfolio_id = client.post("/api/portfolio", json={"name": _name()}, headers=auth_headers).json()["id"]
    holding_id = client.post(f"/api/holdings/{portfolio_id}", json={"ticker": "GOOGL", "shares": 3.0}, headers=auth_headers).json()["id"]
    resp = client.delete(f"/api/holdings/{portfolio_id}/{holding_id}", headers=auth_headers)
    assert resp.status_code == 200


def test_add_holding_to_nonexistent_portfolio_returns_404(client, auth_headers):
    resp = client.post("/api/holdings/99999", json={"ticker": "AAPL", "shares": 1.0}, headers=auth_headers)
    assert resp.status_code == 404


def test_portfolio_summary_empty_portfolio_returns_no_data(client, auth_headers):
    portfolio_id = client.post("/api/portfolio", json={"name": _name()}, headers=auth_headers).json()["id"]
    resp = client.get(f"/api/portfolio/{portfolio_id}/summary", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == "No sentiment data is available"
