# Azure Container Apps Deployment

This project is intended for Azure Container Apps Consumption. Azure currently provides a monthly free grant for Container Apps Consumption, including 180,000 vCPU-seconds, 360,000 GiB-seconds, and 2 million requests per subscription; usage beyond the grant is billed. citeturn0search4

## 1. Create the app

From the repository root:

    az login
    az extension add --name containerapp --upgrade
    az containerapp up --name job-application-mcp --resource-group job-application-mcp-rg --location centralindia --source . --ingress external --target-port 8000

Azure documents `az containerapp up` as a way to deploy from local source or GitHub, using the Dockerfile when present. citeturn0search1turn0search2

## 2. Configure the MCP secret

Generate a token locally:

    python -c "import secrets; print(secrets.token_urlsafe(32))"

Store it as a Container Apps secret:

    az containerapp secret set --name job-application-mcp --resource-group job-application-mcp-rg --secrets mcp-auth-token='PASTE_TOKEN_HERE'

Reference it from the environment:

    az containerapp update --name job-application-mcp --resource-group job-application-mcp-rg --set-env-vars MCP_AUTH_TOKENS=secretref:mcp-auth-token APP_ENV=production LOG_LEVEL=INFO MCP_HOST=0.0.0.0 MCP_PORT=8000

Azure supports secret references with `secretref:`. citeturn1search2turn1search5

## 3. Configure PostgreSQL

For production, set `DATABASE_URL` to durable PostgreSQL. Azure Database for PostgreSQL can use your Azure for Students credit, or another PostgreSQL provider can be used if you need to avoid Azure database charges.

Example format:

    postgresql+asyncpg://USER:PASSWORD@HOST:5432/DATABASE

Store it as a secret:

    az containerapp secret set --name job-application-mcp --resource-group job-application-mcp-rg --secrets database-url='PASTE_DATABASE_URL_HERE'

Then reference it:

    az containerapp update --name job-application-mcp --resource-group job-application-mcp-rg --set-env-vars DATABASE_URL=secretref:database-url

Do not commit database credentials.

## 4. Keep it cheap

Use scale-to-zero and one maximum replica for this single-user MCP server:

    az containerapp update --name job-application-mcp --resource-group job-application-mcp-rg --min-replicas 0 --max-replicas 1 --scale-rule-name http-scale --scale-rule-type http --scale-rule-http-concurrency 1

Azure supports minimum replicas of 0 and HTTP scaling. No usage charges apply while an app is scaled to zero. citeturn1search0turn1search1

The trade-off is a cold start after inactivity. If Claude times out on the first request, set minimum replicas to 1, accepting the additional usage cost.

## 5. Verify

Get the public hostname:

    az containerapp show --name job-application-mcp --resource-group job-application-mcp-rg --query properties.configuration.ingress.fqdn --output tsv

Then test:

    export URL=https://YOUR-FQDN
    curl -fsS $URL/health
    curl -fsS $URL/ready
    curl -i $URL/mcp

`/health` should return 200 and `/mcp` should return 401 without authentication.

## 6. GitHub deployments

Azure supports GitHub Actions for building and publishing new Container Apps revisions. The Azure CLI can generate the workflow when deploying from a GitHub repository. citeturn0search0turn0search3

    az containerapp up --name job-application-mcp --resource-group job-application-mcp-rg --repo https://github.com/Mzaq1559/job-application-mcp

Do not rerun this blindly if the resources already exist; use the existing resource group and Container App.

## Production checklist

- [ ] External HTTPS ingress on port 8000
- [ ] MCP bearer token stored as an Azure secret
- [ ] Durable PostgreSQL configured
- [ ] `/health` returns 200
- [ ] `/mcp` returns 401 without a token
- [ ] Authenticated MCP initialize/tools-list works
- [ ] Resume uploads moved to durable storage before relying on hosted files
- [ ] Claude Web authentication configured

Static bearer authentication only works with Claude accounts that expose request-header authentication. Otherwise the server needs OAuth 2.1.