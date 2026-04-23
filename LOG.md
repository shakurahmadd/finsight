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

---

## V2 Phase 3 — Anomaly Detection (Isolation Forest)

### 2026-04-13
- Added `AnomalyFeatures` SQLAlchemy model to `db/models.py` — composite primary key on `(ticker, date)`, five signal columns: `sentiment_score`, `earnings_surprise`, `insider_volume`, `filing_frequency`, `price_volatility`, plus nullable `anomaly_score` and `is_anomaly` for when the model runs
- Generated Alembic migration `e404aaea36e6_add_anomaly_features_table.py` and applied it
- Built `build_feature_vectors()` (Job C) in `api/jobs.py` — computes all five signals per watchlisted ticker and stores one row per ticker per day in `anomaly_features`
- Chained Job C to end of Job B — runs after sentiment scores are guaranteed to exist
- Signal sources:
  - `price_volatility`: `yf.Ticker.history(period='30d')` → daily returns via `pct_change()` → `std()`
  - `sentiment_score`: read directly from `sentiment_history` table for today's date
  - `earnings_surprise`: `yf.Ticker.earnings_history.iloc[0]` → `(epsActual - epsEstimate) / |epsEstimate| * 100`
  - `insider_volume`: `get_sec_filings` Form 4 → sum of `Shares` across all trades, defaults to 0 if no Form 4
  - `filing_frequency`: `edgar.Company.get_filings()` filtered to last 30 days for 10-K, 8-K, and Form 4 → total count
- Skips ticker entirely if no sentiment score exists for today — incomplete feature vectors not stored
- Wrapped `price_volatility` and `earnings_surprise` in `float()` — pandas/numpy scalar types rejected by PostgreSQL

**Key decisions:**
- Isolation Forest training deferred — no historical sentiment data exists yet. Nightly job will accumulate real feature vectors; model will be trained once sufficient data is available. Training on incomplete data would undermine the signal quality
- `insider_volume = 0` when no Form 4 exists — absence of insider trading is not an anomaly, defaulting to 0 is correct rather than skipping the ticker
- Filing frequency counts all three form types (10-K, 8-K, Form 4) — a spike in any filing type is a meaningful signal
- `date_filed` filter uses `f"{cutoff}:"` string format — edgartools requires date range as `"YYYY-MM-DD:"` not a datetime object

---

## V2 Phase 5 — User Auth + Portfolio System

### 2026-04-14
- Added `passlib[bcrypt]`, `python-jose`, and `bcrypt==4.0.1` to requirements.txt — pinned bcrypt to 4.0.1 due to passlib incompatibility with bcrypt 4.x (`__about__` attribute missing)
- Created `api/auth.py` with full JWT auth utilities:
  - `CryptContext(schemes=["bcrypt_sha256"])` — bcrypt_sha256 pre-hashes with SHA256, removing the 72-byte password limit
  - `hash_password(password)` — hashes plain password for storage
  - `verify_password(plain, hashed)` — uses `pwd_context.verify()`, extracts salt from stored hash internally
  - `create_token(user_id)` — encodes `{"user_id": id, "exp": now + 24h}` signed with HS256
  - `decode_token(token)` — decodes and verifies token, raises 401 on `JWTError`
  - `OAuth2PasswordBearer(tokenUrl="/login")` — extracts bearer token from Authorization header
  - `get_current_user(token, db)` — decodes token, looks up user in DB, returns user object or raises 401
- Added `User` SQLAlchemy model to `db/models.py` — `id`, `email` (UNIQUE), `hashed_password`, `created_at`
- Generated and applied Alembic migration for `users` table
- Added `POST /register` — checks for duplicate email (409), hashes password, stores user, returns 201
- Added `POST /login` — looks up by email, verifies password with `pwd_context.verify`, returns `{"access_token": token, "token_type": "bearer"}`
- Added `Portfolio` and `Holdings` SQLAlchemy models with ForeignKey CASCADE relationships
- Generated and applied Alembic migration for `portfolios` and `holdings` tables
- Added 6 portfolio/holdings endpoints — all protected with `Depends(get_current_user)`:
  - `POST /portfolio` — creates portfolio linked to current user
  - `GET /portfolio` — returns all portfolios for current user
  - `DELETE /portfolio/{portfolio_id}` — 404 if not found, 403 if not owner
  - `POST /holdings/{portfolio_id}` — adds holding, 404 if portfolio not found, 403 if not owner
  - `GET /holdings/{portfolio_id}` — returns all holdings, 404/403 checks
  - `DELETE /holdings/{portfolio_id}/{holdings_id}` — 404/403 checks, deletes holding
