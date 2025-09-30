from __future__ import annotations

from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.main import create_app


def _get_cors_options(app):
    for middleware in app.user_middleware:
        if middleware.cls is CORSMiddleware:
            return getattr(middleware, "kwargs", {})
    return None


def test_dev_defaults_allow_local_origins(monkeypatch):
    monkeypatch.setattr(settings, "app_env", "dev", raising=False)
    monkeypatch.setattr(settings, "cors_allow_origins", [], raising=False)
    app = create_app()

    opts = _get_cors_options(app)
    assert opts is not None
    assert "http://localhost:5173" in opts["allow_origins"]
    assert "http://127.0.0.1:5173" in opts["allow_origins"]


def test_prod_without_origins_disables_cors(monkeypatch):
    monkeypatch.setattr(settings, "app_env", "prod", raising=False)
    monkeypatch.setattr(settings, "cors_allow_origins", [], raising=False)
    monkeypatch.setattr(settings, "cors_allow_origin_regex", None, raising=False)
    app = create_app()

    assert _get_cors_options(app) is None


def test_prod_uses_configured_origins(monkeypatch):
    monkeypatch.setattr(settings, "app_env", "prod", raising=False)
    monkeypatch.setattr(
        settings,
        "cors_allow_origins",
        ["https://app.example.com", "https://admin.example.com"],
        raising=False,
    )
    app = create_app()

    opts = _get_cors_options(app)
    assert opts is not None
    assert opts["allow_origins"] == [
        "https://app.example.com",
        "https://admin.example.com",
    ]