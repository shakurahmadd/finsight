# FinSight — Reference Notes

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
- **State**: TypedDict shared between all nodes — each node reads from and writes to it
- **Nodes**: Python functions that take state and return updated state dict
- **Edges**: define execution order (fixed = deterministic pipeline, conditional = ReAct agent)

**V1 is a fixed pipeline** — not truly agentic. V2 fixes this with a proper ReAct pattern where the LLM decides which tools to call and loops until it has enough to produce a final answer.

**Building the graph:**
```python
graph = StateGraph(AgentState)
graph.add_node("name", function_reference)
graph.set_entry_point("first_node")
graph.add_edge("from_node", "to_node")
app = graph.compile()
result = app.invoke({"ticker": "AAPL"})
```

**Node pattern:**
```python
def some_node(state):
    value = state['field']
    result = do_something(value)
    return {'field': result}
```

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
