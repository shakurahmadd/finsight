# FinSight — Reference Notes

---

## Interview Questions

*Built up throughout V2. Each entry covers: the question → the decision made → why → what the alternative was and why it was rejected.*

---

**Q: Why did V1 use a fixed linear pipeline instead of a ReAct agent from the start?**

In V1 there were only three tools and all of them were always needed to produce a meaningful summary — news, stock data, and sentiment. There was no conditional logic to implement. A ReAct agent would have added architectural complexity with no benefit since the LLM would have called the same three tools in the same order every time. V2 introduces EDGAR filings, anomaly detection, and domain knowledge retrieval — tools that aren't always needed. If sentiment is already strong and clear, there may be no reason to check SEC filings. If there are no recent insider trades, Form 4 analysis adds nothing. A ReAct agent can reason about what signal it already has and decide whether additional tool calls are justified. That conditional reasoning is where the agentic pattern earns its complexity.

---

**Q: Walk me through your nightly sentiment scoring job — why do you weight by both confidence and recency, and what does the decay parameter λ=0.5 control?**

The weighted average combines two confidence signals. Recency is modelled exponentially — `e^(-λ × days_old)` — because financial sentiment moves fast and today's articles should dominate over week-old ones. Model confidence is taken from the softmax of the DistilBERT logits — `max(softmax(logits))` — and represents how certain the model is about its prediction. A high-confidence Bullish article from today gets the most weight; a low-confidence Neutral article from 6 days ago contributes almost nothing. The label is converted to a numeric score (Bearish=-1, Neutral=0, Bullish=1), multiplied by the combined weight, and averaged across all articles. λ=0.5 controls the speed of decay — increasing it to 2.0 would cause articles from even a day ago to carry minimal weight, making the signal very reactive. Decreasing it to 0.1 would smooth the signal, giving older articles nearly as much influence as today's. λ=0.5 is a reasonable starting point that can be tuned once real data accumulates.

---

**Q: Walk me through the POST /watchlist endpoint — what does it do, how does it handle duplicates, and why did you use a 409 status code instead of returning a 200?**

`POST /watchlist` accepts a ticker string in the request body via a Pydantic model. It opens a DB session via FastAPI dependency injection, creates a `Watchlist` ORM object, and attempts to commit it. Since `ticker` is the primary key, inserting a duplicate raises a SQLAlchemy `IntegrityError` — the endpoint catches this, rolls back the session, and raises an `HTTPException` with status code 409. The reason for 409 over a 200 with a message string is that HTTP status codes are machine-readable — a frontend or API client can branch on `response.status_code == 409` without parsing text. A 200 with "already exists" in the body requires the client to interpret a string, which is fragile and non-standard.

---

**Q: You implemented DK-CoT in your LangGraph agent. Walk me through how it works — how does the agent know which sector to use, how do you retrieve the relevant data, and how does it get into the prompt?**

The agent node runs in a loop as part of the ReAct pattern. On the first pass, only the human message exists — no sector is known yet, so the LLM is invoked normally and decides which tools to call. Once the LLM calls `get_stock_data`, the result is added to the messages as a ToolMessage containing the fundamentals dict serialised as JSON, which includes the sector field. On subsequent passes, `agent_node` searches through `state['messages']` for any ToolMessage where `"sector"` appears in the content. When found, it parses the JSON with `json.loads()` and extracts the sector string. It then queries three PostgreSQL tables: `dk_knowledge` filtered by sector for benchmark metrics (P/E, P/B, profit margin etc.), `sector_macro_mapping` to find which macro indicator IDs are relevant to that sector, and `macro_indicators` to fetch those rows using a SQLAlchemy `in_()` query. The benchmark and macro data is formatted into a system prompt string and prepended to the messages as a `SystemMessage` before the LLM is invoked. The LLM then reasons against real sector benchmarks and current macro conditions rather than from general knowledge alone — which is the core idea from the DK-CoT paper.

---

**Q: You added an SEC EDGAR tool to your LangGraph agent. Walk me through how it works, how you handled the token budget problem, and why you used `try/except` for 8-K and Form 4 but not for 10-K.**

