"""Control buzzer on GPIO 18 with mock fallback."""
import os
import logging

logger = logging.getLogger(__name__)


try:
    if os.name == 'nt':
        os.environ.setdefault('GPIOZERO_PIN_FACTORY', 'mock')
    from gpiozero import Buzzer as _GpioBuzzer
    _buzzer = _GpioBuzzer(18)
    logger.info('Buzzer on GPIO 18')
except Exception as e:
    logger.warning(f'Buzzer mock ({e})')
    class _MockBuzzer:
        is_active = False
        def on(self):  self.is_active = True;  logger.info('[BUZZER] ON')
        def off(self): self.is_active = False; logger.info('[BUZZER] OFF')
    _buzzer = _MockBuzzer()


def alarm_on():  _buzzer.on()
def alarm_off(): _buzzer.off()
def is_active(): return bool(getattr(_buzzer, 'is_active', False)
                              or getattr(_buzzer, 'is_lit', False))
