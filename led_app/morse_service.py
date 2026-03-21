"""
led_app/morse_service.py

Konwertuje tekst na kod Morse'a i odgrywa go na diodzie LED przez gpiozero.
"""

import time
import logging

logger = logging.getLogger(__name__)

# ── Timings (sekundy) ──────────────────────────────────────────────────────
DOT_DURATION  = 0.15   # ·
DASH_DURATION = 0.45   # −  (3× dot)
SYMBOL_GAP    = 0.15   # przerwa między · i − w tej samej literze
LETTER_GAP    = 0.45   # przerwa między literami
WORD_GAP      = 1.05   # przerwa między słowami

# ── Tablica Morse'a ────────────────────────────────────────────────────────
MORSE_TABLE = {
    'A': '.-',    'B': '-...',  'C': '-.-.',  'D': '-..',
    'E': '.',     'F': '..-.',  'G': '--.',   'H': '....',
    'I': '..',    'J': '.---',  'K': '-.-',   'L': '.-..',
    'M': '--',    'N': '-.',    'O': '---',   'P': '.--.',
    'Q': '--.-',  'R': '.-.',   'S': '...',   'T': '-',
    'U': '..-',   'V': '...-',  'W': '.--',   'X': '-..-',
    'Y': '-.--',  'Z': '--..',
    '0': '-----', '1': '.----', '2': '..---', '3': '...--',
    '4': '....-', '5': '.....', '6': '-....', '7': '--...',
    '8': '---..',  '9': '----.',
    '.': '.-.-.-', ',': '--..--', '?': '..--..', '!': '-.-.--',
}


def text_to_morse(text: str) -> str:
    """Konwertuje tekst na stringa Morse'a (np. '... --- ...')"""
    words = text.upper().split()
    morse_words = []
    for word in words:
        letters = [MORSE_TABLE[ch] for ch in word if ch in MORSE_TABLE]
        if letters:
            morse_words.append(' '.join(letters))
    return '  '.join(morse_words)  # podwójna spacja = przerwa słowna


def play_morse_on_led(led, morse_string: str):
    """
    Odgrywa kod Morse'a na przekazanym obiekcie LED (gpiozero lub DummyLED).
    Wywołuj w osobnym wątku żeby nie blokować serwera.
    """
    logger.info(f"[MORSE] Start: {morse_string!r}")

    i = 0
    while i < len(morse_string):
        ch = morse_string[i]

        if ch == '.':
            led.on()
            time.sleep(DOT_DURATION)
            led.off()
            time.sleep(SYMBOL_GAP)

        elif ch == '-':
            led.on()
            time.sleep(DASH_DURATION)
            led.off()
            time.sleep(SYMBOL_GAP)

        elif ch == ' ':
            # Podwójna spacja → przerwa między słowami
            if i + 1 < len(morse_string) and morse_string[i + 1] == ' ':
                time.sleep(WORD_GAP - SYMBOL_GAP)
                i += 1
            else:
                time.sleep(LETTER_GAP - SYMBOL_GAP)

        i += 1

    logger.info("[MORSE] Zakończono odgrywanie.")
