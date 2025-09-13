from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )
    app_env: str = Field(default="dev", alias="APP_ENV")
    api_port: int = Field(default=8000, alias="API_PORT")
    db_url: str = Field(default="sqlite:///./wallet.db", alias="DB_URL")
    alchemy_rpc_url: str | None = Field(default=None, alias="ALCHEMY_RPC_URL")
    oneinch_base_url: str = Field(default="https://api.1inch.dev", alias="ONEINCH_BASE_URL")
    coingecko_base_url: str = Field(default="https://api.coingecko.com/api/v3", alias="COINGECKO_BASE_URL")
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

settings = Settings()
