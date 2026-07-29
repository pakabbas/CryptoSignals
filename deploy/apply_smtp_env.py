"""Apply SMTP settings using MySQL only (no Flask app import)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default)


def main() -> None:
    import pymysql

    host = _env("MYSQL_HOST", "localhost")
    port = int(_env("MYSQL_PORT", "3306"))
    user = _env("MYSQL_USER", "root")
    password = _env("MYSQL_PASSWORD", "")
    database = _env("MYSQL_DATABASE", "crypto_signals")

    smtp_host = _env("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(_env("SMTP_PORT", "587"))
    smtp_user = _env("SMTP_USERNAME", "")
    smtp_pass = _env("SMTP_PASSWORD", "").replace(" ", "")
    smtp_from_name = _env("SMTP_FROM_NAME", "")
    smtp_from = _env("SMTP_FROM_EMAIL", smtp_user)
    smtp_to = _env("SMTP_TO_EMAIL", smtp_from)
    use_tls = _env("SMTP_USE_TLS", "true").lower() in {"1", "true", "yes"}
    use_ssl = _env("SMTP_USE_SSL", "false").lower() in {"1", "true", "yes"}

    connection = pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        charset="utf8mb4",
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM information_schema.columns "
                "WHERE table_schema=%s AND table_name='smtp_settings' AND column_name='sender_name'",
                (database,),
            )
            if cursor.fetchone()[0] == 0:
                cursor.execute(
                    "ALTER TABLE smtp_settings "
                    "ADD COLUMN sender_name VARCHAR(128) NOT NULL DEFAULT ''"
                )

            cursor.execute("SELECT id FROM smtp_settings ORDER BY id ASC LIMIT 1")
            row = cursor.fetchone()
            if row is None:
                cursor.execute(
                    "INSERT INTO smtp_settings "
                    "(smtp_server, smtp_port, username, password, use_tls, use_ssl, "
                    "sender_name, sender_email, receiver_email, subject_template, created_at, updated_at) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW(),NOW())",
                    (
                        smtp_host,
                        smtp_port,
                        smtp_user,
                        smtp_pass,
                        int(use_tls),
                        int(use_ssl),
                        smtp_from_name,
                        smtp_from,
                        smtp_to,
                        "Crypto Signal: {signal_type} {symbol}",
                    ),
                )
            else:
                smtp_id = row[0]
                updates = [
                    smtp_host,
                    smtp_port,
                    smtp_user,
                    int(use_tls),
                    int(use_ssl),
                    smtp_from_name,
                    smtp_from,
                    smtp_to,
                ]
                sql = (
                    "UPDATE smtp_settings SET "
                    "smtp_server=%s, smtp_port=%s, username=%s, "
                    "use_tls=%s, use_ssl=%s, sender_name=%s, sender_email=%s, receiver_email=%s, updated_at=NOW() "
                )
                if smtp_pass:
                    sql += ", password=%s WHERE id=%s"
                    updates.append(smtp_pass)
                    updates.append(smtp_id)
                else:
                    sql += "WHERE id=%s"
                    updates.append(smtp_id)
                cursor.execute(sql, tuple(updates))
        connection.commit()
    finally:
        connection.close()

    print("SMTP settings updated in MySQL.")


if __name__ == "__main__":
    main()
