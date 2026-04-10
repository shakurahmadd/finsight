# FinSight CI/CD — Project Log

## 2026-04-09

### What I did
- Created .github/workflows/ci.yml — GitHub Actions CI pipeline
- Added pytest to requirements.txt
- Added NEWS_API as a GitHub repository secret
- CI pipeline passing all 3 tests

### Decisions made
- Trigger on every push (`on: push`) — simple for now, can restrict to branches later
- Single job called `test` running on `ubuntu-latest`
- PostgreSQL spun up as a GitHub Actions service container — equivalent to docker-compose db service
- Host is `localhost` in CI (not `db` like in docker-compose) — no compose network in CI
- pg_isready loop used to wait for PostgreSQL to be ready before running migrations
- DB_URL set in job-level `env` — safe because it's a throwaway dev credential
- NEWS_API passed via `${{ secrets.NEWS_API }}` — stored as encrypted GitHub repository secret
- GROQ_API not needed yet — no tests cover the LLM pipeline

### Blockers / questions
- Next: deploy to AWS EC2

## 2026-04-09 / 2026-04-10

### What I did
- Launched AWS EC2 t3.micro instance (Amazon Linux 2023, free tier)
- Installed Docker, docker-compose v2.24.0, and git on the server
- Cloned repo from GitHub onto the server
- Created .env on the server with secrets
- Fixed pg_isready missing — added postgresql-client to Dockerfile
- Opened port 8000 in EC2 security group
- App fully deployed and accessible at http://13.48.106.201:8000/docs

### Decisions made
- t3.micro chosen — free tier eligible in eu-north-1 region
- Amazon Linux 2023 — AWS-optimised, lightweight
- Key pair (finsight.pem) stored in ~/.ssh/ with chmod 400 — SSH authentication
- docker-compose v2.24.0 installed manually — v5 required newer buildx not available on Amazon Linux
- postgresql-client installed in Dockerfile — provides pg_isready for the readiness loop
- Port 8000 opened in security group inbound rules — required for external access
- Secrets (.env) created directly on server — never committed to git
- docker-compose up -d — detached mode keeps app running after SSH session ends

### Blockers / questions
- MVP complete
