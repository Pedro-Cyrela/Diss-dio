from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CONFIG_PATH = DATA_DIR / "config.json"


DEFAULT_CONFIG: Dict[str, Any] = {
    "data_acordo_anterior": None,
    "data_acordo_atual": None,
    "percentual_reajuste": 0.0,
    "teto_reajuste": 0.0,
    "valor_fixo_teto": 0.0,
}


def ensure_storage() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_PATH.exists():
        with CONFIG_PATH.open("w", encoding="utf-8") as file:
            json.dump(DEFAULT_CONFIG, file, ensure_ascii=True, indent=2)


def load_config() -> Dict[str, Any]:
    ensure_storage()
    with CONFIG_PATH.open("r", encoding="utf-8") as file:
        loaded = json.load(file)
    return {**DEFAULT_CONFIG, **loaded}


def save_config(config: Dict[str, Any]) -> None:
    ensure_storage()
    with CONFIG_PATH.open("w", encoding="utf-8") as file:
        json.dump({**DEFAULT_CONFIG, **config}, file, ensure_ascii=True, indent=2)
