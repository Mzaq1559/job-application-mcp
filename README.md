# Job Application MCP

A personal job-application assistant, exposed as a remote MCP server for **Claude Web**. It manages your profile, resumes, job analysis, and application tracking — it does **not** scrape or automate any job platform. Job descriptions are supplied by you (pasted or typed); the final submission is always done by you, manually.

> Status: early scaffold (Phase 1–2 of the build). See [Roadmap](#roadmap).

## Why no scraping/automation

Platforms like LinkedIn explicitly prohibit automated scraping and bot-driven activity in their Terms of Service, and have pursued account bans and legal action over it. This project only ever works from information you provide directly — it never logs into or automates a third-party site on your behalf.

## Architecture

```text
Claude Web
    │  MCP over Streamable HTTP (bearer auth)
    ▼
Remote MCP Server (FastAPI + official MCP Python SDK)
    │
    ├── Profile Service
    ├── Resume/CV Service
    ├── Job Analysis Service (AI-assisted, evidence-based, no fabrication)
    ├── Application Preparation Service
    ├── Application Tracking Service
    ├── Interview Service
    └── Database (SQLAlchemy — SQLite in dev, PostgreSQL in prod)
```

## Tech stack

- Python 3.12+, official `mcp` SDK (Streamable HTTP transport)
- FastAPI, Pydantic, SQLAlchemy (async), Alembic
- SQLite (dev) / PostgreSQL (prod) — swap via `DATABASE_URL` only
- Docker, GitHub Actions

## Roadmap

- [x] Repo scaffold, license, `.gitignore`, `pyproject.toml`
- [x] Settings (env-driven config)
- [x] Database models (Profile, Resume, ResumeVersion, Job, Application, ApplicationDocument, ScreeningQuestion, Interview, InterviewNote, ApplicationEvent)
- [ ] Alembic migrations
- [ ] Service layer (profile, resume, job, application, interview)
- [ ] MCP server + tools (`profile_*`, `resume_*`, `job_*`, `application_*`, `interview_*`)
- [ ] AI provider abstraction + prompts (no-fabrication rules)
- [ ] Tests (unit + integration)
- [ ] Docker + docker-compose
- [ ] CI (lint + tests)
- [ ] Deployment guide
- [ ] Claude Web connector guide

## License

MIT — see [LICENSE](LICENSE).
