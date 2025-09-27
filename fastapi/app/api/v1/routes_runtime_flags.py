from __future__ import annotations

from datetime import UTC, datetime
from typing import List

from backend.db.models import RuntimeFlag
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...db import get_db
from ...schemas import EmergencyStopOut, EmergencyStopSetIn, RuntimeFlagOut, RuntimeFlagSetIn

router = APIRouter(tags=["runtime_flags"])


@router.get("/runtime-flags/emergency-stop", response_model=EmergencyStopOut)
def get_emergency_stop(db: Session = Depends(get_db)):
    flag = db.get(RuntimeFlag, "emergency_stop")
    if not flag:
        return {"enabled": False, "updated_at": None}
    enabled = flag.value.lower() in {"1", "true", "on", "yes"}
    return {"enabled": enabled, "updated_at": flag.updated_at}


@router.put("/runtime-flags/emergency-stop", response_model=EmergencyStopOut)
def set_emergency_stop(payload: EmergencyStopSetIn, db: Session = Depends(get_db)):
    flag = db.get(RuntimeFlag, "emergency_stop")
    now = datetime.now(UTC)
    value = "true" if payload.enabled else "false"
    if not flag:
        flag = RuntimeFlag(key="emergency_stop", value=value, updated_at=now)
        db.add(flag)
    else:
        flag.value = value
        flag.updated_at = now
    db.commit()
    db.refresh(flag)
    return {"enabled": payload.enabled, "updated_at": flag.updated_at}


@router.get("/runtime-flags", response_model=List[RuntimeFlagOut])
def list_runtime_flags(db: Session = Depends(get_db)):
    stmt = select(RuntimeFlag)
    rows = list(db.execute(stmt).scalars())
    return rows


@router.get("/runtime-flags/{key}", response_model=RuntimeFlagOut)
def get_runtime_flag(key: str, db: Session = Depends(get_db)):
    flag = db.get(RuntimeFlag, key)
    if not flag:
        raise HTTPException(status_code=404, detail="runtime flag not found")
    return flag


@router.put("/runtime-flags/{key}", response_model=RuntimeFlagOut)
def set_runtime_flag(key: str, payload: RuntimeFlagSetIn, db: Session = Depends(get_db)):
    flag = db.get(RuntimeFlag, key)
    now = datetime.now(UTC)
    if not flag:
        flag = RuntimeFlag(key=key, value=str(payload.value), updated_at=now)
        db.add(flag)
    else:
        flag.value = str(payload.value)
        flag.updated_at = now
    db.commit()
    db.refresh(flag)
    return flag
