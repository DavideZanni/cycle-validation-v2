"""Errori ciechi: copie dei cicli veri con un solo errore messo dal programma.

I 12 errori noti li conosce chi scrive le migliorie: una miglioria può «impararli a memoria»
(funziona su quelli e non su errori nuovi). Qui il programma prende cicli veri e in ognuno
cambia **una** operazione con un errore di cui il codice è sicuro:

- `numero_una_lingua`: un numero cambiato solo in italiano o solo in inglese (le due lingue
  non dicono più la stessa cosa);
- `numero_manuale`: un numero che c'è nelle due lingue **e** nel testo del manuale con cui la
  v2 confronta l'operazione, cambiato in tutte e due le lingue con un valore che il manuale
  non ha (il ciclo contraddice il manuale);
- `negazione_una_lingua`: un «non» / «not» tolto in una lingua sola (le due lingue dicono il
  contrario);
- `task_inesistente`: l'ultimo gruppo di un codice di task cambiato in uno che nessun
  documento ha, mentre i suoi fratelli ci sono.

La copia ha solo l'operazione cambiata (le altre si provano già con i cicli veri): costa come
una operazione. Le mutazioni dipendono da un **seme**: con un seme nuovo escono errori nuovi,
che nessuno ha visto. Chi scrive le migliorie vede solo quante ne trova per tipo, mai quali.
"""

import random
import re
from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal

from cycle_validation.checks.languages import LANGUAGE_SEPARATOR, language_parts
from cycle_validation.domain.cycle import Cycle, Operation
from cycle_validation.errors import CycleValidationError
from cycle_validation.kb.documents import read_lines
from cycle_validation.kb.port import KnowledgeBase
from cycle_validation.resolve.civil import (
    context_locations,
    manuals_for_operation,
    wrong_code_siblings,
)
from cycle_validation.text import normalize_code

KINDS = (
    "numero_una_lingua",
    "numero_manuale",
    "negazione_una_lingua",
    "task_inesistente",
    # dal 24-11: errori in tutte e due le lingue, che si vedono solo confrontando con il
    # manuale (le due lingue restano d'accordo tra loro)
    "negazione_due_lingue",
    "limite_invertito",
)
# chi deve trovare ogni tipo: il codice (`INCOERENZA_LINGUE`, `TASK_INESISTENTE`) li trova con
# la stessa regola che li ha messi, quindi non dicono se la v2 generalizza; solo i tipi del
# modello (e il gruppo nascosto) lo dicono
CODE_KINDS = frozenset({"numero_una_lingua", "task_inesistente"})
MODEL_KINDS = tuple(kind for kind in KINDS if kind not in CODE_KINDS)
DESCRIPTIONS = {
    "numero_una_lingua": "un numero cambiato in una lingua sola",
    "numero_manuale": "un numero del manuale cambiato in tutte e due le lingue",
    "negazione_una_lingua": "una negazione tolta in una lingua sola",
    "task_inesistente": "un codice di task che non esiste",
    "negazione_due_lingue": "una negazione tolta in tutte e due le lingue",
    "limite_invertito": "un limite invertito (minimo/massimo) in tutte e due le lingue",
}
# coppie di parole di limite: si scambia la prima trovata, nelle due lingue
_ITALIAN_LIMITS = (
    ("al massimo", "almeno"),
    ("almeno", "al massimo"),
    ("massimo", "minimo"),
    ("minimo", "massimo"),
    ("max", "min"),
    ("min", "max"),
)
_ENGLISH_LIMITS = (
    ("at most", "at least"),
    ("at least", "at most"),
    ("maximum", "minimum"),
    ("minimum", "maximum"),
    ("max", "min"),
    ("min", "max"),
)
# un numero a sé: non attaccato a lettere, trattini (codici e sezioni), barre o altre cifre
_NUMBER = re.compile(r"(?<![\w.,/-])\d+(?:[.,]\d+)?(?![\w/-]|[.,]\d)")
_LIST_MARKER = re.compile(r"^\s*(?:[-*#>]+\s*)*\(?\d+[.)]\s+")
_ITALIAN_NOT = re.compile(r"\bnon\s+", re.IGNORECASE)
_ENGLISH_NOT = (
    (re.compile(r"\bdo(?:es)? not\s+", re.IGNORECASE), ""),
    (re.compile(r"\b(must|shall|should|is|are|can|may|will)\s+not\b", re.IGNORECASE), r"\1"),
)
_FULL_TASK = re.compile(r"^(\d{2}-\d{2}-\d{2}-\d{3})-(\d{3})$")
# copie al massimo da uno stesso ciclo vero. Era 2: il 24-11 con 16 cicli si è fermato a 32
# copie e solo 3 «numero_manuale», troppo poche per misurare
PER_CYCLE = 6
# i tipi del codice servono solo a vedere che non si rompe niente: bastano pochi, così il posto
# va ai tipi del modello, che misurano la generalizzazione
CODE_KIND_MAX = 5


