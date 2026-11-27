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

Dal 27-11 sera i numeri si confrontano anche quando righe di asterischi dentro il testo
dividono una lingua in più parti (`language_blocks`): nelle stampe di raccordatura la 010 ha
quattro parti (italiano, nota, inglese, nota) e prima non si confrontava, così i limiti
cambiati in una lingua sola non si vedevano.
"""

import difflib
import re
from collections import Counter
from decimal import Decimal

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


# Parole che dicono la lingua di una parte (solo parole brevi e frequenti, che non sono
# nell'altra lingua): bastano a distinguere italiano e inglese nelle stampe.
_ITALIAN_WORDS = frozenset(
    [
        "di",
        "del",
        "della",
        "delle",
        "dei",
        "degli",
        "il",
        "lo",
        "gli",
        "la",
        "le",
        "con",
        "per",
        "su",
        "sul",
        "sulla",
        "sulle",
        "da",
        "dal",
        "dalla",
        "che",
        "non",
        "sono",
        "e",
        "ed",
        "alla",
        "alle",
        "al",
        "nel",
        "nella",
        "un",
        "una",
        "come",
        "deve",
        "devono",
        "essere",
        "se",
    ]
)
_ENGLISH_WORDS = frozenset(
    [
        "the",
        "of",
        "and",
        "to",
        "with",
        "for",
        "is",
        "are",
        "on",
        "be",
        "not",
        "this",
        "if",
        "as",
        "by",
        "must",
        "should",
        "than",
        "from",
        "all",
        "each",
        "it",
        "that",
    ]
)
_WORD = re.compile(r"[^\W\d_]+")


def _language(text: str) -> str | None:
    words = [word.casefold() for word in _WORD.findall(text)]
    italian = sum(word in _ITALIAN_WORDS for word in words)
    english = sum(word in _ENGLISH_WORDS for word in words)
    if italian == english:
        return None
    return "it" if italian > english else "en"


def language_blocks(description: str) -> tuple[str, str] | None:
    """Parte italiana e parte inglese, anche quando una lingua è divisa in più parti da righe di
    asterischi dentro il testo: le parti vicine della stessa lingua si uniscono (una parte che
    non si riconosce va con quella prima). Solo se alla fine resta italiano e poi inglese."""
    parts = description.split(LANGUAGE_SEPARATOR)
    if len(parts) <= 2:
        return language_parts(description)
    languages: list[str | None] = []
    blocks: list[list[str]] = []
    for part in parts:
        language = _language(part)
        if blocks and (language is None or languages[-1] in (None, language)):
            blocks[-1].append(part)
            languages[-1] = languages[-1] or language
        else:
            languages.append(language)
            blocks.append([part])
    if languages != ["it", "en"]:
        return None
    return " ".join(blocks[0]), " ".join(blocks[1])


# Rimandi: il numero di un'operazione, di una figura, di una pagina... (MG78, 27-11 notte).
# «NELLA OPERAZIONE 70 SUCCESSIVA» contro «IN NEXT STEP ... REFER TO FIGURE 903» non è un numero
# cambiato: i rimandi si confrontano solo con quelli dello stesso tipo dell'altra lingua.
_REFERENCE_KINDS = {
    "operazione": r"OPERAZION[EI]|OPER|OP|FASE|FASI|STEPS?",
    "figura": r"FIGUR[AEI]|FIGURES?|FIGG?|FIGS?",
    "pagina": r"PAGIN[AE]|PAGES?|PAGG?|PP?",
    "tabella": r"TABELL[AE]|TABLES?|TABB?",
    "sezione": r"SEZION[EI]|SECTIONS?|SEZ|SECT?|PARAGRAF[OI]|PARAGRAPHS?|PAR|PARA",
}
_REFERENCE = {
    kind: re.compile(rf"\b(?:{words})\s*\.?\s*(?:N\s*[°.]?\s*)?$", re.IGNORECASE)
    for kind, words in _REFERENCE_KINDS.items()
}


def _reference_kind(text: str, start: int) -> str | None:
    """Il tipo di rimando del numero che comincia in `start`, None se è un valore."""
    before = text[max(0, start - 20) : start]
    return next((kind for kind, rule in _REFERENCE.items() if rule.search(before)), None)


def _numbers(text: str, kind: str | None = None) -> list[tuple[str, Decimal]]:
    """I numeri del testo: i valori (`kind` None) o i rimandi di un tipo (`_REFERENCE_KINDS`)."""
    # ogni numero trovato da `_NUMBER` è un decimale valido (Decimal accetta ogni cifra Unicode)
    return [
        (match.group(), Decimal(match.group().replace(",", ".")))
        for match in _NUMBER.finditer(text)
        if not match["code"] and _reference_kind(text, match.start()) == kind
    ]


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
    parts = language_blocks(description)
    if parts is None:
        return []
    italian, english = (_numbers(part) for part in parts)
    # una lingua scrive anche la conversione («0.38 MM (0.015 IN)», «248 °F (120 °C)») e l'altra
    # no: senza le conversioni le due lingue si allineano di nuovo (26-11)
    italian, english = _without_pairs(italian, english), _without_pairs(english, italian)
    found = _aligned_mismatches(italian, english) or _single_swap(italian, english)
    for kind in _REFERENCE_KINDS:
        # un rimando che c'è in una lingua sola è una frase scritta in un altro modo («nella
        # operazione 70 successiva» contro «in next step»): si confronta solo se ci sono tutti e due
        it_refs, en_refs = (_numbers(part, kind) for part in parts)
        if it_refs and en_refs:
            found += _aligned_mismatches(it_refs, en_refs) or _single_swap(it_refs, en_refs)
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


# --- Versione stretta del confronto tra le lingue (`agent.compare_languages_strict`, I15) ---
#
# Il modello dice che tipo di differenza ha visto e copia le parole delle due lingue; il codice
# accetta solo quello che ritrova in quelle parole: una negazione che c'è in una lingua sola, o
# due limiti di verso opposto. Così una traduzione libera non diventa ERRATO.

_NEGATION = {
    "it": re.compile(r"\b(?:non|né|mai|vietat[oaie]|evitare|senza)\b", re.IGNORECASE),
    "en": re.compile(
        r"\b(?:not|never|nor|without|avoid|prohibited|don'?t|doesn'?t|no(?!\.))\b",
        re.IGNORECASE,
    ),
}
# Limiti «verso il basso» (al massimo) e «verso l'alto» (almeno). Quelli negati («non oltre»,
# «not to exceed») si cercano per primi: dicono il contrario della parola che contengono.
_LIMIT_DOWN = {
    "it": re.compile(
        r"\b(?:non\s+(?:superiore|oltre|più\s+di|maggiore)\w*|al\s+massimo|massim[oaie]|"
        r"inferior[ei]|sotto|meno\s+di|minore|fino\s+a|max)\b",
        re.IGNORECASE,
    ),
    "en": re.compile(
        r"\b(?:not\s+(?:to\s+)?exceed\w*|not\s+more\s+than|no\s+more\s+than|at\s+most|"
        r"maximum|max|below|under|less\s+than|lower\s+than|up\s+to)\b",
        re.IGNORECASE,
    ),
}
_LIMIT_UP = {
    "it": re.compile(
        r"\b(?:almeno|minim[oaie]|superior[ei]|oltre|sopra|più\s+di|maggiore|min)\b",
        re.IGNORECASE,
    ),
    "en": re.compile(
        r"\b(?:at\s+least|minimum|min|above|over|more\s+than|greater\s+than|higher\s+than|"
        r"exceed\w*)\b",
        re.IGNORECASE,
    ),
}


def has_negation(text: str, language: str) -> bool:
    """Nel testo c'è una negazione o un divieto (`language`: `it` o `en`)."""
    return _NEGATION[language].search(text) is not None


