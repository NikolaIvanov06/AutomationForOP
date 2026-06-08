#!/usr/bin/env python3
"""
Desktop launcher за Автоматизация Обществени Поръчки.

Стартира Streamlit сървъра и го показва в нативен прозорец чрез pywebview.
За потребителя изглежда и работи като обикновено настолно приложение —
без браузър, без терминал.

Стартиране в dev:   python desktop_app.py
Билд на .exe:        виж build_exe.py / README

⚠️ ВАЖНО (fork-bomb fix):
В замразен .exe `sys.executable` сочи към САМИЯ .exe, а не към python.exe.
Затова `[sys.executable, "-m", "streamlit", ...]` НЕ стартира Streamlit, а
пуска отново лаунчъра → нов прозорец → пак лаунчъра → ... безкрайно
(десетки прозорци, "streamlit timeout"). За да не се случва това:

  • Когато сме замразени, стартираме Streamlit В СЪЩИЯ процес чрез
    streamlit.web.bootstrap (никакъв нов .exe не се пуска).
  • Имаме и guard през променлива на средата като втора защита: ако някак
    се преекзекутираме, новият процес директно подкарва Streamlit, а не GUI.
"""
import os
import sys
import time
import socket
import threading
import multiprocessing
from contextlib import closing

from paths import resource_path

APP_TITLE = "Автоматизация Обществени Поръчки"
HOST = "127.0.0.1"

# Маркер: ако е зададен, текущият процес трябва да е Streamlit worker, не GUI.
_CHILD_ENV = "AUTOMATIONFOROP_STREAMLIT_CHILD"


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


def _set_streamlit_env(port: int) -> None:
    os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
    os.environ["STREAMLIT_SERVER_PORT"] = str(port)
    os.environ["STREAMLIT_SERVER_ADDRESS"] = HOST
    os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    os.environ["STREAMLIT_SERVER_FILE_WATCHER_TYPE"] = "none"
    os.environ["STREAMLIT_GLOBAL_DEVELOPMENT_MODE"] = "false"
    os.environ["STREAMLIT_SERVER_RUN_ON_SAVE"] = "false"
    os.environ["PYTHONPATH"] = (
        str(resource_path(".")) + os.pathsep + os.environ.get("PYTHONPATH", "")
    )


def run_streamlit_inprocess(port: int) -> None:
    """Стартира Streamlit В ТЕКУЩИЯ процес (без нов .exe).

    Това е ключовата разлика спрямо предишната версия — не извикваме
    subprocess със sys.executable, който в замразен .exe пуска самия .exe
    наново и води до безкраен порой от прозорци.
    """
    _set_streamlit_env(port)
    app_py = str(resource_path("app.py"))

    from streamlit import config as st_config
    from streamlit.web import bootstrap

    # Изчистваме argv, за да не обърка Streamlit/Click.
    sys.argv = ["streamlit", "run", app_py]

    # Налагаме настройките ДИРЕКТНО в config-а. Само env променливи не са
    # надеждни (config модулът може вече да е зареден), затова сме изрични.
    flag_options = {
        "server.port": port,
        "server.address": HOST,
        "server.headless": True,
        "browser.gatherUsageStats": False,
        "global.developmentMode": False,
        "server.fileWatcherType": "none",
        "server.runOnSave": False,
    }
    for key, value in flag_options.items():
        try:
            st_config.set_option(key, value)
        except Exception:
            pass

    try:
        # По-нови версии на Streamlit
        bootstrap.run(app_py, False, [], flag_options)
    except TypeError:
        # По-стари сигнатури: run(file, command_line, args, flag_options)
        bootstrap.run(app_py, "", [], flag_options)


def _start_streamlit_process(port: int) -> "multiprocessing.Process":
    """Подкарва Streamlit в отделен ПРОЦЕС чрез multiprocessing.

    Защо процес, а не нишка:
      • Streamlit (bootstrap.run) слага signal handlers, които работят само
        в ГЛАВНАТА нишка на процеса. В нишка хвърля
        "signal only works in main thread".
      • multiprocessing + freeze_support() стартира детето БЕЗОПАСНО: в
        замразен .exe детето се пуска като worker за зададената функция, а
        НЕ като нов GUI → няма порой от прозорци (fork bomb).
    """
    ctx = multiprocessing.get_context("spawn")
    p = ctx.Process(target=run_streamlit_inprocess, args=(port,), daemon=True)
    p.start()
    return p


def gui_main():
    """Главният GUI процес: вдига Streamlit (в отделен процес) и показва прозорец."""
    import webview  # импортираме тук, за да не товари Streamlit worker-а

    port = find_free_port()
    proc = _start_streamlit_process(port)
    url = f"http://{HOST}:{port}"

    def shutdown():
        try:
            if proc.is_alive():
                proc.terminate()
        except Exception:
            pass

    ready = {"ok": False}

    def boot():
        ready["ok"] = wait_for_server(port)

    t = threading.Thread(target=boot, daemon=True)
    t.start()
    t.join(timeout=65)

    if not ready["ok"]:
        shutdown()
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
    window.events.closed += shutdown
    webview.start()
    shutdown()
    os._exit(0)


def _error_html() -> str:
    return """
    <html><body style="font-family:sans-serif;padding:40px">
    <h2>⚠️ Streamlit сървърът не стартира навреме</h2>
    <p>Опитай отново. Ако проблемът продължава, провери дали порт е свободен
    и дали зависимостите са инсталирани.</p>
    </body></html>
    """


def main():
    # Втора защита срещу "fork bomb": ако сме били преекзекутирани като
    # Streamlit дете, не вдигаме GUI, а директно пускаме сървъра.
    child_port = os.environ.get(_CHILD_ENV)
    if child_port:
        run_streamlit_inprocess(int(child_port))
        return
    gui_main()


if __name__ == "__main__":
    # КРИТИЧНО за замразени .exe: без freeze_support() multiprocessing/спауни
    # могат да рестартират целия .exe и да наплодят прозорци.
    multiprocessing.freeze_support()
    main()
