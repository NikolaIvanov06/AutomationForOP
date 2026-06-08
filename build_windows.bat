@echo off
REM ============================================================
REM  Билд на Windows .exe за Автоматизация Обществени Поръчки
REM  Двоен клик върху този файл на Windows машина.
REM ============================================================
setlocal

echo.
echo === 1/4 Проверка на Python ===
python --version
if errorlevel 1 (
  echo [ГРЕШКА] Python не е намерен в PATH. Инсталирай Python 3.10+.
  pause
  exit /b 1
)

echo.
echo === 2/4 Създаване на виртуална среда ===
if not exist .venv (
  python -m venv .venv
)
call .venv\Scripts\activate.bat

echo.
echo === 3/4 Инсталиране на зависимости ===
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pillow

echo.
echo === 4/4 Билд на .exe ===
python build_exe.py

echo.
echo ============================================================
echo  ГОТОВО! Приложението е в:  dist\AutomationForOP\
echo  Стартирай:  dist\AutomationForOP\AutomationForOP.exe
echo ============================================================
pause
