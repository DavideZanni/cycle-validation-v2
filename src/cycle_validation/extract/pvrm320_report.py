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
nulla è un errore di estrazione (mai righe perse in silenzio), tranne il blocco dopo il banner
di fine pagina `*** C O N T I N U A ***`: nelle stampe vere è il seguito di un'operazione della
pagina rimasta a metà frase (solo la prima riga in tabella, senza la parte in inglese), e va a
quella se è una sola (vedi `_truncated`). Il piè dell'ultima pagina riporta
`RIP: <riparazione> OEM: <manuale>`.

Cosa si assume (da confermare sui PDF veri): la colonna TARGA è la targa macchina (la riga
`NOTE` non ne ha una), la seconda riga della colonna (centro responsabile) non si
estrae (la targa si legge solo sulla riga che porta il numero), il codice di riparazione
dell'operazione è la `RIPARAZIONE :` della testata della pagina dove l'operazione compare,
la riga `SCHEDA :` in fondo al blocco può non avere gli asterischi di colonna, il manuale di
un ciclo civile è l'OEM del piè e il task sta in `NOTE`, i riferimenti EJ200 sono le RDR, RN
ed EF citate nel testo. I glifi d'asterisco ammessi sono in `_STAR_GLYPHS`.
"""

import re
from dataclasses import dataclass, field

from cycle_validation.checks.languages import LANGUAGE_SEPARATOR
from cycle_validation.domain.cycle import Cycle, Operation, ProcessSheet, Source
from cycle_validation.errors import ExtractionError
from cycle_validation.ingest.pdf import PdfDocument
from cycle_validation.text import normalize_code

# Glifi che l'estrazione dal PDF o una trascrizione possono restituire al posto di `*`:
# si riportano tutti all'asterisco prima di leggere le righe.
_STAR_GLYPHS = str.maketrans(dict.fromkeys("•★∗＊⁎✱", "*"))
_ROW = re.compile(r"^(?P<left>[^*]{0,22}?)\*\s*(?P<num>\d{3})?\s*\*(?P<right>.*)$")
_TRAILING_STAR = re.compile(r"\s*\*(?:\s+PRE)?\s*$")
_STAR_RULE = re.compile(r"^(?:\*\s*){5,}$")
_DASHES = re.compile(r"^\s*-{10,}\s*$")
_EQUALS = re.compile(r"^\s*={10,}\s*$")
# Banner di fine pagina a lettere spaziate. Nelle stampe DR vere (21-11-2026) dopo il banner
# c'è il seguito di un'operazione della pagina che in tabella si ferma a metà frase.
PAGE_END_BANNER = re.compile(r"C\s+O\s+N\s+T\s+I\s+N\s+U\s+A\b")
_CONTINUED_FROM = re.compile(r"CONTINUAZIONE DALLA PAGINA PRECEDENTE", re.IGNORECASE)
_CONTINUES_ON = re.compile(
    r"CONTINUA ALLA PAGINA SEGUENTE|C\s*O\s*N\s*T\s*I\s*N\s*U\s*A\s*\*", re.IGNORECASE
)
# data di modifica sopra il blocco, con o senza "D.T."
_DT = re.compile(r"^(?:D\.T\.\s+)?\d{2}-\d{2}-\d{2}$")
# Riga con i codici del data-module dell'operazione: "SP.ORIG. <codice>   SP.FIAT [<codice>]".
# Lo SP.FIAT è quasi sempre vuoto. Un codice contiene almeno una cifra, così una sigla vuota
# non prende come codice la sigla che segue.
_SP_LINE = re.compile(r"^\s*SP\.(?:ORIG|FIAT)\b")
_SP_CODE = re.compile(r"\bSP\.(?P<kind>ORIG|FIAT)\.?\s+(?P<code>(?!SP\.)(?=\S*\d)\S+)")
_TOOLING_HEADER = re.compile(r"^\*?\s*ATTREZZATURA PREVISTA", re.IGNORECASE)
_TOOLING_CODE = re.compile(r"^[A-Z]\d{7}\s+\S")
_FILL_IN = re.compile(r"\.{5,}")
_SHEET = re.compile(r"^SCHEDA\s*:\s*(?P<code>.*)$", re.IGNORECASE)
# la riga SCHEDA in fondo al blocco è più larga della colonna TARGA e non ha asterischi:
# "SCHEDA : PG 900        SP.ORIG. X1Y22300001Z999ZZ     SP.XXXX"
_SHEET_LINE = re.compile(
    r"^\s*SCHEDA\s*:\s*(?P<code>.*?)\s*(?:\bSP\.(?:ORIG|FIAT)\b.*)?$", re.IGNORECASE
)
# riparazione nella testata ripetuta a ogni pagina: vale per le operazioni di quella pagina
_PAGE_REPAIR = re.compile(r"^\s*RIPARAZIONE\s*:\s*(?P<repair>\S+)", re.IGNORECASE | re.MULTILINE)
# Il task per intero: codice completo (70-42-00-350-002) o sezione con tipo e numero
# (72-00-00 REPAIR 001). Il codice completo va letto tutto: tagliato alle prime tre coppie
# non corrisponde a nessun task del manuale. Vale anche SUBTASK, che sta dentro un task.
_TASK = re.compile(
    r"\b(?:SUB-?)?TASK\s+(\d{2}-\d{2}-\d{2}(?:-\d{3}-\d{3}|\s+REPAIR\s+\d+)?)(?![\dA-Za-z-])",
    re.IGNORECASE,
)
# Fonti EJ200: il codice dopo la parola RDR, RN o EF ("DELLA RDR EJ00010X-01"); i codici RN
# ed EF si riconoscono anche da soli, perché cominciano con il tipo ("RN-EJ-000-0000-01",
# "EF000A0000-01"). Un codice contiene almeno una cifra: "RDR ALLEGATA" non è un riferimento.
_CODE = r"(?=[A-Z0-9-]*\d)[A-Z0-9]+(?:-[A-Z0-9]+)*"
_REFERENCE = re.compile(rf"\b(?:RDR|RN|EF)\s+({_CODE})|\b(RN-{_CODE}|EF\d[A-Z0-9]*(?:-[A-Z0-9]+)*)")
# Punto della fonte citato accanto al codice: "RDR EJ00010X-01 PAR. 1.1" oppure
# "AL PAR. 1.1 DELLA RDR EJ00010X-01". "RIF. SD S00/00000" è un riferimento di richiesta, non un punto.
_POINT = (
    r"(?:PAR(?:AGRAFO|A)?|FIG(?:URA)?|TAB(?:ELLA)?|SEZ(?:IONE)?|STEP|PUNTO)\.?\s*"
    r"\d+(?:\.\d+)*[A-Z]?\b"
)
_SECTION_AFTER = re.compile(rf"^[\s,;:(]*(?:(?:AL|ALLA|DEL|DELLA)\s+)?({_POINT})")
_SECTION_BEFORE = re.compile(
    rf"({_POINT})[\s,]*(?:(?:DEL|DELLA|DELLE|DELL')\s*)?(?:(?:RDR|RN|EF)\s+)?$"
)
_FOOTER = re.compile(r"^\s*RIP\s*:\s*(?P<repair>\S+)\s+OEM\s*:\s*(?P<oem>\S+)", re.IGNORECASE)
# Task nella colonna NOTE della testata, accanto alla riparazione: «72-00-00 REPAIR 001»,
# «CIR 72-00-00, REPAIR 001», «BLENDING 72-00-00-200-801» (una parola prima del codice) o la
# sola sezione «CIR 72-00-00». Si prende il primo codice con la forma di una sezione ATA.
_TASK_NOTE = re.compile(
    r"(?<![\dA-Za-z-])(?P<section>\d{2}-\d{2}-\d{2})"
    r"(?:(?P<full>-\d{3}-\d{3})|\s*,?\s*(?P<kind>REPAIR|INSPECTION|CHECK)\s+(?P<number>\d{3}))?"
    r"(?![\dA-Za-z-])",
    re.IGNORECASE,
)
# Riparazione e nota nella testata di ogni pagina.
_PAGE_REPAIR_NOTE = re.compile(
    r"^[ \t]*RIPARAZIONE[ \t]*:[ \t]*(?P<repair>\S+)(?:[ \t]+(?P<note>\S.*?))?[ \t]*$",
    re.IGNORECASE | re.MULTILINE,
)


def note_task(note: str | None) -> str | None:
    """Il task citato nella nota della testata, nella forma dei task del ciclo
    (`72-00-00 REPAIR 001`, `72-00-00-200-801`), oppure la sola sezione (`72-00-00`)."""
    match = _TASK_NOTE.search(note or "")
    if match is None:
        return None
    if match["full"]:
        return match["section"] + match["full"]
    if match["kind"]:
        return f"{match['section']} {match['kind'].upper()} {match['number']}"
    return match["section"]


# segnaposto tra le parti della descrizione (la riga di asterischi tra italiano e inglese)
_SECTION = "\x00"


@dataclass
class _Op:
    number: str
    page: int
    tag: str | None = None
    text: list[str] = field(default_factory=list)
    sheet: str | None = None
    sp_orig: str | None = None
    sp_fiat: str | None = None
    repair: str | None = None

    def take_codes(self, line: str) -> None:
        """Codici SP.ORIG. e SP.FIAT della riga, se ci sono (il primo trovato resta)."""
        for match in _SP_CODE.finditer(line):
            if match["kind"] == "ORIG":
                self.sp_orig = self.sp_orig or match["code"]
            else:
                self.sp_fiat = self.sp_fiat or match["code"]

    def absorb(self, other: "_Op") -> None:
        """Prende testo, scheda e codici di un blocco senza numero (scheda e codici: il primo
        trovato resta)."""
        self.text.extend(other.text)
        self.sheet = self.sheet or other.sheet
        self.sp_orig = self.sp_orig or other.sp_orig
        self.sp_fiat = self.sp_fiat or other.sp_fiat


def _section_near(text: str, start: int, end: int) -> str | None:
    """Il punto citato subito dopo il codice o subito prima della sua sigla, se c'è."""
    found = _SECTION_AFTER.match(text[end : end + 40]) or _SECTION_BEFORE.search(
        text[max(start - 40, 0) : start]
    )
    return " ".join(found[1].split()) if found else None


