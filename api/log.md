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
