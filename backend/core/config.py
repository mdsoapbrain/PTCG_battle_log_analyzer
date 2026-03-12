from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


def _env(name: str, default: str) -> str:
    return os.getenv(name, default)


def _env_with_fallback(primary: str, fallback: str, default: str) -> str:
    return os.getenv(primary) or os.getenv(fallback) or default


def _parse_csv(value: str) -> list[str]:
    return [x.strip() for x in value.split(",") if x.strip()]


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_version: str
    app_env: str
    app_host: str
    app_port: int
    database_url: str
    api_prefix: str
    cors_allowed_origins: list[str]
    cors_allowed_origin_regex: str | None
    api_base_url: str
    secret_key: str
    auth_mode: str


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    app_port_raw = _env("APP_PORT", "8001")
    try:
        app_port = int(app_port_raw)
    except ValueError:
        app_port = 8001

    cors_raw = _env("CORS_ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173")
    cors_regex_raw = _env("CORS_ALLOWED_ORIGIN_REGEX", r"https://.*\.vercel\.app")

    return Settings(
        app_name=_env_with_fallback("APP_NAME", "PTCG_APP_NAME", "PTCG Battle Log Backend"),
        app_version=_env_with_fallback("APP_VERSION", "PTCG_APP_VERSION", "0.2.0"),
        app_env=_env("APP_ENV", "development"),
        app_host=_env("APP_HOST", "0.0.0.0"),
        app_port=app_port,
        database_url=_env_with_fallback("DATABASE_URL", "PTCG_DATABASE_URL", "sqlite:///./backend.db"),
        api_prefix=_env_with_fallback("API_PREFIX", "PTCG_API_PREFIX", ""),
        cors_allowed_origins=_parse_csv(cors_raw),
        cors_allowed_origin_regex=cors_regex_raw.strip() or None,
        api_base_url=_env("API_BASE_URL", "http://localhost:8001"),
        secret_key=_env("SECRET_KEY", "change-me"),
        auth_mode=_env("AUTH_MODE", "stub"),
    )
