"""Dal PDF al payload del frontend con la conoscenza nel formato pubblicato da knowledge-index.

I formati sono quelli dei file veri (20-11-2026): manifest con più capitoli per manuale, task
legati alla `key` del documento, targhe e schede con `needs_review`, recommendation DR con
`manual: null`, catalogo EJ200 con la issue dentro `code`. La stampa EJ200 ha il layout vero
(riga SCHEDA senza asterischi, data senza D.T., operazione che continua alla pagina dopo,
riga NOTE). Tutti i valori sono inventati. Il modello è simulato: il resto è il codice vero.
"""

import json
from pathlib import Path
from typing import Any

from fakes import ScriptedSession
from kb_fixtures import profile

from cycle_validation.agent.session import SessionRequest
from cycle_validation.config import load_settings
from cycle_validation.domain.check import CheckName, Reason
from cycle_validation.domain.cycle import Cycle, Operation, ProcessSheet, Source
from cycle_validation.extract.from_file import FileCycleExtractor
from cycle_validation.extract.pvrm320 import Pvrm320LayoutExtractor
from cycle_validation.kb.ej200 import (
    DEFAULT_CATALOG_KEY,
    DEFAULT_TEXT_PREFIX,
    Ej200Catalog,
    Ej200KnowledgeBase,
)
from cycle_validation.kb.local import load_local_knowledge
from cycle_validation.kb.stores import InMemoryObjectStore
from cycle_validation.kb.structured import StructuredLayout
from cycle_validation.pipeline import Dependencies, RunRequest, run_validation
from cycle_validation.resolve.dr import DrSelectors
from cycle_validation.services.machines import StaticMachineRegistry
from cycle_validation.testing.pdf import build_pdf, synthetic_cycle_pdf

# --- conoscenza civile nel formato pubblicato ------------------------------------------------

CHAPTER_21 = "SPM_GEK0000_pb70-21-00-010_ch1"
CHAPTER_10 = "SPM_GEK0000_spm-all-em-ic-70-10-00-010-100_ch1"
TEXTS = {
    CHAPTER_21: [
        "# SPM GEK0000 70-21-00",
        "",
        "TASK 70-21-00-110-030 PULIZIA",
        "Pulire il particolare con solvente tipo A.",
        "",
        "TASK 70-21-00-110-031 RACCORDATURA",
        "Raccordare il difetto con raggio minimo 6 mm.",
        "Profondità massima di raccordatura 0.31 mm.",
    ],
    CHAPTER_10: [
        "# SPM GEK0000 70-10-00",
        "",
        "TASK 70-10-00-340-001 CONTROLLO",
        "Controllo visivo con lente 10x delle aree riparate.",
    ],
}
ACTIVE = ["XX/457", "PREC01", "YY/766", "IM0001", "A 0100", "ZZ/095"]


def civil_knowledge(directory: Path) -> Path:
    (directory / "documents").mkdir(parents=True)
    documents = []
    for key, lines in TEXTS.items():
        (directory / "documents" / f"{key}.md").write_text("\n".join(lines) + "\n", "utf-8")
        documents.append(
            {
                "key": key,
                "file": f"documents/{key}.md",
                "lines": len(lines),
                "version": "ch1",
                "title": key,
                "code": "GEK0000",
                "kind": "SPM",
            }
        )
    files: dict[str, Any] = {
        "manifest.json": {"format": 1, "version": "20260101T090000Z", "documents": documents},
        "tasks.json": [
            {"manual": CHAPTER_21, "task": "70-21-00-110-030", "line_start": 3, "line_end": 4},
            {"manual": CHAPTER_21, "task": "70-21-00-110-031", "line_start": 6, "line_end": 8},
            {"manual": CHAPTER_10, "task": "70-10-00-340-001", "line_start": 3, "line_end": 4},
        ],
        "machine_tags.json": [
            {"tag": tag, "function": "LAVORAZIONE DI PROVA; ALTRA", "needs_review": True}
            for tag in ACTIVE
        ],
        "process_sheets.json": [
            {"code": "16", "edition": "13", "treatment": "LEV.3", "engine_families": ["GENX"]},
            {
                "code": "CPEC 100-BR",
                "edition": "51",
                "treatment": "ATTACCO LOCALE A TAMPONE",
                "engine_families": [],
                "needs_review": True,
            },
        ],
        "dr_recommendations.json": [
            {
                "serial_number": "AAAA1CCC",
                "conditions": [],
                "procedure": "Repair",
                "reference": "01000002",
                "manual": None,
                "tasks": ["70-21-00-110-031"],
                "needs_review": True,
            },
            {
                "serial_number": "BBBB2DDD",
                "conditions": [1],
                "procedure": "Repair",
                "reference": "01000003",
                "manual": None,
                "tasks": ["70-21-00-110-030"],
            },
            {
                "serial_number": "BBBB2DDD",
                "conditions": [2],
                "procedure": "Accept as is",
                "reference": "01000003",
                "manual": None,
                "tasks": ["70-21-00-110-031"],
            },
        ],
    }
    for name, content in files.items():
        (directory / name).write_text(json.dumps(content), "utf-8")
    return directory


