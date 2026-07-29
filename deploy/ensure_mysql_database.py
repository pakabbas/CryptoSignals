"""Create crypto_signals database using credentials from .env (no table migration)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from app.database.bootstrap import ensure_database_exists  # noqa: E402


def main() -> None:
    ensure_database_exists()
    print("MySQL database ready (crypto_signals).")


if __name__ == "__main__":
    main()
