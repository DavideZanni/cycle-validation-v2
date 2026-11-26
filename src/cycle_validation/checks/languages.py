"""Le due lingue della descrizione dicono gli stessi numeri?

Nelle stampe PVRM320 la descrizione di un'operazione è scritta in italiano e poi in inglese,
divise da una riga di asterischi (nel testo letto: ` / `). Se un numero cambia in una sola
delle due lingue (13-38 micron in italiano, 13-58 in inglese), una delle due è sbagliata: lo
si vede senza manuale e senza modello.

Si confrontano le due sequenze di numeri e si segnala solo una **sostituzione**: un numero al
posto di un altro, nello stesso punto. Un numero che c'è in una sola lingua non conta (una
frase in più), né una conversione tra millimetri e pollici o tra gradi C e F. Dal 26-11 una
conversione scritta in una lingua sola («0.38 MM (0.015 IN)») non sposta l'allineamento: prima
un numero cambiato lì vicino non si vedeva.
"""

import difflib
import re
from decimal import Decimal, InvalidOperation

# separatore tra le parti della descrizione (riga di asterischi), come la scrive il parser
LANGUAGE_SEPARATOR = " / "
# Un codice fatto di cifre (part number «1234567/89», numeri di 5 cifre o più) non è una misura:
# si lascia fuori, così non si spezza in numeri e non sposta l'allineamento (le due lingue lo
# scrivono spesso in punti diversi della frase).
_NUMBER = re.compile(r"(?<![\w.,/])(?:(?P<code>\d+(?:/\d+)+|\d{5,})|\d+(?:[.,]\d+)?|[.,]\d+)")
_INCH = Decimal("25.4")


def language_parts(description: str) -> tuple[str, str] | None:
    """Parte italiana e parte inglese, se la descrizione ne ha esattamente due."""
    parts = description.split(LANGUAGE_SEPARATOR)
    return (parts[0], parts[1]) if len(parts) == 2 else None


def _numbers(text: str) -> list[tuple[str, Decimal]]:
    found: list[tuple[str, Decimal]] = []
    for match in _NUMBER.finditer(text):
        raw = match.group()
        if match["code"]:
            continue
        try:
            found.append((raw, Decimal(raw.replace(",", "."))))
        except InvalidOperation:
            continue
    return found


def _converted(a: Decimal, b: Decimal) -> bool:
    """Lo stesso valore in un'altra unità: mm ↔ pollici (tolleranza 2%), °C ↔ °F (±1)."""
    if a == 0 or b == 0:
        return False
    for big, small in ((a, b), (b, a)):
        if abs(big / small - _INCH) <= _INCH * Decimal("0.02"):
            return True
        if abs(small * 9 / 5 + 32 - big) <= 1:
            return True
    return False


def number_mismatches(description: str) -> list[tuple[str, str]]:
    """Coppie (numero italiano, numero inglese) diverse nello stesso punto delle due lingue."""
    parts = language_parts(description)
    if parts is None:
        return []
    italian, english = (_numbers(part) for part in parts)
    matcher = difflib.SequenceMatcher(
        a=[value for _, value in italian], b=[value for _, value in english], autojunk=False
    )
    found: list[tuple[str, str]] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag != "replace":
            continue
        left, right = italian[i1:i2], english[j1:j2]
        if len(left) != len(right):
            # una lingua scrive anche la conversione («0.38 MM (0.015 IN)») e l'altra no: senza
            # le conversioni i due pezzi si allineano di nuovo (26-11)
            left, right = (
                _without_conversions(italian, i1, i2),
                _without_conversions(english, j1, j2),
            )
            if len(left) != len(right):
                continue
        for (raw_a, a), (raw_b, b) in zip(left, right, strict=True):
            if a != b and not _converted(a, b):
                found.append((raw_a, raw_b))
    return found


def _without_conversions(
    numbers: list[tuple[str, Decimal]], start: int, end: int
) -> list[tuple[str, Decimal]]:
    """I numeri del pezzo [start, end) senza quelli che sono la conversione del numero subito
    prima (mm ↔ pollici, °C ↔ °F)."""
    return [
        numbers[k]
        for k in range(start, end)
        if k == 0 or not _converted(numbers[k - 1][1], numbers[k][1])
    ]
