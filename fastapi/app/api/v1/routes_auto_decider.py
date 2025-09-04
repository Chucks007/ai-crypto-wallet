from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException

from ...config import settings
from .. import routes_meta  # noqa: F401  # keep import style parity
from ...worker import run_once


router = APIRouter(tags=["auto_decider"]) 


@router.post("/auto-decider/run")
def auto_decider_run(
    x_admin_secret: str | None = Header(default=None, alias="X-Admin-Secret"),
    execute_dry_run: bool = True,
    limit: int = 50,
):
    # Require secret to be configured and provided
    if not settings.auto_decider_secret:
        raise HTTPException(status_code=403, detail="endpoint_disabled")
    if x_admin_secret != settings.auto_decider_secret:
        raise HTTPException(status_code=403, detail="forbidden")

    summary = run_once(execute_dry_run=execute_dry_run, limit=limit)
    return summary

