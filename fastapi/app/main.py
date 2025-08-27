from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.v1.routes_meta import router as meta_router

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
    return app

app = create_app()
