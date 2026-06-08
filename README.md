# 📋 Автоматизация Обществени Поръчки — Desktop

Настолно приложение (Windows) за полу-автоматичен workflow при обществени
поръчки за техника (лаптопи, монитори, интерактивни дисплеи, VR).

Workflow: **ЕОП имейл → скрейпър → AI филтър (ISO 20000 / серийни номера) →
имейл до доставчик (Polycomp) → генериране на проект на оферта.**

Това е същата автоматизация като преди, но опакована като **истинско настолно
приложение** — стартираш `.exe`, отваря се нативен прозорец, без браузър и без
терминал. Всички предишни функции са запазени.

---

## 🚀 Бързо стартиране (готов .exe)

1. Свали папката `dist/AutomationForOP/` (след билд).
2. Двоен клик върху **`AutomationForOP.exe`**.
3. Отваря се прозорецът на приложението.

Настройките и резултатите се пазят в:
`%APPDATA%\AutomationForOP\` (config.yaml, папка `output\`).

---

## 🖥️ Режими на работа

В страничната лента има превключвател **🔴 LIVE режим**:

| Режим | Какво прави |
|-------|-------------|
| 🟢 **DEMO** (по подразбиране) | Работи с примерни данни. Не пипа имейл, интернет или Gemini. Идеален за тестване и демонстрация. |
| 🔴 **LIVE** | Реален IMAP за ЕОП имейли, по избор Playwright скрейпър и Google Gemini анализ. |

В LIVE режим можеш да включиш допълнително:
- ☑️ **Playwright скрейпър** — сваля реални данни от `app.eop.bg`
- ☑️ **Gemini анализ** — изисква `GEMINI_API_KEY` (или `GOOGLE_API_KEY`) като environment variable.
  По избор `GEMINI_MODEL` (по подразбиране `gemini-1.5-flash`).

---

## ✨ Функции (всички запазени + подобрени)

- **🔍 Нови поръчки** — „Провери сега“ стартира целия pipeline; таблица с
  намерените поръчки, статус (подходяща/пропусната) и причина; детайли с анализ,
  готов имейл до Polycomp и Excel оферта за сваляне. Показва се и лог.
- **📊 Активни** — реален списък с подходящите поръчки (вече не е mock).
- **💰 Калкулатор** — рентабилност (себестойност, печалба, марж) с цел спрямо
  минималния марж.
- **⚙️ Настройки** — *вече се запазват изцяло*: режим, филтри, ISO/серийни,
  IMAP данни (сървър/имейл/парола), имейл на доставчика, минимален бюджет и марж.

---

## 🛠️ Билд на Windows .exe

На **Windows** машина (PyInstaller билдва за ОС-а, на който се пуска):

```bat
:: Най-лесно — двоен клик или в cmd:
build_windows.bat
```

Скриптът създава виртуална среда, инсталира зависимостите и билдва.
Резултат: `dist\AutomationForOP\AutomationForOP.exe`

Ръчно:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install pillow            # за конвертиране на иконката
python build_exe.py
```

> 💡 За macOS/Linux изпълни същия `python build_exe.py` на съответната ОС —
> ще получиш `.app` / изпълним файл за тази платформа.

### ⚠️ Чести проблеми при билд

- **„Failed to load Python DLL … python3XX.dll … The specified module could
  not be found."**
  1. **Стартирай правилния файл.** Готовото приложение е в
     **`dist\AutomationForOP\AutomationForOP.exe`**, а НЕ в `build\...`.
     Папка `build\` е временна и не работи директно.
  2. **Версия на Python.** Тази грешка често идва от твърде нов Python
     (напр. 3.14) с PyInstaller. Най-надеждно билдвай с **Python 3.11/3.12**.
     Ако оставаш на 3.14 — трябва `pyinstaller>=6.16`.
  3. **VC++ Redistributable.** Инсталирай
     [Microsoft VC++ x64](https://aka.ms/vs/17/release/vc_redist.x64.exe).
  4. **Чист билд:** `rmdir /s /q build dist` и билдни наново.

---

## 👩‍💻 Стартиране за разработка (без билд)

```bash
pip install -r requirements.txt

# Десктоп прозорец (pywebview):
python desktop_app.py

# Или само в браузър (Streamlit):
python -m streamlit run app.py
# на Linux/macOS: ./run_dev.sh   или   ./run_dev.sh web
```

> На Linux pywebview изисква GTK/Qt backend (`pip install pywebview[qt]`
> или системни GTK пакети). На Windows работи веднага (WebView2/Edge).

---

## 📂 Структура

```
AutomationForOP/
├─ desktop_app.py        # Десктоп launcher (pywebview + Streamlit подпроцес)
├─ app.py                # Streamlit UI (табове, настройки, калкулатор)
├─ automation.py         # Ядро: имейл → анализ → филтри → имейл/оферта
├─ analyzer_ai.py        # Google Gemini анализ (LIVE)
├─ scraper_eop.py        # Playwright скрейпър за app.eop.bg (LIVE)
├─ paths.py              # Пътища за dev и за .exe + потребителска папка
├─ config.example.yaml   # Примерна конфигурация
├─ requirements.txt
├─ build_exe.py          # PyInstaller билд
├─ build_windows.bat     # 1-клик билд за Windows
├─ run_dev.sh            # Старт за разработка (Linux/macOS)
└─ assets/icon.png       # Иконка
```

---

## 🔐 Бележки за сигурност

- IMAP паролата се пази локално в `%APPDATA%\AutomationForOP\config.yaml`.
  За Gmail използвай **App Password**, не основната парола.
- `GEMINI_API_KEY` се чете от environment, не се записва в config.
- `config.yaml` (с реални данни) **не** се качва в Git — виж `.gitignore`.
