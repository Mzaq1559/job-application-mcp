# Deployment

## Render

The repository includes render.yaml for a Docker web service and managed PostgreSQL.

1. Open Render and choose New -> Blueprint.
2. Connect this GitHub repository and deploy the main branch.
3. When prompted for secrets, set MCP_AUTH_TOKENS to a long random value.
4. Leave AI_API_KEY empty unless the future AI layer is enabled.
5. Wait for the health check at /health to pass.

Render provides public HTTPS endpoints and managed PostgreSQL. The application also converts a standard postgresql:// URL into SQLAlchemy's postgresql+asyncpg:// form automatically.

### Smoke test

Set the deployed URL:

    export URL=https://YOUR-SERVICE.onrender.com

Then:

    curl -fsS "$URL/health"
    curl -fsS "$URL/ready"

The MCP endpoint is:

    https://YOUR-SERVICE.onrender.com/mcp

Without Authorization, /mcp must return 401.

With Authorization: Bearer YOUR_MCP_AUTH_TOKENS, the MCP initialize request should succeed.

## Important production notes

- PostgreSQL data is persistent.
- Uploaded resume files are currently stored on the container filesystem at /app/uploads. They are not yet durable across container replacement. Move uploads to object storage or attach a persistent disk before relying on the hosted service as the only copy.
- Alembic is installed but startup currently uses SQLAlchemy create_all. Add and run migrations before making schema changes in production.
- Keep MCP_AUTH_TOKENS secret and rotate it if exposed.
- The current server is single-user.

## Claude Web authentication

Anthropic's current custom connector flow is OAuth-oriented. Some Claude organizations/accounts also expose request-header authentication.

If your Claude connector UI shows Request headers, configure:

    Authorization: Bearer YOUR_MCP_AUTH_TOKENS

with the URL:

    https://YOUR-SERVICE.onrender.com/mcp

If Request headers are unavailable, do not disable authentication. The next required hardening step is OAuth 2.1 with dynamic client registration and PKCE.

## Cost

The Blueprint uses a small paid web service and small managed Postgres instance so the MCP server does not depend on free-tier cold starts. Render's current published pricing lists the 0.5 CPU / 512 MB web plan at $7/month and the 0.1 CPU / 256 MB Postgres plan at $6/month, before other usage. Check Render's pricing page before deploying.