The tool uses edgartools to fetch the three most relevant SEC filings for a given ticker. For the 10-K it extracts the MD&A and Risk Factors sections directly as strings. For the 8-K it extracts the full filing text. For Form 4 it reads the `market_trades` DataFrame and converts it to a list of dicts the LLM can interpret. The token budget is handled with simple truncation — each section is capped at 3,000 characters. This is a pragmatic starting point; the plan is to extend it to RAG if truncation proves lossy in practice. The 10-K is not wrapped in `try/except` because every public company files one annually — it is mandatory. 8-K and Form 4 are event-driven: an 8-K only exists when a material event has occurred, and a Form 4 only exists when an insider has recently traded. Their absence is normal, not an error, so the tool returns a fallback string rather than crashing.

---

**Q: Why did you implement the ReAct pattern manually rather than using LangGraph's `create_react_agent` constructor?**

Building the graph manually gives us full control over the agent node. In V2 we're implementing DK-CoT (Domain Knowledge Chain-of-Thought) — before the LLM reasons about a stock, we retrieve relevant sector benchmarks and macroeconomic indicators from the database and inject them into the prompt. This means the agent node needs to be customised on every invocation based on the ticker's sector. `create_react_agent` handles the agent node internally as a black box — you get a working ReAct graph in one line but you can't modify what the LLM sees on each reasoning step. Building it manually means we own every component and can extend it without fighting the framework.

---

## LoRA (Low-Rank Adaptation)

Instead of updating a weight matrix W directly, LoRA learns two small matrices A and B where the update is A × B. If W is 768×768 (589K params), and A is 768×r and B is r×768, you only train 2×768×r params. At rank r=8: 12,288 params vs 589,824 — ~48x fewer. Original weights are frozen; only A and B are trained.

**Config:**
- `r=8` — rank, controls expressiveness vs parameter count
- `lora_alpha=16` — scaling factor, convention: set to 2x rank
- `target_modules=["q_lin", "v_lin"]` — DistilBERT attention projection layers
- `task_type=TaskType.SEQ_CLS` — sequence classification

**Watch-outs:**
- Don't apply LoRA to the classification head — randomly initialised, train it fully
- Don't use `"all-linear"` — it includes the classification head

---

## Training Loop

**Step order:** zero gradients → forward pass → compute loss → backward pass → update weights

PyTorch accumulates gradients by default — must zero each step. `loss.item()` extracts scalar from tensor — use this when accumulating, not `loss` itself (prevents GPU memory leak). Model and input tensors must be on the same device.

**Validation:** `model.eval()` disables dropout. `torch.no_grad()` disables gradient tracking. Access logits via `output.logits`. `torch.argmax(output.logits, dim=1)` gives predicted class.

**Watch-outs:**
- Reset `metric = evaluate.load("f1")` each epoch — otherwise predictions accumulate across epochs
- F1 plateauing while training loss drops may indicate overfitting — track validation loss to confirm
- Neutral class will always score highest due to class imbalance

---

## Evaluation & Class Imbalance

**Accuracy** is unreliable under class imbalance — a model always predicting neutral scores ~65% without learning. Use **per-class F1** instead. F1 is the harmonic mean of precision and recall — punishes imbalance (precision=1.0, recall=0.0 gives F1=0, not 0.5).

**Weighted loss:** `weight = 1 / class_frequency`. PyTorch normalises internally — ratios are what matter. In PyTorch: `nn.CrossEntropyLoss(weight=class_weights)`.

---

## Tokenisation

Converts raw text to token IDs and attention masks. `input_ids`: integer token IDs. `attention_mask`: 1 for real tokens, 0 for padding. `padding="max_length"` pads to exactly max_length. `max_length=128` safe for financial headlines.

**Watch-outs:**
- String columns must be removed before batching — PyTorch cannot collate them
- `.remove_columns()` returns a new dataset — reassign the result
- `.set_format(type="torch")` is inplace

---

## LangGraph

**Key concepts:**
- **Graph**: nodes connected by edges, state flows through
- **State**: the shared data structure passed between all nodes
- **Nodes**: Python functions that take state and return updated state
- **Edges**: fixed (always go to next node) or conditional (LLM decides)
- **MessagesState**: pre-built LangGraph state with a single `messages` key — a list of HumanMessage, AIMessage, and ToolMessage objects

