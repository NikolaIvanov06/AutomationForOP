"""
Реален scraper за app.eop.bg с Playwright
Изисква: playwright install chromium
"""
from playwright.sync_api import sync_playwright
import time

def fetch_procurement_details(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until='networkidle')
        
        # Изчакай зареждане
        time.sleep(3)
        
        data = {
            'title': page.locator('h1').first.inner_text(),
            'budget': extract_budget(page.content()),
            'deadline': extract_deadline(page.content()),
            'documents': []
        }
        
        # Свали PDF документи
        for link in page.locator('a[href$=".pdf"]').all():
            pdf_url = link.get_attribute('href')
            # download logic
            
        browser.close()
        return data

def extract_budget(html):
    import re
    m = re.search(r'Прогнозна стойност.*?(\d[\d\s]+)', html)
    return int(m.group(1).replace(' ', '')) if m else 0

def extract_deadline(html):
    import re
    m = re.search(r'(\d{2}\.\d{2}\.\d{4}.*?час)', html)
    return m.group(1) if m else ''