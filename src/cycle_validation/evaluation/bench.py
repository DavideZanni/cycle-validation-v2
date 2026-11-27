"""Banco di prova sulle 14 stampe vere (27-11 notte, chiesto dall'utente: «metriche più
specifiche, per verificare davvero che il sistema funzioni»).

Le campagne misurano gli errori noti: una trentina di operazioni. Qui, gratis e in pochi
secondi, il programma mette **un errore alla volta su ogni operazione possibile** delle 14
stampe di `docs/CONFRONTO_V1_14_CICLI.md` (testo vero) e guarda se i controlli del codice lo
trovano, senza modello e senza manuali:

- `numero_una_lingua`: un numero scritto nelle due lingue, cambiato in una sola;
- `limite_una_lingua`: lo stesso numero con lo stesso limite nelle due lingue, il limite
  girato al contrario in una sola («al massimo» → «almeno»);
- `massimo_minimo`: «massimo» nelle due lingue, cambiato in «minimo» in una sola (o il
  contrario);
- `azione_una_lingua`: la stessa azione nelle due lingue, cambiata in un'altra in una sola
  («raccordare» → «rimuovere»);
- `dr_diverso`: il numero «D.R. CASE #» di un'operazione cambiato di una cifra.

Per ogni tipo: quante copie, quante trovate sull'operazione giusta, e quanti ERRATO nuovi su
altre operazioni (falsi allarmi: devono essere 0). Un errore si mette solo dove il codice lo
deve trovare (per esempio il limite solo dove le due lingue hanno lo stesso limite): quello
che resta è del modello.

In più la **lettura della stampa** contro la tabella delle operazioni della v1 (stesso
documento): numeri delle operazioni, targhe, schede. La v1 legge con il modello e può
sbagliare: una differenza si guarda, non è per forza un errore della v2.

Solo impronte, numeri di operazione e conteggi: niente testo delle stampe a schermo."""

import random
import re
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from pathlib import Path

from cycle_validation.checks.base import CheckContext
from cycle_validation.checks.dr_recommendation import cited_dr_numbers
from cycle_validation.checks.languages import (
    LANGUAGE_SEPARATOR,
    _language,
    actions,
    language_blocks,
)
from cycle_validation.checks.operation import plan_operation_checks
from cycle_validation.config import AgentSettings, ProfileConfig
from cycle_validation.domain.check import Verdict
from cycle_validation.domain.cycle import Cycle, Operation
from cycle_validation.extract.pvrm320_report import parse_pvrm320_report
from cycle_validation.ingest.pdf import PdfDocument, PdfPage
from cycle_validation.kb.port import KnowledgeBase
from cycle_validation.services.machines import StaticMachineRegistry

PRINTS = Path("docs/CONFRONTO_V1_14_CICLI.md")
KINDS = (
    "numero_una_lingua",
    "limite_una_lingua",
    "massimo_minimo",
    "azione_una_lingua",
    "dr_diverso",
)
DESCRIPTIONS = {
    "numero_una_lingua": "un numero cambiato in una lingua",
    "limite_una_lingua": "un limite girato al contrario in una lingua",
    "massimo_minimo": "«massimo» diventa «minimo» in una lingua",
    "azione_una_lingua": "un'azione cambiata in una lingua",
    "dr_diverso": "il numero del DR cambiato in un'operazione",
}


# --- Le stampe ------------------------------------------------------------------------------


def read_prints(path: Path = PRINTS) -> dict[str, Cycle]:
    """Le 14 stampe del documento, lette con il parser della v2 (impronta → ciclo)."""
    text = path.read_text("utf-8")
    parts = re.split(r"^### Testo originale (\w+)\n", text, flags=re.MULTILINE)
    cycles: dict[str, Cycle] = {}
    for fingerprint, body in zip(parts[1::2], parts[2::2], strict=True):
        pages = re.findall(r"```text\n(.*?)```", body, flags=re.DOTALL)
        pdf = PdfDocument(
            name=f"{fingerprint}.pdf",
            sha256="0" * 64,
            size_bytes=1,
            pages=tuple(PdfPage(number=n, text=page) for n, page in enumerate(pages, start=1)),
        )
        cycles[fingerprint] = parse_pvrm320_report(pdf)
    return cycles


@dataclass(frozen=True)
class V1Row:
    op: str
    machine: str | None
    sheet: str | None


