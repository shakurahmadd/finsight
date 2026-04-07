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
