import json
import random
import threading
from datetime import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .led_device import led
from .morse_service import play_morse_on_led
from .gemini_service import ask_gemini_for_morse
from .temperature_service import read_temperature
from .buzzer_service import alarm_on, alarm_off, is_active as buzzer_active
from .servo_service import get_state as servo_state, set_angle, start_tracking, stop_tracking
from .color_service import read_color
from .models import TemperatureReading, LEDSchedule, BuzzerConfig
from .pdf_service import generate_pdf


# ── LED Control ───────────────────────────────────────────────────────────────

@login_required
def led_control(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'on':
            led.on()
        elif action == 'off':
            led.off()

    status_text = 'Włączona' if led.is_lit else 'Wyłączona'
    temp, hum   = read_temperature()
    cfg = BuzzerConfig.objects.first()

    return render(request, 'led.html', {
        'status':           status_text,
        'temperature':      temp,
        'humidity':         hum,
        'buzzer_threshold': cfg.threshold if cfg else 30.0,
        'buzzer_enabled':   cfg.enabled   if cfg else True,
        'buzzer_active':    buzzer_active(),
    })


# ── Temperature API ───────────────────────────────────────────────────────────

@login_required
def temperature_api(request):
    qs = list(reversed(list(TemperatureReading.objects.all()[:50])))
    data = [
        {'timestamp': r.timestamp.strftime('%H:%M'),
         'temperature': r.temperature,
         'humidity': r.humidity}
        for r in qs
    ]
    return JsonResponse({'readings': data, 'latest': data[-1] if data else None})


# ── Chart ─────────────────────────────────────────────────────────────────────

@login_required
def chart_view(request):
    return render(request, 'chart.html')


# ── LED Schedule ──────────────────────────────────────────────────────────────

@login_required
def schedule_view(request):
    if request.method == 'POST':
        name     = request.POST.get('name', '').strip()
        on_time  = request.POST.get('on_time')
        off_time = request.POST.get('off_time')
        days     = ''.join('1' if request.POST.get(f'day_{i}') else '0' for i in range(7))

        if name and on_time and off_time and '1' in days:
            LEDSchedule.objects.create(
                name=name, on_time=on_time, off_time=off_time, days=days)
            messages.success(request, f'Harmonogram „{name}" dodany.')
        else:
            messages.error(request, 'Wypełnij wszystkie pola i zaznacz co najmniej jeden dzień.')
        return redirect('schedule')

    return render(request, 'schedule.html',
                  {'schedules': LEDSchedule.objects.order_by('on_time')})


@login_required
@require_POST
def schedule_toggle(request, pk):
    s = get_object_or_404(LEDSchedule, pk=pk)
    s.enabled = not s.enabled
    s.save()
    return redirect('schedule')


@login_required
@require_POST
def schedule_delete(request, pk):
    get_object_or_404(LEDSchedule, pk=pk).delete()
    return redirect('schedule')


# ── Buzzer Config ─────────────────────────────────────────────────────────────

@login_required
@require_POST
def buzzer_config(request):
    try:
        data      = json.loads(request.body)
        threshold = float(data.get('threshold', 30.0))
        enabled   = bool(data.get('enabled', True))
        cfg, _    = BuzzerConfig.objects.get_or_create(pk=1)
        cfg.threshold = threshold
        cfg.enabled   = enabled
        cfg.save()
        return JsonResponse({'success': True, 'threshold': threshold, 'enabled': enabled})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ── Servo ─────────────────────────────────────────────────────────────────────

@login_required
def servo_view(request):
    return render(request, 'servo.html', {'servo': servo_state()})


@login_required
def servo_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            if 'tracking' in data:
                start_tracking() if data['tracking'] else stop_tracking()
            elif 'angle' in data:
                stop_tracking()
                set_angle(float(data['angle']))
            return JsonResponse({'success': True, **servo_state()})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    return JsonResponse(servo_state())


# ── Color Sensor ──────────────────────────────────────────────────────────────

@login_required
def color_view(request):
    return render(request, 'color.html')


@login_required
def color_api(request):
    return JsonResponse(read_color())


# ── PDF Report ────────────────────────────────────────────────────────────────

@login_required
def pdf_report(request):
    readings = list(TemperatureReading.objects.all()[:200])
    buf      = generate_pdf(readings)
    ts       = datetime.now().strftime('%Y%m%d_%H%M')
    resp     = HttpResponse(buf, content_type='application/pdf')
    resp['Content-Disposition'] = f'attachment; filename="raport_{ts}.pdf"'
    return resp


# ── Morse / Gemini ────────────────────────────────────────────────────────────

@csrf_exempt
@require_POST
def morse_prompt(request):
    body = None
    for enc in ('utf-8', 'cp1250', 'latin-1'):
        try:
            body = json.loads(request.body.decode(enc))
            break
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue

    if body is None:
        return JsonResponse({'success': False, 'error': 'Nieprawidłowy JSON.'}, status=400)

    prompt = body.get('prompt', '').strip()
    if not prompt:
        return JsonResponse({'success': False, 'error': "Pole 'prompt' jest wymagane."}, status=400)
    if len(prompt) > 500:
        return JsonResponse({'success': False, 'error': 'Prompt max 500 znaków.'}, status=400)

    try:
        result = ask_gemini_for_morse(prompt)
    except ValueError as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Błąd Gemini: {e}'}, status=502)

    morse_string = result['morse']
    if not morse_string:
        return JsonResponse({'success': False, 'error': 'Brak kodu Morse.',
                             'raw_response': result.get('raw_response')}, status=502)

    threading.Thread(target=play_morse_on_led, args=(led, morse_string), daemon=True).start()

    return JsonResponse({
        'success':    True,
        'prompt':     prompt,
        'morse':      morse_string,
        'model':      result['model'],
        'led_status': 'playing',
        'message':    'Kod Morse odgrywany na LED.',
    })


# ── Roulette ──────────────────────────────────────────────────────────────────

_ROULETTE_RED = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
_STARTING_BALANCE = 10_000


def _shutdown_pi():
    import platform, subprocess
    if platform.system() != 'Linux':
        return  # Safety: only executes on the Pi, never on a dev Mac/Windows
    subprocess.run(['sudo', 'shutdown', '-h', 'now'], check=False)


@login_required
def roulette_view(request):
    if 'roulette_balance' not in request.session:
        request.session['roulette_balance'] = _STARTING_BALANCE
    return render(request, 'roulette.html', {
        'balance': request.session['roulette_balance'],
    })


@login_required
def roulette_spin(request):
    if request.method != 'POST':
        return JsonResponse({'balance': request.session.get('roulette_balance', _STARTING_BALANCE)})

    try:
        data = json.loads(request.body)
        bet_type = str(data.get('bet_type', ''))
        bet_amount = int(data.get('bet_amount', 0))
    except (json.JSONDecodeError, ValueError, TypeError):
        return JsonResponse({'success': False, 'error': 'Invalid data'}, status=400)

    balance = request.session.get('roulette_balance', _STARTING_BALANCE)

    if bet_amount <= 0 or bet_amount > balance:
        return JsonResponse({'success': False, 'error': 'Invalid bet amount'}, status=400)

    result = random.randint(0, 36)

    win_amount = 0
    if bet_type == 'red' and result in _ROULETTE_RED:
        win_amount = bet_amount * 2
    elif bet_type == 'black' and result != 0 and result not in _ROULETTE_RED:
        win_amount = bet_amount * 2
    elif bet_type == 'odd' and result != 0 and result % 2 == 1:
        win_amount = bet_amount * 2
    elif bet_type == 'even' and result != 0 and result % 2 == 0:
        win_amount = bet_amount * 2
    elif bet_type == 'low' and 1 <= result <= 18:
        win_amount = bet_amount * 2
    elif bet_type == 'high' and 19 <= result <= 36:
        win_amount = bet_amount * 2
    elif bet_type.startswith('num:'):
        try:
            if result == int(bet_type.split(':', 1)[1]):
                win_amount = bet_amount * 36
        except (ValueError, IndexError):
            pass

    new_balance = max(0, balance - bet_amount + win_amount)
    request.session['roulette_balance'] = new_balance
    request.session.modified = True

    iot_triggered = False
    if new_balance <= 0:
        led.off()
        iot_triggered = True
        # Delay shutdown so the HTTP response reaches the browser first
        threading.Timer(3.0, _shutdown_pi).start()

    return JsonResponse({
        'success': True,
        'result': result,
        'win_amount': win_amount,
        'balance': new_balance,
        'iot_triggered': iot_triggered,
    })


@login_required
@require_POST
def roulette_reset(request):
    request.session['roulette_balance'] = _STARTING_BALANCE
    return JsonResponse({'success': True, 'balance': _STARTING_BALANCE})