def read_v1_tables(path: Path = PRINTS) -> dict[str, list[V1Row]]:
    """La tabella «Operazioni» della v1 per ogni ciclo che la v1 ha validato."""
    text = path.read_text("utf-8")
    tables: dict[str, list[V1Row]] = {}
    for match in re.finditer(r"^### Ciclo (\w+)\n(.*?)(?=^### |\Z)", text, re.M | re.S):
        fingerprint, body = match.groups()
        start = body.find("#### Operazioni")
        if start < 0:
            continue
        rows: list[V1Row] = []
        for line in body[start:].splitlines()[1:]:
            if not line.strip():
                if rows:
                    break
                continue
            if not line.startswith("|"):
                break
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if len(cells) < 6 or cells[0] in ("Op.", "") or set(cells[0]) <= {"-", " "}:
                continue
            rows.append(V1Row(op=_op(cells[0]), machine=_cell(cells[2]), sheet=_cell(cells[4])))
        tables[fingerprint] = rows
    return tables


def _cell(cell: str) -> str | None:
    """Il primo valore di una cella della v1 («codice · task · classe»), None se è vuota."""
    first = cell.split("·")[0].strip()
    return None if first in ("", "—", "-") else first


def _op(label: str) -> str:
    text = label.strip()
    return f"{int(text):03d}" if text.isdigit() else text


# --- Le parti di una lingua dentro la descrizione --------------------------------------------


def _parts_by_language(description: str) -> list[tuple[str, str | None]]:
    """Le parti della descrizione (divise da ` / `) con la lingua del blocco a cui vanno, con la
    stessa regola di `language_blocks`."""
    parts = description.split(LANGUAGE_SEPARATOR)
    if len(parts) == 2:
        return [(parts[0], "it"), (parts[1], "en")]
    result: list[tuple[str, str | None]] = []
    current: str | None = None
    for part in parts:
        language = _language(part)
        if result and (language is None or current in (None, language)):
            current = current or language
        else:
            current = language
        result.append((part, current))
    # le parti prima della prima lingua riconosciuta vanno con quella
    first = next((lang for _, lang in result if lang), None)
    return [(part, lang or first) for part, lang in result]


def _change_in(description: str, language: str, change: Callable[[str], str | None]) -> str | None:
    """La descrizione con `change` applicato alla prima parte della lingua data che cambia."""
    parts = _parts_by_language(description)
    for index, (part, lang) in enumerate(parts):
        if lang != language:
            continue
        new = change(part)
        if new is not None and new != part:
            texts = [p for p, _ in parts]
            texts[index] = new
            return LANGUAGE_SEPARATOR.join(texts)
    return None


# --- Gli errori ---------------------------------------------------------------------------

_NUMBER = re.compile(r"(?<![\w.,/-])\d+(?:[.,]\d+)?(?![\w/-]|[.,]\d)")


def _values(text: str) -> set[str]:
    """I valori del testo (non codici, non rimandi, non numeri di un elenco «4)»), come li
    vede il controllo dei numeri: si cambia solo un valore, non un codice di task."""
    from cycle_validation.checks.languages import _numbers as code_numbers

    values = {raw for raw, _ in code_numbers(text)}
    listed = {m.group(1) for m in re.finditer(r"(?<![\w.,])(\d+)\)", text)}
    # «ABC 1234», «REPAIR 001»: il numero di un documento o di un codice (esempi inventati)
    in_codes = {m.group(1) for m in re.finditer(r"\b[A-Za-z]{2,}-?\s?(\d{3,})\b", text)}
    return {
        raw
        for raw in values - listed - in_codes
        if _NUMBER.fullmatch(raw) and not (len(raw) > 1 and raw.startswith("0") and raw[1] != ".")
    }


def _other_number(raw: str) -> str:
    if "." in raw or "," in raw:
        separator = "." if "." in raw else ","
        whole, decimals = raw.split(separator)
        return f"{int(whole) + 1}{separator}{decimals}"
    return str(int(raw) * 2 + 1)


def _replace_number(text: str, raw: str, new: str) -> str | None:
    # come il controllo dei numeri: «4X» è il numero 4 (lettere attaccate dopo vanno bene)
    pattern = re.compile(rf"(?<![\w.,/-]){re.escape(raw)}(?!\d|[.,]\d)")
    result = pattern.sub(new, text, count=1)
    return result if result != text else None


def _number_mutations(description: str, rng: random.Random) -> Iterator[str]:
    blocks = language_blocks(description)
    if blocks is None:
        return
    shared = sorted(_values(blocks[0]) & _values(blocks[1]))
    if not shared:
        return
    raw = rng.choice(shared)
    language = rng.choice(["it", "en"])
    new = _other_number(raw)
    mutated = _change_in(description, language, lambda text: _replace_number(text, raw, new))
    if mutated is not None:
        yield mutated