def coherent(request: SessionRequest, attempt: int) -> dict[str, Any]:
    """Il modello finto: contraddice la profondità 0.50 mm, il resto è coerente. Cita
    alla lettera la riga del documento che ha ricevuto."""
    if "0.50" in request.prompt:
        return {
            "judgement": "contraddetto",
            "rationale": "Il documento ammette al massimo 0.31 mm.",
            "citations": [_cite(request, "0.31")],
        }
    return {"judgement": "coerente", "rationale": "Corrisponde.", "citations": [_cite(request)]}


def _cite(request: SessionRequest, needle: str = "") -> dict[str, Any]:
    """La prima riga di testo del documento nel messaggio che contiene `needle`."""
    current, wanted = None, None
    for raw in request.prompt.splitlines():
        if raw.startswith("File: "):
            current = raw.removeprefix("File: ").split(" (")[0]
            continue
        parts = raw.split(":", 1) if current else []
        if len(parts) == 2 and parts[0].strip().isdigit() and needle in parts[1]:
            text = parts[1].strip()
            if text and not text.startswith(("#", "<!--")):
                wanted = {"file": current, "line": int(parts[0]), "quote": text}
                break
    assert wanted is not None, request.prompt
    return wanted


def civil_deps(tmp_path: Path, name: str, cycle: Cycle) -> tuple[Dependencies, ScriptedSession]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    path = tmp_path / "ciclo.json"
    path.write_text(cycle.model_dump_json(), "utf-8")
    session = ScriptedSession(coherent)
    deps = Dependencies(
        settings=load_settings(None).model_copy(),
        profile=profile(name),
        kb=load_local_knowledge(civil_knowledge(tmp_path / "knowledge")),
        machines=StaticMachineRegistry(ACTIVE),
        extractor=FileCycleExtractor(path),
        session=session,
        system_prompt="sistema",
        prompt_version="test",
    )
    return deps, session


def reasons(report: Any, check: CheckName) -> list[Reason]:
    return [r.reason for r in report.results if r.check is check]


MOS = Cycle(
    cycle_code="PROVA-0001-1",
    engine_model="GENX-1B",
    repair_code="B1",
    sources=[Source(manual="GEK0000", task="70-21-00-110-031", repair_code="B1")],
    operations=[
        Operation(
            operation_number="010",
            operation_description="PULIRE IL PARTICOLARE CON SOLVENTE TIPO A.",
            repair_code="B1",
            machine_tag="A0100",  # nell'indice "A 0100"
            task_codes=["70-21-00-110-030"],
            process_sheet=ProcessSheet(code="CPEC100-BR"),  # nell'indice "CPEC 100-BR"
        ),
        Operation(
            operation_number="020",
            operation_description="RACCORDARE IL DIFETTO. PROFONDITA' MASSIMA 0.50 MM.",
            repair_code="B1",
            machine_tag="XX/457",
            task_codes=["70-21-00-110-031"],
            process_sheet=ProcessSheet(code="16"),
        ),
        Operation(
            operation_number="030",
            operation_description="CONTROLLO VISIVO CON LENTE 10X DELLE AREE RIPARATE.",
            repair_code="B1",
            machine_tag="QQ/999",  # non nel registro delle macchine attive
            task_codes=["70-10-00-340-001"],  # in un altro capitolo dello stesso manuale
        ),
    ],
)


