import uuid


def _ticker():
    # Unique 5-char ticker that won't conflict with seeded watchlist tickers
    return "T" + uuid.uuid4().hex[:4].upper()


def test_add_ticker_to_watchlist(client):
    resp = client.post("/api/watchlist", json={"ticker": _ticker()})
    assert resp.status_code == 201


def test_add_duplicate_ticker_returns_409(client):
    ticker = _ticker()
    client.post("/api/watchlist", json={"ticker": ticker})
    resp = client.post("/api/watchlist", json={"ticker": ticker})
    assert resp.status_code == 409


def test_get_watchlist_contains_added_ticker(client):
    ticker = _ticker()
    client.post("/api/watchlist", json={"ticker": ticker})
    resp = client.get("/api/watchlist")
    assert resp.status_code == 200
    tickers = [item["ticker"] for item in resp.json()]
    assert ticker in tickers


def test_delete_ticker_from_watchlist(client):
    ticker = _ticker()
    client.post("/api/watchlist", json={"ticker": ticker})
    resp = client.delete(f"/api/watchlist/{ticker}")
    assert resp.status_code == 200


def test_delete_nonexistent_ticker_returns_404(client):
    resp = client.delete("/api/watchlist/DEFINITELYNOTREAL999")
    assert resp.status_code == 404
