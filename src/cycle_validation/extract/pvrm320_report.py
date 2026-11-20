"""Parser della stampa reale del modulo PVRM320 («CICLO DI LAVORAZIONE»), MOS ed EJ200.

Il formato è quello della stampa aziendale: testata ripetuta a ogni pagina
(`CICLO :`, `DESCR.CICLO :`, `PROGETTO...`, `RIPARAZIONE :`, `NOTE.......`), poi una tabella a
colonne separate da asterischi:

    TARGA       * NUM.   *    DESCRIZIONE  OPERAZIONE            *
    C.RESP.     * OPER   *                                       * PRE
    <targa>     * 010    *  testo italiano
    <c.resp>    *        *  * * * * * * *   (separatore)
                *        *  testo inglese
    SCHEDA : X  *        *  SP.ORIG. <specifica>
    -------------------------------------------------   (fine operazione)

Le operazioni che proseguono sulla pagina dopo (`*** CONTINUAZIONE DALLA PAGINA PRECEDENTE ***`)
si uniscono per numero; le righe senza numero in cima a una pagina restano all'operazione
rimasta aperta alla fine della pagina prima. Un blocco di testo senza numero che non continua
nulla è un errore di estrazione (mai righe perse in silenzio). Il piè
dell'ultima pagina riporta `RIP: <riparazione> OEM: <manuale>`.

Cosa si assume (da confermare sui PDF veri): la colonna TARGA è la targa macchina (la riga
`NOTE` non ne ha una), la seconda riga della colonna (centro responsabile) non si
estrae (la targa si legge solo sulla riga che porta il numero), il codice di riparazione
dell'operazione è la `RIPARAZIONE :` della testata della pagina dove l'operazione compare,
la riga `SCHEDA :` in fondo al blocco può non avere gli asterischi di colonna, il manuale di un ciclo civile è l'OEM del piè e il task sta in `NOTE`, i riferimenti
EJ200 sono le `RDR` citate nel testo. I glifi d'asterisco ammessi sono in `_STAR_GLYPHS`.
"""

import re
from dataclasses import dataclass, field

from cycle_validation.domain.cycle import Cycle, Operation, ProcessSheet, Source
from cycle_validation.errors import ExtractionError
from cycle_validation.ingest.pdf import PdfDocument

# Glifi che l'estrazione dal PDF o una trascrizione possono restituire al posto di `*`:
# si riportano tutti all'asterisco prima di leggere le righe.
_STAR_GLYPHS = str.maketrans(dict.fromkeys("•★∗＊⁎✱", "*"))
_ROW = re.compile(r"^(?P<left>[^*]{0,22}?)\*\s*(?P<num>\d{3})?\s*\*(?P<right>.*)$")
_TRAILING_STAR = re.compile(r"\s*\*(?:\s+PRE)?\s*$")
_STAR_RULE = re.compile(r"^(?:\*\s*){5,}$")
_DASHES = re.compile(r"^\s*-{10,}\s*$")
_EQUALS = re.compile(r"^\s*={10,}\s*$")
_CONTINUED_FROM = re.compile(r"CONTINUAZIONE DALLA PAGINA PRECEDENTE", re.IGNORECASE)
_CONTINUES_ON = re.compile(
    r"CONTINUA ALLA PAGINA SEGUENTE|C\s*O\s*N\s*T\s*I\s*N\s*U\s*A\s*\*", re.IGNORECASE
)
# data di modifica sopra il blocco, con o senza "D.T."
_DT = re.compile(r"^(?:D\.T\.\s+)?\d{2}-\d{2}-\d{2}$")
_SP_ORIG = re.compile(r"^SP\.ORIG\.\s+(?P<code>\S+)")
_TOOLING_HEADER = re.compile(r"^\*?\s*ATTREZZATURA PREVISTA", re.IGNORECASE)
_TOOLING_CODE = re.compile(r"^[A-Z]\d{7}\s+\S")
_FILL_IN = re.compile(r"\.{5,}")
_SHEET = re.compile(r"^SCHEDA\s*:\s*(?P<code>.*)$", re.IGNORECASE)
# la riga SCHEDA in fondo al blocco è più larga della colonna TARGA e non ha asterischi:
# "SCHEDA : PG 300        SP.ORIG. E2A70200001A653AD     SP.FIAT"
_SHEET_LINE = re.compile(
    r"^\s*SCHEDA\s*:\s*(?P<code>.*?)\s*(?:SP\.ORIG\.\s+(?P<sp>\S+).*)?$", re.IGNORECASE
)
# riparazione nella testata ripetuta a ogni pagina: vale per le operazioni di quella pagina
_PAGE_REPAIR = re.compile(r"^\s*RIPARAZIONE\s*:\s*(?P<repair>\S+)", re.IGNORECASE | re.MULTILINE)
_TASK = re.compile(r"\bTASK\s+(\d{2}-\d{2}-\d{2}(?:\s+REPAIR\s+\d+)?)", re.IGNORECASE)
# un codice RDR contiene almeno una cifra: "RDR ALLEGATA" non è un riferimento
_RDR = re.compile(r"\bRDR\s+((?=[A-Z0-9-]*\d)[A-Z0-9]+(?:-[A-Z0-9]+)*)")
_FOOTER = re.compile(r"^\s*RIP\s*:\s*(?P<repair>\S+)\s+OEM\s*:\s*(?P<oem>\S+)", re.IGNORECASE)
_TASK_NOTE = re.compile(r"^\d{2}-\d{2}-\d{2}\b")
_SECTION = "\x00"