def is_pvrm320_report(pdf: PdfDocument) -> bool:
    text = pdf.text
    return bool(
        re.search(r"PVRM320", text, re.IGNORECASE)
        and "C.RESP" in text
        and re.search(r"\bTARGA\b", text)
    )


def _right(raw: str) -> str:
    return _TRAILING_STAR.sub("", raw, count=1).strip()


_HAS_WORD = re.compile(r"[^\W_]")
_FRAME = re.compile(r"^[\s*]+|[\s*]+$")
# asterisco da solo in mezzo alla riga: cornice di un riquadro finita sulla stessa riga
_LONE_STAR = re.compile(r"(?:^|\s)\*(?=\s|$)")


def _add_text(op: _Op, text: str) -> None:
    # i puntini sono campi da compilare a mano: si tolgono, il resto della riga (che può
    # contenere limiti e valori) resta nella descrizione
    text = " ".join(_FILL_IN.sub(" ", text).split())
    if _STAR_RULE.match(text):
        if op.text and op.text[-1] != _SECTION:
            op.text.append(_SECTION)
        return
    if (
        not _HAS_WORD.search(text)  # trattini, «/ .» e altri segni senza lettere né cifre
        or _CONTINUED_FROM.search(text)
        or _CONTINUES_ON.search(text)
        or _DT.match(text)
        or _TOOLING_HEADER.match(text)
        or _TOOLING_CODE.match(text)
    ):
        return
    if _SP_LINE.match(text):
        op.take_codes(text)
        return
    op.text.append(" ".join(_LONE_STAR.sub(" ", text).split()))


