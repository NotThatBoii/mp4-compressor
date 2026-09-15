import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import sys


def setup_logging():
    root = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "Compressly" if getattr(sys, "frozen", False) else Path(__file__).resolve().parents[2]
    folder = root / "logs"
    try:
        folder.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(folder / "compressly.log", maxBytes=2_000_000, backupCount=3, encoding="utf-8")
    except OSError:
        handler = logging.StreamHandler()
    logging.basicConfig(level=logging.INFO, handlers=[handler], format="%(asctime)s %(levelname)s %(name)s: %(message)s")
