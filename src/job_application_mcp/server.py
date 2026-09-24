"""Remote MCP server entrypoint with OAuth 2.1 resource-server authentication."""

from __future__ import annotations

import contextlib
import logging

import uvicorn
from mcp.server.transport_security import TransportSecuritySettings
from starlette.requests import Request
from starlette.responses import JSONResponse

from job_application_mcp.config.settings import get_settings
from job_application_mcp.database.database import init_db
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


def create_app():
    # OAuth (auth / token_verifier) is configured on the MCPServer instance
    # itself in mcp_app.py — this SDK version's streamable_http_app() only
    # accepts transport-level options, not auth.
    # Azure Container Apps terminates the public connection before forwarding
    # it to this container. The MCP endpoint is already protected by the
    # OAuth bearer-token middleware, so SDK Host-header DNS-rebinding checks
    # are not useful at this public edge and were rejecting Azure's forwarded
    # Host header with HTTP 421. Disable only this SDK-level check; OAuth
    # authentication remains enforced by MCPServer.
    transport_security = TransportSecuritySettings(
        enable_dns_rebinding_protection=False,
    )

    # Use the standard stateful Streamable HTTP/SSE transport for maximum
    # compatibility with hosted MCP clients such as Claude Web. JSON-only
    # responses and legacy stateless mode are optional SDK modes and can cause
    # clients that expect the normal Streamable HTTP session flow to reject the
    # endpoint even though the server itself is reachable.
    mcp_asgi_app = mcp.streamable_http_app(
        transport_security=transport_security,
    )

    original_lifespan = mcp_asgi_app.router.lifespan_context

    @contextlib.asynccontextmanager
    async def lifespan_with_db_init(app):
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
