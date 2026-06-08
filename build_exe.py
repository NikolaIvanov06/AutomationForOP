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


def check_python():
    """Предупреждава при много нова версия на Python.

    PyInstaller + Python 3.14 често дава грешка
    'Failed to load Python DLL ... python314.dll'. За най-надежден
    билд използвай Python 3.11 или 3.12.
    """
    major, minor = sys.version_info[:2]
    print(f"→ Python за билда: {major}.{minor} ({sys.executable})")
    if (major, minor) >= (3, 13):
        print(
            "\n⚠️  ВНИМАНИЕ: Python "
            f"{major}.{minor} е много нов за PyInstaller.\n"
            "   Това е честа причина за 'Failed to load Python DLL "
            "(python3XX.dll)'.\n"
            "   Препоръка: билдвай с Python 3.11 или 3.12, напр.:\n"
            "       py -3.12 -m venv .venv\n"
            "       .venv\\Scripts\\activate\n"
            "       pip install -r requirements.txt && pip install pillow\n"
            "       python build_exe.py\n"
            "   Ако оставаш на този Python, трябва PyInstaller >= 6.16.\n"
        )


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
    check_python()
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
    print("\n✅ Готово!")
    print("   Стартирай ИМЕННО този файл (от dist, НЕ от build):")
    print("       dist/AutomationForOP/AutomationForOP.exe")
    print("   Папка 'build/' е временна и не се пуска директно.")


if __name__ == "__main__":
    build()
