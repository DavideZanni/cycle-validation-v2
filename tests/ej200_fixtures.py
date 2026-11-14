"""Pubblicazioni EJ200 sintetiche: catalogo, testi, dati TM. Tutto inventato."""

from pathlib import Path
from typing import Any

from cycle_validation.agent.session import SessionRequest
from cycle_validation.kb.ej200 import (
    DEFAULT_CATALOG_KEY,
    DEFAULT_TEXT_PREFIX,
    Ej200Catalog,
    Ej200KnowledgeBase,
)
from cycle_validation.kb.stores import InMemoryObjectStore
from cycle_validation.kb.structured import StructuredLayout

DM_A = "DMC-EJ200-A-72-31-00-00A-520A-A"
DM_B = "DMC-EJ200-A-72-31-00-00A-720A-A"
DM_C = "DMC-EJ200-A-72-41-00-00A-250A-A"

# (code, kind, issue, document_id, content_hash, published, partial, references, pages)
PUBLICATIONS: list[dict[str, Any]] = [
    {
        "code": "RN-100",
        "kind": "RN",
        "issue": "1",
        "document_id": "rn100-1",
        "content_hash": "h-rn100-1",
    },
    {
        "code": "RN-100",
        "kind": "RN",
        "issue": "2",
        "document_id": "rn100-2",
        "content_hash": "h-rn100-2",
    },
    {
        "code": "EF-200",
        "kind": "EF",
        "issue": "1",
        "document_id": "ef200-1",
        "content_hash": "h-ef200-1",
    },
    {
        "code": "RDR-300",
        "kind": "RDR",
        "issue": "1",
        "document_id": "rdr300-1",
        "content_hash": "h-rdr300-1",
    },
    {
        "code": "RDR-9A",
        "kind": "RDR",
        "issue": "1",
        "document_id": "rdr9a",
        "content_hash": "h9a",
        "references": ["RDR-9"],
    },
    {
        "code": "RDR-9B",
        "kind": "RDR",
        "issue": "1",
        "document_id": "rdr9b",
        "content_hash": "h9b",
        "references": ["RDR-9"],
    },
    {
        "code": "RN-400",
        "kind": "RN",
        "issue": "1",
        "document_id": "rn400",
        "content_hash": "h400",
        "published": False,
    },
    {
        "code": "EF-500",
        "kind": "EF",
        "issue": "1",
        "document_id": "ef500",
        "content_hash": "h500",
        "partial": True,
    },
]

TEXTS: dict[str, list[str]] = {
    "rn100-1": ["Edizione vecchia: usare solvente tipo B."],
    "rn100-2": [
        "RN-100 Issue 2",
        f"Data module {DM_A}: pulizia della pala.",
        "Pulire la pala con solvente tipo A.",
        f"Data module {DM_B}: ispezione della pala.",
        "Ispezionare la pala con lente 10x.",
    ],
    "ef200-1": [
        "EF-200 Issue 1",
        f"Data module {DM_C}: rettifica della sede.",
        "Rettificare la sede fino al diametro 45,00 mm.",
    ],
    "rdr300-1": ["RDR-300", "Deroga: la sede si rettifica a 45,00 mm massimo."],
    "rdr9a": ["RDR-9A"],
    "rdr9b": ["RDR-9B"],
    "rn400": ["non pubblicato"],
    "ef500": ["parziale"],
}


def catalog_entries() -> list[dict[str, Any]]:
    entries = []
    for item in PUBLICATIONS:
        entries.append({"title": item["code"], "published": True, "partial": False, **item})
    return entries


class RecordingStore(InMemoryObjectStore):
    """Store che ricorda quali testi di pubblicazione sono stati letti."""

    def __init__(self, objects: dict[str, Any]) -> None:
        super().__init__(objects)
        self.reads: list[str] = []

    def get_bytes(self, key: str) -> bytes:
        self.reads.append(key)
        return super().get_bytes(key)

    def text_reads(self) -> list[str]:
        return [key for key in self.reads if key.startswith(DEFAULT_TEXT_PREFIX)]


def text_key(document_id: str) -> str:
    content_hash = next(p["content_hash"] for p in PUBLICATIONS if p["document_id"] == document_id)
    return f"{DEFAULT_TEXT_PREFIX}{document_id}/{content_hash}.md"


def text_objects(long_document: str | None = None) -> dict[str, str]:
    """Il testo di ogni pubblicazione come markdown a righe, con un marcatore ogni 50 righe."""
    texts = dict(TEXTS)
    if long_document:
        texts[long_document] = [f"riga di prova {n}" for n in range(400)]
    out: dict[str, str] = {}
    for document_id, lines in texts.items():
        body: list[str] = []
        for number, line in enumerate(lines):
            if number % 50 == 0:
                body.append(f"<!-- page {1 + number // 50} -->")
            body.append(line)
        out[text_key(document_id)] = "\n".join(body) + "\n"
    return out


def make_store(
    entries: list[dict[str, Any]] | None = None, long_document: str | None = None
) -> RecordingStore:
    return RecordingStore(
        {
            DEFAULT_CATALOG_KEY: entries if entries is not None else catalog_entries(),
            "structured/TM/tm.json": [
                {"tag": "TM-1001", "function": "Banco di lavaggio"},
                {"tag": "TM-2002", "function": "Rettificatrice"},
            ],
            **text_objects(long_document),
        }
    )


def make_kb(
    workdir: Path, *, long_document: str | None = None, store: RecordingStore | None = None
) -> tuple[Ej200KnowledgeBase, RecordingStore]:
    store = store or make_store(long_document=long_document)
    kb = Ej200KnowledgeBase(
        "ej200-sintetico",
        Ej200Catalog(store),
        workdir,
        store,
        StructuredLayout(sp=None, dr=None),
    )
    return kb, store


def pvrm320_pages() -> list[str]:
    """Un ciclo PVRM320 su due pagine: l'operazione 0020 continua nella seconda."""
    return [
        "\n".join(
            [
                "PVRM320 EJ200 REPAIR CYCLE",
                "CYCLE: EJ-C-001",
                "DESCRIPTION: Riparazione dimostrativa",
                "ENGINE: EJ200",
                "REFERENCES: RN-100 Issue 2; EF-200; RDR-300",
                "OP 0010 Pulire la pala con solvente tipo A.",
                "MACHINE: TM-1001",
                f"DM: {DM_A}",
                "NOTE: attenzione ai residui",
                "continua la nota che non e una descrizione",
                "OP 0020 Rettificare la sede fino al",
                "MACHINE: TM-2002",
            ]
        ),
        "\n".join(
            [
                "PVRM320 EJ200 REPAIR CYCLE",
                "OP 0020 (cont.) diametro 46,00 mm.",
                f"DM: {DM_C}",
                "NOTE: seconda nota",
            ]
        ),
    ]


def judge(request: SessionRequest, attempt: int) -> dict[str, Any]:
    if "46,00" in request.prompt:
        return {
            "judgement": "contraddetto",
            "rationale": "Il valore è 45,00 mm.",
            "citations": [
                {
                    "file": "EF-200-1.md",
                    "line": 3,
                    "quote": "Rettificare la sede fino al diametro 45,00 mm.",
                }
            ],
        }
    return {
        "judgement": "coerente",
        "rationale": "Corrisponde.",
        "citations": [
            {"file": "RN-100-2.md", "line": 3, "quote": "Pulire la pala con solvente tipo A."}
        ],
    }
