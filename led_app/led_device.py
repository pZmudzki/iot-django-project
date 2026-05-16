"""Singleton LED instance shared across the application."""
import os
import warnings


def _make_dummy():
    class _DummyLED:
        _lit = False
        def on(self):     self._lit = True
        def off(self):    self._lit = False
        def toggle(self): self._lit = not self._lit
        @property
        def is_lit(self):    return self._lit
        @property
        def is_active(self): return self._lit
    return _DummyLED()


try:
    if os.name == 'nt':
        os.environ.setdefault('GPIOZERO_PIN_FACTORY', 'mock')
    from gpiozero import LED as _LED
    led = _LED(17)
except ImportError:
    warnings.warn("gpiozero not found; using mock LED.")
    led = _make_dummy()
except Exception as e:
    warnings.warn(f"GPIO error ({e}); using mock LED.")
    led = _make_dummy()