**V1 (linear pipeline):** fixed edges, LLM only at the end for summarisation. Not truly agentic.

**V2 (ReAct pattern):** LLM sits in the agent node, decides which tools to call, loops until it has enough to produce a final answer.

**ReAct graph structure:**
```python
from langgraph.graph import StateGraph, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import HumanMessage

tools = [get_news, get_stock_data, analyze_sentiment]
llm_with_tools = llm.bind_tools(tools)

def agent_node(state):
    messages = state['messages']
    response = llm_with_tools.invoke(messages)
    return {'messages': response}

graph = StateGraph(MessagesState)
graph.add_node("agent", agent_node)
graph.add_node("tools", ToolNode(tools))
graph.set_entry_point("agent")
graph.add_conditional_edges("agent", tools_condition)  # → tools or END
graph.add_edge("tools", "agent")  # always loop back to LLM
graph_app = graph.compile()

result = graph_app.invoke({"messages": [HumanMessage(content="Analyse: AAPL")]})
print(result['messages'][-1].content)
```

**MessagesState message types:**
- `HumanMessage` — initial input from the user
- `AIMessage` — LLM response (tool call request or final answer)
- `ToolMessage` — result of a tool execution

**`@tool` decorator:** wraps a function so the LLM knows it exists and can request it. The docstring becomes the tool description — the LLM reads it to decide when to use the tool. After decoration, call with `.invoke({"param": value})` not directly.

**`bind_tools(tools)`:** attaches tool schemas (name, description, parameters) to the LLM so it can request them in its responses.

**`ToolNode`:** pre-built node that executes whatever tool the LLM requested and adds the result as a ToolMessage.

**`tools_condition`:** pre-built conditional edge function — checks last message, routes to `"tools"` if LLM made a tool call, routes to `END` if LLM produced a final answer.

**Why build manually instead of `create_react_agent`:** DK-CoT in Phase 1 requires customising the agent node to inject domain knowledge into the prompt. `create_react_agent` hides the internals and can't be customised.

---

## FastAPI

Python web framework for REST APIs. Async-native, built around type hints. Auto-generates Swagger docs at `/docs`. Validates requests automatically via Pydantic.

**Run:** `uvicorn api.main:app --reload` (drop `--reload` in Docker)

**Pydantic pattern:**
```python
class MyModel(BaseModel):
    field: type
```

**Dependency injection:**
```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/route")
def my_route(db: Session = Depends(get_db)):
    pass
```
`yield` pauses the function — FastAPI runs the route, then resumes to hit `finally: db.close()`. Guarantees session always closes.

**HTTPException:** `raise HTTPException(status_code=404, detail="Not found")`

**HTTP Status Codes used in FinSight:**

| Code | Name | When to use | Example in project |
|------|------|-------------|--------------------|
| 200 | OK | Successful GET or POST that doesn't create | Login, get results |
| 201 | Created | Successfully created a new resource | Register, add to watchlist, create portfolio |
| 400 | Bad Request | Malformed request from client | Invalid input |
| 401 | Unauthorised | No token, invalid token, or wrong password | Missing JWT, failed login |
| 403 | Forbidden | Valid token but accessing another user's resource | Accessing someone else's portfolio |
| 404 | Not Found | Resource doesn't exist | Ticker not in DB, portfolio ID not found |
| 409 | Conflict | Resource already exists | Duplicate email, duplicate watchlist ticker |
| 500 | Internal Server Error | Unhandled exception in server code | Bug in route logic |

**Key distinctions:**
- 401 vs 403: not authenticated vs authenticated but not allowed
- 404 vs 403: doesn't exist vs exists but forbidden — always check 404 first
- 200 vs 201: both success, but 201 specifically means something was created

---

## Cache-Aside Pattern

1. Check DB — does a recent result for this ticker exist?
2. If fresh → return cached result
3. If stale or missing → run pipeline → store → return

Cache threshold: 1 day — markets move daily, aligns with NewsAPI 100 req/day limit.

---

## SQLAlchemy ORM

Lets you define tables as Python classes and write queries in Python.

```python
class MyModel(Base):
    __tablename__ = "my_table"
    id = Column(Integer, primary_key=True)
    field = Column(String, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
```