# limiti: (parola, contraria), le più lunghe prima
_LIMITS = {
    "it": (
        ("non superiore a", "almeno"),
        ("superiore a", "inferiore a"),
        ("inferiore a", "superiore a"),
        ("al massimo", "almeno"),
        ("almeno", "al massimo"),
        ("fino a", "oltre"),
        ("massimo", "minimo"),
        ("minimo", "massimo"),
    ),
    "en": (
        ("not to exceed", "at least"),
        ("not exceeding", "at least"),
        ("more than", "less than"),
        ("less than", "more than"),
        ("greater than", "less than"),
        ("at most", "at least"),
        ("at least", "at most"),
        ("up to", "over"),
        ("maximum", "minimum"),
        ("minimum", "maximum"),
        ("max", "min"),
        ("min", "max"),
    ),
}


def _swap(text: str, pairs: tuple[tuple[str, str], ...]) -> str | None:
    """Il testo con la prima parola della lista scambiata (stesse maiuscole)."""
    hits = []
    for word, other in pairs:
        match = re.search(rf"(?<![\w]){re.escape(word)}(?![\w])", text, re.IGNORECASE)
        if match:
            hits.append((match.start(), -len(word), match, other))
    if not hits:
        return None
    _, _, match, other = min(hits, key=lambda hit: (hit[0], hit[1]))
    new = other.upper() if match.group().isupper() else other
    return text[: match.start()] + new + text[match.end() :]


def _limit_mutations(description: str, rng: random.Random) -> Iterator[str]:
    """Solo dove lo stesso numero ha lo stesso limite nelle due lingue (MG75)."""
    from cycle_validation.checks.languages import _limited_values

    blocks = language_blocks(description)
    if blocks is None:
        return
    italian, english = _limited_values(blocks[0], "it"), _limited_values(blocks[1], "en")
    same = [
        value
        for value, limits in italian.items()
        if {way for way, _ in limits} == {way for way, _ in english.get(value, [])}
        and len({way for way, _ in limits}) == 1
    ]
    if not same:
        return
    language = rng.choice(["it", "en"])
    value = rng.choice(sorted(same))
    phrase = (italian if language == "it" else english)[value][0][1]
    clause = phrase.rsplit(" ", 1)[0] if " " in phrase else phrase
    swapped = _swap(clause, _LIMITS[language])
    if swapped is None:
        return

    def change(text: str) -> str | None:
        flat = " ".join(text.split())
        if clause not in flat:
            return None
        return flat.replace(clause, swapped, 1)

    mutated = _change_in(description, language, change)
    if mutated is not None:
        yield mutated


_EXTREME_SWAP = {
    "it": (("massimo", "minimo"), ("massima", "minima"), ("massimi", "minimi"),
           ("massime", "minime"), ("minimo", "massimo"), ("minima", "massima"),
           ("minimi", "massimi"), ("minime", "massime"), ("max", "min")),
    "en": (("maximum", "minimum"), ("minimum", "maximum"), ("max", "min")),
}  # fmt: skip


def _same_case(word: str) -> Callable[[re.Match[str]], str]:
    """La parola nuova con le maiuscole di quella che sostituisce."""
    return lambda match: word.upper() if match.group().isupper() else word


def _extreme_mutations(description: str, rng: random.Random) -> Iterator[str]:
    """Solo dove le due lingue dicono la stessa parola, «massimo» o «minimo» (MG81)."""
    from cycle_validation.checks.languages import _extreme

    blocks = language_blocks(description)
    if blocks is None:
        return
    italian, english = _extreme(blocks[0], "it"), _extreme(blocks[1], "en")
    if italian is None or italian != english:
        return
    language = rng.choice(["it", "en"])

    def change(text: str) -> str | None:
        # tutte le parole della lingua, così l'altra parola non resta
        result = text
        for word, other in _EXTREME_SWAP[language]:
            if (word.startswith("mass") or word in ("max", "maximum")) != (italian == "max"):
                continue
            result = re.sub(
                rf"(?<![\w]){word}(?![\w])", _same_case(other), result, flags=re.IGNORECASE
            )
        return result

    mutated = _change_in(description, language, change)
    if mutated is not None:
        yield mutated


