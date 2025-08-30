from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure repo root is importable so we can import `backend.*`
from . import bootstrap  # noqa: F401

from .api.v1.routes_meta import router as meta_router
from .api.v1.routes_wallet import router as wallet_router
from .api.v1.routes_approvals import router as approvals_router
from .db import on_startup, on_shutdown

def create_app() -> FastAPI:
    app = FastAPI(title="AI Crypto Wallet API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(meta_router, prefix="/v1")
    app.include_router(wallet_router, prefix="/v1")
    app.include_router(approvals_router, prefix="/v1")
    app.add_event_handler("startup", on_startup)
    app.add_event_handler("shutdown", on_shutdown)
    return app

app = create_app()
