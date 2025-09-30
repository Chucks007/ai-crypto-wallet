from __future__ import annotations

from app.config import Settings


def test_settings_parse_cors_lists(monkeypatch):
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "https://a.example, https://b.example")
    monkeypatch.setenv("CORS_ALLOW_METHODS", "GET,POST")
    monkeypatch.setenv("CORS_ALLOW_HEADERS", "Authorization,Content-Type")

    settings = Settings()

    assert settings.cors_allow_origins == ["https://a.example", "https://b.example"]
    assert settings.cors_allow_methods == ["GET", "POST"]
    assert settings.cors_allow_headers == ["Authorization", "Content-Type"]


def test_settings_empty_cors_values(monkeypatch):
    monkeypatch.delenv("CORS_ALLOW_ORIGINS", raising=False)
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", " ")

    settings = Settings()

    assert settings.cors_allow_origins == []


def test_settings_clamps_min_price_ttl(monkeypatch):
    monkeypatch.setenv("COINGECKO_PRICE_TTL_SECONDS", "5")

    settings = Settings()

    assert settings.coingecko_price_ttl_seconds == 10


def test_settings_clamps_max_price_ttl(monkeypatch):
    monkeypatch.setenv("COINGECKO_PRICE_TTL_SECONDS", "7200")

    settings = Settings()

    assert settings.coingecko_price_ttl_seconds == 3600
