# FinSight Docker — Reference Notes

## Docker

### What it is
Packages your app and all its dependencies into a container — a self-contained unit that runs identically everywhere (local, EC2, colleague's machine).

### Dockerfile
A set of instructions to build a container image. Each instruction is a layer.

### Key instructions
```dockerfile
FROM python:3.9-slim       # base image — Linux + Python 3.9
WORKDIR /app               # set working directory for all subsequent commands
COPY . /app                # copy project files into container
RUN pip install -r requirements.txt  # install dependencies
EXPOSE 8000                # document that container listens on port 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0"]  # start server
```

### CMD format
List format — each part of the command is a separate string:
```dockerfile
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0"]
```

### Host binding
- `127.0.0.1` — loopback, only accessible from inside the container. Default.
- `0.0.0.0` — all interfaces, accessible from outside the container. Required for Docker.

### Ports
- Uvicorn listens on port 8000 by default
- `EXPOSE 8000` documents this in the Dockerfile
- Actual port mapping (host → container) is done in docker-compose

### Why no virtual environment in Docker
The container itself is isolated — dependencies are installed directly. No venv needed.

### Why not copy .env into container
`.env` contains secrets. Instead, pass environment variables via docker-compose at runtime.

---

## docker-compose

### What it is
Orchestrates multiple containers together. Defines all services, how they connect, ports, volumes, and environment variables in one file.

### Key commands
```bash
docker-compose up --build    # build images and start all containers
docker-compose up            # start without rebuilding
docker-compose down          # stop and remove containers
docker-compose logs          # view container logs
```

### Service names as hostnames
Containers in the same docker-compose file can reach each other using the service name as a hostname. So `db` resolves to the PostgreSQL container's IP automatically — no need for `localhost`.

### depends_on
```yaml
app:
  depends_on:
    - db
```
Waits for `db` container to start before starting `app`. Note: only waits for the container to start, not for PostgreSQL to be ready to accept connections.

### Volumes
```yaml
db:
  volumes:
    - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```
- Maps a named Docker volume to the PostgreSQL data directory
- Data persists across container restarts and deletions
- `volumes:` must be declared at the top level (same indentation as `services:`)

### Environment variable override
```yaml
app:
  env_file:
    - .env           # load all vars from .env
  environment:
    - DB_URL=...     # override specific vars
```
`environment` takes precedence over `env_file`.

---

## entrypoint.sh

### What it is
A shell script that runs before the main process starts. Used to run setup commands (like migrations) before the app starts.

### Pattern
```bash
#!/bin/bash
alembic upgrade head
uvicorn api.main:app --host 0.0.0.0
```

### Why needed
Docker's PostgreSQL container starts empty — no tables. Running `alembic upgrade head` in the entrypoint ensures tables are created before FastAPI starts accepting requests.

---

## .dockerignore

### What it is
Tells Docker which files to exclude from the build context. Without it, Docker sends everything in the project directory to the build process.

### What to exclude
- `venv/` — Docker installs its own dependencies via pip, no venv needed
- `tests/` — not needed at runtime
- `ml/`, `docker/` — docs/notes only
- `.git/` — git history not needed in the image
- `.env` — secrets must never be baked into the image
- `.pytest_cache/` — dev artefact

---

## PyTorch CPU-only install

### Why
Default `torch` from PyPI pulls in full CUDA support (~2GB of nvidia packages). Containers have no GPU, so CUDA is wasted space.

### How
Install PyTorch separately in Dockerfile before requirements.txt:
```dockerfile
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install -r requirements.txt
```
Reduces PyTorch from ~2GB to ~200MB.

---

## pg_isready loop

### The problem
`depends_on: db` only waits for the db container to start — not for PostgreSQL to be ready to accept connections. If alembic runs too early, it fails with "Connection refused".

### The fix
Use `pg_isready` in entrypoint.sh to poll until PostgreSQL is ready:
```bash
until pg_isready -h db -p 5432; do
  echo "Waiting for database..."
  sleep 1
done
alembic upgrade head
uvicorn api.main:app --host 0.0.0.0
```

### Why not sleep
`sleep` is a guess — too short and it still fails, too long and every startup is slower than needed.
