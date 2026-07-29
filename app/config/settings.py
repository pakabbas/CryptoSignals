"""Application configuration loaded from environment."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class MySQLConfig:
    host: str
    port: int
    user: str
    password: str
    database: str

    @property
    def sqlalchemy_uri(self) -> str:
        user = quote_plus(self.user)
        password = quote_plus(self.password)
        return (
            f"mysql+pymysql://{user}:{password}"
            f"@{self.host}:{self.port}/{self.database}?charset=utf8mb4"
        )


class Config:
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-change-me")
    DEBUG: bool = _env_bool("DEBUG_MODE", False) or os.getenv("FLASK_ENV") == "development"

    TIMEZONE: str = os.getenv("TIMEZONE", "UTC")
    EXCHANGE: str = os.getenv("EXCHANGE", "kraken")
    SCANNER_INTERVAL_SECONDS: int = int(os.getenv("SCANNER_INTERVAL_SECONDS", "60"))
    DEFAULT_TIMEFRAME: str = os.getenv("DEFAULT_TIMEFRAME", "1H")
    THEME: str = os.getenv("THEME", "light")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()

    PRIMARY_SYMBOL: str = "BTC/USDT"
    DEFAULT_SYMBOLS: tuple[str, ...] = (
        "BTC/USDT",
        "ETH/USDT",
        "SOL/USDT",
        "DOGE/USDT",
    )

    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_ENGINE_OPTIONS: dict = {
        "pool_pre_ping": True,
        "pool_recycle": 3600,
    }

    LOG_DIR: Path = BASE_DIR / "logs"

    @classmethod
    def mysql(cls) -> MySQLConfig:
        return MySQLConfig(
            host=os.getenv("MYSQL_HOST", "127.0.0.1"),
            port=int(os.getenv("MYSQL_PORT", "3306")),
            user=os.getenv("MYSQL_USER", "root"),
            password=os.getenv("MYSQL_PASSWORD", ""),
            database=os.getenv("MYSQL_DATABASE", "crypto_signals"),
        )

    @classmethod
    def database_uri(cls) -> str:
        explicit = os.getenv("DATABASE_URL")
        if explicit:
            return explicit
        return cls.mysql().sqlalchemy_uri
