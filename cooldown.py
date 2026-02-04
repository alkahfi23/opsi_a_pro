# =====================================================
# OPSI A PRO — SIGNAL COOLDOWN ENGINE
# =====================================================

import os
import json
from datetime import datetime, timedelta

from config import (
    COOLDOWN_FILE,
    SPOT_SIGNAL_COOLDOWN_MIN,
    FUTURES_SIGNAL_COOLDOWN_MIN
)


def _load():
    if not os.path.exists(COOLDOWN_FILE):
        return {}
    try:
        with open(COOLDOWN_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def _save(data):
    with open(COOLDOWN_FILE, "w") as f:
        json.dump(data, f, indent=2)


def is_on_cooldown(symbol: str, mode: str) -> bool:
    data = _load()
    key = f"{symbol}_{mode}"

    if key not in data:
        return False

    last_time = datetime.fromisoformat(data[key])
    cooldown_min = (
        FUTURES_SIGNAL_COOLDOWN_MIN
        if mode == "FUTURES"
        else SPOT_SIGNAL_COOLDOWN_MIN
    )

    return datetime.utcnow() < last_time + timedelta(minutes=cooldown_min)


def set_cooldown(symbol: str, mode: str):
    data = _load()
    key = f"{symbol}_{mode}"
    data[key] = datetime.utcnow().isoformat()
    _save(data)
