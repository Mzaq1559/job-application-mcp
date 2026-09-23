![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)
![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)
![Status: pre-1.0](https://img.shields.io/badge/status-pre--1.0-orange.svg)

# Job Application MCP

A personal job-application assistant, exposed as a remote [MCP](https://modelcontextprotocol.io) server for **Claude Web**. It manages your profile, resumes, job analysis, and application tracking. It does **not** scrape or automate any job platform — job descriptions are supplied by you (pasted or typed), and the final submission is always done by you, manually.

> **Status:** the core server is implemented and verified end-to-end (21 MCP tools, real JSON-RPC handshake over HTTP, bearer auth, Docker build, and CI). A Render deployment Blueprint is included; public deployment and Claude connector authentication remain the final operational steps.

## Table of contents

- [Why no scraping or automation](#why-no-scraping-or-automation)
- [Features](#features)
- [Architecture](#architecture)
- [MCP tools](#mcp-tools)
- [Tech stack](#tech-stack)
- [Project structure](#project-structure)
- [Getting started](#getting-started)
- [Environment variables](#environment-variables)
- [Database](#database)
- [Running tests](#running-tests)
- [Docker](#docker)
- [Deployment](#deployment)
- [Connecting to Claude Web](#connecting-to-claude-web)
- [Example prompts](#example-prompts)
- [Security](#security)
- [Limitations](#limitations)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)

## Why no scraping or automation

Platforms like LinkedIn explicitly prohibit automated scraping and bot-driven activity in their Terms of Service, and have pursued account suspensions and legal action over it. This project deliberately stays on the right side of that line: it only ever works from information *you* provide directly (pasted job descriptions, uploaded resumes), and it never logs into, scrapes, or automates form submission on a third-party site. You stay in control of every application you actually send.

## Features

- **Profile management** — one structured profile (education, skills, projects, experience, research interests, certifications, achievements) that every other tool reads from. Nothing about you is hard-coded into the source.
- **Resume/CV management** — upload multiple resumes (PDF, DOCX, TXT, MD), keep multiple versions of each, and get a transparent, keyword-based recommendation for which resume fits a given job description.
- **Job tracking** — save jobs with full description/requirements text, automatic duplicate detection (by URL, then by company+title), and a status workflow (`saved → analyzing → ready_to_apply → applied → screening → interview → offer`, with `rejected`/`withdrawn` reachable from most states).
- **Transparent job analysis** — literal keyword comparison between a job's text and your stored skills. No fabricated "hireability score" — matches and gaps are reported plainly so you can judge fit yourself.
- **Application tracking** — persistent records per job, full event history, and duplicate-application prevention. Nothing is ever marked `applied` except in response to *you* telling Claude you submitted it — the tools never submit anything themselves.
- **Interview tracking** — scheduled interviews, prep/post-interview notes, linked to the application they belong to.

## Architecture

```text
Claude Web
    │  MCP over Streamable HTTP (bearer auth)
    ▼
Remote MCP Server (Starlette + official `mcp` v2.x SDK)
    │
    ├── Profile Service
    ├── Resume/CV Service        (upload, versioning, text extraction, keyword-based selection)
    ├── Job Service               (create, duplicate detection, transparent keyword analysis)
    ├── Application Service       (create, status workflow, duplicate rejection, event history)
    ├── Interview Service
    └── Database (SQLAlchemy async — SQLite in dev, PostgreSQL in prod)
```

## MCP tools

| Domain | Tools |
|---|---|
| Profile | `profile_get`, `profile_update`, `profile_summary` |
| Resume | `resume_list`, `resume_get`, `resume_upload`, `resume_update`, `resume_delete`, `resume_select_for_job` |
| Job | `job_create`, `job_get`, `job_list`, `job_analyze`, `job_update_status` |
| Application | `application_create`, `application_get`, `application_list`, `application_update_status`, `application_history`, `application_delete` |
| Interview | `interview_create`, `interview_list`, `interview_update`, `interview_notes` |

Every tool's description is explicit about what it does and doesn't do. For example: `job_create` states it never fetches or scrapes a URL itself — the job description must come from you; `application_update_status` states that moving an application to `applied` only records what you report, it never submits anything on your behalf; destructive tools (`resume_delete`, `application_delete`) require an explicit `confirm=true` flag.

## Tech stack

- **Python 3.12+**, official [`mcp`](https://github.com/modelcontextprotocol/python-sdk) SDK v2.x (`MCPServer`, Streamable HTTP transport)
- **Starlette** for the ASGI app, **Pydantic** for validation, **SQLAlchemy** (async) + **Alembic** for the database
- **SQLite** in development, **PostgreSQL** in production — swap by changing `DATABASE_URL` only, no code changes
- **pypdf** / **python-docx** for resume text extraction
- **Docker** for packaging; **pytest** + **ruff** for tests and linting

## Project structure

```text
job-application-mcp/
├── src/job_application_mcp/
│   ├── server.py              # ASGI app: health/ready routes, bearer auth, uvicorn entrypoint
│   ├── mcp_app.py             # shared MCPServer instance
│   ├── config/settings.py     # env-driven configuration
│   ├── database/              # SQLAlchemy engine/session + models
│   ├── models/                # Pydantic schemas at the MCP tool boundary
│   ├── services/               # business logic (profile, resume, job, application, interview)
│   ├── mcp/tools/               # MCP tool definitions, one module per domain
│   └── utils/                  # document text extraction, upload validation
├── tests/unit/                 # service-layer unit tests
├── Dockerfile, docker-compose.yml
├── pyproject.toml
└── .env.example
```

## Getting started

Requires Python 3.12+.

```bash
git clone https://github.com/Mzaq1559/job-application-mcp.git
cd job-application-mcp
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

cp .env.example .env
# edit .env: at minimum, set MCP_AUTH_TOKENS to a random secret
python -c "import secrets; print(secrets.token_urlsafe(32))"

python -m job_application_mcp.server
```

The server starts on `http://0.0.0.0:8000` by default. Check it's alive:

```bash
curl http://localhost:8000/health
# {"status": "ok"}
```

## Environment variables

See [`.env.example`](.env.example) for the full, current list. The essentials:

| Variable | Purpose | Default |
|---|---|---|
| `DATABASE_URL` | SQLAlchemy async connection string | `sqlite+aiosqlite:///./data/app.db` |
| `MCP_AUTH_TOKENS` | Comma-separated bearer token(s) required on `/mcp` | *(empty — server refuses to serve `/mcp` until set)* |
| `MCP_HOST` / `MCP_PORT` | Bind address | `0.0.0.0` / `8000` |
| `UPLOAD_DIR` | Where resume files are stored on disk | `./uploads` |
| `AI_PROVIDER` / `AI_API_KEY` / `AI_MODEL` | Reserved for the AI-assisted analysis layer (not yet implemented) | — |

## Database

Development uses SQLite and creates tables automatically on server startup — nothing to run manually. Production should point `DATABASE_URL` at PostgreSQL; Alembic migrations for that path are on the [roadmap](#roadmap) but not yet implemented (the auto-create-on-startup behavior works against Postgres too in the meantime).

## Running tests

```bash
pip install -e ".[dev]"
pytest -q          # 16 tests, run against an isolated per-test SQLite database
ruff check .        # lint
```

## Docker

```bash
docker compose up --build
```

This starts the app plus a PostgreSQL container. Set a real `MCP_AUTH_TOKENS` value in `docker-compose.yml` (or via an env file) before using it for anything beyond local testing — the checked-in value is a placeholder.

To build and run standalone (SQLite, no Postgres container):

```bash
docker build -t job-application-mcp .
docker run -p 8000:8000 -e MCP_AUTH_TOKENS=your-secret-here job-application-mcp
```

## Deployment

Any platform that runs a long-lived container works — the server just needs a public HTTPS URL and a couple of environment variables. Options that fit a personal, single-user deployment like this one:

- **Render** or **Railway** — connect the GitHub repo, they build the `Dockerfile` automatically, set env vars in their dashboard, get a public HTTPS URL.
- **Azure Container Apps** — a good fit if you have Azure for Students credit; deploy the same `Dockerfile` via `az containerapp up` or the portal's "deploy from GitHub" flow.
- **Fly.io** — `fly launch` against this repo's `Dockerfile`.

Whichever you use, at minimum set:

```text
DATABASE_URL=<sqlite path on a persistent volume, or a managed Postgres URL>
MCP_AUTH_TOKENS=<a long random secret — generate with secrets.token_urlsafe(32)>
```

A step-by-step guide for one specific platform will land in `docs/deployment.md`.

## Connecting to Claude Web

Once deployed, add it in Claude Web as a **custom remote MCP connector**, pointing at:

```text
https://<your-deployed-domain>/mcp
```

with the bearer token you set in `MCP_AUTH_TOKENS` as the connector's auth credential. The exact steps/labels in Claude's UI can change — follow [Claude's current documentation](https://docs.claude.com) for adding a custom connector if what you see doesn't match an older guide. A dedicated walkthrough will land in `docs/claude-web.md`.

## Example prompts

Once connected, things like:

- *"Here's a job description I found — [paste text]. Save it and tell me how well I match it."*
- *"Which of my resumes fits this job best?"*
- *"I just submitted the ML intern application at Example Co — mark it as applied."*
- *"What applications do I have in the interview stage?"*

## Security

- The `/mcp` endpoint is protected by a static bearer token (`MCP_AUTH_TOKENS`); the server refuses to serve it at all if no token is configured, rather than defaulting to open access.
- No secrets, `.env` files, or database files are committed — see `.gitignore` / `.dockerignore`.
- File uploads are validated by extension and size, and filenames are checked for path traversal before being written to disk.
- The Docker image runs as a non-root user.
- This is a single-user server by design — see [Limitations](#limitations) for what that means for auth.

## Limitations

- **Single-user.** Auth is one shared bearer token, not per-user OAuth. Fine for personal use; not meant to be handed out to multiple people.
- **No AI-assisted analysis yet.** Resume selection and job analysis are transparent keyword-matching heuristics, not LLM-based reasoning — by design, so there's nothing to audit for fabrication yet. A proper AI-assisted layer (with explicit no-fabrication prompt rules) is on the roadmap.
- **No migrations yet.** Schema changes currently mean dropping and recreating tables in development; Alembic migrations for safe production upgrades aren't wired up yet.
- **Never submits anything.** By design, not a bug — this project prepares and tracks applications; you always click submit yourself.

## Roadmap

- [x] Repo scaffold, license, `.gitignore`, `pyproject.toml`
- [x] Settings (env-driven config)
- [x] Database models (Profile, Resume, ResumeVersion, Job, Application, ApplicationDocument, ScreeningQuestion, Interview, InterviewNote, ApplicationEvent)
- [x] Service layer (profile, resume, job, application, interview)
- [x] MCP server + tools, verified end-to-end over HTTP (health check, bearer auth, `initialize`, `tools/list`)
- [x] Unit tests (16 passing) + clean `ruff` lint
- [x] Docker + docker-compose, verified with a production-equivalent install and boot
- [x] CI (GitHub Actions for lint + tests)
- [ ] Alembic migrations
- [ ] AI provider abstraction + prompts (no-fabrication rules) for deeper job analysis and cover-letter generation
- [ ] Integration tests against the running HTTP server
- [x] Render deployment Blueprint (`render.yaml`)
- [ ] Public deployment
- [ ] OAuth 2.1 for Claude Web accounts without static request-header support
- [ ] Durable resume-file storage

## Contributing

This started as a personal project, but issues and PRs are welcome — especially around the AI-assisted analysis layer, Alembic migrations, or additional ATS-adjacent tooling that doesn't involve scraping or unauthorized automation.

## License

MIT — see [LICENSE](LICENSE).