# «non inferiore a», «no less than»: un minimo scritto con una negazione (27-11 notte: senza
# questa regola «NO LESS THAN 5» sembrava un massimo). Si cercano prima di tutto.
_LIMIT_UP_NEGATED = {
    "it": re.compile(r"\bnon\s+(?:inferior\w*|meno\s+di|sotto|minore)\b", re.IGNORECASE),
    "en": re.compile(
        r"\b(?:not|no)\s+(?:less|lower|fewer|below|under|smaller)(?:\s+than)?\b", re.IGNORECASE
    ),
}


def limit_direction(text: str, language: str) -> str | None:
    """Il verso del limite nel testo: `giù` (al massimo), `su` (almeno), None se non ce n'è
    uno solo (nessun limite, oppure un intervallo con minimo e massimo)."""
    negated_up = _LIMIT_UP_NEGATED[language].search(text) is not None
    text = _LIMIT_UP_NEGATED[language].sub(" ", text)
    down = _LIMIT_DOWN[language].search(text) is not None
    rest = _LIMIT_DOWN[language].sub(" ", text)
    up = negated_up or _LIMIT_UP[language].search(rest) is not None
    if down == up:
        return None
    return "giù" if down else "su"


def strict_difference(kind: str, italian: str, english: str) -> bool:
    """Il codice ritrova la differenza dichiarata dal modello nelle parole copiate."""
    if kind == "negazione":
        return has_negation(italian, "it") != has_negation(english, "en")
    if kind == "limite":
        first, second = limit_direction(italian, "it"), limit_direction(english, "en")
        return first is not None and second is not None and first != second
    return False