# Titolo in un blocco a sé, tra due tratteggi: «***** OPERAZIONE EVENTUALE *****». Riguarda
# l'operazione che viene dopo (stampe MOS vere, 22-11-2026).
_HEADING = re.compile(r"^\*{3,}[^*]+\*{3,}$")


def _is_heading(pending: _Op) -> bool:
    lines = [line for line in pending.text if line != _SECTION]
    return (
        bool(lines)
        and not (pending.sheet or pending.sp_orig or pending.sp_fiat)
        and all(_HEADING.match(line) for line in lines)
    )


def _no_orphan(pending: _Op) -> None:
    """Testo o scheda senza un numero di operazione a cui attaccarli: il layout non è quello
    atteso. Meglio fermarsi (e lasciare il passo all'estrattore di riserva) che perdere righe."""
    if pending.text or pending.sheet:
        first = next((line for line in pending.text if line != _SECTION), None)
        start = f" (comincia con «{first[:60]}»)" if first else f" (scheda {pending.sheet})"
        raise ExtractionError(
            f"Stampa PVRM320, pagina {pending.page}: blocco senza numero di operazione{start}."
        )


def _truncated(operations: dict[str, _Op], page: int, continuing: _Op | None) -> list[_Op]:
    """Operazioni cominciate su questa pagina e rimaste a metà: hanno testo ma non ancora la
    parte dopo il separatore (l'inglese) e non sono quella che continua alla pagina dopo.
    Stampe DR vere: la riga NOTE a pagina 2 («… FORNISCE LE»), l'op. 050 a pagina 5
    («… A TAMPONE DELLE»); il loro seguito, scheda compresa, sta dopo il banner."""
    return [
        op
        for op in operations.values()
        if op.page == page and op is not continuing and op.text and _SECTION not in op.text
    ]


