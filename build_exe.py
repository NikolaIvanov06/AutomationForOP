#!/usr/bin/env python3
"""
Билд скрипт: създава самостоятелен Windows .exe чрез PyInstaller.

Употреба (на Windows машина с инсталирани зависимости):
    pip install -r requirements.txt
    python build_exe.py

Резултат: dist/AutomationForOP/AutomationForOP.exe  (папка-режим, по-надежден за Streamlit)

Бележка: PyInstaller прави билд за ОС-а, на който се изпълнява.
За Windows .exe → пусни този скрипт на Windows.
"""
import os
import sys
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ICON_PNG = HERE / "assets" / "icon.png"
ICON_ICO = HERE / "assets" / "icon.ico"


def ensure_ico():
    """Конвертира PNG -> ICO (нужно за Windows иконка), ако липсва."""
    if ICON_ICO.exists() or not ICON_PNG.exists():
        return
    try:
        from PIL import Image
        img = Image.open(ICON_PNG)
        img.save(ICON_ICO, sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
        print(f"✓ Създаден {ICON_ICO}")
    except Exception as e:
        print(f"! Пропускам иконка ({e})")


def build():
    ensure_ico()
    sep = ";" if os.name == "nt" else ":"

    add_data = [
        f"app.py{sep}.",
        f"automation.py{sep}.",
        f"analyzer_ai.py{sep}.",
        f"scraper_eop.py{sep}.",
        f"paths.py{sep}.",
        f"config.example.yaml{sep}.",
        f"assets{sep}assets",
    ]

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "AutomationForOP",
        "--noconfirm",
        "--clean",
        "--windowed",            # без конзолен прозорец
        # Streamlit метаданни и данни:
        "--collect-all", "streamlit",
        "--collect-all", "altair",
        "--collect-all", "pandas",
        "--collect-all", "pyarrow",
        "--copy-metadata", "streamlit",
        # Скрити импорти, които PyInstaller често пропуска:
        "--hidden-import", "streamlit.runtime.scriptrunner.magic_funcs",
        "--hidden-import", "yaml",
        "--hidden-import", "openpyxl",
        "--hidden-import", "webview",
    ]

    for d in add_data:
        cmd += ["--add-data", d]

    if ICON_ICO.exists():
        cmd += ["--icon", str(ICON_ICO)]

    cmd.append("desktop_app.py")

    print("→ PyInstaller команда:\n  " + " ".join(cmd))
    subprocess.check_call(cmd, cwd=str(HERE))
    print("\n✅ Готово! Виж: dist/AutomationForOP/AutomationForOP.exe")


if __name__ == "__main__":
    build()