def test_mos_with_the_published_civil_format(tmp_path: Path) -> None:
    deps, session = civil_deps(tmp_path, "mos", MOS)
    report = run_validation(RunRequest(pdf_bytes=synthetic_cycle_pdf(MOS)), deps, tmp_path / "run")

    assert reasons(report, CheckName.EXTRACTION_INTEGRITY) == [Reason.VERIFICATO]
    assert reasons(report, CheckName.SOURCE) == [Reason.VERIFICATO]
    # ogni task si trova nel capitolo giusto del manuale citato per codice
    assert reasons(report, CheckName.TASK_CODE) == [Reason.VERIFICATO] * 3
    # needs_review non cambia gli esiti; spazi nei codici ignorati
    assert reasons(report, CheckName.MACHINE_TAG) == [
        Reason.VERIFICATO,
        Reason.VERIFICATO,
        Reason.MACCHINA_NON_ATTIVA,
    ]
    assert reasons(report, CheckName.PROCESS_SHEET) == [
        Reason.VERIFICATO,
        Reason.VERIFICATO,
        Reason.CAMPO_ASSENTE,
    ]
    assert reasons(report, CheckName.OPERATION_DESCRIPTION) == [
        Reason.VERIFICATO,
        Reason.CONTRADDIZIONE,
        Reason.VERIFICATO,
    ]
    assert report.meta.knowledge_version == "20260101T090000Z"
    assert len(session.requests) == 3

    payload = json.loads((tmp_path / "run" / "payload.json").read_text("utf-8"))
    feedback = [
        (op["operationFeedback"][:5], op["targaCRespFeedback"][:5], op["schedaFeedback"][:5])
        for op in payload["operations"]
    ]
    assert feedback == [
        ("No er", "No er", "No er"),
        ("Error", "No er", "No er"),
        ("No er", "Error", "N/A -"),
    ]


def dr_run(tmp_path: Path, serial: str, conditions: tuple[int, ...]) -> Any:
    operation = MOS.operations[1].model_copy(update={"task_codes": [], "process_sheet": None})
    cycle = MOS.model_copy(
        update={"sources": [Source(manual="GEK0000")], "operations": [operation]}
    )
    deps, session = civil_deps(tmp_path, "dr", cycle)
    request = RunRequest(
        pdf_bytes=synthetic_cycle_pdf(cycle), selectors=DrSelectors(serial, conditions)
    )
    return run_validation(request, deps), session


def test_dr_with_manual_null_and_empty_conditions(tmp_path: Path) -> None:
    # una sola recommendation, conditions [], manual null: vale per la condition 3 e il suo
    # task si cerca nel manuale citato dal ciclo
    report, session = dr_run(tmp_path, "AAAA1CCC", (3,))
    assert reasons(report, CheckName.DR_RECOMMENDATION) == [Reason.VERIFICATO]
    (request,) = session.requests
    assert "70-21-00-110-031" in request.prompt and "0.31 mm" in request.prompt


def test_dr_accept_as_is_for_the_requested_condition_is_an_error(tmp_path: Path) -> None:
    report, _ = dr_run(tmp_path / "a", "BBBB2DDD", (2,))
    assert reasons(report, CheckName.DR_RECOMMENDATION) == [Reason.DR_NON_APPLICABILE]
    report, _ = dr_run(tmp_path / "b", "BBBB2DDD", (1,))
    assert reasons(report, CheckName.DR_RECOMMENDATION) == [Reason.VERIFICATO]


# --- EJ200: stampa con il layout vero e catalogo nel formato pubblicato -------------------

EQ, DASH = "=" * 78, "-" * 78
CONT = "*******  CONTINUA ALLA PAGINA SEGUENTE  ******"
CONT_FROM = "*** CONTINUAZIONE DALLA PAGINA PRECEDENTE ***"
CONTINUA = "                         *** C O N T I N U A ***"