def _settle(pending: _Op, after_banner: bool, candidates: list[_Op]) -> None:
    """Blocco senza numero: dopo il banner va all'unica operazione rimasta a metà; altrimenti
    è un errore (nessuna supposizione se i candidati sono zero o più di uno)."""
    has_content = bool(pending.text or pending.sheet or pending.sp_orig or pending.sp_fiat)
    if after_banner and has_content and len(candidates) == 1:
        candidates[0].absorb(pending)
        return
    _no_orphan(pending)


def _description(op: _Op) -> str:
    sections: list[list[str]] = [[]]
    for item in op.text:
        if item == _SECTION:
            sections.append([])
        else:
            sections[-1].append(item)
    return LANGUAGE_SEPARATOR.join(" ".join(lines) for lines in sections if lines)


def footer_oems(pdf: PdfDocument) -> list[str]:
    """Il codice OEM scritto nel piè di pagina, una volta per valore: da qui viene il manuale
    delle fonti dei cicli civili."""
    found: list[str] = []
    for page in pdf.pages:
        _, footer = _body(page.text)
        if footer is not None and (m := _FOOTER.match(footer)) is not None:
            found.append(m["oem"])
    return list(dict.fromkeys(found))


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
    # la riga vuota della tabella (solo asterischi) e il tratteggio subito dopo l'intestazione
    # non chiudono nessuna operazione: quella che continua dalla pagina prima resta aperta
    while body and (not body[0].strip("* \t") or _DASHES.match(body[0])):
        body.pop(0)
    return body, footer


