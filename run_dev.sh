#!/usr/bin/env bash
# Стартиране в режим за разработка (Linux/macOS).
# Десктоп прозорец:  ./run_dev.sh
# Само браузър:      ./run_dev.sh web
set -e
cd "$(dirname "$0")"
if [ "$1" = "web" ]; then
  python -m streamlit run app.py
else
  python desktop_app.py
fi
