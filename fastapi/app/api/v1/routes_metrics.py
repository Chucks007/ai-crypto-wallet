from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Dict

from backend.db.models import Decision, RuntimeFlag, Suggestion, Trade
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ...db import get_db

router = APIRouter(tags=["metrics"])


def _utc_day_bounds(dt: datetime) -> tuple[datetime, datetime]:
    start = dt.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=UTC)
    end = start + timedelta(days=1)
    return start, end


@router.get("/metrics/daily")
def daily_metrics(db: Session = Depends(get_db)):
    now = datetime.now(UTC)
    start, end = _utc_day_bounds(now)

    # Suggestions today
    sug_stmt = (
        select(func.count())
        .select_from(Suggestion)
        .where(Suggestion.created_at >= start, Suggestion.created_at < end)
    )
    suggestions = int(db.execute(sug_stmt).scalar() or 0)

    # Decisions today by decision value
    dec_stmt = (
        select(Decision.decision, func.count())
        .where(Decision.decided_at >= start, Decision.decided_at < end)
        .group_by(Decision.decision)
    )
    decisions: Dict[str, int] = {row[0]: int(row[1]) for row in db.execute(dec_stmt).all()}

    # Trades today by status (using executed_at)
    tr_stmt = (
        select(Trade.status, func.count())
        .where(Trade.executed_at.is_not(None), Trade.executed_at >= start, Trade.executed_at < end)
        .group_by(Trade.status)
    )
    trades: Dict[str, int] = {row[0]: int(row[1]) for row in db.execute(tr_stmt).all()}

    # Last worker run flags
    last_start = db.get(RuntimeFlag, "auto_last_start")
    last_finish = db.get(RuntimeFlag, "auto_last_finish")

    return {
        "today": {
            "suggestions": suggestions,
            "decisions": decisions,
            "trades": trades,
        },
        "last_worker": {
            "last_start": last_start.value if last_start else None,
            "last_finish": last_finish.value if last_finish else None,
        },
    }
