# FinSight Docker — Project Log

## 2026-04-07

### What I did
- Created Dockerfile in project root for the FastAPI app container
- Added uvicorn and sqlalchemy to requirements.txt (were missing)

### Decisions made
- Base image: python:3.9-slim — matches local Python version, slim reduces image size
- WORKDIR /app set before COPY so all files land in the working directory
- COPY . /app — copies entire project into container
- RUN pip install -r requirements.txt — installs all dependencies
- EXPOSE 8000 — documents that the container listens on port 8000 (uvicorn default)
- CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0"] — binds to all interfaces so container is reachable from outside
- --reload flag dropped for Docker (dev-only flag)
- 0.0.0.0 host required — 127.0.0.1 (default) is only accessible from within the container itself

### Blockers / questions
- Next: docker-compose.yml to define FastAPI + PostgreSQL services together

## 2026-04-08

### What I did
- Created docker-compose.yml with two services: app and db
- Created entrypoint.sh to run alembic migrations before starting uvicorn
- Updated Dockerfile CMD to use entrypoint.sh instead of uvicorn directly

### Decisions made
- Two services: app (FastAPI) and db (PostgreSQL) — separate containers, each with one responsibility
- app service builds from local Dockerfile, db service uses official postgres:15 image
- Port mapping "8000:8000" — laptop port 8000 maps to container port 8000
- depends_on: db — app container waits for db container to start first
- DB_URL overridden in environment to use `db` hostname instead of `localhost` — containers communicate via service name not localhost
- env_file: .env — loads local secrets at runtime, never copied into image
- postgres_data volume — persists PostgreSQL data across container restarts, declared at top level
- entrypoint.sh runs `alembic upgrade head` before uvicorn — ensures tables exist in the fresh PostgreSQL container on every startup
- CMD ["bash", "entrypoint.sh"] — bash used explicitly since Docker doesn't execute scripts directly

### Blockers / questions
- Next: run docker-compose up --build and test

## 2026-04-08 (continued)

### What I did
- Added .dockerignore to exclude venv/, tests/, ml/, docker/, .git/, .env, .pytest_cache/, README.md — reduced build context from 1GB+ to ~5KB
- Fixed POSTGRES_PASSWORD missing in docker-compose.yml — PostgreSQL refused to start without it
- Switched PyTorch to CPU-only install in Dockerfile to avoid downloading 2GB+ of CUDA packages
- Added pg_isready loop in entrypoint.sh to wait for PostgreSQL to be ready before running alembic
- Full stack verified working end-to-end in Docker

### Decisions made
- .dockerignore excludes everything not needed at runtime — venv (Docker installs its own), dev/test files, secrets
- POSTGRES_PASSWORD=postgres for local development — simple convention
- PyTorch CPU installed via separate RUN step in Dockerfile with --index-url https://download.pytorch.org/whl/cpu — reduces image size ~10x
- pg_isready loop preferred over sleep — sleep is a guess, loop waits exactly as long as needed
- depends_on only waits for container start, not for PostgreSQL to be ready — pg_isready loop is required to handle this gap

### Blockers / questions
- Next: GitHub Actions CI/CD
