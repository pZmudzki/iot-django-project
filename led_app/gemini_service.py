"""
led_app/gemini_service.py

Wysyła prompt do Gemini API.
Gemini zwraca odpowiedź WYŁĄCZNIE w kodzie Morse'a.
"""

import re
import logging
import google.generativeai as genai
from django.conf import settings

logger = logging.getLogger(__name__)

SYSTEM_INSTRUCTION = """
Jesteś asystentem, który odpowiada WYŁĄCZNIE w kodzie Morse'a.

Zasady:
1. Odpowiadaj krótko i rzeczowo (maksymalnie 10 słów).
2. Zamień swoją odpowiedź na kod Morse'a: '.' (kropka) i '-' (kreska).
3. Litery oddzielaj pojedynczą spacją, słowa podwójną spacją.
4. Nie dodawaj ŻADNEGO innego tekstu — tylko czysty kod Morse'a.
5. Nie używaj nawiasów, opisów ani tłumaczeń.

Przykład odpowiedzi na "Jak masz na imię?":
.- ..
"""


def ask_gemini_for_morse(prompt: str) -> dict:
    """
    Pyta Gemini i zwraca dict:
    {
        "morse":        "... --- ...",
        "raw_response": "...",
        "model":        "gemini-1.5-flash",
    }
    Rzuca ValueError gdy brak klucza, Exception przy błędzie API.
    """
    api_key = getattr(settings, "GEMINI_API_KEY", None)
    if not api_key:
        raise ValueError(
            "Brak GEMINI_API_KEY w settings.py. "
            "Dodaj: GEMINI_API_KEY = 'twój-klucz'"
        )

    genai.configure(api_key=api_key)

    model_name = getattr(settings, "GEMINI_MODEL", "gemini-1.5-flash")
    model = genai.GenerativeModel(
        model_name=model_name,
        system_instruction=SYSTEM_INSTRUCTION,
    )

    logger.info(f"[GEMINI] Wysyłam prompt: {prompt!r}")
    response = model.generate_content(prompt)
    raw = response.text.strip()
    logger.info(f"[GEMINI] Surowa odpowiedź: {raw!r}")

    # Sanitacja — zostaw tylko dozwolone znaki Morse'a
    cleaned = re.sub(r"[^.\- ]", "", raw).strip()
    cleaned = re.sub(r" {3,}", "  ", cleaned)  # max podwójna spacja

    return {
        "morse":        cleaned,
        "raw_response": raw,
        "model":        model_name,
    }
