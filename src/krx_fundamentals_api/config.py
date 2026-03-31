from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    redis_url: str = "redis://localhost:6379"
    dart_api_key: str = ""

    crawl_interval_master: int = 86400  # 종목마스터: 24시간
    crawl_interval_financials: int = 86400  # 재무제표: 24시간
    crawl_interval_ratios: int = 3600  # 투자지표: 1시간

    cors_origins: list[str] = ["*"]
    log_level: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
