import os
from datetime import datetime, timezone

SUMMARY_FLAG_FILE = "daily_summary.flag"


def summary_sent_today() -> bool:
    if not os.path.exists(SUMMARY_FLAG_FILE):
        return False

    with open(SUMMARY_FLAG_FILE, "r") as f:
        last_date = f.read().strip()

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return last_date == today


def mark_summary_sent():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    with open(SUMMARY_FLAG_FILE, "w") as f:
        f.write(today)
