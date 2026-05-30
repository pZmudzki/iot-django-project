"""Read temperature from DS18B20 (1-wire). Returns (None, None) if sensor absent."""
import glob
import logging

logger = logging.getLogger(__name__)


def read_temperature():
    """Return (temperature_celsius, None) or (None, None) if sensor unavailable."""
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
