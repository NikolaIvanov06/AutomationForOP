import json
import io
from pathlib import Path

import streamlit as st
import pandas as pd
import yaml

from paths import resource_path, user_data_path, user_data_dir
from automation import check_email, calc_profit

st.set_page_config(page_title="ЕОП Автоматизация", page_icon="📋", layout="wide")

# ── Зареждане на конфиг ─────────────────────────────────────────────────
CONFIG_PATH = user_data_path("config.yaml")
EXAMPLE_PATH = resource_path("config.example.yaml")


def load_config():
    path = CONFIG_PATH if CONFIG_PATH.exists() else EXAMPLE_PATH
    cfg = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    cfg.setdefault("runtime", {})
    cfg["runtime"].setdefault("live_mode", False)
    cfg["runtime"].setdefault("use_scraper", False)
    cfg["runtime"].setdefault("use_ai", False)
    return cfg


def save_config(cfg):
    CONFIG_PATH.write_text(yaml.dump(cfg, allow_unicode=True), encoding="utf-8")


config = load_config()
OUTPUT_DIR = user_data_path("output")

st.title("📋 Автоматизация Обществени Поръчки – Tech")
st.caption("За доставки на лаптопи, монитори, интерактивни дисплеи, VR")

# ── Sidebar ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Настройки")

    live_mode = st.toggle("🔴 LIVE режим", value=config["runtime"]["live_mode"],
                          help="Изключено = DEMO с примерни данни. Включено = реален IMAP/скрейпър/AI.")
    use_scraper = st.checkbox("Playwright скрейпър", value=config["runtime"]["use_scraper"], disabled=not live_mode)
    use_ai = st.checkbox("OpenAI анализ", value=config["runtime"]["use_ai"], disabled=not live_mode)

    st.divider()
    min_budget = st.number_input("Мин. бюджет (лв)", value=int(config["filters"]["min_budget_bgn"]), step=500)
    min_margin = st.slider("Мин. марж %", 5, 30, int(config["profitability"]["min_margin_percent"]))
    skip_iso = st.checkbox("Пропускай ISO 20000", value=config["filters"].get("require_iso_20000_skip", True))
    skip_serial = st.checkbox("Пропускай серийни номера", value=config["filters"].get("require_serial_numbers_skip", True))

    st.divider()
    st.subheader("📧 ЕОП Имейл (IMAP)")
    imap_server = st.text_input("IMAP сървър", value=config["eop"]["imap_server"])
    imap_user = st.text_input("Имейл", value=config["eop"]["imap_user"])
    imap_pass = st.text_input("Парола/App password", value=config["eop"]["imap_password"], type="password")

    st.divider()
    st.subheader("Polycomp")
    poly_email = st.text_input("Имейл на доставчика", value=config["polycomp"]["email"])

    if st.button("💾 Запази настройки", use_container_width=True):
        config["runtime"]["live_mode"] = live_mode
        config["runtime"]["use_scraper"] = use_scraper
        config["runtime"]["use_ai"] = use_ai
        config["filters"]["min_budget_bgn"] = min_budget
        config["filters"]["require_iso_20000_skip"] = skip_iso
        config["filters"]["require_serial_numbers_skip"] = skip_serial
        config["profitability"]["min_margin_percent"] = min_margin
        config["eop"]["imap_server"] = imap_server
        config["eop"]["imap_user"] = imap_user
        config["eop"]["imap_password"] = imap_pass
        config["polycomp"]["email"] = poly_email
        save_config(config)
        st.success("Запазено!")

    st.divider()
    st.caption(f"📁 Данни: {user_data_dir()}")

# ── Tabs ────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["🔍 Нови поръчки", "📊 Активни", "💰 Калкулатор"])

