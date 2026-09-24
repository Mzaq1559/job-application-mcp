"""OAuth 2.1 resource-server token verification for Auth0."""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any

import httpx
import jwt
from mcp.server.auth.provider import AccessToken, TokenVerifier
from mcp.server.auth.settings import AuthSettings
from pydantic import AnyHttpUrl


class Auth0TokenVerifier(TokenVerifier):
    """Validate Auth0 RS256 access tokens locally against JWKS."""

    def __init__(
        self,
        *,
        issuer_url: str,
        audience: str,
        jwks_url: str | None = None,
        cache_ttl_seconds: int = 600,
    ) -> None:
        self.issuer_url = issuer_url.rstrip("/") + "/"
        self.audience = audience
        self.jwks_url = jwks_url or f"{self.issuer_url}.well-known/jwks.json"
        self.cache_ttl_seconds = cache_ttl_seconds
        self._jwks: dict[str, dict[str, Any]] | None = None
        self._jwks_expires_at = 0.0
        self._lock = asyncio.Lock()

    async def _get_jwks(self) -> dict[str, dict[str, Any]]:
        now = time.monotonic()
        if self._jwks is not None and now < self._jwks_expires_at:
            return self._jwks

        async with self._lock:
            now = time.monotonic()
            if self._jwks is not None and now < self._jwks_expires_at:
                return self._jwks

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.jwks_url)
                response.raise_for_status()
                payload = response.json()

            keys = {
                item["kid"]: item
                for item in payload.get("keys", [])
                if item.get("kid") and item.get("kty") == "RSA"
            }
            if not keys:
                raise ValueError("Auth0 JWKS contains no usable RSA keys")

            self._jwks = keys
            self._jwks_expires_at = time.monotonic() + self.cache_ttl_seconds
            return keys

    async def verify_token(self, token: str) -> AccessToken | None:
        try:
            header = jwt.get_unverified_header(token)
            if header.get("alg") != "RS256" or not header.get("kid"):
                return None

            jwks = await self._get_jwks()
            jwk = jwks.get(header["kid"])
            if jwk is None:
                self._jwks = None
                jwks = await self._get_jwks()
                jwk = jwks.get(header["kid"])
                if jwk is None:
                    return None

            key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(jwk))
            claims = jwt.decode(
                token,
                key=key,
                algorithms=["RS256"],
                audience=self.audience,
                issuer=self.issuer_url,
                options={"require": ["exp", "iat", "sub"]},
            )
            scope_claim = claims.get("scope", "")
            scopes = scope_claim.split() if isinstance(scope_claim, str) else []
            if not scopes:
                permissions_claim = claims.get("permissions", [])
                if isinstance(permissions_claim, list):
                    scopes = [item for item in permissions_claim if isinstance(item, str)]
            return AccessToken(
                token=token,
                client_id=str(claims.get("azp") or claims.get("client_id") or ""),
                scopes=scopes,
                expires_at=int(claims["exp"]),
                resource=self.audience,
                subject=str(claims["sub"]),
                claims=claims,
            )
        except (
            jwt.InvalidTokenError,
            ValueError,
            KeyError,
            TypeError,
            httpx.HTTPError,
        ):
            return None


def build_auth_settings(
    *,
    issuer_url: str,
    resource_url: str,
    required_scope: str,
) -> AuthSettings:
    return AuthSettings(
        issuer_url=AnyHttpUrl(issuer_url),
        resource_server_url=AnyHttpUrl(resource_url),
        required_scopes=[required_scope],
        validate_token_resource=True,
    )
