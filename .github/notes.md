# FinSight CI/CD — Reference Notes

## GitHub Actions

### What it is
A CI/CD platform built into GitHub. On specified events (e.g. push), GitHub spins up a fresh virtual machine and runs your workflow automatically.

### Workflow file location
Must be at `.github/workflows/<name>.yml` — GitHub looks for this exact path.

### Workflow structure
```yaml
name: CI                    # display name
on: push                    # trigger

jobs:
  test:                     # job name (you choose)
    runs-on: ubuntu-latest  # machine to run on
    env:                    # environment variables for all steps
      DB_URL: ...
    services:               # containers to run alongside
      postgres:
        image: postgres:15
    steps:                  # ordered list of things to do
      - uses: actions/checkout@v3
      - run: pytest tests
```

### Key concepts
- **Job** — a set of steps that runs on one machine. Multiple jobs run in parallel by default.
- **Step** — a single action, either a pre-built action (`uses:`) or a shell command (`run:`)
- **Service** — a container that runs alongside the job (e.g. PostgreSQL)
- **Secret** — encrypted value stored in GitHub repo settings, referenced as `${{ secrets.NAME }}`

### Pre-built actions
- `actions/checkout@v3` — checks out your code onto the machine
- `actions/setup-python@v4` — installs Python

### Services vs docker-compose
| docker-compose | GitHub Actions |
|---|---|
| `services: db:` | `services: postgres:` |
| hostname: `db` | hostname: `localhost` |
| `depends_on` | pg_isready loop |

### Secrets
- Stored in GitHub repo → Settings → Secrets and variables → Actions
- Never appear in logs (shown as `***`)
- Referenced in workflow as `${{ secrets.SECRET_NAME }}`
- Use for real API keys and credentials — not throwaway dev passwords
