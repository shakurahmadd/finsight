# FinSight — Project Log

---

## Phase 1 — ML: Fine-tuning DistilBERT

### 2026-03-31
- Began Phase 1: fine-tuning DistilBERT for financial sentiment classification
- Discussed LoRA mechanics and why it reduces compute vs full fine-tuning
- Decided on training strategy: LoRA on attention layers, full training on classification head, everything else frozen
- Applied LoRA only to attention layers — classification head trained fully because it has no pretrained knowledge to preserve

### 2026-04-01
- Opened Colab notebook: finsight_sentiment_training.ipynb (T4 GPU runtime)
- Installed dependencies: torch, numpy, transformers, peft, huggingface_hub, datasets, evaluate
- Loaded dataset: zeroshot/twitter-financial-news-sentiment
- Verified splits (train/validation) and features (text, label)
- Confirmed class distribution: negative=1442, positive=1923, neutral=6178
- Computed class weights tensor and moved to GPU
- Tokenised dataset using AutoTokenizer.from_pretrained("distilbert-base-uncased")
- max_length=128 (financial headlines are short), padding="max_length", truncation=True
- Removed "text" column (strings cause batching errors in PyTorch)
- Set dataset format to PyTorch tensors with .set_format(type="torch")
- Loaded DistilBERT for sequence classification: AutoModelForSequenceClassification with num_labels=3
- Applied LoRA via PEFT: LoraConfig with r=8, lora_alpha=16, target_modules=["q_lin", "v_lin"]
- Verified: 740,355 trainable params out of 67,696,134 total (1.09%)
- Created train and validation DataLoaders (batch_size=32, shuffle=True for train)
- Defined AdamW optimiser (lr=2e-5) and CrossEntropyLoss with class weights
- Wrote training and validation loops with per-class F1 using evaluate library
- Ran 3 epochs of training
- Results: train loss 0.591 → 0.575 → 0.557, per-class F1 after epoch 3: negative=0.642, positive=0.706, neutral=0.839
- F1 plateaued across epochs despite loss still decreasing — added validation loss tracking

### 2026-04-02
- Added validation loss tracking and transformers.set_seed(42) for reproducibility
- Re-ran training for 3 epochs with full metrics:
  - Epoch 0: train loss 1.032, val loss 0.815, F1: [neg=0.517, pos=0.577, neu=0.824]
  - Epoch 1: train loss 0.742, val loss 0.588, F1: [neg=0.635, pos=0.638, neu=0.852]
  - Epoch 2: train loss 0.653, val loss 0.610, F1: [neg=0.613, pos=0.645, neu=0.833]
- Set epochs=2: val loss increases at epoch 2 — early overfitting signal, epoch 1 is best checkpoint
- Pushed model and tokenizer to HuggingFace Hub: shakurahmad/finsight-distilbert
- **Phase 1 complete**

---

## Phase 2 — Agent: LangGraph + Tools

### 2026-04-02
- Started Phase 2: LangGraph agent
- Designed AgentState TypedDict in agent/graph.py with fields: ticker, news, stock_data, sentiment, summary
- Created agent/tools.py with three tool functions:
  - get_news: NewsAPI via newsapi-python, returns 10 articles from last 7 days sorted by publishedAt
  - get_stock_data: yfinance, returns dict with history DataFrame and fundamentals (marketCap, trailingPE, sector, longName)
  - analyze_sentiment: loads DistilBERT+LoRA from HuggingFace Hub, tokenizes titles, runs inference
- Built graph.py with four nodes: get_news_node, get_stock_data_node, analyze_sentiment_node, generate_summary_node
- Connected nodes with fixed edges: get_news → get_stock_data → analyze_sentiment → generate_summary
- Added Groq LLM (llama-3.1-8b-instant) loaded once at top of graph.py
- generate_summary_node builds f-string prompt with all state fields and calls llm.invoke()
- Tested end-to-end with app.invoke({"ticker": "AAPL"}) — produced full research summary
- Added __init__.py to agent/ and tests/
- Wrote tests/test_tools.py — all 3 tests passing

**Key decisions:**
- Fixed graph (not ReAct) — V1 is a linear pipeline; V2 will fix this with proper ReAct pattern
- Model loaded once at module level — avoids repeated weight loading on EC2
- Label mapping: 0=Bearish, 1=Bullish, 2=Neutral
- Groq ChatGroq loaded once at module level — same reasoning as sentiment model
- **Phase 2 complete**

