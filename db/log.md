# FinSight DB — Project Log

## 2026-04-07

### What I did
- Created db/models.py with two SQLAlchemy ORM models: NewsArticle and AnalysisResult
- Both models inherit from Base (defined in db/database.py)
- Installed alembic and ran `alembic init alembic` from project root
- Configured alembic/env.py:
  - Load DB_URL from .env via dotenv (not hardcoded in alembic.ini — security risk)
  - Pointed target_metadata at Base.metadata
  - Imported db.models so Alembic can detect all registered tables
  - Replaced engine_from_config with create_engine(url) in run_migrations_online()
- Ran `alembic revision --autogenerate -m "create news_articles and analysis_results tables"`
  - Alembic detected both tables and generated migration script in alembic/versions/
- Ran `alembic upgrade head` — both tables created in PostgreSQL finsight database
- Verified tables exist via psql: analysis_results, news_articles, alembic_version all present

### Decisions made
- Two separate tables, no foreign key between them — they serve independent caching purposes (news caches API calls, analysis caches pipeline output) and the cache-aside logic doesn't need to join them
- Auto-incrementing integer primary key (id) on both tables — standard approach, SQLAlchemy handles it automatically
- nullable=False on ticker, title, content, summary — invalid to store a row without these fields
- timestamp default=lambda: datetime.now(datetime.UTC) — UTC always for storage regardless of local timezone; lambda used so the function is called per-insert not once at import time
- Staleness threshold will be calculated at query time (now - timestamp > threshold) rather than stored as a separate column
- Cache threshold to be decided: 1 day is a reasonable starting point given markets move daily and NewsAPI rate limit is 100 req/day

### Blockers / questions
- Next: implement cache-aside logic in POST /analyse and add GET /results/{ticker} endpoint
