"""Read RGB color from TCS3200 sensor. Returns available=False if sensor absent.

TCS3200 pin mapping (BCM):
  S0=23, S1=22  – output frequency scaling (set to 20 %)
  S2=25, S3=24  – color filter select
  OUT=27         – frequency output
"""
import os
import time
import logging

logger = logging.getLogger(__name__)
_gpio_available = False

S0, S1, S2, S3, OUT = 23, 22, 25, 24, 27


try:
    if os.name != 'nt':
        import RPi.GPIO as GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup([S0, S1, S2, S3], GPIO.OUT)
        GPIO.setup(OUT, GPIO.IN)
        GPIO.output(S0, GPIO.HIGH)
        GPIO.output(S1, GPIO.LOW)   # 20 % scaling
        _gpio_available = True
        logger.info('TCS3200 initialized')
except Exception as e:
    logger.warning(f'TCS3200 mock ({e})')


def _count_pulses(s2: bool, s3: bool, duration: float = 0.1) -> int:
    import RPi.GPIO as GPIO
    GPIO.output(S2, GPIO.HIGH if s2 else GPIO.LOW)
    GPIO.output(S3, GPIO.HIGH if s3 else GPIO.LOW)
    time.sleep(0.01)
    count = 0
    last = GPIO.input(OUT)
    end = time.time() + duration
    while time.time() < end:
        cur = GPIO.input(OUT)
        if last == 1 and cur == 0:  # falling edge via polling
            count += 1
        last = cur
    return count


def read_color() -> dict:
    """Return {'r', 'g', 'b', 'hex', 'available'}.
    When sensor is absent all values are None and available is False.
    """
    if _gpio_available:
        try:
            r_raw = _count_pulses(False, False)
            g_raw = _count_pulses(True,  True)
            b_raw = _count_pulses(False, True)
            total = max(r_raw + g_raw + b_raw, 1)
            r = int(min(255, r_raw / total * 765))
            g = int(min(255, g_raw / total * 765))
            b = int(min(255, b_raw / total * 765))
            return {'r': r, 'g': g, 'b': b,
                    'hex': f'#{r:02X}{g:02X}{b:02X}', 'available': True}
        except Exception as e:
            logger.warning(f'Color read error: {e}')

    return {'r': None, 'g': None, 'b': None, 'hex': None, 'available': False}
