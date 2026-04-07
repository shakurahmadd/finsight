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
