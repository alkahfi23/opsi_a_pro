# =====================================================
# OPSI A PRO — SCHEDULER
# ONLY RUN AT OPTIMAL HOURS
# =====================================================

from datetime import datetime
import pytz

WIB = pytz.timezone("Asia/Jakarta")

def wib_hour():
    return datetime.now(WIB).hour


def is_optimal_spot():
    h = wib_hour()
    return 8 <= h <= 22


def is_optimal_futures():
    h = wib_hour()
    return 19 <= h <= 23
