"""Background daemon threads: temperature recorder, LED schedule checker."""
import threading
import time
import logging

logger  = logging.getLogger(__name__)
_lock   = threading.Lock()
_started = False


def _temperature_recorder():
    from .models import TemperatureReading, BuzzerConfig
    from .temperature_service import read_temperature
    from .buzzer_service import alarm_on, alarm_off

    while True:
        try:
            temp, hum = read_temperature()
            TemperatureReading.objects.create(temperature=temp, humidity=hum)

            # Prune to last 5000 readings so the DB stays small
            oldest_keep = TemperatureReading.objects.order_by('-timestamp') \
                                                    .values_list('id', flat=True)[4999:5000]
            if oldest_keep:
                TemperatureReading.objects.filter(id__lt=oldest_keep[0]).delete()

            cfg = BuzzerConfig.objects.first()
            if cfg and cfg.enabled and temp >= cfg.threshold:
                alarm_on()
            else:
                alarm_off()
        except Exception as e:
            logger.error(f'Temperature recorder: {e}')
        time.sleep(60)


def _schedule_checker():
    from datetime import datetime
    from .models import LEDSchedule
    from .led_device import led

    while True:
        try:
            now       = datetime.now()
            weekday   = now.weekday()           # 0=Mon … 6=Sun
            cur_time  = now.time().replace(second=0, microsecond=0)
            schedules = list(LEDSchedule.objects.filter(enabled=True))

            if schedules:
                should_on = any(
                    len(s.days) > weekday
                    and s.days[weekday] == '1'
                    and s.on_time <= cur_time < s.off_time
                    for s in schedules
                )
                led.on() if should_on else led.off()
        except Exception as e:
            logger.error(f'Schedule checker: {e}')
        time.sleep(30)


def start_background_tasks():
    global _started
    with _lock:
        if _started:
            return
        _started = True

    threading.Thread(target=_temperature_recorder, daemon=True).start()
    threading.Thread(target=_schedule_checker,     daemon=True).start()

    from .servo_service import start_tracking
    start_tracking()

    logger.info('Background tasks started.')
