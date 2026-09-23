from __future__ import annotations

import pytest
import pytest_asyncio


@pytest.fixture(autouse=True)
def _isolated_env(tmp_path, monkeypatch):
    """Give every test a fresh SQLite file and a fresh Settings cache, so tests
    never touch a developer's real ./data/app.db and never leak state between
    tests."""
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{db_path}")
    monkeypatch.setenv("MCP_AUTH_TOKENS", "test-token")
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))

    from job_application_mcp.config.settings import get_settings
    from job_application_mcp.database import database as db_module

    get_settings.cache_clear()
    db_module._engine = None
    db_module._session_factory = None
    yield
    get_settings.cache_clear()
    db_module._engine = None
    db_module._session_factory = None


@pytest_asyncio.fixture
async def db_session():
    from job_application_mcp.database.database import init_db, session_scope

    await init_db()
    async with session_scope() as session:
        yield session
