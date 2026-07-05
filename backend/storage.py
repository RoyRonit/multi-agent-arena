"""JSON per-debate persistence — kept from the llm-council fork's spirit.

Each debate is a single append-only record in debates/{id}.json. The (state, turn,
score) triples stored here are the future RL dataset (ARCHITECTURE §7).
"""
from __future__ import annotations

import json
import os
import threading

from . import config

_lock = threading.Lock()


def _path(debate_id: str) -> str:
    os.makedirs(config.DEBATES_DIR, exist_ok=True)
    return os.path.join(config.DEBATES_DIR, f"{debate_id}.json")


def save(debate_id: str, record: dict) -> None:
    with _lock:
        with open(_path(debate_id), "w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False, indent=2)


def load(debate_id: str) -> dict | None:
    p = _path(debate_id)
    if not os.path.exists(p):
        return None
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)
