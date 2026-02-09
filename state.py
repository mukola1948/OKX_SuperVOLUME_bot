# ============================================================
# ФАЙЛ: state.py
# Опис:
# Робота зі state.json (CEP між запусками)
# ============================================================

import json
from typing import Dict, Optional
from json import JSONDecodeError

STATE_FILE = "state.json"


def load_state() -> Dict:
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"last_run_id": None, "intervals": {}}
    except JSONDecodeError:
        return {"last_run_id": None, "intervals": {}}


def save_state(state: Dict) -> None:
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def get_cep(state: Dict, interval_label: str) -> Optional[float]:
    return state.get("intervals", {}).get(interval_label, {}).get("cep")


def set_cep(state: Dict, interval_label: str, value: float) -> None:
    state.setdefault("intervals", {}).setdefault(interval_label, {})
    state["intervals"][interval_label]["cep"] = value
