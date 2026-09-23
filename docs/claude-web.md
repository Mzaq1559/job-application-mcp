# Claude Web

1. Deploy the repository and obtain its public HTTPS URL.
2. In Claude, open Customize -> Connectors -> + -> Add custom connector.
3. Enter https://YOUR-SERVICE.onrender.com/mcp.
4. If Request headers are available, add:
   
   Authorization: Bearer YOUR_MCP_AUTH_TOKENS

5. Add the connector and enable it in a conversation.
6. Test with: Show my profile summary.

Claude's remote connector requests originate from Anthropic's cloud infrastructure, so the server must be publicly reachable.

If your Claude account does not expose request-header authentication, the current static bearer implementation cannot be authenticated through that UI. Do not make /mcp public; implement OAuth 2.1 before using it with that account.