Every model inherits from Base — registers it in Base.metadata automatically.

**Always use `DateTime(timezone=True)`** — avoids naive/aware comparison errors. Always store UTC.

---

## Alembic

Version control for database schemas. Each migration is a versioned script that can be applied or rolled back.

```bash
alembic init alembic                          # initialise
alembic revision --autogenerate -m "message"  # generate migration from model diff
alembic upgrade head                          # apply all pending migrations
alembic downgrade -1                          # roll back last migration
```

`alembic_version` table in PostgreSQL tracks which migrations have been applied — running `upgrade head` twice is safe.

**env.py must have:** DB_URL loaded from .env (never hardcoded), `target_metadata = Base.metadata`, all models imported so Base.metadata is populated.

---

## edgartools (SEC EDGAR)

Free Python library wrapping the SEC EDGAR API. No API key needed — only requires identity registration.

**Identity:** `set_identity("Name email@example.com")` — called once at module level. Registers with EDGAR so SEC can contact you if you abuse the rate limit. Not a secret, does not go in `.env`.

**Key pattern:**
```python
from edgar import Company, set_identity
set_identity("Name email@example.com")

c = Company("AAPL")
ten_k = c.get_filings(form="10-K").latest().obj()   # TenK object
eight_k = c.get_filings(form="8-K").latest().obj()  # EightK object
form_4 = c.get_filings(form="4").latest().obj()     # Ownership object
```

**TenK attributes:** `management_discussion` (str), `risk_factors` (str), `financials`, `income_statement`, `balance_sheet`

**EightK attributes:** `text()` (callable, returns full filing as str), `items`, `has_press_release`

**Form 4 attributes:** `market_trades` (DataFrame — Date, Shares, Price, AcquiredDisposed, TransactionType), `reporting_owners`, `shares_traded`

**Token budget:** Sections are plain strings and can be long (MD&A = 20,000–50,000 words). Truncate with `[:3000]` for now. RAG is the proper solution but deferred.

**DK-CoT known limitation:** Injection does not fire on the first `agent_node` call because no ToolMessage exists yet — `sector` is only detected after `get_stock_data` runs. The LLM reasons without domain knowledge on pass 1. Future improvement: extract the ticker from the HumanMessage on pass 1 and pre-fetch the sector directly via yfinance before the LLM is invoked, so DK-CoT is available from the first pass.

**Watch-outs:**
- `eight_k.text` is a method — call it as `eight_k.text()`, not `eight_k.text`
- 8-K and Form 4 are event-driven — wrap in `try/except`, return fallback string if missing. 10-K is mandatory annually so no fallback needed
- `market_trades.to_dict(orient='records')` converts DataFrame to list of dicts — required for LLM serialisation

---

## Docker

Packages your app and all its dependencies into a container — runs identically everywhere.

**Dockerfile key instructions:**
```dockerfile
FROM python:3.9-slim
RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu
COPY . /app           # COPY should come after pip installs for layer caching
RUN pip install -r requirements.txt
EXPOSE 8000
CMD ["bash", "entrypoint.sh"]
```

**Layer caching:** Docker reuses cached layers until something changes. Once a layer changes, everything after rebuilds. Put dependencies before COPY so code changes don't trigger full reinstalls.

**Host binding:** `0.0.0.0` required in Docker — `127.0.0.1` is only accessible from within the container.

**Why CPU PyTorch:** Containers have no GPU. Default torch pulls ~2GB of CUDA packages. CPU-only version is ~200MB. Install via `--index-url https://download.pytorch.org/whl/cpu`.

**Why no venv in Docker:** The container itself is isolated — install directly, no venv needed.

---

## docker-compose

Orchestrates multiple containers together.

```bash
docker-compose up --build    # build and start
docker-compose up -d         # start in background (detached)
docker-compose down          # stop and remove containers
docker-compose logs app      # view logs for a service
```

**Service names as hostnames:** Containers reach each other via service name (e.g. `db`), not `localhost`.

**depends_on** only waits for the container to start, not for PostgreSQL to be ready — use pg_isready loop.

**Volumes:** persist PostgreSQL data across container restarts.

