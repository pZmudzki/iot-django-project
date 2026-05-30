"""
Diagnostics for servo (GPIO 12) and TCS3200 color sensor.
Run on the Pi:  python3 diagnostics.py
"""
import time

# ── Servo ─────────────────────────────────────────────────────────────────────

def test_servo():
    print("\n=== SERVO TEST (GPIO 12) ===")
    try:
        from gpiozero import Servo
        s = Servo(12)
        for label, val in [("center (0.0)", 0.0), ("max (+1.0)", 1.0), ("min (-1.0)", -1.0), ("center (0.0)", 0.0)]:
            print(f"  value={val}  ({label}) — czekam 2s...")
            s.value = val
            time.sleep(2)
        s.value = None  # detach PWM
        print("  Servo OK — jesli stalo w centrum przy 0.0 to standard 180 deg servo.")
        print("  Jesli krecilo sie przy 0.0 to continuous rotation servo — wymaga kalibracji.")
    except Exception as e:
        print(f"  BLAD: {e}")


# ── Color sensor ──────────────────────────────────────────────────────────────

S0, S1, S2, S3, OUT = 23, 22, 25, 24, 27


def _count_pulses_poll(s2_val, s3_val, duration=0.1):
    """Poll-based pulse counting — avoids wait_for_edge errors."""
    import RPi.GPIO as GPIO
    GPIO.output(S2, GPIO.HIGH if s2_val else GPIO.LOW)
    GPIO.output(S3, GPIO.HIGH if s3_val else GPIO.LOW)
    time.sleep(0.01)  # let filter settle
    count = 0
    last = GPIO.input(OUT)
    end = time.time() + duration
    while time.time() < end:
        cur = GPIO.input(OUT)
        if last == 1 and cur == 0:  # falling edge
            count += 1
        last = cur
    return count


def test_color():
    print("\n=== COLOR SENSOR TEST (TCS3200) ===")
    try:
        import RPi.GPIO as GPIO
    except ImportError:
        print("  BLAD: RPi.GPIO nie jest zainstalowane.")
        return

    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup([S0, S1, S2, S3], GPIO.OUT)
        GPIO.setup(OUT, GPIO.IN)
        GPIO.output(S0, GPIO.HIGH)
        GPIO.output(S1, GPIO.LOW)   # 20% scaling
        print("  GPIO zainicjalizowane OK")
    except Exception as e:
        print(f"  BLAD inicjalizacji GPIO: {e}")
        return

    # Raw pulse test
    print("  Liczenie impulsow na OUT (0.1s per kolor)...")
    try:
        r = _count_pulses_poll(False, False)
        g = _count_pulses_poll(True,  True)
        b = _count_pulses_poll(False, True)
        print(f"  Raw pulses  R={r}  G={g}  B={b}")

        if r == 0 and g == 0 and b == 0:
            print("  PROBLEM: brak impulsow na OUT.")
            print("    - Sprawdz czy OUT (GPIO 27) jest poprawnie podlaczony")
            print("    - Sprawdz zasilanie VCC czujnika (moze wymagac 5V)")
            print("    - Sprawdz czy S0/S1 sa HIGH/LOW (wlacza czujnik)")
        else:
            total = max(r + g + b, 1)
            rv = int(min(255, r / total * 765))
            gv = int(min(255, g / total * 765))
            bv = int(min(255, b / total * 765))
            print(f"  Kolor  R={rv}  G={gv}  B={bv}  hex=#{rv:02X}{gv:02X}{bv:02X}")
            print("  Czujnik dziala. Jesli kolory sa bledne — skalibruj w jasnym oswietleniu.")
    except Exception as e:
        print(f"  BLAD odczytu: {e}")
    finally:
        GPIO.cleanup()
        print("  GPIO wyczyszczone.")


# ── OUT pin raw check ─────────────────────────────────────────────────────────

def test_out_pin():
    print("\n=== RAW OUT PIN CHECK (GPIO 27, 2s) ===")
    try:
        import RPi.GPIO as GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup([S0, S1], GPIO.OUT)
        GPIO.setup(OUT, GPIO.IN)
        GPIO.output(S0, GPIO.HIGH)
        GPIO.output(S1, GPIO.LOW)

        count = 0
        last = GPIO.input(OUT)
        end = time.time() + 2.0
        while time.time() < end:
            cur = GPIO.input(OUT)
            if last == 1 and cur == 0:
                count += 1
            last = cur

        print(f"  Impulsy w 2s: {count}")
        if count == 0:
            print("  Brak sygnalu — zly kabel OUT lub czujnik bez zasilania.")
        elif count < 10:
            print("  Bardzo malo impulsow — slabe oswietlenie lub bledne S0/S1.")
        else:
            print("  Sygnal OK.")
        GPIO.cleanup()
    except Exception as e:
        print(f"  BLAD: {e}")


if __name__ == "__main__":
    test_out_pin()
    test_color()
    test_servo()
