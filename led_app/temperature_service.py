"""Read temperature from DS18B20 (1-wire) with simulation fallback."""
import glob
import random
import threading
import logging

logger = logging.getLogger(__name__)
_lock  = threading.Lock()
_state = {'temp': 22.5, 'hum': 55.0}


def _read_ds18b20():
    try:
        devices = glob.glob('/sys/bus/w1/devices/28*/w1_slave')
        if not devices:
            return None, None
        with open(devices[0]) as f:
            lines = f.readlines()
        if 'YES' not in lines[0]:
            return None, None
        return round(float(lines[1].split('t=')[1]) / 1000.0, 2), None
    except Exception as e:
        logger.debug(f'DS18B20: {e}')
        return None, None


def read_temperature():
    """Return (temperature_celsius, humidity_or_None)."""
    temp, hum = _read_ds18b20()
    if temp is not None:
        with _lock:
            _state['temp'] = temp
            _state['hum']  = hum
        return temp, hum

    with _lock:
        _state['temp'] = round(max(15.0, min(45.0,
            _state['temp'] + random.uniform(-0.3, 0.3))), 2)
        _state['hum']  = round(max(20.0, min(90.0,
            _state['hum']  + random.uniform(-0.5, 0.5))), 1)
        return _state['temp'], _state['hum']
