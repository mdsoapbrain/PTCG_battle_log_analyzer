from __future__ import annotations

from backend.core.config import get_settings


def test_normalize_postgresql_url(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@db.example.com:5432/postgres")
    get_settings.cache_clear()
    try:
        settings = get_settings()
        assert settings.database_url == "postgresql+psycopg://user:pass@db.example.com:5432/postgres"
    finally:
        get_settings.cache_clear()


def test_normalize_legacy_postgres_url(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgres://user:pass@db.example.com:5432/postgres")
    get_settings.cache_clear()
    try:
        settings = get_settings()
        assert settings.database_url == "postgresql+psycopg://user:pass@db.example.com:5432/postgres"
    finally:
        get_settings.cache_clear()
