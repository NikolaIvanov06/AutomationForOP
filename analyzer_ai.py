"""
AI анализ на документи за обществени поръчки
Използва OpenAI за извличане на структурирани данни
"""
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

PROMPT = """
Ти си експерт по ЗОП. Анализирай този текст от документация за обществена поръчка.

Върни JSON с:
{
  "requires_iso20000": true/false,
  "requires_serial_numbers": true/false,
  "items": [{"name": "", "qty": 0, "specs": ""}],
  "warranty_months": 0,
  "delivery_days": 0
}

Текст:
{text}
"""

def analyze_text(text):
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": PROMPT.format(text=text[:8000])}],
        response_format={"type": "json_object"}
    )
    return resp.choices[0].message.content