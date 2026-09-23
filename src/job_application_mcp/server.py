"""Remote MCP server entrypoint.

Composes: health/ready endpoints, bearer-auth middleware, and the FastMCP
streamable-HTTP app, all served over one HTTPS-fronted process.
"""

from __future__ import annotations

import contextlib
import logging

import uvicorn
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

from job_application_mcp.config.settings import get_settings
from job_application_mcp.database.database import init_db
from job_application_mcp.mcp_app import mcp

# Imported for their side effect: each module registers its tools on the
# shared `mcp` instance via @mcp.tool(). The noqa is because the names
# themselves are never referenced below.
from job_application_mcp.mcp.tools import (  # noqa: F401
    application_tools,
    interview_tools,
    job_tools,
    profile_tools,
    resume_tools,
)

logger = logging.getLogger("job_application_mcp")


class BearerAuthMiddleware(BaseHTTPMiddleware):
    """Static shared-secret bearer auth in front of the /mcp endpoint.

    This is a personal, single-user server, so a long random bearer token
    (MCP_AUTH_TOKENS) is used instead of standing up a full OAuth 2.1
    authorization server. See docs/security.md for the reasoning and for
    what you'd need to add for a multi-user deployment.
    """

    def __init__(self, app, protected_prefix: str = "/mcp") -> None:
        super().__init__(app)
        self.protected_prefix = protected_prefix

    async def dispatch(self, request: Request, call_next):
        if not request.url.path.startswith(self.protected_prefix):
            return await call_next(request)

        settings = get_settings()
        tokens = settings.auth_tokens
        if not tokens:
            # Refuse to serve an unprotected MCP endpoint rather than silently
            # allowing open access when no token has been configured.
            return JSONResponse(
                {"error": "Server has no MCP_AUTH_TOKENS configured; refusing to serve /mcp."},
                status_code=503,
            )

        auth_header = request.headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse({"error": "Missing bearer token."}, status_code=401)

        token = auth_header.removeprefix("Bearer ").strip()
        if token not in tokens:
            return JSONResponse({"error": "Invalid bearer token."}, status_code=401)

        return await call_next(request)


async def health(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


async def ready(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ready"})


def create_app() -> Starlette:
    mcp_asgi_app = mcp.streamable_http_app()

    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette):
        # Dev convenience: create tables directly if they don't exist yet.
        # Production deployments should run `alembic upgrade head` instead
        # and can skip this (it's a no-op against an already-migrated DB).
        await init_db()
        async with mcp.session_manager.run():
            yield

    return Starlette(
        routes=[
            Route("/health", health),
            Route("/ready", ready),
            Mount("/mcp", app=mcp_asgi_app),
        ],
        middleware=[Middleware(BearerAuthMiddleware, protected_prefix="/mcp")],
        lifespan=lifespan,
    )


app = create_app()


def main() -> None:
    settings = get_settings()
    logging.basicConfig(level=settings.log_level)
    uvicorn.run(app, host=settings.mcp_host, port=settings.mcp_port)


if __name__ == "__main__":
    main()
