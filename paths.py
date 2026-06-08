"""
Помощни функции за пътища, които работят и в dev, и в PyInstaller bundle.

- resource_path(): четене на вградени файлове (config.example.yaml, app.py...)
- user_data_path(): запис в потребителска папка (config.yaml, output/, logs)
  -> Windows:  %APPDATA%\\AutomationForOP
  -> други:    ~/.automationforop
"""
import os
import sys
from pathlib import Path

APP_NAME = "AutomationForOP"


def _base_dir() -> Path:
    """Папката, от която четем вградени ресурси."""
    if getattr(sys, "frozen", False):
        # PyInstaller разархивира в sys._MEIPASS
        return Path(getattr(sys, "_MEIPASS", os.path.dirname(sys.executable)))
    return Path(__file__).resolve().parent


def resource_path(relative: str) -> Path:
    return _base_dir() / relative


def user_data_dir() -> Path:
    if os.name == "nt":
        root = Path(os.environ.get("APPDATA", Path.home()))
        d = root / APP_NAME
    else:
        d = Path.home() / f".{APP_NAME.lower()}"
    d.mkdir(parents=True, exist_ok=True)
    return d


def user_data_path(relative: str) -> Path:
    return user_data_dir() / relative
