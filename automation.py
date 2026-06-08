#!/usr/bin/env python3
"""
Автоматизация за обществени поръчки - Tech Hardware
Полу-автоматичен workflow: EOP email -> анализ -> draft до Polycomp
"""
import yaml, os, json, re
from datetime import datetime
from imap_tools import MailBox
from pathlib import Path

CONFIG = yaml.safe_load(open("config.yaml" if os.path.exists("config.yaml") else "config.example.yaml"))

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

def check_email():
    """Чете имейли от ЦАИС ЕОП шаблони"""
    print("→ Свързване към IMAP...")
    with MailBox(CONFIG['eop']['imap_server']).login(CONFIG['eop']['imap_user'], CONFIG['eop']['imap_password']) as mailbox:
        # търси имейли от последните 3 дни
        for msg in mailbox.fetch('(FROM "eop.bg" UNSEEN)', mark_seen=False):
            print(f"Намерен имейл: {msg.subject} - {msg.date}")
            # Извлича линкове към поръчки
            links = re.findall(r'https://app\.eop\.bg/today/\d+', msg.html or msg.text)
            for link in set(links):
                process_procurement(link)

def process_procurement(url):
    """Обработва една поръчка"""
    proc_id = url.split('/')[-1]
    out = OUTPUT_DIR / f"PROC-{proc_id}"
    out.mkdir(exist_ok=True)
    
    print(f"\n=== Обработвам {proc_id} ===")
    print(f"URL: {url}")
    
    # 1. Сваляне (mock за демо - в реален код използвай Playwright)
    # Тук ще свалим заглавие, прогнозна стойност, документи
    # За демо създаваме примерни данни
    procurement_data = {
        "id": proc_id,
        "url": url,
        "title": "Доставка на лаптопи и интерактивни дисплеи за училище",
        "buyer": "ОУ Примерно",
        "budget_bgn": 45000,
        "deadline": "2026-06-25",
        "cpv": "30213100-6",
        "documents": []
    }
    
    # 2. Анализ на документи (симулирано)
    # В реален код: свали PDF, използвай PyPDF2 + OpenAI за извличане
    analysis = analyze_documents(procurement_data)
    
    # 3. Приложи филтрите
    decision = apply_filters(procurement_data, analysis)
    
    # 4. Запази
    (out / "data.json").write_text(json.dumps(procurement_data, ensure_ascii=False, indent=2), encoding='utf-8')
    (out / "analysis.json").write_text(json.dumps(analysis, ensure_ascii=False, indent=2), encoding='utf-8')
    (out / "decision.json").write_text(json.dumps(decision, ensure_ascii=False, indent=2), encoding='utf-8')
    
    if decision['proceed']:
        generate_polycomp_email(procurement_data, analysis, out)
        generate_offer_template(procurement_data, analysis, out)
        print(f"✅ ПОДХОДЯЩА - генерирани файлове в {out}")
    else:
        print(f"❌ ПРОПУСНАТА: {decision['reason']}")

def analyze_documents(proc):
    """AI анализ - търси ISO, серийни номера, извлича спецификация"""
    # В реален код тук ще парсваш PDF с pypdf и ще питаш LLM
    # За демо връщаме пример
    sample_text = """
    Техническа спецификация:
    - Лаптоп 15.6", i5, 16GB RAM, 512GB SSD - 20 бр.
    - Интерактивен дисплей 75" 4K с тъч - 3 бр.
    Изисквания към участника: ISO 9001
    Офертата да съдържа техническо предложение без серийни номера.
    """
    
    analysis = {
        "requires_iso20000": bool(re.search(r'ISO\s*20000|ISO/IEC\s*20000', sample_text, re.I)),
        "requires_iso9001": bool(re.search(r'ISO\s*9001', sample_text, re.I)),
        "requires_serial_numbers": bool(re.search(r'сериен номер|серийни номера', sample_text, re.I)),
        "items": [
            {"name": "Лаптоп 15.6\" i5 16GB/512GB", "qty": 20, "unit": "бр."},
            {"name": "Интерактивен дисплей 75\" 4K тъч", "qty": 3, "unit": "бр."}
        ],
        "extracted_text": sample_text
    }
    return analysis