**restart: unless-stopped** — restarts containers automatically on crash or reboot (not yet implemented in V1 — add in Phase 0 of V2).

---

## entrypoint.sh

```bash
#!/bin/bash
until pg_isready -h db -p 5432; do
  echo "Waiting for database..."
  sleep 1
done
alembic upgrade head
uvicorn api.main:app --host 0.0.0.0
```

Runs before the main process. `pg_isready` polls until PostgreSQL accepts connections — preferred over `sleep` because sleep is a guess.

---

## GitHub Actions CI

On every push, GitHub spins up a fresh Ubuntu VM and runs your workflow.

```yaml
name: CI
on: push
jobs:
  test:
    runs-on: ubuntu-latest
    env:
      DB_URL: postgresql://user:password@localhost:5432/db
      NEWS_API: ${{ secrets.NEWS_API }}
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: ...
          POSTGRES_PASSWORD: ...
          POSTGRES_DB: ...
        ports:
          - 5432:5432
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: "3.9"
      - run: pip install -r requirements.txt
      - run: |
          until pg_isready -h localhost -p 5432; do
            echo "Waiting..."
            sleep 1
          done
      - run: alembic upgrade head
      - run: pytest tests
```

**Secrets:** stored in GitHub repo → Settings → Secrets → Actions. Referenced as `${{ secrets.NAME }}`. Never appear in logs.

**CI vs docker-compose:** In CI the db hostname is `localhost` not `db` — no compose network.

---

## AWS EC2

A virtual machine (instance) running in Amazon's data centre. Accessible over the internet 24/7.

**SSH:** `ssh -i ~/.ssh/finsight.pem ec2-user@<public-ip>` — key pair authenticates you without a password. Store `.pem` in `~/.ssh/` with `chmod 400`.

**Security groups:** firewall rules controlling inbound/outbound traffic. Must explicitly open ports (22 for SSH, 8000 for the API).

**Setup on a fresh EC2 instance:**
```bash
sudo yum install -y docker git
sudo systemctl start docker && sudo systemctl enable docker
sudo usermod -aG docker ec2-user
# re-login, then:
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
git clone https://github.com/<user>/finsight.git
cd finsight && nano .env
docker-compose up --build -d
```

**systemctl enable docker** — starts Docker automatically on reboot. Containers still need `restart: unless-stopped` in docker-compose to auto-restart.

**docker-compose up -d** — detached mode keeps containers running after SSH session ends.

---

## APScheduler

Runs background jobs on a schedule inside a FastAPI app.

**Integration pattern — FastAPI lifespan:**
```python
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager

scheduler = BackgroundScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()
    scheduler.add_job(my_job, 'cron', hour=1, minute=0)
    yield  # app runs here
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)
```

`BackgroundScheduler` runs jobs in a background thread without blocking FastAPI. Lifespan ties the scheduler lifecycle to the app — starts on startup, shuts down cleanly on shutdown.

**Trigger types:**
- `'cron'` — run at a specific time: `hour=1, minute=0` = 1am daily
- `'interval'` — run every N seconds/minutes: useful for testing

**Watch-outs:**
- Jobs run in a background thread — no FastAPI `Depends` injection available. Use `SessionLocal()` directly in a `try/finally` block
- `BackgroundScheduler` is not async — do not use `AsyncIOScheduler` unless you need async job functions
- Per-ticker `try/except` with `db.rollback()` inside jobs — one failing ticker must never kill the whole run. `rollback()` resets the session to a clean state for the next ticker

---

## Anomaly Detection — Feature Matrix

The Isolation Forest trains on a multi-signal feature matrix. One row per ticker per day, five signals per row:

| Signal | Source | How computed |
|---|---|---|
| `sentiment_score` | `sentiment_history` table | Read directly — already computed by Job B |
| `earnings_surprise` | `yf.Ticker.earnings_history` | `(epsActual - epsEstimate) / \|epsEstimate\| * 100` on most recent quarter |
| `insider_volume` | SEC EDGAR Form 4 | Sum of `Shares` across all trades in latest Form 4. Default 0 if no filing |
| `filing_frequency` | SEC EDGAR | Count of 10-K + 8-K + Form 4 filings in last 30 days |
| `price_volatility` | yfinance 30-day history | `pct_change().std()` on daily closing prices |

