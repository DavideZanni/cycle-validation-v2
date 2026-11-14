"""Knowledge base sintetiche per i test. Tutti i dati sono inventati."""

from pathlib import Path

from cycle_validation.config import ProfileConfig, load_profile
from cycle_validation.kb.memory import IndexedKnowledgeBase
from cycle_validation.kb.port import (
    DocumentInfo,
    DrRecommendation,
    MachineTagEntry,
    ProcessSheetEntry,
    TaskLocation,
)
from cycle_validation.kb.remote import RemoteKnowledgeBase
from cycle_validation.kb.stores import InMemoryObjectStore

REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_DIR = REPO_ROOT / "examples" / "sintetico"
EXAMPLE_KB = EXAMPLE_DIR / "knowledge"
PROFILES_DIR = REPO_ROOT / "config" / "profiles"

DOC_72 = DocumentInfo(
    key="MAN-DEMO-72",
    path=EXAMPLE_KB / "documents" / "MAN-DEMO-72.md",
    version="Rev. 12",
    title="Manuale dimostrativo, capitolo 72",
)
DOC_75 = DocumentInfo(
    key="MAN-DEMO-75",
    path=EXAMPLE_KB / "documents" / "MAN-DEMO-75.md",
    version="Rev. 3",
    title="Manuale dimostrativo, capitolo 75",
)


def _task(document: DocumentInfo, task: str, start: int, end: int) -> TaskLocation:
    return TaskLocation(
        manual_key=document.key, task=task, document=document, line_start=start, line_end=end
    )


def memory_knowledge() -> IndexedKnowledgeBase:
    """Stesso contenuto di examples/sintetico/knowledge, costruito a mano."""
    return IndexedKnowledgeBase(
        "sintetico-2026-11",
        documents=[DOC_72, DOC_75],
        aliases={"MAN-DEMO-72": ["Manuale Demo 72", "MD72"], "MAN-DEMO-75": ["MD75"]},
        tasks=[
            _task(DOC_72, "72-00-01-110-001", 5, 9),
            _task(DOC_72, "72-00-01-220-002", 12, 15),
            _task(DOC_72, "72-00-01-350-003", 17, 20),
            _task(DOC_75, "75-10-02-400-001", 5, 8),
        ],
        machine_tags=[
            MachineTagEntry(tag="TM-1001", function="Banco di lavaggio"),
            MachineTagEntry(tag="TM-2002", function="Rettificatrice per interni"),
            MachineTagEntry(tag="TM-3003", function="Banco di ispezione"),
        ],
        process_sheets=[
            ProcessSheetEntry(
                code="SP-0101",
                edition="B",
                treatment="Lavaggio con solvente",
                engine_families=("GENX",),
            ),
            ProcessSheetEntry(
                code="SP-0202",
                edition="A",
                treatment="Controllo dimensionale",
                engine_families=("LEAP",),
            ),
        ],
        dr_recommendations=[
            DrRecommendation(
                serial_number="SN-DEMO-001",
                conditions=(1,),
                procedure="Repair",
                reference="DR-DEMO-01",
                manual="MAN-DEMO-72",
                tasks=("72-00-01-350-003",),
            ),
            DrRecommendation(
                serial_number="SN-DEMO-001",
                conditions=(2,),
                procedure="Accept as is",
                reference="DR-DEMO-02",
            ),
            DrRecommendation(
                serial_number="SN-DEMO-002",
                conditions=(1, 2),
                procedure="Reject",
                reference="DR-DEMO-03",
            ),
        ],
    )


def profile(name: str = "mos") -> ProfileConfig:
    return load_profile(name, PROFILES_DIR)


class BrokenKnowledge(IndexedKnowledgeBase):
    """Knowledge base la cui sorgente non risponde."""

    def __init__(self) -> None:
        super().__init__("rotta")

    def _fail(self) -> None:
        from cycle_validation.errors import SourceUnavailableError

        raise SourceUnavailableError("sorgente non raggiungibile")

    def find_manuals(self, manual: str) -> list[DocumentInfo]:
        self._fail()
        return []

    def find_task(self, manual: str, task: str) -> TaskLocation | None:
        self._fail()
        return None

    def find_machine_tag(self, tag: str) -> MachineTagEntry | None:
        self._fail()
        return None

    def find_process_sheet(self, code: str) -> ProcessSheetEntry | None:
        self._fail()
        return None

    def find_dr_recommendations(self, serial_number: str) -> list[DrRecommendation]:
        self._fail()
        return []


def example_store() -> "InMemoryObjectStore":
    """Dati strutturati dell'esempio, nel layout S3 atteso dall'adattatore."""
    import json

    from cycle_validation.kb.stores import InMemoryObjectStore

    def load(name: str) -> object:
        return json.loads((EXAMPLE_KB / name).read_text(encoding="utf-8"))

    return InMemoryObjectStore(
        {
            "structured/TM/tm.json": load("machine_tags.json"),
            "structured/SP/sp.json": load("process_sheets.json"),
            "structured/DR/dr.json": load("dr_recommendations.json"),
        }
    )


def snapshot_store(prefix: str = "kb/sintetico") -> "InMemoryObjectStore":
    """La cartella dell'esempio come oggetti S3 sotto un prefisso."""
    from cycle_validation.kb.stores import InMemoryObjectStore

    store = InMemoryObjectStore()
    for path in EXAMPLE_KB.rglob("*"):
        if path.is_file():
            store.put(f"{prefix}/{path.relative_to(EXAMPLE_KB).as_posix()}", path.read_bytes())
    return store


def remote_knowledge(workdir: Path) -> "RemoteKnowledgeBase":
    from cycle_validation.kb.remote import RemoteKnowledgeBase
    from cycle_validation.kb.snapshot import SnapshotManualSource

    manuals = SnapshotManualSource(snapshot_store(), "kb/sintetico", workdir)
    return RemoteKnowledgeBase("sintetico-2026-11", example_store(), manuals)
