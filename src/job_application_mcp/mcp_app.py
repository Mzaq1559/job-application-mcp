"""The shared MCP server instance. Tool modules import `mcp` from here and
register themselves via the @mcp.tool() decorator; server.py imports the
tool modules for their side effect (registration) and then runs the
transport.

Note: this targets the `mcp` v2.x SDK, where the class historically named
`FastMCP` (mcp.server.fastmcp) was renamed to `MCPServer`
(mcp.server.mcpserver). See:
https://py.sdk.modelcontextprotocol.io/v2/migration/#fastmcp-renamed-to-mcpserver
"""

from __future__ import annotations

from mcp.server.mcpserver import MCPServer

mcp = MCPServer("Job Application MCP")