# un verbo per azione, da mettere al posto di un'altra
_ACTION_WORDS = {
    "rimuovere": ("RIMUOVERE", "REMOVE"),
    "raccordare": ("RACCORDARE", "BLEND"),
    "sostituire": ("SOSTITUIRE", "REPLACE"),
    "lucidare": ("LUCIDARE", "POLISH"),
    "sabbiare": ("SABBIARE", "BLAST"),
    "saldare": ("SALDARE", "WELD"),
    "pulire": ("PULIRE", "CLEAN"),
}


def _action_mutations(description: str, rng: random.Random) -> Iterator[str]:
    """Solo dove le due lingue hanno la stessa azione: in una lingua diventa un'altra che
    l'altra lingua non ha (MG47)."""
    from cycle_validation.checks.languages import _ACTION, _CONDITION

    blocks = language_blocks(description)
    if blocks is None:
        return
    italian, english = actions(blocks[0], "it"), actions(blocks[1], "en")
    shared = sorted(italian & english)
    if not shared:
        return
    action = rng.choice(shared)
    language = rng.choice(["it", "en"])
    other_side = english if language == "it" else italian
    choices = sorted(set(_ACTION_WORDS) - italian - english - other_side)
    if not choices:
        return
    new_word = _ACTION_WORDS[rng.choice(choices)][0 if language == "it" else 1]
    rule = _ACTION[language][action]

    def change(text: str) -> str | None:
        # ogni parola dell'azione (fuori dalle condizioni) diventa la nuova azione
        conditions = [m.span() for m in _CONDITION.finditer(text)]
        pieces, last = [], 0
        for match in rule.finditer(text):
            if any(a <= match.start() < b for a, b in conditions):
                continue
            end = match.end()
            while end < len(text) and text[end].isalpha():
                end += 1
            pieces += [text[last : match.start()], new_word]
            last = end
        if not pieces:
            return None
        return "".join(pieces) + text[last:]

    mutated = _change_in(description, language, change)
    after = language_blocks(mutated) if mutated is not None else None
    # conta solo se l'azione è sparita davvero da quella lingua
    side = 0 if language == "it" else 1
    if mutated is not None and after is not None and action not in actions(after[side], language):
        yield mutated


def _dr_mutation(cycle: Cycle, index: int) -> Cycle | None:
    """Il numero del DR di un'operazione (non la prima che lo cita) cambiato di una cifra."""
    citing = [
        i for i, op in enumerate(cycle.operations) if cited_dr_numbers(op.operation_description)
    ]
    if index not in citing[1:]:
        return None
    operation = cycle.operations[index]
    number = cited_dr_numbers(operation.operation_description)[0]
    last = number[-1]
    changed = number[:-1] + str((int(last) + 1) % 10) if last.isdigit() else None
    if changed is None:
        return None
    description = operation.operation_description.replace(number, changed, 1)
    return _replace(cycle, index, description)


def _replace(cycle: Cycle, index: int, description: str) -> Cycle:
    operations = list(cycle.operations)
    operations[index] = operations[index].model_copy(update={"operation_description": description})
    return cycle.model_copy(update={"operations": operations})


# --- La misura ------------------------------------------------------------------------------


@dataclass
class KindResult:
    kind: str
    copies: int = 0
    found: int = 0
    other_errato: int = 0  # ERRATO nuovi su altre operazioni (falsi allarmi)
    missed: list[str] = field(default_factory=list)  # «impronta op»


@dataclass
class ReadingResult:
    cycles: int = 0
    operations_v1: int = 0
    operations_same: int = 0
    machines_v1: int = 0
    machines_same: int = 0
    sheets_v1: int = 0
    sheets_same: int = 0
    differences: list[str] = field(default_factory=list)  # «impronta op: cosa»
    # operazioni che la v2 legge e la v1 no (di solito la 005 della testata)
    only_v2: list[str] = field(default_factory=list)


@dataclass
class BenchResult:
    kinds: dict[str, KindResult]
    reading: ReadingResult


def _errato_ops(
    cycle: Cycle, kb: KnowledgeBase, settings: AgentSettings, profile: ProfileConfig
) -> set[int]:
    ctx = CheckContext(cycle, kb, StaticMachineRegistry([]), profile, agent=settings)
    _, immediate = plan_operation_checks(ctx, settings, "s")
    return {
        r.target.index
        for r in immediate
        if r.verdict is Verdict.ERRATO and r.target.index is not None
    }


_MUTATORS: dict[str, Callable[[str, random.Random], Iterator[str]]] = {
    "numero_una_lingua": _number_mutations,
    "limite_una_lingua": _limit_mutations,
    "massimo_minimo": _extreme_mutations,
    "azione_una_lingua": _action_mutations,
}


