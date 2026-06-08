"""
Реален scraper за app.eop.bg с Playwright.
Изисква: pip install playwright && playwright install chromium
"""
import re
import time


def fetch_procurement_details(url: str) -> dict:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle")
        time.sleep(3)

        html = page.content()
        try:
            title = page.locator("h1").first.inner_text()
        except Exception:
            title = "Без заглавие"

        documents = []
        for link in page.locator('a[href$=".pdf"]').all():
            pdf_url = link.get_attribute("href")
            if pdf_url:
                documents.append({"url": pdf_url, "text": ""})

        data = {
            "title": title,
            "buyer": extract_buyer(html),
            "budget": extract_budget(html),
            "deadline": extract_deadline(html),
            "cpv": extract_cpv(html),
            "documents": documents,
        }
        browser.close()
        return data


def extract_budget(html: str) -> int:
    m = re.search(r"Прогнозна стойност.*?(\d[\d\s]+)", html)
    return int(m.group(1).replace(" ", "")) if m else 0


def extract_deadline(html: str) -> str:
    m = re.search(r"(\d{2}\.\d{2}\.\d{4}.*?час)", html)
    return m.group(1) if m else ""


def extract_buyer(html: str) -> str:
    m = re.search(r"Възложител[:\s]*</?[^>]*>?\s*([^<\n]{3,80})", html)
    return m.group(1).strip() if m else "—"


def extract_cpv(html: str) -> str:
    m = re.search(r"(\d{8}-\d)", html)
    return m.group(1) if m else ""
