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
