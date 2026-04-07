# FinSight API — Reference Notes

## FastAPI

### What it is
A Python web framework for building REST APIs. Faster than Flask, async-native, and built around Python type hints.

### Key advantages over Flask
- Automatic request validation via Pydantic — invalid input returns 422 automatically
- Auto-generated interactive docs at /docs (Swagger UI)
- Type hints are central — no separate schema definitions needed

### How to run
```bash
uvicorn api.main:app --reload
```
- `api.main` — module path (folder.file)
- `app` — the FastAPI instance name
- `--reload` — auto-restarts on code changes (dev only)

---

## Pydantic

### What it is
A Python data validation library. You define classes that inherit from BaseModel with typed fields. FastAPI uses these to parse and validate request/response data automatically.

### Pattern
```python
from pydantic import BaseModel

class MyModel(BaseModel):
    field: type
```

### In FastAPI
- Request body model → passed as a typed parameter to the route function
- Response model → passed as `response_model=` on the route decorator

---

## REST API Concepts

### HTTP methods
- GET — fetch data
- POST — send data / trigger an action
- PUT — update data
- DELETE — delete data

### Route naming convention
- Use nouns not verbs — the HTTP method describes the action
- Good: `POST /analyse`, Bad: `POST /run-analysis`

### Path parameters vs request body
- Path parameter: `GET /results/{ticker}` — ticker is in the URL
- Request body: `POST /analyse` with `{"ticker": "AAPL"}` — data sent in the body

---

## Caching (Cache-Aside Pattern)

### What it is
Store computed results so you don't recompute on repeated requests.

### Flow for /analyse
1. Check DB — does a recent result for this ticker exist?
2. If yes → return cached result (fast, cheap)
3. If no → run full pipeline → store result → return it

### Why it matters for FinSight
- NewsAPI: 100 requests/day free tier
- EC2 t2.micro: 1GB RAM — running DistilBERT + Groq is expensive
- Pipeline takes 10-30 seconds — cache avoids repeat cost

---

## Uvicorn

### What it is
An ASGI web server that runs FastAPI apps and handles incoming HTTP requests. FastAPI defines the logic; uvicorn handles the networking layer.

---

## FastAPI Dependency Injection

### What it is
A way to declare shared logic (like DB sessions) that FastAPI runs automatically before each request.

### Pattern
```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/route")
def my_route(db: Session = Depends(get_db)):
    # db is ready to use
```

### Why yield not return
`yield` pauses the function — FastAPI runs the route, then resumes `get_db()` to hit `finally: db.close()`. Guarantees the session always closes even if the route crashes.

---

## Path Parameters

### Pattern
```python
@app.get("/results/{ticker}")
def get_results(ticker: str, ...):
```
FastAPI extracts `ticker` from the URL automatically when the parameter name matches the path placeholder.

### vs Request Body
- Path parameter: data in the URL — used for GET endpoints identifying a resource
- Request body: data in POST body — used when sending structured input

---

## HTTPException

### Pattern
```python
from fastapi import HTTPException

raise HTTPException(status_code=404, detail="Not found")
```
FastAPI catches this and returns the appropriate HTTP error response automatically.

---

## Datetime Timezone Notes

### timezone-naive vs timezone-aware
- Naive: `datetime(2026, 4, 7, 12, 0)` — no timezone info
- Aware: `datetime(2026, 4, 7, 12, 0, tzinfo=timezone.utc)` — knows it's UTC
- Python refuses to subtract naive from aware — always use aware datetimes

### Correct pattern (Python 3.9 compatible)
```python
from datetime import datetime, timezone
datetime.now(timezone.utc)  # aware, works on Python 3.2+
```

### SQLAlchemy column
Use `DateTime(timezone=True)` to store timezone-aware timestamps in PostgreSQL.
