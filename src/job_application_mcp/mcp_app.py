"""The shared MCP server instance. Tool modules import `mcp` from here and
register themselves via the @mcp.tool() decorator; server.py imports the
tool modules for their side effect (registration) and then runs the
transport.

Note: this targets the `mcp` v2.x SDK, where the class historically named
`FastMCP` (mcp.server.fastmcp) was renamed to `MCPServer`
(mcp.server.mcpserver). See:
https://py.sdk.modelcontextprotocol.io/v2/migration/#fastmcp-renamed-to-mcpserver

OAuth 2.1 resource-server auth (`auth` / `token_verifier`) is configured here,
at MCPServer construction time — in this SDK version that's where those
parameters actually live. They are NOT accepted by streamable_http_app()
(see server.py), which only takes transport-level options.
"""

from __future__ import annotations

from mcp.server.mcpserver import MCPServer

from job_application_mcp.auth import Auth0TokenVerifier, build_auth_settings
from job_application_mcp.config.settings import get_settings

_settings = get_settings()

if not _settings.oauth_issuer_url:
    raise RuntimeError("OAUTH_ISSUER_URL must be configured for the remote MCP server.")
if not _settings.oauth_audience:
    raise RuntimeError("OAUTH_AUDIENCE must be configured for the remote MCP server.")
if not _settings.oauth_resource_url:
    raise RuntimeError("OAUTH_RESOURCE_URL must be configured for the remote MCP server.")

_verifier = Auth0TokenVerifier(
    issuer_url=_settings.oauth_issuer_url,
    audience=_settings.oauth_audience,
    jwks_url=_settings.oauth_jwks_url or None,
)
_auth = build_auth_settings(
    issuer_url=_settings.oauth_issuer_url,
    resource_url=_settings.oauth_resource_url,
    required_scope=_settings.oauth_required_scope,
)

mcp = MCPServer("Job Application MCP", auth=_auth, token_verifier=_verifier)