def run_bench(
    kb: KnowledgeBase,
    settings: AgentSettings,
    profile: ProfileConfig,
    rounds: int = 5,
    path: Path = PRINTS,
) -> BenchResult:
    """`rounds` giri con semi diversi: ogni giro può cambiare un altro numero, l'altra lingua,
    un'altra azione. Le copie uguali si contano una volta."""
    cycles = read_prints(path)
    kinds = {kind: KindResult(kind) for kind in KINDS}
    for fingerprint, cycle in cycles.items():
        base = _errato_ops(cycle, kb, settings, profile)
        for index, operation in enumerate(cycle.operations):
            if index in base:
                continue  # già ERRATO: non misura niente
            copies: list[tuple[str, Cycle]] = []
            for kind, mutator in _MUTATORS.items():
                seen: set[str] = set()
                for seed in range(1, rounds + 1):
                    # un seme per copia: la stessa copia esce sempre uguale
                    rng = random.Random(f"{seed}-{fingerprint}-{operation.operation_number}-{kind}")
                    for description in mutator(operation.operation_description, rng):
                        if description not in seen:
                            seen.add(description)
                            copies.append((kind, _replace(cycle, index, description)))
            dr_copy = _dr_mutation(cycle, index)
            if dr_copy is not None:
                copies.append(("dr_diverso", dr_copy))
            for kind, copy in copies:
                result = kinds[kind]
                errato = _errato_ops(copy, kb, settings, profile) - base
                result.copies += 1
                if index in errato:
                    result.found += 1
                else:
                    result.missed.append(f"{fingerprint} {operation.operation_number}")
                result.other_errato += len(errato - {index})
    return BenchResult(kinds=kinds, reading=compare_reading(cycles, path))


def compare_reading(cycles: dict[str, Cycle], path: Path = PRINTS) -> ReadingResult:
    """Operazioni, targhe e schede lette dalla v2 contro la tabella della v1."""
    result = ReadingResult()
    for fingerprint, rows in read_v1_tables(path).items():
        cycle = cycles.get(fingerprint)
        if cycle is None:
            continue
        result.cycles += 1
        ours: dict[str, Operation] = {_op(op.operation_number): op for op in cycle.operations}
        for row in rows:
            result.operations_v1 += 1
            operation = ours.get(row.op)
            if operation is None:
                result.differences.append(f"{fingerprint} {row.op}: operazione non letta")
                continue
            result.operations_same += 1
            if row.machine is not None:
                result.machines_v1 += 1
                tags = {operation.machine_tag, *operation.other_machine_tags}
                if row.machine in tags:
                    result.machines_same += 1
                else:
                    result.differences.append(f"{fingerprint} {row.op}: targa diversa")
            if row.sheet is not None:
                result.sheets_v1 += 1
                sheet = operation.process_sheet.code if operation.process_sheet else None
                if sheet == row.sheet:
                    result.sheets_same += 1
                else:
                    result.differences.append(f"{fingerprint} {row.op}: scheda diversa")
        extra = set(ours) - {row.op for row in rows}
        result.only_v2 += [f"{fingerprint} {op}" for op in sorted(extra)]
    return result


def render_bench(result: BenchResult) -> list[str]:
    """Le righe da stampare: solo impronte, operazioni e conteggi."""
    lines = ["Errori messi dal programma sulle 14 stampe vere (un errore per copia):"]
    for kind in KINDS:
        k = result.kinds[kind]
        share = f"{100 * k.found / k.copies:.0f}%" if k.copies else "-"
        lines.append(
            f"  {kind}: trovati {k.found} su {k.copies} ({share}) · falsi allarmi "
            f"{k.other_errato} · {DESCRIPTIONS[kind]}"
        )
        if k.missed:
            lines.append(
                f"    mancati: {', '.join(k.missed[:12])}{' ...' if len(k.missed) > 12 else ''}"
            )
    r = result.reading
    lines += [
        f"Lettura della stampa contro la v1 ({r.cycles} cicli): operazioni {r.operations_same} su "
        f"{r.operations_v1} · targhe {r.machines_same} su {r.machines_v1} · schede "
        f"{r.sheets_same} su {r.sheets_v1}",
    ]
    if r.differences:
        lines.append(f"  differenze (da guardare): {', '.join(r.differences)}")
    if r.only_v2:
        lines.append(f"  operazioni lette solo dalla v2: {len(r.only_v2)}")
    return lines