def _header(page: int) -> list[str]:
    return [
        f"PGM PVRM320                                      DATA STAMPA 01-01-2030 PAG.   {page}",
        " ** C I C L O    D I   L A V O R A Z I O N E **      *** SENZA TEMPI ***",
        "CICLO :   EJPR-00000001-001-1          DESCR.CICLO : PEZZO DI PROVA",
        "",
        "TIPO CICLO : NORMALE                   PROGETTO...   EJ200 RICAMBI N",
        "DISEGNO..                              TIPO CICLO.   R",
        "STATO... AGG.ALTR.UT.                  NOTE.......",
        "RIPARAZIONE : A3".ljust(39) + "S26/00001",
    ]


_TABLE = [
    EQ,
    "",
    EQ,
    "TARGA     * NUM.  *   DESCRIZIONE  OPERAZIONE                          *",
    "C.RESP.   * OPER  *                                                    * PRE",
    "          *       *                                                    *",
    DASH,
]


def _r(left: str = "", num: str = "", text: str = "") -> str:
    return f"{left:<10}* {num:<5} *   {text:<49}*"


def _plain(left: str, text: str) -> str:
    """Riga in fondo al blocco, più larga della colonna TARGA: senza asterischi."""
    return f"{left:<20}{text}"


def ej200_pages() -> list[str]:
    first = [*_header(1), EQ, "MODIFICHE TESTATA CICLO", "** NESSUNA MODIFICA **", EQ]
    second = (
        _header(2)
        + _TABLE
        + [
            _r("NOTE", "005"),
            _r("999999", "", "IL PRESENTE CICLO FORNISCE LE ISTRUZIONI PER"),
            _r("", "", "RIPARARE UNA INTACCA. RIPARAZIONE IN ACCORDO"),
            _r("", "", "ALLE DISPOSIZIONI DELLA RDR"),
            _r("", "", "EJ00020L-01 (RIF. SD S26/00001)."),
            DASH,
            _r("XX/457", "010"),
            _r("AVM700", "", "PRELIEVO ED IDENTIFICAZIONE DEL PARTICOLARE."),
            _r("", "", "* ATTREZZATURA PREVISTA *"),
            _r("", "", "B0000001        MARKER DI PROVA"),
            DASH,
            _r("PREC01", "015"),
            _r("AVM701", "", "PRESA IN CARICO DA PERIZIA."),
            DASH,
            _r("", "", "D.T.    01-01-30"),
            _r("YY/766", "020"),
            _r("AVM702", "", "RIMUOVERE I DIFETTI MEDIANTE RACCORDATURA"),
            _r("", "", "MANUALE LOCALE. PROFONDITA' MASSIMA DI"),
            _r("", "", "RACCORDATURA 0.50MM;"),
            _r("", "", CONT),
            DASH,
            CONTINUA,
        ]
    )
    third = (
        _header(3)
        + _TABLE
        + [
            _r("", "", CONT_FROM),
            _plain("", "SP.ORIG. X1Y00000001Z000ZZ     SP.XXXX"),
            DASH,
            _r("IM0001", "030"),
            _r("AVM703", "", "LAVAGGIO DEL COMPONENTE SECONDO SCHEDA PROCESSO."),
            _plain("SCHEDA : PG 900", "SP.ORIG. X1Y00000002Z000ZZ     SP.XXXX"),
            DASH,
            _r("", "", "01-01-30"),
            _r("ZZ/095", "040"),
            _r("AVM704", "", "COLLAUDO VISIVO CON LENTE 10X DELLE AREE"),
            _r("", "", "RIPARATE SECONDO DT."),
            _plain("SCHEDA : 16", "SP.ORIG. X1Y00000003Z000ZZ     SP.XXXX"),
            DASH,
            _r("QQ/999", "050"),
            _r("AVM705", "", "CONTROLLO VISIVO FINALE DEL PARTICOLARE."),
            EQ,
            "RIP: A3 OEM: XX/YY/ZZZ".ljust(40) + "CHANGE: -",
            "FIRMA ME CHECKER          NOME COGNOME         01-01-2030",
        ]
    )
    return ["\n".join(page) for page in (first, second, third)]


RDR_TEXT = "\n".join(
    [
        "<!-- page 1 -->",
        "RDR EJ00020L - Housing",
        "Rimuovere i difetti mediante raccordatura manuale locale.",
        "Profondita' massima di raccordatura 0.31 mm; raggio minimo 6 mm.",
        "Lavare il componente secondo scheda processo.",
        "Controllo visivo con lente 10x delle aree riparate.",
    ]
)


