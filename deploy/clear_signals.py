"""Delete all signal history (production cleanup)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)


def main() -> None:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
    os.environ.setdefault("ENABLE_SCHEDULER", "false")

    from app import create_app
    from app.services.signal_service import SignalService

    app = create_app()
    with app.app_context():
        deleted = SignalService().delete_all()
        print(f"Deleted {deleted} signal(s)")


if __name__ == "__main__":
    main()
