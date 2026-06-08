import streamlit as st
import pandas as pd
import json
from pathlib import Path
from datetime import datetime
import yaml

st.set_page_config(page_title="ЕОП Автоматизация", page_icon="📋", layout="wide")

# Зареждане на конфиг
CONFIG_PATH = Path("config.yaml")
if CONFIG_PATH.exists():
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding='utf-8'))
else:
    config = yaml.safe_load(Path("config.example.yaml").read_text(encoding='utf-8'))

st.title("📋 Автоматизация Обществени Поръчки – Tech")
st.caption("За доставки на лаптопи, монитори, интерактивни дисплеи, VR")

# Sidebar
with st.sidebar:
    st.header("⚙️ Настройки")
    min_budget = st.number_input("Мин. бюджет (лв)", value=config['filters']['min_budget_bgn'], step=500)
    min_margin = st.slider("Мин. марж %", 5, 30, config['profitability']['min_margin_percent'])
    skip_iso = st.checkbox("Пропускай ISO 20000", value=True)
    skip_serial = st.checkbox("Пропускай серийни номера", value=True)
    
    st.divider()
    st.subheader("Polycomp")
    poly_email = st.text_input("Имейл", value=config['polycomp']['email'])
    
    if st.button("💾 Запази настройки", use_container_width=True):
        config['filters']['min_budget_bgn'] = min_budget
        config['profitability']['min_margin_percent'] = min_margin
        CONFIG_PATH.write_text(yaml.dump(config, allow_unicode=True), encoding='utf-8')
        st.success("Запазено!")

# Tabs
tab1, tab2, tab3 = st.tabs(["🔍 Нови поръчки", "📊 Активни", "💰 Калкулатор"])

with tab1:
    col1, col2 = st.columns([3,1])
    with col1:
        st.subheader("Проверка на имейли от ЕОП")
    with col2:
        if st.button("🔄 Провери сега", type="primary", use_container_width=True):
            with st.spinner("Чета имейли от ЦАИС ЕОП..."):
                # Тук викаме реалната функция
                from automation import check_email
                try:
                    check_email()
                    st.success("Проверката завърши!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Грешка: {e}. Провери config.yaml")
    
    # Покажи намерени поръчки
    output_dir = Path("output")
    if output_dir.exists():
        procs = []
        for folder in sorted(output_dir.glob("PROC-*"), reverse=True)[:20]:
            try:
                data = json.loads((folder / "data.json").read_text(encoding='utf-8'))
                decision = json.loads((folder / "decision.json").read_text(encoding='utf-8'))
                procs.append({
                    "ID": data['id'],
                    "Заглавие": data['title'][:60]+"...",
                    "Възложител": data['buyer'],
                    "Бюджет": f"{data['budget_bgn']:,} лв",
                    "Статус": "✅ Подходяща" if decision['proceed'] else "❌ Пропусната",
                    "Причина": decision['reason'],
                    "Папка": str(folder)
                })
            except:
                pass
        
        if procs:
            df = pd.DataFrame(procs)
            st.dataframe(df[['ID','Заглавие','Бюджет','Статус','Причина']], use_container_width=True, hide_index=True)
            
            # Детайли
            selected = st.selectbox("Избери поръчка за детайли:", [p['ID'] for p in procs])
            if selected:
                folder = output_dir / f"PROC-{selected}"
                col_a, col_b = st.columns(2)
                
                with col_a:
                    st.markdown("### 📄 Анализ")
                    analysis = json.loads((folder / "analysis.json").read_text(encoding='utf-8'))
                    for item in analysis['items']:
                        st.write(f"- **{item['name']}** – {item['qty']} бр.")
                    
                    st.write(f"ISO 20000: {'❌ Да (пропускаме)' if analysis['requires_iso20000'] else '✅ Не'}")
                    st.write(f"Серийни номера: {'❌ Да' if analysis['requires_serial_numbers'] else '✅ Не'}")
                
                with col_b:
                    st.markdown("### ✉️ Имейл до Polycomp")
                    email_path = folder / "email_to_polycomp.txt"
                    if email_path.exists():
                        email_text = email_path.read_text(encoding='utf-8')
                        st.code(email_text, language=None)
                        st.download_button("📥 Свали имейла", email_text, file_name=f"polycomp_{selected}.txt")
                        if st.button("📧 Копирай в клипборда"):
                            st.toast("Копирано! Постави в Outlook/Gmail")
        else:
            st.info("Няма обработени поръчки още. Натисни 'Провери сега'.")

with tab2:
    st.subheader("Активни поръчки за офериране")
    st.write("Тук ще виждаш само подходящите, за които чакаш цени от Polycomp")
    
    # Mock данни
    active_data = {
        "Поръчка": ["ОУ София - лаптопи", "Детска градина Пловдив"],
        "Краен срок": ["25.06.2026", "28.06.2026"],
        "Бюджет": ["45,000 лв", "12,500 лв"],
        "Статус Polycomp": ["⏳ Чака цена", "✅ Получена"],
        "Прогнозен марж": ["—", "14.2%"]
    }
    st.dataframe(pd.DataFrame(active_data), use_container_width=True)

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
    
    if poly_price > 0:
        total_cost = poly_price + shipping
        margin_bgn = budget - total_cost
        margin_pct = (margin_bgn / budget * 100) if budget else 0
        
        st.divider()
        c1, c2, c3 = st.columns(3)
        c1.metric("Себестойност", f"{total_cost:,.0f} лв")
        c2.metric("Печалба", f"{margin_bgn:,.0f} лв")
        c3.metric("Марж", f"{margin_pct:.1f}%", delta=f"{margin_pct-min_margin:.1f}% над минимума")
        
        if margin_pct >= min_margin:
            st.success(f"✅ КАНДИДАТСТВАЙ – маржът е над {min_margin}%")
        else:
            st.error(f"❌ ПРОПУСНИ – маржът е под {min_margin}%")

# Footer
st.divider()
st.caption("Автоматизация v1.0 | Работи с ЦАИС ЕОП и Polycomp")