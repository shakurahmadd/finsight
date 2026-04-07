# FinSight DB — Reference Notes

## SQLAlchemy ORM

### What it is
An Object Relational Mapper — lets you define database tables as Python classes and write queries in Python instead of raw SQL. SQLAlchemy translates Python into SQL behind the scenes.

### Core components
- `create_engine(url)` — connects to the database
- `sessionmaker` — factory for database sessions (used to run queries)
- `declarative_base()` — creates the Base class that all models inherit from
- `Base.metadata` — registry of all tables defined across all models that inherit from Base

### Model pattern
```python
class MyModel(Base):
    __tablename__ = "my_table"

    id = Column(Integer, primary_key=True)
    field = Column(String, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(datetime.UTC))
```

### Key concepts
- Every model class inherits from Base — this registers it in Base.metadata automatically
- Column types: Integer, String (short text), Text (long text), DateTime
- nullable=False — database rejects rows missing this field
- primary_key=True — auto-incrementing unique ID, implicitly not null
- default=lambda: datetime.now(datetime.UTC) — lambda called per-insert, not once at import time

### Why UTC for timestamps
Always store in UTC regardless of server or user location. Markets, EC2, and DB may be in different timezones. UTC has no daylight saving ambiguity. Convert to local time at the presentation layer only.

---

## Alembic

### What it is
Version control for database schemas. Each migration is a versioned script that can be applied (upgrade) or rolled back (downgrade). Prevents data loss when modifying live databases.

### Why not Base.metadata.create_all()
`create_all()` only creates tables that don't exist — it cannot alter existing tables. Alembic generates precise ALTER TABLE statements for safe schema evolution in production.

### Key commands
```bash
alembic init alembic                          # initialise alembic folder
alembic revision --autogenerate -m "message"  # generate migration from model changes
alembic upgrade head                          # apply all pending migrations
alembic downgrade -1                          # roll back last migration
alembic downgrade base                        # roll back everything
```

### How autogenerate works
1. Connects to the database
2. Reads current schema from the live DB
3. Compares against Base.metadata (your models)
4. Generates upgrade() and downgrade() functions for the diff

### alembic_version table
Alembic creates this table automatically. It tracks which migrations have been applied so it never runs the same migration twice.

### env.py configuration
Two things must be set:
1. `url` — database connection string, loaded from .env (never hardcode in alembic.ini)
2. `target_metadata = Base.metadata` — tells Alembic what the schema should look like

Models must be imported in env.py so Base.metadata is populated before autogenerate runs.

---

## Cache-Aside Pattern (DB side)

### news_articles table
- Purpose: avoid burning NewsAPI rate limit (100 req/day) fetching the same ticker twice
- Staleness check: `now - timestamp > threshold` at query time

### analysis_results table
- Purpose: avoid re-running the full pipeline (slow + expensive) for repeated ticker queries
- Staleness check: same threshold approach

### Threshold justification
Markets move daily. A 1-day threshold means results stay fresh for one trading day and are invalidated overnight — aligns with NewsAPI rate limits and market data cadence.