---

## Phase 3 — API + DB: FastAPI + PostgreSQL

### 2026-04-03
- Started Phase 3: FastAPI endpoints
- Built api/main.py with POST /analyse endpoint
- Defined Pydantic models: AnalyseRequest (ticker: str) and AnalyseResponse (ticker, summary, timestamp)
- Renamed compiled LangGraph graph from `app` to `graph_app` to avoid naming conflict with FastAPI instance
- Tested endpoint via Swagger UI at /docs — full pipeline ran end-to-end

### 2026-04-07
- Created db/models.py with two SQLAlchemy ORM models: NewsArticle and AnalysisResult
- Installed alembic, ran `alembic init alembic`
- Configured alembic/env.py: load DB_URL from .env, pointed target_metadata at Base.metadata
- Generated and applied first migration: news_articles and analysis_results tables
- Verified tables via psql: analysis_results, news_articles, alembic_version all present
- Added get_db() dependency — opens SessionLocal per request, yields it, closes in finally block
- Updated POST /analyse with cache-aside logic (check → run if stale/missing → store → return)
- Added GET /results/{ticker} endpoint — returns AnalyseResponse or 404
- Fixed datetime issues: replaced datetime.UTC with timezone.utc (Python 3.9 compatible)
- Fixed timezone-naive vs timezone-aware subtraction by changing DateTime column to DateTime(timezone=True)
- Generated and applied second migration for timezone column change
- Tested both endpoints via Swagger UI — cache hit confirmed on second request

**Key decisions:**
- Two separate tables, no foreign key — they serve independent caching purposes
- Cache threshold: 1 day — markets move daily, aligns with NewsAPI rate limit
- DateTime(timezone=True) — store timezone-aware timestamps to avoid naive/aware comparison errors
- Synchronous def used (not async) — acceptable for MVP
- **Phase 3 complete**

---

## Phase 4 — Docker

### 2026-04-07
- Created Dockerfile: python:3.9-slim base image, WORKDIR /app, COPY, pip install, EXPOSE 8000
- --reload flag dropped for Docker (dev-only)
- 0.0.0.0 host required — 127.0.0.1 only accessible from within the container

### 2026-04-08
- Created docker-compose.yml with two services: app and db
- Created entrypoint.sh: runs alembic upgrade head before uvicorn
- Updated Dockerfile CMD to use entrypoint.sh
- Added .dockerignore — reduced build context from 1GB+ to ~5KB
- Fixed POSTGRES_PASSWORD missing — PostgreSQL refused to start without it
- Switched PyTorch to CPU-only install: separate RUN step with --index-url https://download.pytorch.org/whl/cpu
- Added pg_isready loop in entrypoint.sh — waits for PostgreSQL to be ready before running migrations
- Added postgresql-client to Dockerfile (provides pg_isready)
- Full stack verified working end-to-end locally

**Key decisions:**
- pg_isready loop preferred over sleep — sleep is a guess, loop waits exactly as long as needed
- depends_on only waits for container start, not PostgreSQL readiness — loop is required
- CPU PyTorch reduces image size ~10x (2GB → 200MB)
- **Phase 4 complete**

---

## Phase 5 — CI/CD: GitHub Actions

### 2026-04-09
- Created .github/workflows/ci.yml — GitHub Actions CI pipeline
- Added pytest to requirements.txt
- Added NEWS_API as a GitHub repository secret
- CI pipeline passing all 3 tests

**Key decisions:**
- Trigger on every push (`on: push`)
- PostgreSQL spun up as a GitHub Actions service container
- Host is `localhost` in CI (not `db` — no compose network)
- pg_isready loop used to wait for PostgreSQL before running migrations
- DB_URL set in job-level env — safe because it's a throwaway dev credential
- NEWS_API passed via `${{ secrets.NEWS_API }}` — encrypted GitHub repository secret
- **Phase 5 complete**

---

## Phase 6 — Deployment: AWS EC2

### 2026-04-09 / 2026-04-10
- Launched AWS EC2 t3.micro instance (Amazon Linux 2023, free tier)
- Installed Docker, docker-compose v2.24.0, and git on the server
- Cloned repo from GitHub onto the server
- Created .env on the server with secrets (never committed to git)
- Fixed pg_isready missing — added postgresql-client to Dockerfile
- Opened port 8000 in EC2 security group inbound rules
- App fully deployed and accessible at http://13.48.106.201:8000/docs

