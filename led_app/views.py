import os
import json
import threading
import warnings
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .morse_service import play_morse_on_led
from .gemini_service import ask_gemini_for_morse

# ── Inicjalizacja LED (bez zmian względem oryginału) ──────────────────────

try:
    if os.name == 'nt':  # Windows
        os.environ['GPIOZERO_PIN_FACTORY'] = 'mock'

    from gpiozero import LED
    led = LED(17)
except ImportError:
    warnings.warn("Nie znaleziono biblioteki gpiozero. Używam atrapy diody LED.")

    class DummyLED:
        def __init__(self):
            self._is_lit = False
        def on(self):
            self._is_lit = True
        def off(self):
            self._is_lit = False
        def toggle(self):
            self._is_lit = not self._is_lit
        @property
        def is_lit(self):
            return self._is_lit
        @property
        def is_active(self):
            return self._is_lit

    led = DummyLED()
except Exception as e:
    warnings.warn(f"Błąd inicjalizacji GPIO: {e}. Używam atrapy.")

    class DummyLED:
        def __init__(self):
            self.is_active = False
        def on(self):
            self.is_active = True
        def off(self):
            self.is_active = False
        @property
        def is_lit(self):
            return self.is_active

    led = DummyLED()


# ── Istniejący widok (bez zmian) ──────────────────────────────────────────

def led_control(request):
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "on":
            led.on()
        elif action == "off":
            led.off()

    try:
        status_text = "Włączona" if getattr(led, 'is_lit', led.is_active) else "Wyłączona"
    except Exception:
        status_text = "Brak danych"

    context = {'status': status_text}
    return render(request, 'led.html', context)


# ── Nowy endpoint: Prompt → Gemini → Morse → LED ─────────────────────────

@csrf_exempt
@require_POST
def morse_prompt(request):
    """
    POST /led/morse/

    Payload (JSON):
        { "prompt": "Ile planet ma Uklad Sloneczny?" }
    """
    # 1. Parsuj JSON z obsługą różnych enkodowań.
    #    PowerShell na Windows wysyła domyślnie CP1250 zamiast UTF-8.
    raw_body = request.body
    body = None
    for encoding in ("utf-8", "cp1250", "latin-1"):
        try:
            body = json.loads(raw_body.decode(encoding))
            break
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue

    if body is None:
        return JsonResponse(
            {"success": False, "error": "Nieprawidlowy JSON lub nieobslugiwane enkodowanie."},
            status=400,
        )

    prompt = body.get("prompt", "").strip()

    if not prompt:
        return JsonResponse(
            {"success": False, "error": "Pole 'prompt' jest wymagane i nie moze byc puste."},
            status=400,
        )

    if len(prompt) > 500:
        return JsonResponse(
            {"success": False, "error": "Prompt nie moze przekraczac 500 znakow."},
            status=400,
        )

    # 2. Zapytaj Gemini
    try:
        result = ask_gemini_for_morse(prompt)
    except ValueError as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)
    except Exception as e:
        return JsonResponse(
            {"success": False, "error": f"Blad Gemini API: {str(e)}"},
            status=502,
        )

    morse_string = result["morse"]

    if not morse_string:
        return JsonResponse(
            {
                "success": False,
                "error": "Gemini nie zwrocil poprawnego kodu Morse'a.",
                "raw_response": result.get("raw_response"),
            },
            status=502,
        )

    # 3. Odegraj Morse'a na LED w tle (nie blokuj odpowiedzi HTTP)
    thread = threading.Thread(
        target=play_morse_on_led,
        args=(led, morse_string),
        daemon=True,
    )
    thread.start()

    # 4. Zwroc odpowiedz natychmiast
    return JsonResponse({
        "success":    True,
        "prompt":     prompt,
        "morse":      morse_string,
        "model":      result["model"],
        "led_status": "playing",
        "message":    "Kod Morse'a jest odgrywany na diodzie LED.",
    })