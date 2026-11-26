"""Le due lingue della descrizione dicono gli stessi numeri?

Nelle stampe PVRM320 la descrizione di un'operazione è scritta in italiano e poi in inglese,
divise da una riga di asterischi (nel testo letto: ` / `). Se un numero cambia in una sola
delle due lingue (13-38 micron in italiano, 13-58 in inglese), una delle due è sbagliata: lo
si vede senza manuale e senza modello.

Si confrontano le due sequenze di numeri e si segnala solo una **sostituzione**: un numero al
posto di un altro, nello stesso punto. Un numero che c'è in una sola lingua non conta (una
frase in più), né una conversione tra millimetri e pollici o tra gradi C e F. Dal 26-11 una
conversione scritta in una lingua sola («0.38 MM (0.015 IN)») non sposta l'allineamento: prima
un numero cambiato lì vicino non si vedeva. Dal 26-11 sera vale anche quando la conversione
viene prima del numero («248 °F (120 °C)»).

I codici fatti di cifre (part number, numeri di 5 cifre o più) le due lingue li scrivono spesso
in punti diversi: si confrontano a parte, come elenco. Un codice che c'è solo in una lingua al
posto di un altro che c'è solo nell'altra è un codice cambiato (26-11 sera: prima i codici non
si confrontavano).
"""

import difflib
import re
from collections import Counter
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


def _codes(text: str) -> list[str]:
    return [match["code"] for match in _NUMBER.finditer(text) if match["code"]]


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
    """Coppie (numero italiano, numero inglese) diverse nello stesso punto delle due lingue,
    poi i codici cambiati."""
    parts = language_parts(description)
    if parts is None:
        return []
    italian, english = (_numbers(part) for part in parts)
    # una lingua scrive anche la conversione («0.38 MM (0.015 IN)», «248 °F (120 °C)») e l'altra
    # no: senza le conversioni le due lingue si allineano di nuovo (26-11)
    italian, english = _without_pairs(italian, english), _without_pairs(english, italian)
    found = _aligned_mismatches(italian, english) or _single_swap(italian, english)
    return found + _code_mismatches(*parts)


def _aligned_mismatches(
    italian: list[tuple[str, Decimal]], english: list[tuple[str, Decimal]]
) -> list[tuple[str, str]]:
    """Le sostituzioni trovate allineando le due sequenze di numeri."""
    matcher = difflib.SequenceMatcher(
        a=[value for _, value in italian], b=[value for _, value in english], autojunk=False
    )
    found: list[tuple[str, str]] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag != "replace":
            continue
        left, right = italian[i1:i2], english[j1:j2]
        if len(left) != len(right):
            # la conversione può essere del numero cambiato: «248 °F (240 °C)» contro «120 °C».
            # Si tolgono dal pezzo più lungo le conversioni dei numeri dell'altro (26-11 sera)
            left, right = _without_conversions_of(left, right), _without_conversions_of(right, left)
            if len(left) != len(right):
                continue
        for (raw_a, a), (raw_b, b) in zip(left, right, strict=True):
            if a != b and not _converted(a, b):
                found.append((raw_a, raw_b))
    return found


def _single_swap(
    italian: list[tuple[str, Decimal]], english: list[tuple[str, Decimal]]
) -> list[tuple[str, str]]:
    """Tanti numeri quanti nelle due lingue, uguali tranne uno: «VEDI OP. 50, OP. 25» contro
    «SEE OP. 25, OP. 25». L'allineamento qui vede un numero tolto e uno aggiunto, non una
    sostituzione (26-11 sera). Lo stesso ordine non serve: le lingue lo cambiano spesso."""
    if len(italian) != len(english):
        return []
    a, b = Counter(value for _, value in italian), Counter(value for _, value in english)
    only_italian, only_english = list((a - b).elements()), list((b - a).elements())
    if len(only_italian) != 1 or len(only_english) != 1:
        return []
    old, new = only_italian[0], only_english[0]
    if _converted(old, new):
        return []
    raw_a = next(raw for raw, value in italian if value == old)
    raw_b = next(raw for raw, value in english if value == new)
    return [(raw_a, raw_b)]


def _code_mismatches(italian: str, english: str) -> list[tuple[str, str]]:
    """Codici cambiati: quelli che ci sono solo in una lingua, se sono tanti quanti quelli che
    ci sono solo nell'altra (un codice in più in una lingua sola è una frase in più)."""
    a, b = Counter(_codes(italian)), Counter(_codes(english))
    only_italian, only_english = list((a - b).elements()), list((b - a).elements())
    if not only_italian or len(only_italian) != len(only_english):
        return []
    return list(zip(only_italian, only_english, strict=True))


def _without_pairs(
    numbers: list[tuple[str, Decimal]], other: list[tuple[str, Decimal]]
) -> list[tuple[str, Decimal]]:
    """I numeri senza uno dei due di ogni coppia vicina in cui uno è la conversione dell'altro
    (mm ↔ pollici, °C ↔ °F). Resta quello che c'è anche nell'altra lingua; se nessuno dei due
    c'è, quello scritto prima."""
    values = {value for _, value in other}
    dropped: set[int] = set()
    for k in range(len(numbers) - 1):
        if k in dropped or not _converted(numbers[k][1], numbers[k + 1][1]):
            continue
        first_only = numbers[k + 1][1] in values and numbers[k][1] not in values
        dropped.add(k if first_only else k + 1)
    return [number for k, number in enumerate(numbers) if k not in dropped]


def _without_conversions_of(
    numbers: list[tuple[str, Decimal]], other: list[tuple[str, Decimal]]
) -> list[tuple[str, Decimal]]:
    """`numbers` senza le conversioni di un numero di `other`, se `numbers` è il più lungo."""
    if len(numbers) <= len(other):
        return numbers
    return [n for n in numbers if not any(_converted(n[1], o[1]) for o in other)]
