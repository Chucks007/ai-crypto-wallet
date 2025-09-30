from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure repo root is importable so we can import `backend.*`
from . import bootstrap  # noqa: F401
from .api.v1.routes_approvals import router as approvals_router
from .api.v1.routes_auto_decider import router as auto_router
from .api.v1.routes_meta import router as meta_router
from .api.v1.routes_metrics import router as metrics_router
from .api.v1.routes_runtime_flags import router as flags_router
from .api.v1.routes_trades import router as trades_router
from .api.v1.routes_wallet import router as wallet_router
from .config import settings
from .db import on_shutdown, on_startup
from .request_id_middleware import RequestIDMiddleware


def create_app() -> FastAPI:
    app = FastAPI(title="AI Crypto Wallet API", version="0.1.0")
    app.add_middleware(RequestIDMiddleware)
    cors_allow_origins = list(settings.cors_allow_origins)
    if settings.app_env.lower() == "dev" and not cors_allow_origins:
        cors_allow_origins = [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:4173",
            "http://127.0.0.1:4173",
        ]

    cors_kwargs: dict[str, object] = {
        "allow_origins": cors_allow_origins,
        "allow_credentials": settings.cors_allow_credentials,
        "allow_methods": settings.cors_allow_methods or ["GET", "POST", "OPTIONS"],
        "allow_headers": settings.cors_allow_headers or ["*"],
    }

    if settings.cors_allow_origin_regex:
        cors_kwargs["allow_origin_regex"] = settings.cors_allow_origin_regex

    if cors_allow_origins or settings.cors_allow_origin_regex:
        app.add_middleware(CORSMiddleware, **cors_kwargs)
    app.include_router(meta_router, prefix="/v1")
    app.include_router(wallet_router, prefix="/v1")
    app.include_router(approvals_router, prefix="/v1")
    app.include_router(flags_router, prefix="/v1")
    app.include_router(trades_router, prefix="/v1")
    app.include_router(auto_router, prefix="/v1")
    app.include_router(metrics_router, prefix="/v1")
    app.add_event_handler("startup", on_startup)
    app.add_event_handler("shutdown", on_shutdown)
    return app


app = create_app()
