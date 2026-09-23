"""The shared FastMCP instance. Tool modules import `mcp` from here and register
themselves via the @mcp.tool() decorator; server.py imports the tool modules
for their side effect (registration) and then runs the transport.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "Job Application MCP",
    stateless_http=True,
    json_response=True,
    # Served bare ("/") because server.py mounts this whole ASGI app under
    # "/mcp" itself — without this it would double up as /mcp/mcp.
    streamable_http_path="/",
)