def apply_filters(proc, analysis):
    """Прилага твоите бизнес правила"""
    budget = proc.get('budget_bgn', 0)
    
    if analysis['requires_iso20000'] and CONFIG['filters']['require_iso_20000_skip']:
        return {"proceed": False, "reason": "Изисква ISO 20000"}
    
    if analysis['requires_serial_numbers'] and CONFIG['filters']['require_serial_numbers_skip']:
        return {"proceed": False, "reason": "Иска серийни номера в офертата"}
    
    if budget < CONFIG['filters']['min_budget_bgn']:
        return {"proceed": False, "reason": f"Бюджет {budget} лв < минимум {CONFIG['filters']['min_budget_bgn']}"}
    
    # Проверка за ключови думи
    title = proc['title'].lower()
    if not any(k in title for k in CONFIG['filters']['keywords_include']):
        return {"proceed": False, "reason": "Не е техника"}
    
    return {"proceed": True, "reason": "Отговаря на всички филтри"}

def generate_polycomp_email(proc, analysis, out_dir):
    """Генерира имейл до Polycomp"""
    items_text = "\n".join([f"- {i['name']} - {i['qty']} {i['unit']}" for i in analysis['items']])
    
    email = f"""Здравейте Polycomp,

Моля за оферта за следната обществена поръчка:
Поръчка: {proc['title']}
Възложител: {proc['buyer']}
Краен срок: {proc['deadline']}
Бюджет: {proc['budget_bgn']} лв без ДДС
Линк: {proc['url']}

Техническа спецификация:
{items_text}

Моля за:
1. Най-добра цена за посочените количества
2. Наличност и срок на доставка
3. Гаранционни условия
4. Алтернативни предложения ако има

Благодаря!
{CONFIG['polycomp']['your_company_name']}
{CONFIG['polycomp']['your_contact']}
"""
    (out_dir / "email_to_polycomp.txt").write_text(email, encoding='utf-8')

def generate_offer_template(proc, analysis, out_dir):
    """Генерира Excel шаблон за оферта"""
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Ценова оферта"
    
    ws['A1'] = "Обществена поръчка"
    ws['B1'] = proc['title']
    ws['A2'] = "Възложител"
    ws['B2'] = proc['buyer']
    ws['A3'] = "Бюджет"
    ws['B3'] = proc['budget_bgn']
    
    ws['A5'] = "Артикул"
    ws['B5'] = "Количество"
    ws['C5'] = "Ед.цена Polycomp"
    ws['D5'] = "Наша продажна"
    ws['E5'] = "Общо"
    
    row = 6
    for item in analysis['items']:
        ws[f'A{row}'] = item['name']
        ws[f'B{row}'] = item['qty']
        row += 1
    
    ws[f'A{row+1}'] = "Доставка"
    ws[f'D{row+1}'] = f"={CONFIG['profitability']['shipping_cost_percent']}%"
    ws[f'A{row+2}'] = "Марж цел"
    ws[f'D{row+2}'] = f"{CONFIG['profitability']['min_margin_percent']}%"
    
    wb.save(out_dir / "oferta_template.xlsx")

def check_profit(proc_id):
    """След получаване на цени от Polycomp"""
    out = OUTPUT_DIR / f"PROC-{proc_id}"
    data = json.loads((out / "data.json").read_text(encoding='utf-8'))
    
    print(f"Проверка рентабилност за {proc_id}")
    print("→ Попълни цените в oferta_template.xlsx и стартирай отново")
    # Тук ще чете Excel, ще смята марж
    # if margin < min: print("НЕ КАНДИДАТСТВАЙ")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--check-email', action='store_true')
    parser.add_argument('--check-profit', type=str)
    args = parser.parse_args()
    
    if args.check_email:
        check_email()
    elif args.check_profit:
        check_profit(args.check_profit)
    else:
        print("Използвай: python automation.py --check-email")