with tab1:
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("Проверка на имейли от ЕОП")
        mode_label = "🔴 LIVE" if config["runtime"]["live_mode"] else "🟢 DEMO"
        st.caption(f"Текущ режим: **{mode_label}**")
    with col2:
        if st.button("🔄 Провери сега", type="primary", use_container_width=True):
            logs = []
            with st.spinner("Чета имейли от ЦАИС ЕОП..."):
                try:
                    check_email(log=lambda m: logs.append(m))
                    st.success("Проверката завърши!")
                    with st.expander("📜 Лог"):
                        st.code("\n".join(logs) or "—")
                    st.rerun()
                except Exception as e:
                    st.error(f"Грешка: {e}. Провери настройките.")
                    if logs:
                        st.code("\n".join(logs))

    if OUTPUT_DIR.exists():
        procs = []
        for folder in sorted(OUTPUT_DIR.glob("PROC-*"), reverse=True)[:20]:
            try:
                data = json.loads((folder / "data.json").read_text(encoding="utf-8"))
                decision = json.loads((folder / "decision.json").read_text(encoding="utf-8"))
                procs.append({
                    "ID": data["id"],
                    "Заглавие": data["title"][:60] + "...",
                    "Възложител": data["buyer"],
                    "Бюджет": f"{data['budget_bgn']:,} лв",
                    "Статус": "✅ Подходяща" if decision["proceed"] else "❌ Пропусната",
                    "Причина": decision["reason"],
                    "Папка": str(folder),
                })
            except Exception:
                pass

        if procs:
            df = pd.DataFrame(procs)
            st.dataframe(df[["ID", "Заглавие", "Бюджет", "Статус", "Причина"]],
                         use_container_width=True, hide_index=True)

            selected = st.selectbox("Избери поръчка за детайли:", [p["ID"] for p in procs])
            if selected:
                folder = OUTPUT_DIR / f"PROC-{selected}"
                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown("### 📄 Анализ")
                    analysis = json.loads((folder / "analysis.json").read_text(encoding="utf-8"))
                    for item in analysis["items"]:
                        st.write(f"- **{item['name']}** – {item['qty']} {item.get('unit', 'бр.')}")
                    st.write(f"ISO 20000: {'❌ Да (пропускаме)' if analysis.get('requires_iso20000') else '✅ Не'}")
                    st.write(f"Серийни номера: {'❌ Да' if analysis.get('requires_serial_numbers') else '✅ Не'}")
                with col_b:
                    st.markdown("### ✉️ Имейл до Polycomp")
                    email_path = folder / "email_to_polycomp.txt"
                    if email_path.exists():
                        email_text = email_path.read_text(encoding="utf-8")
                        st.code(email_text, language=None)
                        st.download_button("📥 Свали имейла", email_text, file_name=f"polycomp_{selected}.txt")
                    xlsx = folder / "oferta_template.xlsx"
                    if xlsx.exists():
                        st.download_button("📊 Свали Excel оферта", xlsx.read_bytes(),
                                           file_name=f"oferta_{selected}.xlsx")
        else:
            st.info("Няма обработени поръчки още. Натисни 'Провери сега'.")

with tab2:
    st.subheader("Активни поръчки за офериране")
    st.write("Подходящите поръчки, за които чакаш цени от Polycomp:")
    rows = []
    if OUTPUT_DIR.exists():
        for folder in sorted(OUTPUT_DIR.glob("PROC-*"), reverse=True):
            try:
                decision = json.loads((folder / "decision.json").read_text(encoding="utf-8"))
                if not decision.get("proceed"):
                    continue
                data = json.loads((folder / "data.json").read_text(encoding="utf-8"))
                rows.append({
                    "Поръчка": data["title"][:50],
                    "Възложител": data["buyer"],
                    "Краен срок": data["deadline"],
                    "Бюджет": f"{data['budget_bgn']:,} лв",
                    "Статус Polycomp": "⏳ Чака цена",
                })
            except Exception:
                pass
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("Няма активни подходящи поръчки. Стартирай проверка в първия таб.")

with tab3:
    st.subheader("💰 Калкулатор на рентабилност")
    st.write("Качи Excel файла от Polycomp или въведи ръчно")

    col1, col2 = st.columns(2)
    with col1:
        budget = st.number_input("Бюджет на поръчката (без ДДС)", value=45000)
        qty = st.number_input("Брой артикули общо", value=23)
    with col2:
        poly_price = st.number_input("Обща цена Polycomp (без ДДС)", value=38000)
        shipping = st.number_input("Доставка + разходи", value=500)

    overhead = config["profitability"].get("overhead_bgn", 0)

    if poly_price > 0:
        r = calc_profit(budget, poly_price, shipping, overhead)
        st.divider()
        c1, c2, c3 = st.columns(3)
        c1.metric("Себестойност", f"{r['total_cost']:,.0f} лв")
        c2.metric("Печалба", f"{r['margin_bgn']:,.0f} лв")
        c3.metric("Марж", f"{r['margin_pct']:.1f}%",
                  delta=f"{r['margin_pct'] - min_margin:.1f}% спрямо минимума")

        if r["margin_pct"] >= min_margin:
            st.success(f"✅ КАНДИДАТСТВАЙ – маржът е над {min_margin}%")
        else:
            st.error(f"❌ ПРОПУСНИ – маржът е под {min_margin}%")

st.divider()
st.caption("Автоматизация v2.0 (Desktop) | Работи с ЦАИС ЕОП и Polycomp")