def _entry(code: str, issue: str, document_id: str) -> dict[str, Any]:
    return {
        "code": code,
        "kind": "RDR",
        "issue": issue,
        "document_id": document_id,
        "content_hash": f"{document_id}-h",
        "title": f"RDR {code} - Housing",
        "published": True,
        "partial": False,
        "references": [code.split("-")[0][:-1]],
    }


def test_ej200_from_the_print_to_the_frontend_payload(tmp_path: Path) -> None:
    entries = [
        _entry("EJ00020L-01", "01", "EJ00020L-01-0a1b2c3d"),
        _entry("EJ00020L-02", "02", "EJ00020L-02-1b2c3d4e"),
        _entry("EJ00010X-01", "01", "RDR_EJ00010X_-_Housing-2c3d4e5f"),
    ]
    objects: dict[str, Any] = {DEFAULT_CATALOG_KEY: entries}
    for item in entries:
        key = f"{DEFAULT_TEXT_PREFIX}{item['document_id']}/{item['content_hash']}.md"
        objects[key] = RDR_TEXT
    store = InMemoryObjectStore(objects)
    civil = load_local_knowledge(civil_knowledge(tmp_path / "civile"))
    kb = Ej200KnowledgeBase(
        "ej200-prova",
        Ej200Catalog(store),
        tmp_path / "ej200",
        store,
        StructuredLayout(sp=None, dr=None),
        tags=civil.machine_tags,
    )
    session = ScriptedSession(coherent)
    deps = Dependencies(
        settings=load_settings(None).model_copy(),
        profile=profile("ej200"),
        kb=kb,
        machines=StaticMachineRegistry(ACTIVE),
        extractor=Pvrm320LayoutExtractor(),
        session=session,
        system_prompt="sistema",
        prompt_version="test",
    )
    run_dir = tmp_path / "run"
    report = run_validation(RunRequest(pdf_bytes=build_pdf(ej200_pages())), deps, run_dir)

    # lettura della stampa
    assert reasons(report, CheckName.EXTRACTION_INTEGRITY) == [Reason.VERIFICATO]
    payload = json.loads((run_dir / "payload.json").read_text("utf-8"))
    ops = payload["operations"]
    assert [op["operationNumber"] for op in ops] == [
        "005",
        "010",
        "015",
        "020",
        "030",
        "040",
        "050",
    ]
    assert {op["repairCode"] for op in ops} == {"A3"}
    assert [op["targaCResp"] for op in ops] == [
        None,
        "XX/457",
        "PREC01",
        "YY/766",
        "IM0001",
        "ZZ/095",
        "QQ/999",
    ]
    assert [op["scheda"] for op in ops] == [
        None,
        None,
        None,
        None,
        {"code": "PG 900", "sp_orig": "X1Y00000002Z000ZZ"},
        {"code": "16", "sp_orig": "X1Y00000003Z000ZZ"},
        None,
    ]
    assert ops[3]["operationDescription"].endswith("RACCORDATURA 0.50MM;")
    assert ops[5]["operationDescription"].startswith("COLLAUDO VISIVO")  # la data non entra
    assert {op["taskCodeCited"] for op in ops} == {None}

    # fonte: la RDR citata con la issue 01, anche se nel catalogo c'è la 02
    assert [s["manual"] for s in payload["sources"]] == ["EJ00020L-01"]
    assert [s["sourceFeedback"] for s in payload["sources"]] == ["No errors found."]

    # esiti
    assert [op["operationFeedback"][:5] for op in ops] == [
        "No er",
        "No er",
        "No er",
        "Error",
        "No er",
        "No er",
        "No er",
    ]
    assert [op["targaCRespFeedback"][:5] for op in ops] == [
        "N/A -",
        "No er",
        "No er",
        "No er",
        "No er",
        "No er",
        "Error",
    ]
    assert {op["schedaFeedback"][:5] for op in ops} == {"N/A -"}
    assert payload["cycle_errors_count"] == 2
    assert payload["cycle_status"] == "completo"
    assert payload["_pipeline_errors"] == []
    assert len(session.requests) == 7
