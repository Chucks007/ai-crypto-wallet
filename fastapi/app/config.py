from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    app_env: str = Field(default="dev", alias="APP_ENV")
    api_port: int = Field(default=8000, alias="API_PORT")
    db_url: str = Field(default="sqlite:///./wallet.db", alias="DB_URL")
    alchemy_rpc_url: str | None = Field(default=None, alias="ALCHEMY_RPC_URL")
    oneinch_base_url: str = Field(default="https://api.1inch.dev", alias="ONEINCH_BASE_URL")
    coingecko_base_url: str = Field(default="https://api.coingecko.com/api/v3", alias="COINGECKO_BASE_URL")
    max_slippage_bps: int = Field(default=50, alias="MAX_SLIPPAGE_BPS")
    max_trade_size_usd: int = Field(default=250, alias="MAX_TRADE_SIZE_USD")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