@dataclass
class _Op:
    number: str
    page: int
    tag: str | None = None
    text: list[str] = field(default_factory=list)
    sheet: str | None = None
    sp_orig: str | None = None
    repair: str | None = None


def is_pvrm320_report(pdf: PdfDocument) -> bool:
    text = pdf.text
    return bool(
        re.search(r"PVRM320", text, re.IGNORECASE)
        and "C.RESP" in text
        and re.search(r"\bTARGA\b", text)
    )


def _right(raw: str) -> str:
    return _TRAILING_STAR.sub("", raw, count=1).strip()


def _add_text(op: _Op, text: str) -> None:
    # i puntini sono campi da compilare a mano: si tolgono, il resto della riga (che può
    # contenere limiti e valori) resta nella descrizione
    text = " ".join(_FILL_IN.sub(" ", text).split())
    if _STAR_RULE.match(text):
        if op.text and op.text[-1] != _SECTION:
            op.text.append(_SECTION)
        return
    if (
        not text
        or text == "."
        or _CONTINUED_FROM.search(text)
        or _CONTINUES_ON.search(text)
        or _DT.match(text)
        or _TOOLING_HEADER.match(text)
        or _TOOLING_CODE.match(text)
    ):
        return
    if (match := _SP_ORIG.match(text)) is not None:
        op.sp_orig = op.sp_orig or match["code"]
        return
    op.text.append(text)


def _no_orphan(pending: _Op) -> None:
    """Testo o scheda senza un numero di operazione a cui attaccarli: il layout non è quello
    atteso. Meglio fermarsi (e lasciare il passo all'estrattore di riserva) che perdere righe."""
    if pending.text or pending.sheet:
        raise ExtractionError(
            f"Stampa PVRM320, pagina {pending.page}: blocco senza numero di operazione."
        )


_WORD = re.compile(r"[^\W\d_]+")
# Parole brevi che stanno da sole: "SUPERFICI / E" non è "SUPERFICIE", "DA / TE" non è "DATE".
_FUNCTION_WORDS = frozenset(
    [
        "a",
        "ad",
        "al",
        "alla",
        "alle",
        "agli",
        "ai",
        "che",
        "con",
        "col",
        "da",
        "dal",
        "dalla",
        "dalle",
        "dai",
        "degli",
        "dei",
        "del",
        "della",
        "delle",
        "di",
        "e",
        "ed",
        "gli",
        "i",
        "il",
        "in",
        "la",
        "le",
        "lo",
        "nel",
        "nella",
        "nelle",
        "negli",
        "nei",
        "non",
        "o",
        "per",
        "su",
        "sul",
        "sulla",
        "sulle",
        "tra",
        "fra",
        "un",
        "uno",
        "una",
    ]
)