# --- Differenze tra le lingue trovate dal codice, senza modello (27-11 notte) ---------------
# MG75: lo stesso numero con un limite di verso opposto nelle due lingue («LENTE CON
# INGRANDIMENTO SUPERIORE A 4X» contro «MAGNIFICATION NOT TO EXCEED 4X»): prima lo trovava solo
# il modello, 3-4 volte su 6. Conta solo la frase in cui sta il numero, e solo le parole prima.
# Sulle 14 stampe della v1: le 060 di 22f586bb, 895167b9, 737dec71, nessun falso errore.
_CLAUSE_END = re.compile(r"[.;:](?=\s)|\s-\s|\(|\)")


def _limited_values(text: str, language: str) -> dict[Decimal, list[tuple[str, str]]]:
    """Valore → [(verso, frase)] per i numeri preceduti da un limite nella stessa frase. I
    rimandi, i codici e i numeri di un elenco («5)») restano fuori."""
    found: dict[Decimal, list[tuple[str, str]]] = {}
    for match in _NUMBER.finditer(text):
        if match["code"] or _reference_kind(text, match.start()) is not None:
            continue
        if text[match.end() : match.end() + 1] == ")":
            continue  # numero di un elenco: «5) NEL CASO...»
        before = text[max(0, match.start() - 45) : match.start()]
        clause = _CLAUSE_END.split(before)[-1]
        direction = limit_direction(clause, language)
        if direction is None:
            continue
        value = Decimal(match.group().replace(",", "."))
        phrase = " ".join((clause + text[match.start() : match.end() + 3]).split())
        found.setdefault(value, []).append((direction, phrase))
    return found


def limit_mismatches(description: str) -> list[tuple[str, str]]:
    """(frase italiana, frase inglese) per ogni numero con un limite di verso opposto."""
    parts = language_blocks(description)
    if parts is None:
        return []
    italian, english = _limited_values(parts[0], "it"), _limited_values(parts[1], "en")
    found: list[tuple[str, str]] = []
    for value, it_limits in italian.items():
        en_limits = english.get(value, [])
        it_ways, en_ways = {way for way, _ in it_limits}, {way for way, _ in en_limits}
        if len(it_ways) == 1 and len(en_ways) == 1 and it_ways != en_ways:
            found.append((it_limits[0][1], en_limits[0][1]))
    return found


# MG47: un'azione diversa nelle due lingue («VERIFICARE CHE SIA STATO RIMOSSO» contro «HAS BEEN
# BLENDED»). Conta solo se ogni lingua ha un'azione che l'altra non ha: una frase in più in una
# lingua non basta. Sulle 14 stampe della v1: e9b74c84 040 e 298bc28e 035, nessun falso errore.
_ACTIONS: dict[str, tuple[str, str]] = {
    "rimuovere": (r"rimuov\w*|rimoss\w*|rimozion\w*|asport\w*", r"remov\w*"),
    "raccordare": (r"raccord\w*", r"blend\w*"),
    "sostituire": (r"sostitu\w*", r"replac\w*"),
    "lucidare": (r"lucid\w*", r"polish\w*"),
    "sabbiare": (r"sabbi\w*", r"(?:grit\s*)?blast\w*"),
    "saldare": (r"sald\w*", r"weld\w*"),
    "pulire": (r"pulir\w*|pulit\w*|lavagg\w*|lavar\w*", r"clean\w*|wash\w*"),
}
_ACTION = {
    language: {
        action: re.compile(rf"\b(?:{words[k]})", re.IGNORECASE)
        for action, words in _ACTIONS.items()
    }
    for k, language in enumerate(("it", "en"))
}


def actions(text: str, language: str) -> set[str]:
    """Le azioni del testo (nomi italiani di `_ACTIONS`)."""
    return {action for action, rule in _ACTION[language].items() if rule.search(text)}


def action_mismatches(description: str) -> list[tuple[str, str]]:
    """[(azioni solo in italiano, azioni solo in inglese)] se tutte e due le lingue ne hanno."""
    parts = language_blocks(description)
    if parts is None:
        return []
    italian, english = actions(parts[0], "it"), actions(parts[1], "en")
    only_italian, only_english = italian - english, english - italian
    if not only_italian or not only_english:
        return []
    return [(", ".join(sorted(only_italian)), ", ".join(sorted(only_english)))]