- Tested register, duplicate register (409), login, token return — all working

**Key decisions:**
- JWT is stateless — token not stored in DB, verified by decoding on each request
- `get_current_user` as a FastAPI dependency runs before the route — raises 401 automatically if token missing or invalid, two-for-one auth enforcement and user object retrieval
- 401 for unauthenticated (no/invalid token), 403 for unauthorised (valid token, wrong user's resource)
- Weight percentage computed dynamically from shares — never stored. Known limitation: share count ignores stock price, so positions are not truly value-weighted. Upgrade path: `shares × current_price` once price fetching is added
- Portfolio aggregation (weighted average sentiment) deferred to next session

### 2026-04-15
- Fixed Swagger auth — switched from `OAuth2PasswordBearer` to `HTTPBearer` in `auth.py`. `OAuth2PasswordBearer` sends credentials as form data but `/login` expects JSON — incompatible. `HTTPBearer` gives a simple token input field in Swagger instead
- Updated `get_current_user` to extract token via `credentials.credentials` from `HTTPAuthorizationCredentials`
- Added duplicate portfolio name check to `POST /portfolio` — queries by `user_id` + `name`, returns 409 if match found
- Tested all 6 portfolio/holdings endpoints end-to-end — all working correctly
- Committed Phase 5 work to `v2-phase5` branch`

### 2026-04-15 (continued)
- Added `GET /portfolio/{portfolio_id}/summary` — computes weighted average sentiment across all holdings using share count as weight. Pulls most recent sentiment score per ticker from `sentiment_history`. Returns `"No sentiment data is available"` string if no sentiment exists for any holding
- Added `GET /news/{ticker}` — returns last 10 cached news articles for a ticker ordered by timestamp desc, 404 if none
- Added `GET /earnings/{ticker}` — fetches earnings history from yfinance, computes EPS surprise percentage, returns list of dicts with date, eps_actual, eps_estimate, surprise
- Added `GET /filings/{ticker}` — proxies `get_sec_filings` tool response directly to the client
- Added `CORSMiddleware` to FastAPI — allows requests from `http://localhost:5173` (Vite dev server). Without this, all browser requests from the React frontend are blocked by the browser's same-origin policy
- Fixed `POST /analyse` invocation: updated from `{'ticker': ...}` to `{'messages': [HumanMessage(content=...)]}` and updated result extraction to `result['messages'][-1].content` — required after ReAct refactor to MessagesState
- Added `apscheduler` to `requirements.txt` — was missing, causing container crash-loop on EC2

---

## V2 Phase 3 — EC2 Redeploy

### 2026-04-16
- Redeployed to EC2 after adding `apscheduler` to requirements.txt — container was crash-looping with `ModuleNotFoundError: No module named 'apscheduler'`
- Ran `docker-compose down`, `docker-compose up --build -d` — full reinstall triggered because requirements.txt changed
- Added 23 watchlist tickers via bash script hitting `POST /watchlist`: AAPL, MSFT, GOOGL, NVDA, META (Technology), JPM, BAC, GS, MS, V (Financials), AMZN, TSLA, NKE, MCD, WMT (Consumer), XOM, CVX, BP, SHEL (Energy), JNJ, PFE, UNH, ABBV (Healthcare)
- 23 tickers × 1 NewsAPI request per nightly job = 23 requests per night, leaving 77 requests for daytime use
- Removed `frontend/.vite/` from git tracking — Vite dependency cache was accidentally committed. Added `.vite` to `frontend/.gitignore` and ran `git rm -r --cached frontend/.vite`

---

## V2 Phase 6 — React Frontend

### 2026-04-16
- Initialised React frontend with Vite: `npm create vite@latest frontend -- --template react`
- Installed dependencies: `@mui/material`, `@emotion/react`, `@emotion/styled`, `@mui/x-data-grid`, `recharts`, `react-router-dom`, `axios`
- Built `TickerResearchPage.jsx` — main research page with search bar, 5 API calls on submit, renders 5 components. State: `ticker`, `isLoading`, `analysisResult`, `sentimentHistory`, `newsFeed`, `earningsTable`, `secFilingCard`
- Built `SentimentChart.jsx` — Recharts `LineChart` wrapped in MUI `Card`. X-axis formatted to show date strings. Renders 30-day sentiment trend
- Built `NewsFeed.jsx` — MUI `Card` list of articles. MUI `Chip` for sentiment label: Bullish=green, Bearish=red, Neutral=grey
- Built `EarningsTable.jsx` — MUI `DataGrid` with columns: date, epsActual, epsEstimate, surprise (%)
- Built `SecFilingsCard.jsx` — MUI `Card` with truncated MD&A, risk factors, 8-K summary, insider trades list
- Configured React Router with `BrowserRouter` in `main.jsx`, routes defined in `App.jsx`
- Started designing Login/Register page — needs 4 state variables: `email`, `password`, `isLoading`, `error`

### 2026-04-17
- Built `AuthPage.jsx` — combined login/register page with toggle between modes
- State variables: `isLogin`, `email`, `password`, `isLoading`, `error`, `confirmPassword`
- `handleSubmit` — async, calls `/login` or `/register` based on `isLogin`. On login success: stores token in `localStorage`, navigates to `/`. On register success: switches to login mode, clears password fields
- Confirm password validation — checks `password === confirmPassword` before API call, sets error and returns early if mismatch
- Toggle button clears all fields and error state when switching modes
- `Alert` component displays error string when non-empty
- Added `/auth` route to `App.jsx`
- Tested full register → login flow end to end — working

- Built `PortfolioDashboard.jsx` — portfolio and holdings management page
- State variables: `portfolios`, `selectedPortfolio`, `holdings`, `newPortfolioName`, `ticker`, `shares`, `isLoading`, `error`
- Two views controlled by `selectedPortfolio` — `null` shows portfolio list, ID shows holdings view
- `fetchPortfolios` — `GET /portfolio` with auth header, stores in `portfolios` state
- `fetchHoldings` — `GET /holdings/${selectedPortfolio}` with auth header, stores in `holdings` state
- First `useEffect` with `[]` — fetches portfolios on page load
- Second `useEffect` with `[selectedPortfolio]` — fetches holdings whenever selected portfolio changes, guarded with `if (selectedPortfolio === null) return`
- `handleCreatePortfolio` — `POST /portfolio` with `newPortfolioName`, clears input and re-fetches on success
- `handleDeletePortfolio` — `DELETE /portfolio/{id}` with auth header, re-fetches portfolios on success
- `handleSelectPortfolio` — sets `selectedPortfolio` to clicked portfolio ID
- `handleAddHolding` — `POST /holdings/${selectedPortfolio}` with ticker and shares, clears inputs and re-fetches on success
- `handleDeleteHolding` — `DELETE /holdings/${selectedPortfolio}/${holding_id}` with auth header, re-fetches on success
- Added `/portfolio` route to `App.jsx`
- Tested full flow: create portfolio, view holdings, add holding, delete holding, delete portfolio — all working

### 2026-04-18
- Added `GET /watchlist` endpoint to `api/main.py` — queries all `Watchlist` rows, returns list of `{ ticker }` dicts, 404 if empty
- Built `WatchlistPage.jsx` — fetches all watchlist tickers then fetches sentiment history for each in parallel using `Promise.all()`
- `fetch_watchlist` builds a `combined` array of `{ ticker, sentimentHistory }` objects — one entry per watchlisted ticker
- Displays latest sentiment score using `sentimentHistory.at(-1)?.sentiment_score`
- Added `/watchlist` route to `App.jsx`
- Tested locally — renders AAPL with sentiment score

- Built `Navbar.jsx` component — `AppBar` with `Toolbar`, FinSight title navigates to `/`, Watchlist and Portfolio buttons navigate to their routes
- Added `Navbar` to `App.jsx` above `Routes` — renders on every page automatically
- Used React fragments `<>...</>` to return multiple elements from `App.jsx` without an extra DOM node
- Built `AuthPage.jsx` — combined login/register page with toggle between modes
- State variables: `isLogin`, `email`, `password`, `isLoading`, `error`, `confirmPassword`
- `handleSubmit` — async function, calls `/login` or `/register` based on `isLogin`. On login success: stores token in `localStorage`, navigates to `/`. On register success: switches to login mode, clears password fields
- Confirm password validation — checks `password === confirmPassword` before API call, sets error if mismatch, returns early
- Toggle button clears all fields and error state when switching modes
- `Alert` component displays error string when non-empty
- Added `/auth` route to `App.jsx`
- Tested full register → login flow end to end — working

---

## V2 Phase 6 (continued) — Dark Theme Styling

### 2026-04-18
- Created `v2-phase6-styling` branch for all styling work
- Applied Ground News-inspired dark theme globally via MUI `ThemeProvider` + `createTheme` in `main.jsx`:
  - Background: `#0d1117`, paper: `#161b22`, primary: `#58a6ff`
  - Success: `#3fb950`, error: `#f85149`, divider: `#30363d`
  - Component overrides: `MuiCard` (border), `MuiButton` (no text transform), `MuiAppBar` (no box shadow), `MuiTextField` (small default size), `MuiDataGrid` (dark header/cells)
- Replaced `index.css` with minimal CSS (body background, box-sizing only)
- Restyled all pages and components:
  - `Navbar.jsx` — sticky dark AppBar, FinSight in blue, nav buttons with hover effects, Sign Out outlined button
  - `AuthPage.jsx` — centered card with FinSight branding, stacked form, toggle login/register
  - `WatchlistPage.jsx` — card rows with Bullish/Bearish/Neutral chips and sentiment score
  - `PortfolioDashboard.jsx` — card layout with `×` and `←` text icon buttons
  - `TickerResearchPage.jsx` — hero search area with subtitle, `Promise.allSettled` for parallel data fetching, labeled sections
  - `SentimentChart.jsx` — `ResponsiveContainer`, dark tooltip, reference line at y=0
  - `NewsFeed.jsx` — flex rows with title + chip + confidence %
  - `EarningsTable.jsx` — colour-coded surprise %, DataGrid with pagination
  - `SecFilingsCard.jsx` — Divider-separated sections, blue headings, insider trade chips
- Fixed `@mui/icons-material` incompatibility with Vite 8/rolldown — subpath imports (`@mui/icons-material/DeleteOutline`) fail under strict exports resolution. Removed the package entirely, replaced with `×` and `←` Unicode characters
- Build verified clean, dev server running on port 5174
- Merged `v2-phase6-styling` into `main` and deployed to EC2

---

## EC2 Operations + Bug Fixes

### 2026-04-18
- EC2 instance type changed from t3.micro to t3.small — OOM kills during nightly job on 1GB RAM
- IP changed after stop/start: old `13.48.106.201` → new `51.21.129.219`
- SSH username confirmed as `ec2-user` (Amazon Linux 2023, not Ubuntu)
- Added 1GB swap file to EC2 to prevent OOM kills during model loading at startup:
  - `sudo fallocate -l 1G /swapfile` → `sudo chmod 600 /swapfile` → `sudo mkswap /swapfile` → `sudo swapon /swapfile`
  - Made permanent via `echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab`
- Fixed `build_feature_vectors()` bug: `sec_filings['form_4']` → `sec_filings['insider_traders']` — key name mismatch between `get_sec_filings` tool return dict and `jobs.py` consumer
- Fixed second `build_feature_vectors()` bug: `filter(date_filed=...)` → `filter(date=...)` — edgartools `filter()` does not accept `date_filed` as a keyword argument
- Deployed fixes to EC2, confirmed nightly job running: 3 rows per ticker across all 23 tickers as of 2026-04-19

### 2026-04-19
- Added `BASE_SYSTEM_PROMPT` to `agent/graph.py` — always injected as first `SystemMessage` regardless of sector data
- Prompt defines role (senior equity research analyst), 6 output sections (Verdict, Sentiment Signal, Earnings, SEC Signals, Key Risks, Fundamentals), and rules (cite specific numbers, flag anomalies as RED FLAG, no filler phrases)
- DK-CoT sector context is appended to the base prompt when sector data exists — two-layer system
- Verified improved output quality — structured sections with verdict, specific numbers, red flags
- Deleted stale cached AAPL analysis from local DB to force fresh agent run with new prompt

---

## RAG for SEC Filings (F2 Upgrade)

### 2026-04-21
- Switched Docker PostgreSQL image from `postgres:15` to `pgvector/pgvector:pg15` — standard postgres image does not include pgvector extension
- Added `pgvector` to `requirements.txt` and installed locally
- Generated Alembic migration `d3db2ad29937_add_filing_chunks_table.py` manually — autogenerate can't handle pgvector's `Vector` type
- Migration runs `CREATE EXTENSION IF NOT EXISTS vector` then creates `filing_chunks` table:
  - `id`, `ticker`, `section`, `chunk_text`, `embedding` (Vector(384)), `filing_date`, `created_at`
- Added `FilingChunk` SQLAlchemy model to `db/models.py` using `pgvector.sqlalchemy.Vector(384)`
- Created `rag/filing_rag.py` with full RAG pipeline:
  - `chunk_text(text, chunk_size=500, overlap=50)` — sliding window chunker with 50-token overlap to prevent context loss at chunk boundaries
  - `embed_chunks(chunks)` — encodes list of strings using `all-MiniLM-L6-v2` (384 dimensions, lightweight, normalised outputs)
  - `store_chunks(ticker, section, chunks, embeddings, filing_date)` — bulk inserts all chunks as individual rows
  - `fetch_sec_filings(ticker)` — fetches full MD&A, risk factors, and 8-K text via edgartools without truncation. Returns list of `{section, text, date}` dicts
  - `process_filing(ticker)` — orchestrates fetch → chunk → embed → store for all three sections
  - `retrieve_chunks(query, ticker, top_k=5)` — embeds query, uses pgvector `<=>` cosine distance operator to return top-k most relevant chunks
- Exposed Docker PostgreSQL port 5433 on host in `docker-compose.yml` — allows local scripts to connect to Docker DB directly
- Updated local `.env` `DB_URL` to `postgresql://shakurahmad:postgres@localhost:5433/finsight`
- Tested end to end: `process_filing('AAPL')` stored 200 chunks (43 MD&A, 137 risk factors, 20 8-K)
- Tested retrieval: query "What are the main supply chain risks?" returned 5 relevant risk_factors chunks covering China manufacturing, natural disasters, tariffs — correct semantic retrieval confirmed

**Key decisions:**
- `all-MiniLM-L6-v2` chosen for embeddings — 384 dimensions, fast, good retrieval quality, memory-efficient on t3.small
- pgvector over FAISS — keeps everything in one PostgreSQL database, no separate vector store to manage
- No LangChain — built pipeline directly with sentence-transformers and SQLAlchemy for full understanding and control
- Section-aware chunking — split by section first (MD&A, risk factors, 8-K) before chunking, prevents semantically unrelated content mixing within chunks
- Overlap of 50 tokens — prevents signal loss at chunk boundaries where a concept spans two chunks
- `fetch_sec_filings` in `filing_rag.py` fetches full text (no truncation) — separate from `get_sec_filings` in `tools.py` which still truncates for direct LLM tool calls

---

## RAG Wired into Agent + EC2 Deployment

### 2026-04-21 (continued)
- Fixed CI pipeline: updated `.github/workflows/ci.yml` postgres service image from `postgres:15` to `pgvector/pgvector:pg15` — standard image does not have vector extension, `alembic upgrade head` was failing with `extension "vector" is not available`
- Added `sentence-transformers` to `requirements.txt` — was missing, causing CI import error
- Built `retrieve_rag_chunks` `@tool` in `agent/tools.py`:
  - Signature: `retrieve_rag_chunks(query: str, ticker: str, top_k: int = 3)`
  - Calls `retrieve_chunks` from `rag/filing_rag.py` and returns list of `{section, chunk_text[:300]}` dicts
  - Docstring tells the LLM when to call it: risk factors, management discussion, material 8-K events
  - Replaced `get_sec_filings` in the `tools` list in `agent/graph.py` — agent now uses RAG instead of truncated text
  - `get_sec_filings` kept in `tools.py` — still used by `jobs.py` and `api/main.py`
- Added idempotency check to `process_filing` — queries DB for existing chunk with same `func.date(filing_date)` before processing, skips if already stored. Prevents re-embedding unchanged filings nightly
- Added null guard to `fetch_sec_filings` — raises `Exception` if `get_filings(form='10-K').latest()` returns `None`. Handles BP and SHEL which don't file with SEC
- Added `process_all_filings()` to `api/jobs.py` — loops over all watchlisted tickers and calls `process_filing` for each. Called at end of `build_feature_vectors` nightly chain
- Deployed to EC2: ran `docker system prune -a` to free disk (was 99% full from old image layers), rebuilt with pgvector image, ran `process_all_filings` manually
- Result: 21 of 23 tickers populated (BP and SHEL skipped — no SEC 10-K filings as expected)
- Reduced `top_k` from 5 to 3 and truncated chunk text to 300 chars — Groq was returning `tool_use_failed` 400 error when context was too large

**Key decisions:**
- `process_filing` idempotency check uses `func.date()` on `filing_date` column — strips time component for comparison since edgartools returns a `date` object but the column stores `DateTime`
- `process_all_filings` is a separate function from `build_feature_vectors` — different failure domains, SEC filing ingestion should not be blocked by a failed feature vector calculation
- BP and SHEL missing from `filing_chunks` is expected behaviour — both are UK/European companies that don't file 10-Ks with the SEC

---

## LangSmith Integration + Agent Tool Call Bug

### 2026-04-21 (continued)
- Added LangSmith tracing to EC2 `.env`:
  - `LANGSMITH_TRACING=true`
  - `LANGSMITH_ENDPOINT=https://eu.api.smith.langchain.com` — EU region account required different endpoint from default US
  - `LANGSMITH_API_KEY` — Personal Access Token, 1 year expiry
  - `LANGSMITH_PROJECT=finsight`
  - Note: variable prefix is `LANGSMITH_` not `LANGCHAIN_` — newer SDK versions require this prefix
- Confirmed tracing working in LangSmith UI (smith.langchain.com, EU region)
- **Critical finding via LangSmith**: agent is making zero tool calls — `tool_calls: []` on every run. The LLM sees the system prompt instruction "produce a structured research report" and generates the report directly from training data, skipping all tools entirely. EPS, PE ratio, and other numbers in reports are hallucinated, not retrieved
- Root causes identified:
  1. System prompt instructs the LLM to produce a report without explicitly requiring tool calls first
  2. Tool docstrings describe implementation rather than when to call the tool
- Fix needed: update `BASE_SYSTEM_PROMPT` to explicitly require all tools to be called before generating the report. Update tool docstrings to use "use this tool when..." framing

### 2026-04-22
- Updated `BASE_SYSTEM_PROMPT` in `agent/graph.py` — added explicit grounding requirement: every factual claim must trace back to a tool result, never use prior knowledge for numbers or facts. Added graceful degradation instruction: "Data unavailable — [tool name] returned no results" when a tool fails
- Updated all tool docstrings in `agent/tools.py` to "use this tool when..." framing:
  - `get_news` — use to get latest news articles, returns list of article dicts with title, description, publishedAt, url
  - `get_stock_data` — use to find numerical data including historical prices and fundamentals (marketCap, trailingPE, sector)
  - `analyze_sentiment` — use after get_news, pass titles extracted from get_news results
  - `retrieve_rag_chunks` — use for risk factors, management discussion, material 8-K events from SEC filings
- Added `get_earnings` tool to `agent/tools.py` — calls `yfinance.earnings_history`, returns list of dicts with date, eps_actual, eps_estimate, surprise % per quarter. Dates converted to `str()` to avoid Timestamp serialisation errors
- Added `get_earnings` to tools list in `graph.py` and updated system prompt to mention it
- Fixed parallel tool call problem: changed `llm.bind_tools(tools)` to `llm.bind_tools(tools).bind(parallel_tool_calls=False)` — LLM was calling `get_news` and `analyze_sentiment` in the same step, causing LLM to fabricate titles for sentiment analysis since `get_news` results weren't available yet
- Verified fix via LangSmith: tools now called sequentially in separate agent loops — `get_stock_data` → `get_news` → `analyze_sentiment` → `get_earnings` → `retrieve_rag_chunks`
- Final report now grounded in real data: EPS 1.65 vs 1.62 estimate, PE 33.7, real risk factors from 10-K RAG chunks, sentiment with actual confidence scores

**Key decisions:**
- `parallel_tool_calls=False` over combining `get_news` + `analyze_sentiment` into one tool — preserves flexibility for the agent to call each independently if needed
- `parallel_tool_calls=False` over system prompt ordering instructions — LLMs don't reliably follow ordering instructions, framework-level enforcement is more reliable
- Market cap returned as raw integer from yfinance — formatting deferred to frontend display layer, not the agent's responsibility

### 2026-04-22 (continued)
- Fixed `get_stock_data` market cap formatting — was returning raw integer (e.g. `3912147140608`). Added digit-count logic to format as `$3.9T`, `$500.0B`, or `$200.0M` depending on magnitude. `info = ticker_obj.info` was moved above the formatting block — CI caught `UnboundLocalError: local variable 'info' referenced before assignment`
- Fixed `get_sec_filings` null guards:
  - `ten_k` wrapped in `try/except` — returns `"No recent 10-K found"` for both `management_discussion` and `risk_factors` if missing
  - `form_4.market_trades` check changed from `if form_4 and form_4.market_trades` to `if form_4 and not form_4.market_trades.empty` — pandas raises `ValueError: The truth value of a DataFrame is ambiguous` when a DataFrame is used directly in a boolean condition. `.empty` is the correct check
- Verified agent output on EC2: market cap now shows `$3.9T`, EPS 1.65 vs 1.62253, sequential tool calls confirmed via LangSmith
- Known issue: Groq retrying 3 times before responding — context growing large with sequential tool calls accumulating in messages state. Monitor for now

**Key decisions:**
- Market cap formatted in the tool, not the frontend — the LLM writes the number into the markdown report, so formatting must happen before it reaches the LLM
- Digit count used for magnitude detection — avoids hardcoding thresholds, works for any market cap size

---

## Frontend Deployment via Nginx

### 2026-04-23
- Added `/api/` prefix to all 18 FastAPI endpoints in `api/main.py` — required for Nginx to distinguish API requests from frontend requests
- Updated all frontend API calls from `http://localhost:8000/endpoint` to `${import.meta.env.VITE_API_URL}/api/endpoint`
- Created `frontend/.env` with `VITE_API_URL=http://localhost:8000` for local development
- Created `frontend/.env.production` with `VITE_API_URL=` (empty) — Vite uses this automatically on `npm run build`, making all API calls relative URLs that Nginx proxies to FastAPI
- Created `nginx/nginx.conf` — two location blocks:
  - `/api/` → `proxy_pass http://app:8000` — forwards to FastAPI container by service name
  - `/` → serves React static files from `/usr/share/nginx/html` with `try_files $uri $uri/ /index.html` — falls back to index.html for React Router client-side routing
  - Added `proxy_read_timeout 300s` — default 60s timeout was killing long-running agent requests
- Created `frontend/Dockerfile` — multi-stage build:
  - Stage 1 (builder): `node:22-alpine` — copies `frontend/package.json`, runs `npm install`, copies all frontend code, runs `npm run build` to produce `dist/`
  - Stage 2: `nginx:alpine` — copies `dist/` from builder into `/usr/share/nginx/html`, copies `nginx.conf`
  - Node 22 required — Vite requires Node 20.19+ or 22.12+, Node 18 was too old
- Added `nginx` service to `docker-compose.yml`:
  - `build: context: . dockerfile: frontend/Dockerfile` — project root as context so Docker can access both `frontend/` and `nginx/`
  - `ports: "80:80"` — exposes port 80 on EC2
  - `depends_on: app` — waits for FastAPI to start
- Opened port 80 in EC2 security group inbound rules (HTTP, 0.0.0.0/0)
- Fixed `SecFilingsCard.jsx` — `insider_traders` can be a string ("No recent Form 4 found") when no Form 4 exists. Changed condition from `filings.insider_traders?.length > 0` to `Array.isArray(filings.insider_traders) && filings.insider_traders.length > 0`
- Fixed `retrieve_rag_chunks` tool — removed `top_k` parameter from signature. Groq was passing it as string `"5"` instead of integer, causing schema validation error. Hardcoded `top_k=3` inside `retrieve_chunks` call
- Frontend live at `http://51.21.129.219` — full stack deployed and publicly accessible
- Known limitation: Groq free tier 100,000 tokens/day limit. Sequential tool calls accumulate context across agent loops — each LLM call includes full message history. Token usage adds up fast under load

**Key decisions:**
- Multi-stage Docker build — Node.js (~1GB) only needed to build, final Nginx image is ~50MB
- Build context set to project root (not `frontend/`) — allows Dockerfile to access both `frontend/` and `nginx/` directories
- `/api/` prefix on all endpoints — clean separation between API and frontend routes, Nginx can route by prefix without listing every endpoint
- `try_files $uri $uri/ /index.html` — required for React Router. Direct URL visits (e.g. `/portfolio`) have no corresponding HTML file; falling back to `index.html` lets React Router handle the route client-side
- Relative URLs in production — browser automatically prepends the host, no hardcoded IP needed in the frontend code