def _vocabulary(ops: list[_Op]) -> frozenset[str]:
    """Parole intere del ciclo: quelle dentro una riga. In testa e in coda a una riga
    potrebbe esserci il pezzo di una parola andata a capo, e non conta."""
    words: set[str] = set()
    for op in ops:
        for line in op.text:
            words.update(
                m[0].casefold()
                for m in _WORD.finditer(line)
                if m.start() > 0 and m.end() < len(line)
            )
    return frozenset(words)


def _join_lines(lines: list[str], vocabulary: frozenset[str]) -> str:
    """Unisce le righe; una parola spezzata a capo senza trattino ("QUANTITÀ MI" / "NIMA DI")
    si ricuce se la parola intera compare altrove nel ciclo."""
    text = ""
    for line in lines:
        head = re.match(r"[^\W\d_]+", line)
        tail = re.search(r"[^\W\d_]+$", text)
        if head and tail:
            left, right = tail[0].casefold(), head[0].casefold()
            if (
                left + right in vocabulary
                and left not in _FUNCTION_WORDS
                and right not in _FUNCTION_WORDS
            ):
                text += line
                continue
        text = f"{text} {line}" if text else line
    return text


def _description(op: _Op, vocabulary: frozenset[str] = frozenset()) -> str:
    sections: list[list[str]] = [[]]
    for item in op.text:
        if item == _SECTION:
            sections.append([])
        else:
            sections[-1].append(item)
    return " / ".join(_join_lines(lines, vocabulary) for lines in sections if lines)


def _body(page_text: str) -> tuple[list[str], str | None]:
    """Righe della tabella (senza testata) e riga del piè con l'OEM, se la pagina ne ha una."""
    lines = page_text.translate(_STAR_GLYPHS).splitlines()
    start = next((i for i, line in enumerate(lines) if "C.RESP" in line), None)
    if start is None:
        return [], None
    body: list[str] = []
    footer: str | None = None
    for line in lines[start + 1 :]:
        if _FOOTER.match(line):
            footer = line
            break
        body.append(line)
    # la riga tratteggiata subito dopo l'intestazione della tabella non chiude nessuna operazione
    while body and (not body[0].strip() or _DASHES.match(body[0])):
        body.pop(0)
    return body, footer


def _header_fields(pdf: PdfDocument) -> dict[str, str]:
    fields: dict[str, str] = {}
    patterns = {
        "cycle_code": re.compile(r"^\s*CICLO\s*:\s*(\S+)"),
        "cycle_description": re.compile(r"DESCR\.CICLO\s*:\s*(\S.*?)\s*$"),
        "engine_model": re.compile(r"PROGETTO\.*\s+(\S.*?)\s*$"),
    }
    repair = re.compile(r"RIPARAZIONE\s*:\s*(?P<repair>\S+)(?:\s+(?P<note>\S.*?))?\s*$")
    for page in pdf.pages:
        lines = page.text.splitlines()
        for index, line in enumerate(lines):
            for key, pattern in patterns.items():
                if key not in fields and (m := pattern.search(line)) is not None:
                    fields[key] = m[1]
            if "repair_code" not in fields and (m := repair.search(line)) is not None:
                fields["repair_code"] = m["repair"]
                if m["note"]:
                    fields["note"] = m["note"]
            if "note" not in fields and re.search(r"NOTE\.+\s*$", line):
                following = lines[index + 1].strip() if index + 1 < len(lines) else ""
                if following and not _EQUALS.match(following):
                    fields["note"] = following
    return fields