**Why these five signals:** Each captures a different dimension of risk. Price volatility is market reaction. Sentiment is news tone. Earnings surprise is fundamental performance vs expectation. Insider volume surfaces information asymmetry. Filing frequency detects unusual regulatory activity. An anomaly is when multiple signals deviate simultaneously — no single signal is sufficient alone.

**Watch-outs:**
- `pct_change()` and `std()` return numpy scalars — wrap in `float()` before storing in PostgreSQL
- `earnings_history` is a property not a method — no parentheses
- `date_filed` filter in edgartools requires string format `"YYYY-MM-DD:"` — colon suffix means "from this date onwards"
- Skip ticker entirely if no sentiment score exists for today — incomplete vectors corrupt the feature matrix

**Training data constraint:**
Isolation Forest needs historical rows to learn what "normal" looks like. Sentiment scores cannot be backfilled — NewsAPI free tier has no historical news and only 100 req/day. The nightly job must accumulate real data before training is meaningful. Deferred until sufficient rows exist.

---

## JWT Authentication

JSON Web Tokens — stateless authentication. Token is issued on login, sent with every subsequent request in the `Authorization: Bearer <token>` header. Server verifies the token on each request without storing it.

**Token structure:** header.payload.signature — payload contains `user_id` and `exp`. Signed with `JWT_SECRET` using HS256.

**passlib + python-jose pattern:**
```python
from passlib.context import CryptContext
from jose import jwt, JWTError

pwd_context = CryptContext(schemes=["bcrypt_sha256"])  # bcrypt_sha256 avoids 72-byte limit
ALGORITHM = "HS256"

def hash_password(password): return pwd_context.hash(password)
def verify_password(plain, hashed): return pwd_context.verify(plain, hashed)
def create_token(user_id):
    return jwt.encode({"user_id": user_id, "exp": datetime.now(timezone.utc) + timedelta(hours=24)}, SECRET_KEY, algorithm=ALGORITHM)
def decode_token(token):
    try: return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError: raise HTTPException(status_code=401, detail="Invalid token")
```

**`HTTPBearer` vs `OAuth2PasswordBearer`:** `OAuth2PasswordBearer` creates an OAuth2 password flow in Swagger — it expects the login endpoint to accept form data, not JSON. If your login endpoint uses a Pydantic JSON body, use `HTTPBearer` instead — gives a simple token input in Swagger and extracts the bearer token cleanly via `credentials.credentials`.

```python
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    token = credentials.credentials
    ...
```

**`OAuth2PasswordBearer`:** extracts bearer token from Authorization header automatically. Pass `tokenUrl` pointing to your login endpoint.

**`get_current_user` dependency:** chains `oauth2_scheme` → `decode_token` → DB lookup → returns user object. Add as `Depends(get_current_user)` to any protected endpoint — raises 401 before route runs if auth fails.

