# Claude Web

After Azure deployment, get the hostname with:

    az containerapp show --name job-application-mcp --resource-group job-application-mcp-rg --query properties.configuration.ingress.fqdn --output tsv

Your MCP URL is:

    https://YOUR-FQDN/mcp

## Connect

1. Open Claude → Customize → Connectors.
2. Choose Add custom connector.
3. Enter the Azure MCP URL.
4. Complete the authentication method available in your Claude account.

## Current authentication limitation

This repository currently uses a static bearer token, not OAuth 2.1.

If your Claude account exposes Request headers, configure:

    Authorization: Bearer YOUR_MCP_AUTH_TOKENS

If Request headers are unavailable, do not make `/mcp` public. OAuth 2.1 with dynamic client registration and PKCE is the required next step.

## Test

Try: `Show my profile summary.` Then test a harmless write operation.

## Azure cold starts

The low-cost setup uses scale-to-zero. Azure does not charge usage while the app is at zero replicas, but the first request after inactivity can take longer. citeturn0search4turn1search0