@dataclass(frozen=True)
class Mutation:
    kind: str
    source: str  # impronta del ciclo vero
    operation: str  # numero dell'operazione cambiata
    cycle: Cycle  # la copia, con la sola operazione cambiata


def _value(raw: str) -> Decimal:
    return Decimal(raw.replace(",", "."))


def _format(value: Decimal, like: str) -> str:
    """Il valore scritto come `like`: stesso separatore e stesse cifre decimali."""
    separator = "," if "," in like else "."
    decimals = len(like.split(separator)[1]) if separator in like else 0
    text = f"{value:.{decimals}f}"
    return text.replace(".", separator) if decimals else text


def _other_value(raw: str, avoid: set[Decimal]) -> str | None:
    """Un valore diverso, non in `avoid`, che non sia una conversione di unità."""
    value = _value(raw)
    candidates = [value * 2, value + 1, value * 3, value + 5] if value else [Decimal(2)]
    for candidate in candidates:
        if candidate not in avoid and candidate != value:
            return _format(candidate, raw)
    return None


def _numbers(text: str) -> list[re.Match[str]]:
    return list(_NUMBER.finditer(text))


def _replace_first(text: str, raw: str, new: str) -> str:
    pattern = re.compile(rf"(?<![\w.,/-]){re.escape(raw)}(?![\w/-]|[.,]\d)")
    return pattern.sub(new, text, count=1)


def _with(operation: Operation, **changes: object) -> Operation:
    return operation.model_copy(update=changes)


def _alone(cycle: Cycle, operation: Operation) -> Cycle:
    """Il ciclo con la sola operazione data (le fonti restano tutte)."""
    return cycle.model_copy(update={"operations": [operation]})


def _description(italian: str, english: str) -> str:
    return f"{italian}{LANGUAGE_SEPARATOR}{english}"


def _one_language_number(operation: Operation, rng: random.Random) -> Operation | None:
    parts = language_parts(operation.operation_description)
    if parts is None:
        return None
    italian, english = parts
    shared = {m.group() for m in _numbers(italian)} & {m.group() for m in _numbers(english)}
    if not shared:
        return None
    raw = rng.choice(sorted(shared))
    everything = {_value(m.group()) for m in _numbers(italian) + _numbers(english)}
    new = _other_value(raw, everything)
    if new is None:
        return None
    if rng.random() < 0.5:
        italian = _replace_first(italian, raw, new)
    else:
        english = _replace_first(english, raw, new)
    return _with(operation, operation_description=_description(italian, english))


def _context_numbers(cycle: Cycle, operation: Operation, kb: KnowledgeBase) -> set[Decimal]:
    values: set[Decimal] = set()
    for location in context_locations(_alone(cycle, operation), operation, kb):
        lines = read_lines(location.document.path)[location.line_start - 1 : location.line_end]
        for line in lines:
            body = _LIST_MARKER.sub("", line)  # «3.» all'inizio è il numero del passo
            values.update(_value(m.group()) for m in _numbers(body))
    return values


def _manual_number(
    cycle: Cycle, operation: Operation, kb: KnowledgeBase, rng: random.Random
) -> Operation | None:
    parts = language_parts(operation.operation_description)
    if parts is None:
        return None
    italian, english = parts
    shared = {m.group() for m in _numbers(italian)} & {m.group() for m in _numbers(english)}
    if not shared:
        return None
    manual = _context_numbers(cycle, operation, kb)
    in_manual = sorted(raw for raw in shared if _value(raw) in manual)
    if not in_manual:
        return None
    raw = rng.choice(in_manual)
    everything = manual | {_value(m.group()) for m in _numbers(italian) + _numbers(english)}
    new = _other_value(raw, everything)
    if new is None:
        return None
    return _with(
        operation,
        operation_description=_description(
            _replace_first(italian, raw, new), _replace_first(english, raw, new)
        ),
    )


def _one_language_negation(operation: Operation, rng: random.Random) -> Operation | None:
    parts = language_parts(operation.operation_description)
    if parts is None:
        return None
    italian, english = parts
    english_hits = [(p, r) for p, r in _ENGLISH_NOT if p.search(english)]
    choices: list[str] = []
    if _ITALIAN_NOT.search(italian) and english_hits:
        choices = ["italiano", "inglese"]
    if not choices:
        return None
    if rng.choice(choices) == "italiano":
        italian = _ITALIAN_NOT.sub("", italian, count=1)
    else:
        pattern, replacement = english_hits[0]
        english = pattern.sub(replacement, english, count=1)
    return _with(operation, operation_description=_description(italian, english))


def _both_languages_negation(operation: Operation) -> Operation | None:
    parts = language_parts(operation.operation_description)
    if parts is None:
        return None
    italian, english = parts
    english_hits = [(p, r) for p, r in _ENGLISH_NOT if p.search(english)]
    if not _ITALIAN_NOT.search(italian) or not english_hits:
        return None
    pattern, replacement = english_hits[0]
    return _with(
        operation,
        operation_description=_description(
            _ITALIAN_NOT.sub("", italian, count=1), pattern.sub(replacement, english, count=1)
        ),
    )


