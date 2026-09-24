FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps: curl for the HEALTHCHECK, build-essential for any C extensions
# pulled in transitively (e.g. asyncpg).
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md LICENSE ./
COPY src ./src

RUN pip install --no-cache-dir .

# Non-root user.
RUN useradd --create-home --uid 1000 appuser \
    && mkdir -p /app/data /app/uploads \
    && chown -R appuser:appuser /app
USER appuser

ENV MCP_HOST=0.0.0.0 \
    MCP_PORT=8000 \
    DATABASE_URL=sqlite+aiosqlite:////app/data/app.db \
    UPLOAD_DIR=/app/uploads

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://127.0.0.1:${MCP_PORT}/health || exit 1

CMD ["uvicorn", "job_application_mcp.server:app", "--host", "0.0.0.0", "--port", "8000"]