**Key decisions:**
- t3.micro free tier eligible in eu-north-1 region
- docker-compose v2.24.0 installed manually — v5 required newer buildx not on Amazon Linux
- Port 8000 opened in security group — required for external access
- docker-compose up -d — detached mode keeps app running after SSH session ends
- **V1 MVP complete and deployed**

---

---

## V2 Phase 0 — V1 Fixes

### 2026-04-10
- Fixed Dockerfile layer order: COPY requirements.txt first, run all pip installs, then COPY . /app — dependencies now cached independently of code changes
- Added `restart: unless-stopped` to both services in docker-compose.yml — containers now restart automatically on server reboot
- Redeployed to EC2 — confirmed working

---

## V2 Phase 1 — ReAct Agent Refactor

### 2026-04-10
- Created `v2-phase1` git branch — V2 development isolated from deployed main
- Refactored `agent/graph.py` from linear pipeline to proper ReAct pattern:
  - Replaced `AgentState` TypedDict with `MessagesState` — state is now a single messages list
  - Replaced four node functions with a single `agent_node` that calls `llm_with_tools`
  - Added `ToolNode` to handle tool execution automatically
  - Added `tools_condition` conditional edge — routes to tools or END based on LLM output
  - Added unconditional edge from tools back to agent to close the loop
- Decorated all three tools with `@tool` in `agent/tools.py` — LLM can now request them by name
- Changed `analyze_sentiment` to accept `list[str]` (titles) instead of full article objects — full article objects were too large for Groq to serialize as tool call arguments
- Updated tests to use `.invoke()` and `.invoke({"titles": ...})` — required after `@tool` decoration
- Tested end-to-end: LLM called get_news → extracted titles → called analyze_sentiment → called get_stock_data → produced summary
- All 3 tests passing, CI green on v2-phase1 branch

**Key decisions:**
- Built ReAct pattern manually rather than using `create_react_agent` — DK-CoT in later phases requires customising the agent node, which isn't possible with the pre-built constructor
- `analyze_sentiment` accepts titles not articles — keeps the tool simple and avoids Groq payload size errors
- Branching strategy: each V2 phase on its own branch, merge to main when complete and tested

### 2026-04-11
- Explored edgartools API: `Company(ticker).get_filings(form=...).latest().obj()` returns typed objects per form type
- `TenK` object exposes `management_discussion` and `risk_factors` as plain strings
- `EightK` object exposes `text()` as a callable returning the full filing text
- `Form4` object exposes `market_trades` as a pandas DataFrame with columns: Date, Shares, Price, AcquiredDisposed, TransactionType
- Built `get_sec_filings` tool in `agent/tools.py` — fetches 10-K, 8-K, and Form 4 for a given ticker
- Added `set_identity` at module level — required by edgartools to identify the caller to the SEC API, runs once on import
- Added `get_sec_filings` to tools list in `agent/graph.py` — agent now has 4 tools
- Added `test_sec_filings` to `tests/test_tools.py` — all 4 tests passing

### 2026-04-11 (continued)
- Added three new SQLAlchemy models: `DkKnowledge`, `MacroIndicator`, `SectorMacroMapping`
- Generated and applied Alembic migration — all three tables created in PostgreSQL
- Built `db/seed.py` with idempotency checks (`if count == 0`) for all three tables
- Seeded `dk_knowledge` with 25 rows across 5 sectors (Technology, Financials, Energy, Consumer, Healthcare) — 5 metrics each: pe_ratio, pb_ratio, revenue_growth, profit_margin, debt_to_equity
- Seeded `macro_indicators` with 5 FRED indicators: federal_funds_rate, cpi_inflation, gdp_growth, unemployment_rate, ten_year_treasury
- Seeded `sector_macro_mapping` with 10 rows linking each sector to 2 relevant macro indicators
- Implemented DK-CoT injection in `agent_node` in `agent/graph.py`:
  - Searches messages for ToolMessage containing "sector" (from `get_stock_data` output)
  - Parses JSON content with `json.loads()` to extract sector string
  - Queries `dk_knowledge`, `sector_macro_mapping`, and `macro_indicators` from PostgreSQL
  - Builds system prompt with sector benchmarks and macro indicators
  - Prepends `SystemMessage` to messages before LLM invocation
