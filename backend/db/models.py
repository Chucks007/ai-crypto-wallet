from __future__ import annotations

import os
import enum
from typing import Optional
from datetime import datetime

from sqlalchemy import (
    create_engine,
    ForeignKey,
    String,
    Integer,
    Float,
    Text,
    DateTime,
    Index,
    CheckConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker, Session


DEFAULT_DB_URL = os.getenv("DATABASE_URL", "sqlite:///./data.db")


class Base(DeclarativeBase):
    pass


class DecisionType(str, enum.Enum):
    approved = "approved"
    rejected = "rejected"
    expired = "expired"
    cancelled = "cancelled"


class TradeStatus(str, enum.Enum):
    submitted = "submitted"
    confirmed = "confirmed"
    failed = "failed"
    cancelled = "cancelled"


class BalanceSnapshot(Base):
    __tablename__ = "balance_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    asset: Mapped[str] = mapped_column(String, nullable=False)
    balance: Mapped[float] = mapped_column(Float, nullable=False)
    usd_price: Mapped[Optional[float]] = mapped_column(Float)
    usd_value: Mapped[Optional[float]] = mapped_column(Float)
    source: Mapped[Optional[str]] = mapped_column(String)

    __table_args__ = (
        Index("idx_balance_snapshots_captured_at", "captured_at"),
        Index("idx_balance_snapshots_asset_time", "asset", "captured_at"),
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<BalanceSnapshot {self.asset} {self.balance} at {self.captured_at}>"


class Suggestion(Base):
    __tablename__ = "suggestions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    rule: Mapped[str] = mapped_column(String, nullable=False)
    asset_from: Mapped[Optional[str]] = mapped_column(String)
    asset_to: Mapped[Optional[str]] = mapped_column(String)
    amount_usd: Mapped[Optional[float]] = mapped_column(Float)
    confidence: Mapped[Optional[float]] = mapped_column(Float)
    params_json: Mapped[Optional[str]] = mapped_column(Text)  # store JSON as text in SQLite
    reasoning: Mapped[Optional[str]] = mapped_column(Text)

    decisions: Mapped[list[Decision]] = relationship(back_populates="suggestion", cascade="all, delete-orphan")
    trades: Mapped[list[Trade]] = relationship(back_populates="suggestion", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_suggestions_created_at", "created_at"),
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Suggestion {self.rule} {self.asset_from}->{self.asset_to} ${self.amount_usd}>"


class Decision(Base):
    __tablename__ = "decisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    suggestion_id: Mapped[int] = mapped_column(ForeignKey("suggestions.id", ondelete="CASCADE"), nullable=False)
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    decision: Mapped[str] = mapped_column(String, nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text)

    suggestion: Mapped[Suggestion] = relationship(back_populates="decisions")

    __table_args__ = (
        Index("idx_decisions_suggestion_id", "suggestion_id"),
        CheckConstraint("decision in ('approved','rejected','expired','cancelled')", name="ck_decision_type"),
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Decision {self.decision} on suggestion {self.suggestion_id}>"


class Trade(Base):
    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    suggestion_id: Mapped[int] = mapped_column(ForeignKey("suggestions.id", ondelete="CASCADE"), nullable=False)
    executed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String, nullable=False)
    tx_hash: Mapped[Optional[str]] = mapped_column(String, unique=True)
    asset_from: Mapped[Optional[str]] = mapped_column(String)
    amount_from: Mapped[Optional[float]] = mapped_column(Float)
    asset_to: Mapped[Optional[str]] = mapped_column(String)
    amount_to: Mapped[Optional[float]] = mapped_column(Float)
    slippage_bps: Mapped[Optional[int]] = mapped_column(Integer)
    gas_est_usd: Mapped[Optional[float]] = mapped_column(Float)
    error: Mapped[Optional[str]] = mapped_column(Text)

    suggestion: Mapped[Suggestion] = relationship(back_populates="trades")

    __table_args__ = (
        Index("idx_trades_status_time", "status", "executed_at"),
        CheckConstraint("status in ('submitted','confirmed','failed','cancelled')", name="ck_trade_status"),
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Trade {self.status} tx={self.tx_hash}>"


class RuntimeFlag(Base):
    __tablename__ = "runtime_flags"

    key: Mapped[str] = mapped_column(String, primary_key=True)
    value: Mapped[str] = mapped_column(String, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<RuntimeFlag {self.key}={self.value}>"


def get_engine(url: str | None = None):
    return create_engine(url or DEFAULT_DB_URL, future=True)


SessionLocal = sessionmaker(bind=get_engine(), autoflush=False, autocommit=False, future=True)


def get_session() -> Session:
    return SessionLocal()


def init_db(url: str | None = None) -> None:
    engine = get_engine(url)
    Base.metadata.create_all(engine)
