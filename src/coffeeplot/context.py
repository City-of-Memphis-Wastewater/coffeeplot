# src/coffeeplot/context.py
from __future__ import annotations
from pathlib import Path
from dworshak_config import DworshakConfig

APP_NAME = "coffeeplot"
APP_DIR = Path.home() / f".{APP_NAME}"
APP_DIR.mkdir(parents=True, exist_ok=True)

config_mngr = DworshakConfig(path=APP_DIR / "config.json")
