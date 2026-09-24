from __future__ import annotations

import pytest

from job_application_mcp.auth import Auth0TokenVerifier, build_auth_settings


def test_build_auth_settings_uses_mcp_resource():
    settings = build_auth_settings(
        issuer_url="https://example.us.auth0.com/",
        resource_url="https://example.com/mcp",
        required_scope="mcp:access",
    )
    assert str(settings.issuer_url).rstrip("/") == "https://example.us.auth0.com"
    assert str(settings.resource_server_url) == "https://example.com/mcp"
    assert settings.required_scopes == ["mcp:access"]
    assert settings.validate_token_resource is True


@pytest.mark.asyncio
async def test_invalid_token_is_rejected():
    verifier = Auth0TokenVerifier(
        issuer_url="https://example.us.auth0.com/",
        audience="https://example.com/mcp",
        jwks_url="https://example.us.auth0.com/.well-known/jwks.json",
    )
    assert await verifier.verify_token("not-a-jwt") is None
