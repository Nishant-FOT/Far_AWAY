# Running the Disaster Intelligence Platform

Prerequisites:
- Docker Desktop (or Docker Engine) with docker-compose
- Node.js 18+ (for local frontend dev)
- Python 3.10/3.11 for local backend dev (optional)

Quick start (Docker):

1. From repository root run:

```bash
docker-compose -f docker-compose.full.yml pull
docker-compose -f docker-compose.full.yml build --no-cache
docker-compose -f docker-compose.full.yml up -d
```

2. Check services:

```bash
docker-compose -f docker-compose.full.yml ps
docker-compose -f docker-compose.full.yml logs -f <service>
```

PowerShell note: use `curl.exe` (not `curl -sS`) or use `Invoke-RestMethod` for health checks:

```powershell
curl.exe http://localhost:8004/api/v1/health
Invoke-RestMethod -Uri http://localhost:8004/api/v1/health
```

Frontend (local dev):

```bash
cd frontend
npm install
npm run dev
```

Run tests (example):

```bash
# from repo root
pytest -q
```

Optional: add Qdrant to `docker-compose.full.yml` (service name `qdrant`) to allow `Learning_agent` to index vectors.

Stop and cleanup:

```bash
docker-compose -f docker-compose.full.yml down --volumes --remove-orphans
```

If you want, I can add a `qdrant` service snippet to the compose file and bring it up now.

Status: I scaffolded a minimal Next.js frontend and added it to `docker-compose.full.yml`. The frontend is buildable with `npm run build` and served by the included `Dockerfile` on port `3000`.

Ports (expected):
- Detection Agent: 8000
- Assessment Agent: 8001
- Disaster Agents: 8002
- Prediction Agent: 8003
- Learning Agent: 8004
- Frontend (Next.js): 3000
- Ollama: 11434