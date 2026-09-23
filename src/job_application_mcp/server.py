"""Remote MCP server entrypoint with OAuth 2.1 resource-server authentication."""
from __future__ import annotations

import contextlib
import logging

import uvicorn
from starlette.requests import Request
from starlette.responses import JSONResponse

from job_application_mcp.auth import Auth0TokenVerifier, build_auth_settings
from job_application_mcp.config.settings import get_settings
from job_application_mcp.database.database import init_db
from job_application_mcp.mcp_app import mcp
from job_application_mcp.mcp.tools import (  # noqa: F401
    application_tools,
    interview_tools,
    job_tools,
    profile_tools,
    resume_tools,
)


logger = logging.getLogger("job_application_mcp")


@mcp.custom_route("/health", methods=["GET"])
async def health(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


@mcp.custom_route("/ready", methods=["GET"])
async def ready(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ready"})


def create_app():
    settings = get_settings()
    if not settings.oauth_issuer_url:
        raise RuntimeError(
            "OAUTH_ISSUER_URL must be configured for the remote MCP server."
        )
    if not settings.oauth_audience:
        raise RuntimeError(
            "OAUTH_AUDIENCE must be configured for the remote MCP server."
        )
    if not settings.oauth_resource_url:
        raise RuntimeError(
            "OAUTH_RESOURCE_URL must be configured for the remote MCP server."
        )

    verifier = Auth0TokenVerifier(
        issuer_url=settings.oauth_issuer_url,
        audience=settings.oauth_audience,
        jwks_url=settings.oauth_jwks_url or None,
    )
    auth = build_auth_settings(
        issuer_url=settings.oauth_issuer_url,
        resource_url=settings.oauth_resource_url,
        required_scope=settings.oauth_required_scope,
    )
    mcp_asgi_app = mcp.streamable_http_app(
        json_response=True,
        stateless_http=True,
        auth=auth,
        token_verifier=verifier,
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
