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
    from datetime import datetime, timezone

    exchange = os.getenv("EXCHANGE", "bybit").strip().lower() or "bybit"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
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
                "UPDATE app_settings SET value = %s, updated_at = %s WHERE `key` = 'exchange'",
                (exchange, now),
            )
            if cursor.rowcount == 0:
                cursor.execute(
                    """
                    INSERT INTO app_settings (`key`, value, created_at, updated_at)
                    VALUES ('exchange', %s, %s, %s)
                    """,
                    (exchange, now, now),
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