**HTTP status codes:**
- 401 — unauthenticated (no token, invalid token, wrong password)
- 403 — unauthorised (valid token, accessing another user's resource)
- 409 — conflict (duplicate email on register)

**bcrypt watch-out:** passlib is incompatible with bcrypt 4.x — pin to `bcrypt==4.0.1` in requirements.txt.

**Why JWT is stateless:** token contains everything needed to verify identity. Server never stores tokens — just signs them on issue and verifies the signature on each request. Scales horizontally with no shared session state.

---

## Portfolio System

**Schema:**
- `portfolios`: `id`, `user_id` (FK → users.id CASCADE), `name`, `created_at`
- `holdings`: `id`, `portfolio_id` (FK → portfolios.id CASCADE), `ticker`, `shares`, `created_at`
- Weight percentage computed dynamically — `shares_i / total_shares`. Never stored.

**CASCADE delete:** deleting a user deletes their portfolios. Deleting a portfolio deletes its holdings. Defined at the DB level via ForeignKey CASCADE.

**Portfolio aggregation — weighted average sentiment:**
```
weight_i = shares_i / total_shares
portfolio_sentiment = sum(weight_i × sentiment_i)
```
Sentiment pulled from `sentiment_history` for most recent date per ticker.

**Known limitation:** share count ignores stock price — 10 shares of a $5 stock is weighted the same as 10 shares of a $200 stock. Correct weight is `shares × price`. Deferred until price fetching is added.

**Known improvement — value-weighted portfolio aggregation:**
Current implementation weights sentiment by share count. Correct approach weights by position value (`shares × current_price` from yfinance). This gives accurate portfolio representation since share count alone ignores price differences between stocks. Requires yfinance price lookup per holding at query time. Implement after Phase 6 frontend is complete so the improvement is immediately visible in the UI.

---

## React + Vite + MUI — Frontend Stack

**Vite:** build tool and dev server for React. `npm run dev` starts on port 5173 with hot module reload. `npm run build` produces a static `dist/` folder for production deployment via Nginx.

**MUI v6:** component library for React. Provides pre-built accessible components — `Button`, `TextField`, `Card`, `Chip`, `CircularProgress`, `Alert` etc. Import from `@mui/material`.

**Recharts:** charting library for React. Key component for FinSight: `LineChart` with `XAxis`, `YAxis`, `Line`, `Tooltip`. Wrap in `ResponsiveContainer` to make charts responsive.

**React Router:** client-side routing. `BrowserRouter` wraps the whole app in `main.jsx`. Routes defined in `App.jsx` with `<Routes>` and `<Route path="..." element={...} />`. `useNavigate()` hook for programmatic redirect after login.

**Axios:** HTTP client. Makes API calls from React components. Returns promise — use `.then()` or `async/await`.

**State management pattern:**
```jsx
const [data, setData] = useState(null)
const [isLoading, setIsLoading] = useState(false)
const [error, setError] = useState(null)

const handleSubmit = async () => {
  setIsLoading(true)
  try {
    const response = await axios.post('/endpoint', { field: value })
    setData(response.data)
  } catch (err) {
    setError(err.response?.data?.detail || 'Something went wrong')
  } finally {
    setIsLoading(false)
  }
}
```

**CORS:** browsers block requests from one origin (e.g. `localhost:5173`) to another (e.g. `localhost:8000`) by default. FastAPI's `CORSMiddleware` tells the browser that cross-origin requests from the React dev server are allowed. Without it, every API call from the frontend fails with a CORS error before it even reaches the server.

---

## JWT Authentication — Frontend

**Token storage:** store JWT in `localStorage` after login. `localStorage` persists across page refreshes — a state variable would not. Set with `localStorage.setItem('token', token)`, read with `localStorage.getItem('token')`, clear on logout with `localStorage.removeItem('token')`.

**Attaching the token:** every protected API call needs `Authorization: Bearer <token>` in the request header:
```js
const token = localStorage.getItem('token')
axios.get('/portfolio', {
  headers: { Authorization: `Bearer ${token}` }
})
```

**Login flow:**
1. User submits form → POST `/login` with `{ email, password }`
2. Response: `{ access_token: "...", token_type: "bearer" }`
3. `localStorage.setItem('token', response.data.access_token)`
4. `navigate('/portfolio')` — redirect to protected page

**After register success:** switch to login mode rather than auto-logging in — the `/register` endpoint returns a string, not a token. User must log in separately after registering.

**Confirm password validation:** check client-side before making any API call — saves a round trip and gives instant feedback:
```js
if (!isLogin && password !== confirmPassword) {
    setError('Passwords do not match')
    setIsLoading(false)
    return  // early return stops the function
}
```

**Toggle mode pattern:** when switching between login and register, clear fields and error state so stale input doesn't carry over. Keep email pre-filled when switching from register to login — saves the user retyping it.

**Axios instance pattern (for larger apps):** create a configured Axios instance with the token pre-attached so you don't repeat the header on every call:
```js
const api = axios.create({ baseURL: 'http://localhost:8000' })
api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})
```

**Protected route pattern:**
```python
@app.post("/portfolio")
def create_portfolio(request: PortfolioRequest, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    # current_user is the full User ORM object
    # 401 raised automatically if token missing/invalid
```

**Ownership check pattern:**
```python
if port_row is None:
    raise HTTPException(status_code=404, ...)
if port_row.user_id != current_user.id:
    raise HTTPException(status_code=403, ...)
```
Always 404 before 403 — check existence first, then ownership.