def parse_pvrm320_report(pdf: PdfDocument) -> Cycle:
    if not is_pvrm320_report(pdf):
        raise ExtractionError("Il PDF non ha il layout PVRM320 a colonne TARGA / NUM. OPER.")
    operations: dict[str, _Op] = {}
    # Operazione ancora aperta (nessuna riga tratteggiata dopo) alla fine della pagina prima:
    # le righe senza numero in cima alla pagina dopo sono sue, con o senza il marcatore.
    carry: _Op | None = None
    oem: str | None = None
    for page in pdf.pages:
        body, footer = _body(page.text)
        if footer is not None and (m := _FOOTER.match(footer)) is not None:
            oem = oem or m["oem"]
        current = carry
        pending = _Op("", page.number)
        page_repair = m["repair"] if (m := _PAGE_REPAIR.search(page.text)) else None
        for raw in body:
            line = raw.rstrip()
            if not line.strip() or _EQUALS.match(line):
                continue
            if _DASHES.match(line):
                _no_orphan(pending)
                current, pending = None, _Op("", page.number)
                continue
            match = _ROW.match(line)
            if match is None:
                if (sheet := _SHEET_LINE.match(line)) is not None:
                    target = current if current is not None else pending
                    target.sheet = target.sheet or sheet["code"] or None
                    target.sp_orig = target.sp_orig or sheet["sp"]
                elif current is not None and (sp := _SP_ORIG.match(line.strip())) is not None:
                    current.sp_orig = current.sp_orig or sp["code"]
                continue
            left = match["left"].strip()
            text = _right(match["right"])
            if _CONTINUED_FROM.search(text):
                continue
            if match["num"]:
                number = match["num"]
                current = operations.setdefault(
                    number, _Op(number, page.number, repair=page_repair)
                )
                current.text.extend(pending.text)
                current.sp_orig = current.sp_orig or pending.sp_orig
                current.sheet = current.sheet or pending.sheet
                pending = _Op("", page.number)
            target = current if current is not None else pending
            if (sheet := _SHEET.match(left)) is not None:
                target.sheet = target.sheet or sheet["code"].strip() or None
            elif left and match["num"]:
                # la targa sta sulla riga del numero; sotto c'è il centro responsabile, che non è
                # una macchina e non deve mai finire nel controllo delle macchine attive
                target.tag = target.tag or left
            _add_text(target, text)
        _no_orphan(pending)
        carry = current
    if not operations:
        raise ExtractionError("Nessuna operazione trovata nella stampa PVRM320.")

    head = _header_fields(pdf)
    built: list[Operation] = []
    vocabulary = _vocabulary(list(operations.values()))
    for op in operations.values():
        description = _description(op, vocabulary)
        tag = op.tag if op.tag and op.tag.upper() != "NOTE" else None
        process_sheet: ProcessSheet | None = None
        if op.sheet:
            process_sheet = ProcessSheet.model_validate(
                {"code": op.sheet, **({"sp_orig": op.sp_orig} if op.sp_orig else {})}
            )
        tasks = list(dict.fromkeys(" ".join(t.upper().split()) for t in _TASK.findall(description)))
        built.append(
            Operation(
                operation_number=op.number,
                operation_description=description,
                repair_code=op.repair or head.get("repair_code"),
                machine_tag=tag,
                task_codes=tasks,
                process_sheet=process_sheet,
                page=op.page,
            )
        )

    sources: list[Source] = []
    note = head.get("note")
    if oem and "/" not in oem:
        sources.append(
            Source(
                manual=oem,
                task=note if note and _TASK_NOTE.match(note) else None,
                repair_code=head.get("repair_code"),
            )
        )
    text = " ".join(op.operation_description for op in built)
    sources.extend(Source(manual=code) for code in dict.fromkeys(_RDR.findall(text)))
    return Cycle(
        cycle_code=head.get("cycle_code"),
        cycle_description=head.get("cycle_description"),
        engine_model=head.get("engine_model"),
        repair_code=head.get("repair_code"),
        sources=sources,
        operations=built,
    )
