# ============================================================
# ФАЙЛ: state.py
# Опис:
# Робота зі state.json (зберігаємо тільки last_ts)
# ============================================================

import json
from typing import Dict
from json import JSONDecodeError

STATE_FILE = "state.json"


def load_state() -> Dict:
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, JSONDecodeError):
        return {"intervals": {}}


def save_state(state: Dict) -> None:
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def get_last_ts(state: Dict, pair: str):
    return state.get("intervals", {}).get(pair, {}).get("last_ts")


def set_last_ts(state: Dict, pair: str, ts: str):
    state.setdefault("intervals", {}).setdefault(pair, {})
    state["intervals"][pair]["last_ts"] = ts