def page_structure(page_text: str) -> list[str]:
    """Come il parser vede ogni riga della tabella di una pagina, senza il testo: tipo di riga,
    numero di operazione, se c'è una targa o una scheda, prima parola e numero di parole del
    testo. Serve a capire un errore di layout da una foto senza far vedere il documento."""
    body, footer = _body(page_text)
    if not body and footer is None:
        return ["(pagina senza intestazione C.RESP: non è una pagina della tabella)"]
    shapes: list[str] = []
    for raw in body:
        line = raw.rstrip()
        if not line.strip():
            kind = "vuota"
        elif _EQUALS.match(line):
            kind = "riga di ="
        elif _DASHES.match(line):
            kind = "TRATTEGGIO (chiude l'operazione)"
        elif PAGE_END_BANNER.search(line):
            kind = "BANNER «continua»"
        elif (match := _ROW.match(line)) is None:
            if _SHEET_LINE.match(line):
                kind = "riga SCHEDA fuori tabella"
            elif _SP_LINE.match(line.strip()):
                kind = "riga SP fuori tabella"
            else:
                kind = f"fuori tabella, {len(line.split())} parole"
        else:
            left = match["left"].strip()
            text = _right(match["right"])
            words = text.split()
            parts = [f"op {match['num']}" if match["num"] else "senza numero"]
            if _SHEET.match(left):
                parts.append("scheda")
            elif left:
                parts.append("colonna sinistra piena")
            if _CONTINUED_FROM.search(text):
                parts.append("«continuazione dalla pagina precedente»")
            elif _CONTINUES_ON.search(text):
                parts.append("«continua alla pagina seguente»")
            elif _STAR_RULE.match(" ".join(words)):
                parts.append("riga di asterischi")
            elif words:
                parts.append(f"testo «{words[0][:20]}» + {len(words) - 1} parole")
            kind = ", ".join(parts)
        shapes.append(kind)
    if footer is not None:
        shapes.append("piè di pagina (RIP/OEM)")
    return shapes


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
    # per ogni riparazione (in ordine): la nota della testata e il manuale del piè di pagina
    repair_notes: dict[str, str | None] = {}
    repair_oems: dict[str, str] = {}
    # titoli («***** OPERAZIONE EVENTUALE *****») in attesa della prossima operazione
    heading: list[str] = []

    def held(pending: _Op) -> bool:
        if _is_heading(pending):
            heading.extend(line for line in pending.text if line != _SECTION)
            return True
        return False

    for page in pdf.pages:
        body, footer = _body(page.text)
        if footer is not None and (m := _FOOTER.match(footer)) is not None:
            oem = oem or m["oem"]
            repair_oems.setdefault(m["repair"], m["oem"])
        if (m := _PAGE_REPAIR_NOTE.search(page.text)) is not None and not repair_notes.get(
            m["repair"]
        ):
            repair_notes[m["repair"]] = m["note"]
        current = carry
        pending = _Op("", page.number)
        # operazione che la pagina dichiara di continuare ("CONTINUA ALLA PAGINA SEGUENTE"):
        # resta aperta anche se dopo c'è il tratteggio di fine pagina
        continuing: _Op | None = None
        after_banner = False
        page_repair = m["repair"] if (m := _PAGE_REPAIR.search(page.text)) else None
        for raw in body:
            line = raw.rstrip()
            if not line.strip() or _EQUALS.match(line):
                continue
            if _DASHES.match(line):
                if not held(pending):
                    _settle(pending, after_banner, _truncated(operations, page.number, continuing))
                current, pending = None, _Op("", page.number)
                continue
            if PAGE_END_BANNER.search(line):
                if not held(pending):
                    _no_orphan(pending)
                pending, after_banner = _Op("", page.number), True
                continue
            match = _ROW.match(line)
            if match is None:
                if (sheet := _SHEET_LINE.match(line)) is not None:
                    target = current if current is not None else pending
                    target.sheet = target.sheet or sheet["code"] or None
                    target.take_codes(line)
                elif current is not None and _SP_LINE.match(line):
                    current.take_codes(line)
                elif page.reordered and current is not None:
                    # stampa modificata a mano: la riga toccata può aver perso le colonne
                    # TARGA e NUM. OPER, ma sulla pagina sta dentro l'operazione in corso
                    _add_text(current, _FRAME.sub("", line))
                continue
            left = match["left"].strip()
            text = _right(match["right"])
            if _CONTINUED_FROM.search(text):
                continue
            if _CONTINUES_ON.search(text) and current is not None:
                continuing = current
            if match["num"]:
                number = match["num"]
                current = operations.setdefault(
                    number, _Op(number, page.number, repair=page_repair)
                )
                current.text.extend(heading)
                heading.clear()
                current.absorb(pending)
                pending = _Op("", page.number)
            target = current if current is not None else pending
            if (sheet := _SHEET.match(left)) is not None:
                target.sheet = target.sheet or sheet["code"].strip() or None
            elif left and match["num"]:
                # la targa sta sulla riga del numero; sotto c'è il centro responsabile, che non è
                # una macchina e non deve mai finire nel controllo delle macchine attive
                target.tag = target.tag or left
            _add_text(target, text)
        if not held(pending):
            _settle(pending, after_banner, _truncated(operations, page.number, continuing))
        carry = current if current is not None else continuing
    if not operations:
        raise ExtractionError("Nessuna operazione trovata nella stampa PVRM320.")

    head = _header_fields(pdf)
    ej200 = "EJ200" in normalize_code(head.get("engine_model") or "")
    built: list[Operation] = []
    for op in operations.values():
        description = _description(op)
        tag = op.tag if op.tag and op.tag.upper() != "NOTE" else None
        process_sheet: ProcessSheet | None = None
        if op.sheet:
            process_sheet = ProcessSheet.model_validate(
                {"code": op.sheet, **({"sp_orig": op.sp_orig} if op.sp_orig else {})}
            )
        tasks = [" ".join(t.upper().split()) for t in _TASK.findall(description)]
        if ej200:
            # EJ200: i codici del data-module (SP.ORIG., SP.FIAT) si verificano come i task
            # code, come nel servizio precedente. Nei cicli civili il task sta nel testo.
            tasks += [code for code in (op.sp_orig, op.sp_fiat) if code]
        tasks = list(dict.fromkeys(tasks))
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
    # una fonte per riparazione: ogni pagina ha in testata la sua riparazione e, nella colonna
    # NOTE, il task del manuale per quella riparazione
    first: tuple[str | None, str | None] = (head.get("repair_code"), head.get("note"))
    repairs: list[tuple[str | None, str | None]] = list(repair_notes.items()) or [first]
    for repair_code, note in repairs:
        if not note and repair_code == first[0]:
            note = first[1]
        manual = repair_oems.get(repair_code or "") or oem
        if manual and "/" not in manual:
            sources.append(Source(manual=manual, task=note_task(note), repair_code=repair_code))
    text = " ".join(op.operation_description for op in built)
    cited: dict[str, str | None] = {}
    for match in _REFERENCE.finditer(text):
        code = match[1] or match[2]
        cited[code] = cited.get(code) or _section_near(text, match.start(), match.end())
    sources.extend(Source(manual=code, section=section) for code, section in cited.items())
    return Cycle(
        cycle_code=head.get("cycle_code"),
        cycle_description=head.get("cycle_description"),
        engine_model=head.get("engine_model"),
        repair_code=head.get("repair_code"),
        sources=sources,
        operations=built,
    )
