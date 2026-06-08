"""
AI анализ на документи за обществени поръчки.
Използва OpenAI за извличане на структурирани данни.
Клиентът се създава мързеливо, за да не пада при импорт без ключ.
"""
import os
import json

PROMPT = """
Ти си експерт по ЗОП. Анализирай този текст от документация за обществена поръчка.

Върни САМО валиден JSON с:
{{
  "requires_iso20000": true/false,
  "requires_serial_numbers": true/false,
  "items": [{{"name": "", "qty": 0, "unit": "бр.", "specs": ""}}],
  "warranty_months": 0,
  "delivery_days": 0
}}

Текст:
{text}
"""


def _client():
    from openai import OpenAI
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("Липсва OPENAI_API_KEY")
    return OpenAI(api_key=key)


def analyze_text(text: str) -> str:
    """Връща JSON стринг с резултата от анализа."""
    resp = _client().chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[{"role": "user", "content": PROMPT.format(text=text[:8000])}],
        response_format={"type": "json_object"},
    )
    return resp.choices[0].message.content