def _swap_limit(text: str, pairs: Sequence[tuple[str, str]]) -> str | None:
    """Il testo con la prima parola di limite scambiata (stesse maiuscole), o None."""
    found: list[tuple[int, re.Match[str], str]] = []
    for word, other in pairs:
        match = re.search(rf"(?<![\w.]){re.escape(word)}(?![\w])", text, re.IGNORECASE)
        if match:
            found.append((match.start(), match, other))
    if not found:
        return None
    _, match, other = min(found, key=lambda item: (item[0], -len(item[1].group())))
    original = match.group()
    new = other.upper() if original.isupper() else other
    return text[: match.start()] + new + text[match.end() :]


def _inverted_limit(operation: Operation) -> Operation | None:
    parts = language_parts(operation.operation_description)
    if parts is None:
        return None
    italian = _swap_limit(parts[0], _ITALIAN_LIMITS)
    english = _swap_limit(parts[1], _ENGLISH_LIMITS)
    if italian is None or english is None:
        return None
    return _with(operation, operation_description=_description(italian, english))


def _missing_task(cycle: Cycle, operation: Operation, kb: KnowledgeBase) -> Operation | None:
    manuals = manuals_for_operation(cycle, operation)
    for task in operation.task_codes:
        match = _FULL_TASK.match(normalize_code(task))
        if match is None:
            continue
        family, last = match.groups()
        for step in (1, 2, 3, 7, 11):
            new = f"{family}-{(int(last) + step) % 1000:03d}"
            if wrong_code_siblings(kb, manuals, new):
                codes = [new if code == task else code for code in operation.task_codes]
                description = operation.operation_description.replace(task, new)
                return _with(operation, task_codes=codes, operation_description=description)
    return None


def mutate(
    cycle: Cycle, operation: Operation, kind: str, kb: KnowledgeBase, rng: random.Random
) -> Operation | None:
    """L'operazione con un errore del tipo dato, o None se il tipo non si applica."""
    try:
        if kind == "numero_una_lingua":
            return _one_language_number(operation, rng)
        if kind == "numero_manuale":
            return _manual_number(cycle, operation, kb, rng)
        if kind == "negazione_una_lingua":
            return _one_language_negation(operation, rng)
        if kind == "task_inesistente":
            return _missing_task(cycle, operation, kb)
        if kind == "negazione_due_lingue":
            return _both_languages_negation(operation)
        if kind == "limite_invertito":
            return _inverted_limit(operation)
    except CycleValidationError:
        return None  # documento non leggibile: si salta
    raise ValueError(f"tipo di mutazione sconosciuto: {kind}")


def blind_mutations(
    cycles: Sequence[tuple[str, Cycle]],
    kb: KnowledgeBase,
    *,
    count: int,
    seed: int,
    kinds: Sequence[str] = KINDS,
    per_cycle: int = PER_CYCLE,
    code_kind_max: int = CODE_KIND_MAX,
) -> list[Mutation]:
    """Fino a `count` copie, ognuna con un errore, a turno tra i tipi; sempre le stesse per lo
    stesso seme e gli stessi cicli. Al massimo `per_cycle` copie da uno stesso ciclo e
    `code_kind_max` copie per ogni tipo del codice (`CODE_KINDS`)."""
    rng = random.Random(seed)
    pairs = [(name, cycle, op) for name, cycle in cycles for op in cycle.operations]
    rng.shuffle(pairs)
    used: dict[str, int] = {}
    taken: set[tuple[str, str]] = set()
    failed: set[tuple[str, str, str]] = set()  # (ciclo, operazione, tipo) che non si applica
    found: list[Mutation] = []
    per_kind: dict[str, int] = {}
    # due stampe dello stesso ciclo (stesso contenuto, PDF diversi) danno la stessa copia: la
    # seconda avrebbe la stessa impronta e sparirebbe (24-11: 41 copie scritte, 39 diverse)
    copies: set[str] = set()
    for round_ in range(len(pairs)):
        progress = False
        for kind in kinds:
            if len(found) >= count:
                return found
            if kind in CODE_KINDS and per_kind.get(kind, 0) >= code_kind_max:
                continue
            for name, cycle, operation in pairs:
                key = (name, operation.operation_number)
                if key in taken or (*key, kind) in failed or used.get(name, 0) >= per_cycle:
                    continue
                changed = mutate(cycle, operation, kind, kb, rng)
                if changed is None or changed == operation:
                    failed.add((*key, kind))
                    continue
                copy = _alone(cycle, changed)
                text = copy.model_dump_json()
                if text in copies:
                    failed.add((*key, kind))
                    continue
                copies.add(text)
                taken.add(key)
                used[name] = used.get(name, 0) + 1
                per_kind[kind] = per_kind.get(kind, 0) + 1
                found.append(Mutation(kind, name, operation.operation_number, copy))
                progress = True
                break
        if not progress or round_ > count:
            break
    return found
