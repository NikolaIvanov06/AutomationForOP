#!/usr/bin/env python3
"""
Desktop launcher за Автоматизация Обществени Поръчки.

Стартира Streamlit сървъра в отделен процес и го показва в нативен
прозорец чрез pywebview. За потребителя изглежда и работи като
обикновено настолно приложение — без браузър, без терминал.

Стартиране в dev:   python desktop_app.py
Билд на .exe:        виж build_exe.py / README
"""
import os
import sys
import time
import socket
import threading
import subprocess
from contextlib import closing

import webview

from paths import resource_path

APP_TITLE = "Автоматизация Обществени Поръчки"
HOST = "127.0.0.1"


def find_free_port() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind((HOST, 0))
        return s.getsockname()[1]


def wait_for_server(port: int, timeout: float = 60.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
            s.settimeout(1.0)
            if s.connect_ex((HOST, port)) == 0:
                return True
        time.sleep(0.3)
    return False


def start_streamlit(port: int) -> subprocess.Popen:
    """Стартира `streamlit run app.py` като подпроцес."""
    app_py = str(resource_path("app.py"))

    env = os.environ.copy()
    env["STREAMLIT_SERVER_HEADLESS"] = "true"
    env["STREAMLIT_SERVER_PORT"] = str(port)
    env["STREAMLIT_SERVER_ADDRESS"] = HOST
    env["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    env["STREAMLIT_SERVER_FILE_WATCHER_TYPE"] = "none"
    env["STREAMLIT_GLOBAL_DEVELOPMENT_MODE"] = "false"
    env["STREAMLIT_SERVER_RUN_ON_SAVE"] = "false"
    # Гарантира, че локалните модули се намират
    env["PYTHONPATH"] = str(resource_path(".")) + os.pathsep + env.get("PYTHONPATH", "")

    if getattr(sys, "frozen", False):
        # В bundle: викаме streamlit като модул със същия интерпретатор
        cmd = [sys.executable, "-m", "streamlit", "run", app_py,
               "--server.port", str(port), "--server.address", HOST,
               "--server.headless", "true",
               "--browser.gatherUsageStats", "false"]
    else:
        cmd = [sys.executable, "-m", "streamlit", "run", app_py,
               "--server.port", str(port), "--server.address", HOST,
               "--server.headless", "true",
               "--browser.gatherUsageStats", "false"]

    creationflags = 0
    if os.name == "nt":
        creationflags = subprocess.CREATE_NO_WINDOW  # скрива конзолата

    return subprocess.Popen(cmd, env=env, creationflags=creationflags)


def main():
    port = find_free_port()
    proc = start_streamlit(port)

    url = f"http://{HOST}:{port}"

    def on_closed():
        # Затваряме Streamlit когато прозорецът се затвори
        try:
            proc.terminate()
        except Exception:
            pass

    # Изчакваме сървъра (в нишка, за да не блокираме UI thread-а)
    ready = {"ok": False}

    def boot():
        ready["ok"] = wait_for_server(port)

    t = threading.Thread(target=boot, daemon=True)
    t.start()
    t.join(timeout=65)

    if not ready["ok"]:
        try:
            proc.terminate()
        except Exception:
            pass
        # Показваме грешка в прозорец
        webview.create_window(APP_TITLE, html=_error_html())
        webview.start()
        return

    window = webview.create_window(
        APP_TITLE,
        url=url,
        width=1280,
        height=860,
        min_size=(1000, 700),
    )
    window.events.closed += on_closed
    webview.start()

    # подсигуряване след затваряне
    on_closed()


def _error_html() -> str:
    return """
    <html><body style="font-family:sans-serif;padding:40px">
    <h2>⚠️ Streamlit сървърът не стартира навреме</h2>
    <p>Опитай отново. Ако проблемът продължава, провери дали порт е свободен
    и дали зависимостите са инсталирани.</p>
    </body></html>
    """


if __name__ == "__main__":
    main()
