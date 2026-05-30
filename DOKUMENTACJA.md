# Dokumentacja projektu IoT – Django + Raspberry Pi

## Spis treści
1. [Opis projektu](#1-opis-projektu)
2. [Schemat połączeń](#2-schemat-połączeń)
3. [Konfiguracja Raspberry Pi](#3-konfiguracja-raspberry-pi)
4. [Uruchomienie aplikacji](#4-uruchomienie-aplikacji)
5. [Jak działa każda funkcja](#5-jak-działa-każda-funkcja)

---

## 1. Opis projektu

Aplikacja webowa napisana w Django 6, sterująca urządzeniami podłączonymi do Raspberry Pi przez GPIO. Dostęp przez przeglądarkę z dowolnego urządzenia w sieci lokalnej.

**Zrealizowane funkcje:**
| # | Funkcja |
|---|---------|
| 1 | Zapalanie i gaszenie diody LED przez przeglądarkę |
| 2 | Odczyt temperatury z czujnika DS18B20 w przeglądarce |
| 4 | Dynamiczny wykres temperatury (Chart.js, odświeżany co 30 s) |
| 5 | Logowanie użytkownika (Django Auth) |
| 11 | Zapis odczytów temperatury do bazy SQLite |
| 14 | Alarm dźwiękowy buzzerem po przekroczeniu progu temperatury |
| 19 | Sterowanie serwomotorem przez potencjometr |
| 20 | Harmonogram zapalania/gaszenia LED |
| 34 | Generowanie raportu PDF z danymi temperatury |
| ? | Wykrywanie koloru czujnikiem TCS3200 |

**Stos technologiczny:**
- Python 3.13, Django 6.0.3
- SQLite (baza danych)
- gpiozero (LED, buzzer, servo, potencjometr)
- RPi.GPIO (czujnik koloru TCS3200)
- Chart.js (wykresy w przeglądarce)
- ReportLab (generowanie PDF)
- Google Gemini API (Morse – funkcja dodatkowa)

---

## 2. Schemat połączeń

### Numeracja pinów

Projekt używa numeracji **BCM** (nazwy GPIO, nie numery fizyczne pinów).

```
Fizyczny   BCM    Funkcja w projekcie
────────────────────────────────────────
   7        4     DS18B20 DATA (1-wire)
  11       17     LED
  12       18     Buzzer
  13       27     TCS3200 OUT
  15       22     TCS3200 S1
  16       23     TCS3200 S0
  18       24     TCS3200 S3
  19       10     SPI MOSI → MCP3008
  21        9     SPI MISO ← MCP3008
  22       25     TCS3200 S2
  23       11     SPI CLK  → MCP3008
  24        8     SPI CE0  → MCP3008
  32       12     Servo SIGNAL (PWM)
```

---

### Dioda LED (GPIO 17)

```
GPIO 17 (pin 11) ──→ rezystor 220 Ω ──→ anoda (+) LED
GND              ←───────────────────── katoda (−) LED
```

---

### Buzzer (GPIO 18)

```
GPIO 18 (pin 12) ──→ (+) buzzer
GND              ──→ (−) buzzer
```

> Używaj **aktywnego** buzzera (z wbudowanym oscylatorem). Przy stanie wysokim na GPIO brzęczy, przy niskim milczy.

---

### Czujnik temperatury DS18B20 (GPIO 4)

```
3.3V (pin 1)  ──→ VCC (czerwony)   ─┐
                                     ├── rezystor 4,7 kΩ
GPIO 4 (pin 7)──→ DATA (żółty)    ──┘
GND  (pin 9)  ──→ GND (czarny)
```

> Rezystor 4,7 kΩ musi być podciągnięty między DATA a 3,3V – bez niego sensor nie działa.

---

### Serwomotor niebieski (GPIO 12 – PWM)

```
5V  (pin 2)       ──→ czerwony kabel (VCC)
GND (pin 6)       ──→ brązowy/czarny (GND)
GPIO 12 (pin 32)  ──→ pomarańczowy/żółty (SIGNAL)
```

> Przy dużym obciążeniu serwa: zasilaj VCC z zewnętrznego zasilacza 5V.
> GND zewnętrznego zasilacza musi być połączony z GND Raspberry Pi (masa wspólna).

---

### Potencjometr + MCP3008 (SPI, CH0)

**Połączenia MCP3008 z Raspberry Pi:**

```
MCP3008 pin    Sygnał         Pi pin (BCM)
────────────────────────────────────────
    1  (CH0)   → potencjometr (środek)
    9  (DGND)  → GND
   10  (CS)    → GPIO 8 / CE0  (pin 24)
   11  (DIN)   → GPIO 10 / MOSI (pin 19)
   12  (DOUT)  → GPIO 9  / MISO (pin 21)
   13  (CLK)   → GPIO 11 / SCLK (pin 23)
   14  (AGND)  → GND
   15  (VREF)  → 3,3V
   16  (VDD)   → 3,3V
```

**Połączenie potencjometru:**

```
3,3V ──→ lewy pin potencjometru
GND  ──→ prawy pin potencjometru
CH0  ──→ środkowy pin (wiper)
```

---

### Czujnik koloru TCS3200 (GPIO 23, 22, 25, 24, 27)

```
VCC ──→ 3,3V (pin 17)
GND ──→ GND
S0  ──→ GPIO 23 (pin 16)
S1  ──→ GPIO 22 (pin 15)
S2  ──→ GPIO 25 (pin 22)
S3  ──→ GPIO 24 (pin 18)
OUT ──→ GPIO 27 (pin 13)
```

> Moduł Waveshare 9520 ma wbudowany stabilizator, działa na 3,3V i 5V.

---

## 3. Konfiguracja Raspberry Pi

### Krok 1 – Włącz interfejsy

```bash
sudo raspi-config
```

Przejdź do:
- **Interface Options → SPI → Enable** (wymagane dla MCP3008/potencjometru)
- **Interface Options → 1-Wire → Enable** (wymagane dla DS18B20)

Zrestartuj Pi:
```bash
sudo reboot
```

### Krok 2 – Zainstaluj zależności systemowe

```bash
sudo apt update
sudo apt install python3-pip python3-dev pigpio -y

# Uruchom demon pigpio (precyzyjne PWM dla serwa)
sudo systemctl enable pigpiod
sudo systemctl start pigpiod
```

### Krok 3 – Zainstaluj pakiety Python

```bash
cd ~/iot-django-project
pip3 install -r requirements.txt
pip3 install RPi.GPIO
```

### Krok 4 – Skonfiguruj ALLOWED_HOSTS

W pliku `core/settings.py` dodaj adres IP swojego Raspberry Pi:

```python
ALLOWED_HOSTS = ['192.168.1.100', 'raspberrypi.local', 'localhost']
```

Znajdź swój adres IP poleceniem:
```bash
hostname -I
```

### Krok 5 – Przygotuj bazę danych i użytkownika

```bash
python manage.py migrate
python manage.py createsuperuser
```

---

## 4. Uruchomienie aplikacji

```bash
python manage.py runserver 0.0.0.0:8000
```

Otwórz w przeglądarce (na komputerze lub telefonie w tej samej sieci):
```
http://192.168.1.100:8000
```

**Domyślne dane logowania (jeśli używasz konta z dewelopmentu):**
- Login: `admin`
- Hasło: `admin123`

> Zmień hasło po pierwszym logowaniu: `python manage.py changepassword admin`

---

## 5. Jak działa każda funkcja

### 5.1 Sterowanie LED (`/led/`)

Użytkownik klika „Włącz" lub „Wyłącz" w przeglądarce → formularz HTML wysyła `POST` z polem `action=on` lub `action=off` → widok Django wywołuje `led.on()` lub `led.off()` → `gpiozero` ustawia stan wysoki/niski na GPIO 17 → dioda świeci lub gaśnie.

```
Przeglądarka
  POST /led/ {action=on}
        ↓
   views.led_control()
        ↓
   led.on()  ← obiekt gpiozero.LED(17)
        ↓
   GPIO 17 = HIGH → LED świeci
```

---

### 5.2 Odczyt temperatury + zapis do bazy

Temperatura jest odczytywana **w tle** – co 60 sekund przez daemon thread, który startuje razem z serwerem (w `apps.py`).

```
Django startuje
   ↓
apps.py → background.start_background_tasks()
   ↓
wątek: _temperature_recorder()
   ↓ (co 60 sekund)
temperature_service.read_temperature()
   ├── próba: open('/sys/bus/w1/devices/28*/w1_slave')
   │          ← prawdziwy odczyt DS18B20
   └── fallback: random walk ±0.3°C (Windows/brak sensora)
   ↓
TemperatureReading.objects.create(temperature, humidity)
   ↓
baza SQLite (max 5000 rekordów – stare są kasowane)
```

**DS18B20 działa przez protokół 1-wire:** Linux udostępnia odczyt jako plik tekstowy. Wartość temperatura w milikelwinach dzielona przez 1000 daje °C.

Na stronie `/led/` temperatura jest odświeżana co 30 sekund przez `fetch()` do `GET /led/api/temperature/`.

---

### 5.3 Wykres dynamiczny (`/led/chart/`)

```
Przeglądarka otwiera /led/chart/
   ↓
Chart.js pobiera dane: GET /led/api/temperature/
   ↓
views.temperature_api() → ostatnie 50 rekordów z bazy → JSON
   ↓
Chart.js rysuje dwa wykresy:
  - żółty: temperatura (°C), oś lewa
  - niebieski: wilgotność (%), oś prawa
   ↓
co 30 sekund: automatyczne odświeżenie danych
```

---

### 5.4 Alarm buzzer

Buzzer jest kontrolowany przez **ten sam wątek** co temperatura. Po każdym odczycie:

```
temp >= próg  AND  alarm włączony?
      ├── TAK → buzzer.on()   (GPIO 18 = HIGH, buzzer brzęczy)
      └── NIE → buzzer.off()  (GPIO 18 = LOW, cisza)
```

Próg i włącznik są przechowywane w tabeli `BuzzerConfig` (jeden rekord). Użytkownik zmienia je przez kartę „Alarm buzzer" na stronie `/led/` – JavaScript wysyła `POST /led/buzzer/` z danymi JSON.

**Ważne:** sprawdzanie progu odbywa się co 60 sekund (razem z odczytem temperatury). Alarm nie zareaguje natychmiast – maksymalne opóźnienie to 60 sekund.

---

### 5.5 Logowanie użytkownika

Używa wbudowanego systemu autentykacji Django:
- `LoginView` pod adresem `/accounts/login/`
- `LogoutView` pod adresem `/accounts/logout/`
- Wszystkie widoki mają dekorator `@login_required` – niezalogowany użytkownik jest przekierowywany do strony logowania

---

### 5.6 Serwomotor + potencjometr (`/led/servo/`)

Po starcie serwera automatycznie uruchamia się wątek śledzący potencjometr:

```
wątek: servo_service._loop() (co 100 ms)
   ↓
_pot.value  ← MCP3008 CH0, wartość 0.0–1.0
   ↓
przelicz: servo_value = (pot * 2.0) − 1.0   → zakres −1.0 do +1.0
   ↓
_servo.value = servo_value  ← gpiozero.Servo(12)
   ↓
GPIO 12: sygnał PWM → serwomotor obraca się
```

Strona `/led/servo/` pozwala też na ręczne sterowanie suwakiem. Kliknięcie suwaka zatrzymuje śledzenie potencjometru i ustawia kąt ręcznie przez `POST /led/servo/api/`.

---

### 5.7 Harmonogram zapalania LED (`/led/schedule/`)

Osobny wątek sprawdza harmonogramy co 30 sekund:

```
wątek: _schedule_checker() (co 30 s)
   ↓
pobierz wszystkie aktywne harmonogramy z bazy
   ↓
dla każdego: czy dziś jest zaznaczony dzień tygodnia?
             czy bieżący czas jest między on_time a off_time?
   ↓
TAK (choć jeden): led.on()
NIE (żaden):      led.off()
```

Dni tygodnia przechowywane jako 7-znakowy string np. `"1111100"` = Pon–Pt. Indeks 0 = Poniedziałek, 6 = Niedziela.

---

### 5.8 Raport PDF (`/led/pdf/`)

```
GET /led/pdf/
   ↓
pobierz ostatnie 200 rekordów z TemperatureReading
   ↓
pdf_service.generate_pdf(readings)
   ├── tytuł + data wygenerowania
   ├── statystyki: min / max / średnia / liczba pomiarów
   └── tabela: timestamp | temperatura | wilgotność
   ↓
HttpResponse z Content-Type: application/pdf
   ↓
przeglądarka pobiera plik raport_YYYYMMDD_HHMM.pdf
```

---

### 5.9 Czujnik koloru TCS3200 (`/led/color/`)

TCS3200 mierzy natężenie światła w trzech filtrach (R, G, B) i zwraca **częstotliwość** – im więcej danego koloru, tym wyższa częstotliwość na pinie OUT.

```
read_color():
   ↓
Ustaw S2/S3 → filtr czerwony → mierz impulsy przez 50 ms → r_raw
Ustaw S2/S3 → filtr zielony  → mierz impulsy przez 50 ms → g_raw
Ustaw S2/S3 → filtr niebieski→ mierz impulsy przez 50 ms → b_raw
   ↓
normalizuj do 0–255:  r = r_raw / (r+g+b) * 255 * 3
   ↓
zwróć {r, g, b, hex, simulated}
```

Strona `/led/color/` odpytuje `GET /led/color/api/` co 2 sekundy i aktualizuje kolorową „cebulkę" oraz wartości RGB.

---

### 5.10 Morse + Gemini (`/led/morse/`)

```
POST /led/morse/ {prompt: "Ile planet ma Układ Słoneczny?"}
   ↓
Gemini API (system instruction: odpowiadaj TYLKO kodem Morse'a)
   ↓
surowa odpowiedź np. "----. / .----"
   ↓
sanitacja: zostaw tylko . - i spacje
   ↓
threading.Thread → play_morse_on_led(led, morse_string)
   └── . → LED on 0.15s, off 0.15s
   └── - → LED on 0.45s, off 0.15s
   └── spacja → przerwa między literami
   └── podwójna spacja → przerwa między słowami
   ↓
odpowiedź JSON natychmiast (LED gra w tle)
```

> Wymaga prawdziwego klucza Gemini API w `core/settings.py`: `GEMINI_API_KEY = 'twój-klucz'`
> Klucze: https://aistudio.google.com/app/apikey

---

## Adresy URL aplikacji

| Adres | Opis |
|-------|------|
| `/` | Przekierowanie do `/led/` |
| `/led/` | Panel główny: LED, temperatura, buzzer, Morse |
| `/led/chart/` | Wykres historyczny temperatury |
| `/led/schedule/` | Harmonogram zapalania LED |
| `/led/servo/` | Sterowanie serwomotorem |
| `/led/color/` | Odczyt koloru z TCS3200 |
| `/led/pdf/` | Pobierz raport PDF |
| `/accounts/login/` | Logowanie |
| `/accounts/logout/` | Wylogowanie |
| `/admin/` | Panel administracyjny Django |
| `/led/roulette/` | Ruletka – wyłączenie Pi po bankructwie |

---

## 6. Ruletka z wyłączeniem Raspberry Pi (`/led/roulette/`)

### 6.1 Opis funkcji

Żartobliwa funkcja: strona z kołem ruletki i saldem 10 000. Gdy saldo spadnie do zera, serwer automatycznie **wyłącza Raspberry Pi** poleceniem `sudo shutdown -h now`.

---

### 6.2 Jak działa

```
Użytkownik stawia zakład i klika SPIN
   ↓
POST /led/roulette/spin/  {bet_type, bet_amount}
   ↓
views.roulette_spin():
   ├── random.randint(0, 36)  ← losowanie serwera
   ├── oblicz wygraną/przegraną
   ├── zapisz nowe saldo w request.session
   └── jeśli saldo <= 0:
         led.off()
         threading.Timer(3.0, _shutdown_pi).start()
   ↓
JSON z wynikiem → przeglądarka
   ↓
animacja koła (canvas, ~4 sekundy) ląduje na wylosowanej liczbie
   ↓
jeśli iot_triggered == true:
   → nakładka GAME OVER (po 0.9 s)
   → 3 s po odpowiedzi: Pi wyłącza się
```

**Opóźnienie 3 sekundy** przed shutdown jest celowe — daje czas, żeby odpowiedź HTTP dotarła do przeglądarki i animacja koła zdążyła się skończyć. Bez tego Pi wyłączyłoby się przed odesłaniem JSONa.

---

### 6.3 Rodzaje zakładów

| Typ | Wygrana | Opis |
|-----|---------|------|
| Red / Black | 1:1 | 18 liczb każdy kolor |
| Odd / Even | 1:1 | parzystość (0 przegrywa) |
| 1–18 / 19–36 | 1:1 | połowa zakresu (0 przegrywa) |
| Dowolna liczba 0–36 | 35:1 | trafienie konkretnej liczby |

Saldo przechowywane w sesji Django (`request.session['roulette_balance']`). Nie znika po odświeżeniu strony. Przycisk **NEW GAME** resetuje saldo do 10 000 przez `POST /led/roulette/reset/`.

---

### 6.4 Konfiguracja sudoers na Raspberry Pi (wymagane do shutdown)

Bez tego kroku `sudo shutdown` zakończy się błędem i Pi **nie wyłączy się**.

```bash
sudo visudo
```

Dodaj na końcu pliku (zastąp `pi` nazwą użytkownika uruchamiającego Django):

```
pi ALL=(ALL) NOPASSWD: /sbin/shutdown
```

Sprawdź, który użytkownik uruchamia serwer:

```bash
ps aux | grep manage.py
```

Zapis: `Ctrl+X → Y → Enter` (jeśli edytor to nano).

Zweryfikuj działanie ręcznie:

```bash
sudo shutdown -h +1    # zaplanuj wyłączenie za 1 minutę
sudo shutdown -c        # anuluj
```

---

### 6.5 Co się dzieje jeśli polecenie shutdown odpali się na Macu podczas developmentu?

**Nic.** Kod zawiera zabezpieczenie platformowe:

```python
def _shutdown_pi():
    import platform, subprocess
    if platform.system() != 'Linux':
        return  # nie robi nic na macOS ani Windows
    subprocess.run(['sudo', 'shutdown', '-h', 'now'], check=False)
```

`platform.system()` na macOS zwraca `'Darwin'`, na Windows `'Windows'`, na Raspberry Pi `'Linux'`. Funkcja natychmiast kończy działanie bez wywołania żadnego polecenia. Testowanie na laptopie jest w 100% bezpieczne.

> Gdyby zabezpieczenie nie istniało: `sudo shutdown -h now` na macOS **działa** i wyłączyłby Maca. Komenda jest identyczna. Dlatego guard jest obowiązkowy.

---

## 7. Pełna lista kroków – uruchomienie od zera na Raspberry Pi

### Krok 1 — Klonowanie projektu

```bash
git clone <url-repozytorium> ~/iot-django-project
cd ~/iot-django-project
```

### Krok 2 — Włącz interfejsy SPI i 1-Wire

```bash
sudo raspi-config
# Interface Options → SPI → Enable
# Interface Options → 1-Wire → Enable
sudo reboot
```

### Krok 3 — Zainstaluj zależności systemowe

```bash
sudo apt update
sudo apt install python3-pip python3-dev pigpio -y
sudo systemctl enable pigpiod
sudo systemctl start pigpiod
```

### Krok 4 — Zainstaluj pakiety Python

```bash
pip3 install -r requirements.txt
pip3 install RPi.GPIO
```

### Krok 5 — Skonfiguruj ALLOWED_HOSTS

W `core/settings.py`:

```python
ALLOWED_HOSTS = ['192.168.1.100', 'raspberrypi.local', 'localhost']
```

Znajdź IP: `hostname -I`

### Krok 6 — Baza danych i konto użytkownika

```bash
python3 manage.py migrate
python3 manage.py createsuperuser
```

### Krok 7 — (Opcjonalnie) Klucz Gemini API

Jeśli chcesz używać funkcji Morse + Gemini, dodaj do `core/settings.py`:

```python
GEMINI_API_KEY = 'twój-klucz-z-aistudio.google.com'
```

### Krok 8 — Sudoers dla funkcji shutdown (ruletka)

```bash
sudo visudo
```

Dodaj (zastąp `pi` swoją nazwą użytkownika):

```
pi ALL=(ALL) NOPASSWD: /sbin/shutdown
```

### Krok 9 — Uruchom serwer

```bash
python3 manage.py runserver 0.0.0.0:8000
```

Otwórz w przeglądarce:

```
http://<IP-raspberry>:8000
```

---

## 8. Tabela widoków i co wywołują na GPIO

| Strona | URL | GPIO / efekt |
|--------|-----|--------------|
| Panel LED | `/led/` | GPIO 17 (LED on/off) |
| Wykres | `/led/chart/` | brak (tylko odczyt z bazy) |
| Harmonogram | `/led/schedule/` | GPIO 17 (według czasu) |
| Servo | `/led/servo/` | GPIO 12 (PWM) + MCP3008 CH0 |
| Kolor | `/led/color/` | GPIO 23/22/25/24/27 (TCS3200) |
| Ruletka | `/led/roulette/` | GPIO 17 (LED off) + **system shutdown** |
| PDF | `/led/pdf/` | brak |
