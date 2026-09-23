"""Remote MCP server entrypoint.

Composes: health/ready endpoints (registered on the MCP server itself via
@mcp.custom_route, so they live as sibling routes with no extra Mount/prefix
layer — a Starlette Mount here previously caused a 307 redirect from /mcp to
/mcp/, which is exactly the kind of thing that silently breaks a real client)
and bearer-auth middleware around the streamable-HTTP app.
"""

from __future__ import annotations

import contextlib
import logging

import uvicorn
from starlette.requests import Request
from starlette.responses import JSONResponse

from job_application_mcp.config.settings import get_settings
from job_application_mcp.database.database import init_db

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
from job_application_mcp.mcp_app import mcp

logger = logging.getLogger("job_application_mcp")


@mcp.custom_route("/health", methods=["GET"])
async def health(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


@mcp.custom_route("/ready", methods=["GET"])
async def ready(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ready"})


class BearerAuthMiddleware:
    """Static shared-secret bearer auth in front of the /mcp endpoint only.

    Pure ASGI middleware (not BaseHTTPMiddleware) so it doesn't buffer or
    interfere with the streamable-HTTP transport's request/response streaming.

    This is a personal, single-user server, so a long random bearer token
    (MCP_AUTH_TOKENS) is used instead of standing up a full OAuth 2.1
    authorization server. See docs/security.md for the reasoning and for
    what a multi-user deployment would need instead.
    """

    def __init__(self, app, protected_prefix: str = "/mcp") -> None:
        self.app = app
        self.protected_prefix = protected_prefix

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or not scope["path"].startswith(self.protected_prefix):
            await self.app(scope, receive, send)
            return

        settings = get_settings()
        tokens = settings.auth_tokens

        async def deny(status: int, message: str) -> None:
            response = JSONResponse({"error": message}, status_code=status)
            await response(scope, receive, send)

        if not tokens:
            # Refuse to serve an unprotected MCP endpoint rather than
            # silently allowing open access when no token is configured.
            await deny(503, "Server has no MCP_AUTH_TOKENS configured; refusing to serve /mcp.")
            return

        headers = dict(scope.get("headers") or [])
        auth_header = headers.get(b"authorization", b"").decode("latin-1")
        if not auth_header.startswith("Bearer "):
            await deny(401, "Missing bearer token.")
            return

        token = auth_header.removeprefix("Bearer ").strip()
        if token not in tokens:
            await deny(401, "Invalid bearer token.")
            return

        await self.app(scope, receive, send)


def create_app():
    # mcp v2.x (MCPServer, formerly FastMCP): stateless_http + json_response
    # are recommended for production scalability (no server-side session
    # pinning required). streamable_http_path defaults to "/mcp", matching
    # what docs/claude-web.md tells the user to configure.
    mcp_asgi_app = mcp.streamable_http_app(json_response=True, stateless_http=True)
    mcp_asgi_app.add_middleware(BearerAuthMiddleware, protected_prefix="/mcp")

    # Run DB setup as part of the ASGI app's own startup, so this works
    # whether it's launched via main() below or via
    # `uvicorn job_application_mcp.server:app` directly (e.g. on a managed
    # platform that supplies its own process command).
    original_lifespan = mcp_asgi_app.router.lifespan_context

    @contextlib.asynccontextmanager
    async def lifespan_with_db_init(app):
        # Dev convenience: create tables directly if they don't exist yet.
        # Production deployments should run `alembic upgrade head` instead
        # (this is a no-op against an already-migrated database).
        await init_db()
        async with original_lifespan(app) as state:
            yield state

    mcp_asgi_app.router.lifespan_context = lifespan_with_db_init
    return mcp_asgi_app


app = create_app()


def main() -> None:
    settings = get_settings()
    logging.basicConfig(level=settings.log_level)
    uvicorn.run(app, host=settings.mcp_host, port=settings.mcp_port)


if __name__ == "__main__":
    main()
