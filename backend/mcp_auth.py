"""OAuth for the hosted MCP server, in resource-server mode (pattern from Grove).

The server does not issue tokens. WorkOS AuthKit is the authorisation server:
Claude and ChatGPT discover it from this server's protected resource metadata,
sign the user in (or up) there, and send a JWT access token. This module
verifies that token. Sign-up is open, so any verified user gets access unless
ALLOWED_EMAILS / ALLOWED_EMAIL_DOMAIN are set to close it again.

Env: OAUTH_ISSUER_URL, OAUTH_JWKS_URL, OAUTH_AUDIENCE (WorkOS: the environment's
client ID), MCP_PUBLIC_URL; optional ALLOWED_EMAILS, ALLOWED_EMAIL_DOMAIN.
"""

import asyncio
import logging
import os

import jwt
from mcp.server.auth.provider import AccessToken

log = logging.getLogger("playintel.auth")


def _csv(name: str) -> list[str]:
    return [v.strip() for v in (os.getenv(name) or "").split(",") if v.strip()]


class JwtVerifier:
    def __init__(self, issuer: str, jwks_url: str, audiences: list[str]):
        self.issuer = issuer
        self.audiences = audiences
        self.allowed_emails = {e.lower() for e in _csv("ALLOWED_EMAILS")}
        self.allowed_domain = (os.getenv("ALLOWED_EMAIL_DOMAIN") or "").lower()
        self._jwks = jwt.PyJWKClient(jwks_url, cache_keys=True, lifespan=3600)
        self._seen: set[str] = set()

    @classmethod
    def from_env(cls) -> "JwtVerifier":
        public_url = os.environ["MCP_PUBLIC_URL"]
        return cls(
            issuer=os.environ["OAUTH_ISSUER_URL"],
            jwks_url=os.environ["OAUTH_JWKS_URL"],
            audiences=_csv("OAUTH_AUDIENCE") or [public_url],
        )

    def _decode(self, token: str) -> dict:
        key = self._jwks.get_signing_key_from_jwt(token).key
        return jwt.decode(
            token,
            key,
            algorithms=["RS256", "ES256", "PS256"],
            audience=self.audiences,
            issuer=self.issuer,
            options={"require": ["exp", "iss", "aud"]},
        )

    def _allowed(self, claims: dict) -> bool:
        email = str(claims.get("email") or "").lower()
        if not email or claims.get("email_verified") is False:
            # No email means the WorkOS JWT template is missing: {"email": {{ user.email }}}
            return False
        if not self.allowed_emails and not self.allowed_domain:
            return True
        if email in self.allowed_emails:
            return True
        return bool(self.allowed_domain) and email.endswith("@" + self.allowed_domain)

    @staticmethod
    def _unverified_claim(token: str, name: str):
        try:
            return jwt.decode(token, options={"verify_signature": False}).get(name)
        except Exception:
            return None

    async def verify_token(self, token: str) -> AccessToken | None:
        try:
            claims = await asyncio.to_thread(self._decode, token)
        except jwt.InvalidAudienceError as exc:
            # Audiences are not secret; logging the token's value is how OAUTH_AUDIENCE gets set.
            log.info("Rejected token: %s (token aud=%r, expected one of %r)",
                     exc, self._unverified_claim(token, "aud"), self.audiences)
            return None
        except Exception as exc:  # invalid, expired or wrong issuer
            log.info("Rejected token: %s", exc)
            return None
        if not self._allowed(claims):
            log.info("Token valid but user refused: %s", claims.get("email") or claims.get("sub"))
            return None
        email = str(claims.get("email")).lower()
        if email not in self._seen:  # once per instance, so logs show who is using it
            self._seen.add(email)
            log.info("MCP user: %s", email)
        aud = claims.get("aud")
        return AccessToken(
            token=token,
            client_id=str(claims.get("azp") or claims.get("client_id") or "unknown"),
            scopes=str(claims.get("scope") or claims.get("scp") or "").split(),
            expires_at=int(claims["exp"]),
            resource=(aud[0] if isinstance(aud, list) else aud),
            subject=email,
            claims=claims,
        )
