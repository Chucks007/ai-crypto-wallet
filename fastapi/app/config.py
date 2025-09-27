import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_PYTEST = "PYTEST_CURRENT_TEST" in os.environ


def _load_dotenv_files() -> None:
    """Load environment files for local dev without overriding explicit env."""

    if _PYTEST:
        return

    fastapi_dir = Path(__file__).resolve().parents[1]
    repo_root = fastapi_dir.parent

    load_dotenv(fastapi_dir / ".env", override=False)
    load_dotenv(repo_root / ".env", override=False)


_load_dotenv_files()


def _determine_env_files() -> tuple[str, ...] | None:
    """Return env files to load, preferring package-local overrides.

    We support both `fastapi/.env` (package-local) and repository-root `.env`.
    During pytest runs we deliberately skip the repo-level `.env` so that test
    expectations aren't affected by local developer overrides like enabling
    execution or pointing at real RPC URLs.
    """

    if _PYTEST:
        return None

    fastapi_dir = Path(__file__).resolve().parents[1]
    repo_root = fastapi_dir.parent

    candidates: list[Path] = []
    fastapi_env = fastapi_dir / ".env"
    if fastapi_env.exists():
        candidates.append(fastapi_env)

    root_env = repo_root / ".env"
    if root_env.exists():
        candidates.append(root_env)

    if not candidates:
        return None
    return tuple(str(p) for p in candidates)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_determine_env_files(),
        env_file_encoding="utf-8",
        extra="ignore",  # Allow unrelated env vars like TOKEN_ALLOWLIST_JSON
    )

    app_env: str = Field(default="dev", alias="APP_ENV")
    api_port: int = Field(default=8000, alias="API_PORT")
    db_url: str = Field(default="sqlite:///./wallet.db", alias="DB_URL")
    alchemy_rpc_url: str | None = Field(default=None, alias="ALCHEMY_RPC_URL")
    oneinch_base_url: str = Field(default="https://api.1inch.dev", alias="ONEINCH_BASE_URL")
    coingecko_base_url: str = Field(
        default="https://api.coingecko.com/api/v3", alias="COINGECKO_BASE_URL"
    )
    max_slippage_bps: int = Field(default=200, alias="MAX_SLIPPAGE_BPS")
    max_trade_size_usd: int = Field(default=50, alias="MAX_TRADE_SIZE_USD")
    # Per-asset allocation cap used in API risk evaluation
    max_allocation_pct: float = Field(default=0.05, alias="MAX_ALLOCATION_PCT")
    # Execution flags (dev/testnet signer only; disabled by default)
    execution_enabled: bool = Field(default=False, alias="EXECUTION_ENABLED")
    execution_allowed_chain_ids: str = Field(
        default="11155111,84532",  # Sepolia, Base Sepolia
        alias="EXECUTION_ALLOWED_CHAIN_IDS",
    )
    # Admin secret to trigger the auto-decider via HTTP (dev-only)
    auto_decider_secret: str | None = Field(default=None, alias="AUTO_DECIDER_SECRET")
    # Optional dev/test signer configuration (EOA; testnets only)
    rpc_url: str | None = Field(default=None, alias="RPC_URL")
    chain_id: int | None = Field(default=None, alias="CHAIN_ID")
    wallet_private_key: str | None = Field(default=None, alias="WALLET_PRIVATE_KEY")
    # Optional API keys
    oneinch_api_key: str | None = Field(default=None, alias="ONEINCH_API_KEY")
    tenderly_api_key: str | None = Field(default=None, alias="TENDERLY_API_KEY")
    # Optional Permit2 integration
    permit2_enabled: bool = Field(default=False, alias="PERMIT2_ENABLED")
    permit2_contract: str | None = Field(default=None, alias="PERMIT2_CONTRACT")
    permit2_default_spender: str | None = Field(default=None, alias="PERMIT2_DEFAULT_SPENDER")
    permit2_default_expiration_seconds: int = Field(
        default=60 * 30, alias="PERMIT2_DEFAULT_EXPIRATION_SECONDS"
    )
    permit2_min_validity_seconds: int = Field(
        default=60, alias="PERMIT2_MIN_VALIDITY_SECONDS"
    )

    @field_validator("permit2_default_expiration_seconds", "permit2_min_validity_seconds")
    @classmethod
    def _ensure_positive(cls, value: int, info):
        if value < 0:
            raise ValueError(f"{info.field_name} must be non-negative")
        return value

    @model_validator(mode="after")
    def _validate_permit2_config(self):
        if self.permit2_enabled:
            if not self.permit2_contract:
                raise ValueError("PERMIT2_CONTRACT must be provided when Permit2 is enabled")
            if not self.permit2_default_spender:
                raise ValueError(
                    "PERMIT2_DEFAULT_SPENDER must be provided when Permit2 is enabled"
                )
        return self


settings = Settings()
