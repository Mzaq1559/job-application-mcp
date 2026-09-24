# Claude Web

The remote server is deployed on Azure Container Apps. Get the hostname with:

    az containerapp show --name job-application-mcp --resource-group job-application-mcp-rg --query properties.configuration.ingress.fqdn --output tsv

Current MCP URL:

    https://job-application-mcp.happygrass-de5f577c.centralindia.azurecontainerapps.io/mcp

## Authentication architecture

The server uses OAuth 2.1 as an MCP resource server:

    Claude Web
    │ OAuth 2.1 + PKCE
    ▼
    Auth0 Authorization Server
    │ RS256 JWT access token
    ▼
    Job Application MCP (/mcp)

The MCP SDK publishes RFC 9728 protected-resource metadata and requires a valid bearer access token on /mcp. The server verifies the Auth0 JWT locally using Auth0's JWKS.

## Auth0 setup

1. Create or use an Auth0 tenant.
2. In Applications → APIs, create an API.
3. Use the exact MCP URL as the API Identifier:

       https://job-application-mcp.happygrass-de5f577c.centralindia.azurecontainerapps.io/mcp

4. Keep the API signing algorithm at RS256.
5. Add the API permission/scope:

       mcp:access

6. In Applications → Advanced Settings → OAuth, enable the Resource Parameter Compatibility Profile if your tenant requires it. MCP clients send the RFC 8707 resource parameter, and Auth0 documents this compatibility setting for MCP integrations.
7. In Applications, create a Regular Web Application for Claude.
8. Add this Allowed Callback URL:

       https://claude.ai/api/mcp/auth_callback

9. Keep the application Client ID and Client Secret private. You will enter them in Claude's custom connector Advanced settings.

## Azure environment variables

Configure these Container App environment variables:

    OAUTH_ISSUER_URL=https://YOUR-AUTH0-DOMAIN/
    OAUTH_AUDIENCE=https://job-application-mcp.happygrass-de5f577c.centralindia.azurecontainerapps.io/mcp
    OAUTH_RESOURCE_URL=https://job-application-mcp.happygrass-de5f577c.centralindia.azurecontainerapps.io/mcp
    OAUTH_REQUIRED_SCOPE=mcp:access

OAUTH_JWKS_URL can be omitted; the server derives Auth0's standard JWKS endpoint from the issuer.

Do not configure the old MCP_AUTH_TOKENS secret for the OAuth deployment. The OAuth access token replaces the shared bearer secret.

## Deploying the OAuth configuration

After building and pushing the updated image, set the environment variables:

    az containerapp update \
      --name job-application-mcp \
      --resource-group job-application-mcp-rg \
      --set-env-vars \
        "OAUTH_ISSUER_URL=https://YOUR-AUTH0-DOMAIN/" \
        "OAUTH_AUDIENCE=https://job-application-mcp.happygrass-de5f577c.centralindia.azurecontainerapps.io/mcp" \
        "OAUTH_RESOURCE_URL=https://job-application-mcp.happygrass-de5f577c.centralindia.azurecontainerapps.io/mcp" \
        "OAUTH_REQUIRED_SCOPE=mcp:access"

Verify the public metadata endpoint:

    curl -i https://job-application-mcp.happygrass-de5f577c.centralindia.azurecontainerapps.io/.well-known/oauth-protected-resource/mcp

It should return JSON describing the MCP resource and the Auth0 issuer.

Verify unauthenticated MCP access:

    curl -i https://job-application-mcp.happygrass-de5f577c.centralindia.azurecontainerapps.io/mcp

It should return 401 Unauthorized and a WWW-Authenticate header pointing to the protected-resource metadata.

## Connect Claude

For Claude Pro/Max:

1. Open Customize → Connectors.
2. Click + → Add custom connector.
3. Name it Job Application MCP.
4. Enter the MCP URL:

       https://job-application-mcp.happygrass-de5f577c.centralindia.azurecontainerapps.io/mcp

5. Open Advanced settings.
6. Enter the Auth0 Client ID and Client Secret from the Regular Web Application.
7. Add the connector.
8. Click Connect and complete the Auth0 Universal Login/consent flow.
9. Enable the connector in a chat and test with:

       Show my profile summary.

Anthropic's current custom-connector documentation says custom remote MCP connectors use a public HTTPS endpoint and can accept OAuth client ID/secret in Advanced settings.

## Security notes

- Never paste an Auth0 Client Secret or access token into GitHub, chat, or source control.
- The old static MCP bearer token should remain revoked/unused.
- Auth0 API signing should remain RS256.
- The MCP resource URL must exactly match the API Identifier and OAUTH_RESOURCE_URL.