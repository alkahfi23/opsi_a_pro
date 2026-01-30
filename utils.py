# =====================================================
# OPSI A PRO — UTILS
# =====================================================
from datetime import datetime, timezone, timedelta

# ===== TIMEZONE =====
WIB = timezone(timedelta(hours=7))

def now_wib():
    return datetime.now(timezone.utc).astimezone(WIB).strftime("%Y-%m-%d %H:%M WIB")

def wib_hour():
    return datetime.now(timezone.utc).astimezone(WIB).hour

def is_danger_time():
    # midnight – subuh
    return 0 <= wib_hour() < 5

def is_safe_spot_time():
    h = wib_hour()
    return (7 <= h <= 10) or (19 <= h <= 23)

def is_safe_futures_time():
    h = wib_hour()
    return 19 <= h <= 23
