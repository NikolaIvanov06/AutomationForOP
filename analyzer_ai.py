"""
AI анализ на документи за обществени поръчки.
Използва Google Gemini за извличане на структурирани данни.
Клиентът се създава мързеливо, за да не пада при импорт без ключ.
"""
import os
import json

PROMPT = """
Ти си експерт по ЗОП. Анализирай този текст от документация за обществена поръчка.

Върни САМО валиден JSON (без markdown, без ```), със следната структура:
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


def _model():
    """Създава Gemini модел. Изисква GEMINI_API_KEY (или GOOGLE_API_KEY)."""
    import google.generativeai as genai
    key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not key:
        raise RuntimeError("Липсва GEMINI_API_KEY")
    genai.configure(api_key=key)
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    return genai.GenerativeModel(model_name)


def analyze_text(text: str) -> str:
    """Връща JSON стринг с резултата от анализа."""
    import google.generativeai as genai

    model = _model()
    resp = model.generate_content(
        PROMPT.format(text=text[:8000]),
        generation_config=genai.types.GenerationConfig(
            response_mime_type="application/json",
            temperature=0.1,
        ),
    )
    return resp.text
