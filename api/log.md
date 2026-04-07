# FinSight API — Project Log

## 2026-04-03

### What I did
- Started Phase 3: FastAPI endpoints
- Built api/main.py with one POST endpoint: POST /analyse
- Defined two Pydantic models: AnalyseRequest (ticker: str) and AnalyseResponse (ticker: str, summary: str, timestamp: datetime)
- Imported and invoked graph_app from agent/graph.py inside the route handler
- Renamed compiled LangGraph graph from `app` to `graph_app` in agent/graph.py to avoid naming conflict with FastAPI instance
- Tested endpoint via FastAPI auto-generated Swagger UI at /docs — full pipeline ran successfully end-to-end

### Decisions made
- Pydantic models defined before app instantiation — FastAPI requires the shape to be defined before use in routes
- response_model=AnalyseResponse on the route — FastAPI uses this for automatic response validation and docs generation
- datetime.today() used for timestamp — captures when the result was generated, will be useful for cache freshness checks later
- Skipped cache check for now — PostgreSQL not set up yet, will wire in caching logic in Phase 3
- GET /results/{ticker} endpoint deferred until after PostgreSQL is set up — no point building it without the DB
- Synchronous def used (not async) — acceptable for MVP, flagged as future improvement for production

### Blockers / questions
- PostgreSQL schema + Alembic migrations now complete (see db/log.md 2026-04-07)
- Next: cache-aside logic in POST /analyse + GET /results/{ticker} endpoint

## 2026-04-07

### What I did
- Added get_db() dependency to db/database.py — opens a SessionLocal per request, yields it, closes in finally block
- Updated POST /analyse with cache-aside logic:
  - Queries analysis_results for existing result by ticker
  - If None: runs pipeline, inserts new AnalysisResult row, returns response
  - If stale (age > 1 day): runs pipeline, updates existing row, returns response
  - If fresh: returns cached result directly without running pipeline
- Added GET /results/{ticker} endpoint — read-only lookup, returns AnalyseResponse or 404
- Fixed datetime issues: replaced datetime.UTC (Python 3.11+) with timezone.utc (Python 3.2+)
- Fixed timezone-naive vs timezone-aware subtraction error by changing DateTime column to DateTime(timezone=True)
- Generated and applied Alembic migration for timezone column change
- Tested both endpoints via Swagger UI — cache hit confirmed on second request

### Decisions made
- get_db() uses yield + try/finally — guarantees session closes even if route crashes
- Depends(get_db) injects session via FastAPI dependency injection — keeps route functions clean
- Cache threshold: 1 day — markets move daily, aligns with NewsAPI rate limit constraint
- DateTime(timezone=True) — store timezone-aware timestamps in PostgreSQL to avoid naive/aware comparison errors
- GET /results/{ticker} returns same AnalyseResponse shape as POST /analyse — consistent API contract
- 404 raised via HTTPException if no result exists for ticker

### Blockers / questions
- Phase 3 complete — next: Docker + docker-compose (Phase 4)
