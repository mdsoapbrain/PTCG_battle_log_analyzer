from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.core.config import get_settings


security = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthUser:
    user_id: str
    display_name: str
    raw_token: str | None = None


def _parse_stub_user(token: str | None) -> AuthUser:
    if not token:
        return AuthUser(user_id="local-user", display_name="Local User", raw_token=None)

    # Dev convention: `Bearer user:<id>` or just any token string.
    if token.startswith("user:"):
        user_id = token.split(":", 1)[1].strip() or "local-user"
    else:
        user_id = "local-user"

    return AuthUser(user_id=user_id, display_name=user_id, raw_token=token)


def _verify_supabase_jwt(token: str) -> AuthUser:
    # TODO(supabase-auth): replace this stub with real Supabase JWT validation.
    # Suggested implementation point:
    # 1) Validate JWT signature against Supabase JWKS
    # 2) Read `sub` as user_id and email/name claims for display
    # 3) Map to local users table
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="AUTH_MODE=supabase_jwt is configured but JWT verification is not implemented yet.",
    )


def get_current_user_stub(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> AuthUser:
    """Auth abstraction for local and future Supabase modes.

    - AUTH_MODE=stub: optional bearer token, always returns a dev user.
    - AUTH_MODE=supabase_jwt: requires bearer token, verification TODO.
    """
    settings = get_settings()
    token = credentials.credentials if credentials else None

    if settings.auth_mode == "stub":
        return _parse_stub_user(token)

    if settings.auth_mode == "supabase_jwt":
        if not token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
        return _verify_supabase_jwt(token)

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Unsupported AUTH_MODE: {settings.auth_mode}",
    )
