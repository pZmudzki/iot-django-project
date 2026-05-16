"""Servo motor (GPIO 12) controlled by MCP3008 potentiometer (CH0)."""
import os
import random
import logging
import threading
import time

logger  = logging.getLogger(__name__)
_lock   = threading.Lock()
_state  = {'angle': 0.0, 'pot': 0.5, 'tracking': False}
_thread = None


try:
    if os.name == 'nt':
        os.environ.setdefault('GPIOZERO_PIN_FACTORY', 'mock')
    from gpiozero import Servo as _Servo, MCP3008 as _MCP
    _servo = _Servo(12)
    _pot   = _MCP(channel=0)
    logger.info('Servo GPIO 12, potentiometer MCP3008 CH0')
except Exception as e:
    logger.warning(f'Servo/pot mock ({e})')
    class _MockServo:
        value = 0.0
    class _MockPot:
        value     = 0.5
        _target   = 0.5
        def _drift(self):
            if random.random() < 0.04:
                self._target = random.random()
            self.value += (self._target - self.value) * 0.08 + random.uniform(-0.005, 0.005)
            self.value = max(0.0, min(1.0, self.value))
    _servo = _MockServo()
    _pot   = _MockPot()


def get_state():
    with _lock:
        return dict(_state)


def set_angle(degrees):
    degrees = max(-90.0, min(90.0, float(degrees)))
    _servo.value = degrees / 90.0
    with _lock:
        _state['angle'] = round(degrees, 1)


def start_tracking():
    global _thread
    with _lock:
        if _state['tracking']:
            return
        _state['tracking'] = True

    def _loop():
        while True:
            with _lock:
                if not _state['tracking']:
                    break
            try:
                if hasattr(_pot, '_drift'):
                    _pot._drift()
                pot_val = float(_pot.value)
                _servo.value = (pot_val * 2.0) - 1.0
                with _lock:
                    _state['pot']   = round(pot_val, 3)
                    _state['angle'] = round(((pot_val * 2.0) - 1.0) * 90.0, 1)
            except Exception as e:
                logger.debug(f'Pot loop: {e}')
            time.sleep(0.1)

    _thread = threading.Thread(target=_loop, daemon=True)
    _thread.start()


def stop_tracking():
    with _lock:
        _state['tracking'] = False