- Fixed `get_stock_data` to convert DataFrame to `to_dict(orient='records')` — required for JSON serialisation in ToolMessage
- Added type annotations to `get_news`, `get_stock_data`, `get_sec_filings` — required for Groq tool schema validation
- Tested end-to-end: agent reasoning now references sector benchmarks and macro context
- All 4 tests passing

**Key decisions:**
- Direct section extraction from 10-K — `management_discussion` and `risk_factors` truncated to 3000 chars. RAG deferred — targeted section extraction keeps token usage bounded enough for now
- `eight_k` and `form_4` wrapped in `try/except` with graceful fallback — both are event-driven filings that only exist when a material event or insider trade has occurred. Their absence is expected, not an error. 10-K is mandatory annually so it is not wrapped
- `market_trades` DataFrame converted with `to_dict(orient='records')` — returns a list of dicts, one per trade row, which the LLM can read as a list of transactions

---

## V2 Phase 2 — Sentiment Momentum + Scheduled Jobs

### 2026-04-12
- Pre-Phase 2 fixes applied to agent/graph.py: upgraded LLM from llama-3.1-8b-instant to llama-3.3-70b-versatile, replaced global SessionLocal() with per-request session inside agent_node using try/finally pattern
- Added two new SQLAlchemy models: `Watchlist` (ticker primary key) and `SentimentHistory` (composite primary key: ticker + date, sentiment_score Float)
- Generated and applied Alembic migration — both tables created in PostgreSQL
- Built three new FastAPI endpoints:
  - `POST /watchlist` — adds ticker to watchlist, returns 409 on duplicate via IntegrityError catch
  - `DELETE /watchlist/{ticker}` — removes ticker, returns 404 if not found
  - `GET /sentiment/history/{ticker}` — returns last 30 days of sentiment scores ordered by date ascending
- Created `SentimentHistoryResponse` Pydantic model with `model_config = ConfigDict(from_attributes=True)` — required for Pydantic v2 to read SQLAlchemy ORM objects directly
- Tested all three endpoints via Swagger — all working

**Key decisions:**
- `ticker` is the primary key on `Watchlist` — enforces uniqueness at the DB level, `IntegrityError` on duplicate insert maps to 409 Conflict
- 409 over 200 with message — HTTP status codes are machine-readable; a frontend can branch on status code without parsing response text
- `SentimentHistory` composite primary key on `(ticker, date)` — enforces one row per ticker per day at the DB level, enabling idempotent inserts via ON CONFLICT

### 2026-04-13
- Built `api/jobs.py` with two chained nightly jobs: `fetch_and_cache_news` (Job A) and `score_and_store_sentiment` (Job B)
- Job A fetches articles for all watchlisted tickers via NewsAPI, skips articles with null description, stores in `news_articles` table
- Job B reads cached articles, scores with DistilBERT, computes weighted average sentiment, stores one row per ticker in `sentiment_history`
- Job A explicitly calls Job B on completion — chained rather than independently scheduled to ensure articles exist before scoring runs
- Added APScheduler `BackgroundScheduler` to FastAPI via lifespan events — scheduler starts on app startup, shuts down cleanly on app shutdown
- Nightly job scheduled at 1am via `cron` trigger
- Updated `analyze_sentiment` to return confidence alongside label — computes softmax over logits, takes max probability per title as confidence score
- Fixed `analyze_sentiment` to return `conf.item()` not the full tensor — required for JSON serialisation
- Fixed `score_and_store_sentiment` to cast `weighted_average` to `float()` — PostgreSQL rejects numpy float64
- Fixed article filter to 7-day window — matches NewsAPI fetch window and enables recency decay to be meaningful
- Added null timestamp guard in scoring loop — skips articles with no timestamp rather than crashing
- Tested full pipeline end-to-end: AAPL sentiment score -0.146 stored in sentiment_history

**Key decisions:**
- Weighted average formula: `weight = confidence × e^(-λ × days_old)`, `score = sum(label × weight) / sum(weight)`. λ=0.5 starting hyperparameter — higher values decay older articles faster, lower values smooth the signal. Can be tuned once real data accumulates
- Sentiment label mapping: Bearish=-1, Neutral=0, Bullish=1 — maps categorical model output to a continuous score range [-1, 1]
- Per-ticker `try/except` with `db.rollback()` and `continue` — one failing ticker never kills the whole job, and rollback keeps the session clean for subsequent tickers
- Job A and Job B use manual `SessionLocal()` in `try/finally` — FastAPI `Depends` injection is not available outside endpoint context
