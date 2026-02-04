# =====================================================
# SIMPLE LOGGER — RENDER FRIENDLY
# =====================================================

from datetime import datetime

def log(msg: str):
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] {msg}", flush=True)
