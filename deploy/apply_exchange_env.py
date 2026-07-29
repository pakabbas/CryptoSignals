"""Set exchange in app_settings from .env (no Flask import)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


def main() -> None:
    import pymysql

    exchange = os.getenv("EXCHANGE", "bybit").strip().lower() or "bybit"
    connection = pymysql.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        database=os.getenv("MYSQL_DATABASE", "crypto_signals"),
        charset="utf8mb4",
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO app_settings (`key`, value)
                VALUES ('exchange', %s)
                ON DUPLICATE KEY UPDATE value = VALUES(value)
                """,
                (exchange,),
            )
        connection.commit()
        print(f"Exchange set to {exchange} in app_settings")
    finally:
        connection.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"apply_exchange_env failed: {exc}", file=sys.stderr)
        sys.exit(1)
