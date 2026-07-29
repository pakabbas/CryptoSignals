from __future__ import annotations

import pymysql

from app.config.settings import Config


def ensure_database_exists() -> None:
    """Create the MySQL database if it does not exist."""
    cfg = Config.mysql()
    connection = pymysql.connect(
        host=cfg.host,
        port=cfg.port,
        user=cfg.user,
        password=cfg.password,
        charset="utf8mb4",
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{cfg.database}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        connection.commit()
    finally:
        connection.close()
