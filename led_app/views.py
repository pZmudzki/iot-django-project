import os
import warnings
from django.shortcuts import render

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

    context = {
        'status': status_text
    }
    return render(request, 'led.html', context)
