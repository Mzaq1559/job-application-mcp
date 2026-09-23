# Job Application MCP

A personal job-application assistant, exposed as a remote MCP server for **Claude Web**. It manages your profile, resumes, job analysis, and application tracking — it does **not** scrape or automate any job platform. Job descriptions are supplied by you (pasted or typed); the final submission is always done by you, manually.

> Status: core MCP server is running and verified end-to-end (21 tools, real JSON-RPC handshake, bearer auth). See [Roadmap](#roadmap) for what's left before a production deploy.

## Why no scraping/automation

Platforms like LinkedIn explicitly prohibit automated scraping and bot-driven activity in their Terms of Service, and have pursued account bans and legal action over it. This project only ever works from information you provide directly — it never logs into or automates a third-party site on your behalf.

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

## MCP tools implemented

`profile_get`, `profile_update`, `profile_summary` · `resume_list`, `resume_get`, `resume_upload`, `resume_update`, `resume_delete`, `resume_select_for_job` · `job_create`, `job_get`, `job_list`, `job_analyze`, `job_update_status` · `application_create`, `application_get`, `application_list`, `application_update_status`, `application_history`, `application_delete` · `interview_create`, `interview_list`, `interview_update`, `interview_notes`

Every tool's description is explicit about what it does and doesn't do — e.g. `job_create` states it never fetches or scrapes a URL itself, and `application_update_status` states that moving to `applied` only records what the user reports, it never submits anything.

## Tech stack

- Python 3.12+, official `mcp` SDK v2.x (`MCPServer`, Streamable HTTP transport)
- Starlette, Pydantic, SQLAlchemy (async), Alembic
- SQLite (dev) / PostgreSQL (prod) — swap via `DATABASE_URL` only
- Docker, GitHub Actions

## Roadmap

- [x] Repo scaffold, license, `.gitignore`, `pyproject.toml`
- [x] Settings (env-driven config)
- [x] Database models (Profile, Resume, ResumeVersion, Job, Application, ApplicationDocument, ScreeningQuestion, Interview, InterviewNote, ApplicationEvent)
- [x] Service layer (profile, resume, job, application, interview)
- [x] MCP server + tools, verified end-to-end over HTTP (health check, bearer auth, `initialize`, `tools/list`)
- [x] Unit tests (16 passing) + clean `ruff` lint
- [ ] Alembic migrations (currently uses `create_all` for dev convenience)
- [ ] AI provider abstraction + prompts (no-fabrication rules) for deeper job analysis and cover-letter generation
- [ ] Integration tests against the running HTTP server
- [ ] Docker + docker-compose
- [ ] CI (lint + tests)
- [ ] Deployment guide
- [ ] Claude Web connector guide

## License

MIT — see [LICENSE](LICENSE).
