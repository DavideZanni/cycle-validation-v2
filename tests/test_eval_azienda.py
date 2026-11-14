"""Esperimenti sui dati aziendali: fotografia della conoscenza, estrazione dal PDF vero,
bozza degli esiti attesi da rivedere, giro completo con un comando."""

import json
import shutil
from pathlib import Path
from typing import Any

from fakes import ScriptedSession
from support import example_cycle, scripted_judge, write_cycle_pdf
from test_eval_metrics import record, results, write
from test_eval_run import ROOT, baseline, factory, run

from cycle_validation.agent.session import SessionRequest
from cycle_validation.evaluation.draft import draft_case
from cycle_validation.evaluation.leaderboard import build_leaderboard
from cycle_validation.evaluation.metrics import measure
from cycle_validation.evaluation.run import load_suites
from cycle_validation.evaluation.snapshot import take_snapshot
from cycle_validation.golden import load_cases
from cycle_validation.kb.stores import InMemoryObjectStore, LocalDirObjectStore

EXAMPLE = ROOT / "examples" / "sintetico"
MANUALS = "Manufacturing AI/exports/manuali/"


def extracting(cycle: dict[str, Any]) -> Any:
    """Modello finto: all'estrazione risponde con `cycle`, ai controlli come nei test."""

    def script(request: SessionRequest, attempt: int) -> dict[str, Any]:
        if request.session_id == "extract":
            return cycle
        return scripted_judge(request, attempt)

    return script


def s3_mirror(root: Path) -> Path:
    """Una cartella con la struttura delle chiavi S3: manuali dell'ingestion e dati TM/SP/DR."""
    knowledge = EXAMPLE / "knowledge"
    shutil.copytree(knowledge, root / MANUALS, ignore=shutil.ignore_patterns("*_*.json"))
    for name, folder in (
        ("machine_tags", "TM"),
        ("process_sheets", "SP"),
        ("dr_recommendations", "DR"),
    ):
        target = root / "structured" / folder
        target.mkdir(parents=True)
        shutil.copy(knowledge / f"{name}.json", target / f"{name}.json")
    return root


def company_suite(tmp_path: Path, *, extraction: str = "dal_pdf") -> Path:
    suite = tmp_path / "aziendali" / "mos"
    case = suite / "caso_1"
    case.mkdir(parents=True)
    mirror = s3_mirror(tmp_path / "foto")
    (suite / "suite.yaml").write_text(
        f"conoscenza: {mirror.as_posix()}\n"
        "tipo_conoscenza: fotografia\n"
        f"manuali: {MANUALS}\n"
        f"macchine: {(EXAMPLE / 'macchine_attive.json').as_posix()}\n"
        f"estrazione: {extraction}\n",
        encoding="utf-8",
    )
    write_cycle_pdf(case / "ciclo.pdf", example_cycle())
    return suite


def test_a_case_needs_only_the_pdf_and_the_expected_outcomes(tmp_path: Path) -> None:
    folder = tmp_path / "caso"
    folder.mkdir()
    write_cycle_pdf(folder / "ciclo.pdf", example_cycle())
    (folder / "expected.json").write_text('{"profile": "mos", "rows": []}', encoding="utf-8")
    (case,) = load_cases(tmp_path)
    assert case.cycle_json is None
    assert case.expected.rivisto is True


def test_company_knowledge_is_read_from_a_snapshot_with_the_production_code(
    tmp_path: Path,
) -> None:
    suite = company_suite(tmp_path)
    draft_case(
        suite / "caso_1",
        load_suites(suite)[0],
        baseline(tmp_path),
        factory(extracting(json.loads(example_cycle().model_dump_json()))),
        project_root=ROOT,
        workdir=tmp_path / "w",
    )
    expected = json.loads((suite / "caso_1" / "expected.json").read_text(encoding="utf-8"))
    assert expected["rivisto"] is False
    verdicts = {row["verdict"] for row in expected["rows"]}
    assert {"CORRETTO", "ERRATO"} <= verdicts  # targhe e manuali letti dalla fotografia
    review = (suite / "caso_1" / "revisione.md").read_text(encoding="utf-8")
    assert "rivisto" in review and "operation_description" in review
    assert (suite / "caso_1" / "ciclo.json").is_file()


def test_unreviewed_cases_are_skipped(tmp_path: Path) -> None:
    suite = company_suite(tmp_path)
    (suite / "caso_1" / "expected.json").write_text(
        '{"profile": "mos", "rivisto": false, "rows": []}', encoding="utf-8"
    )
    lines: list[str] = []
    path = run(tmp_path, baseline(tmp_path), cases=suite, progress=lines.append)
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["esecuzioni"] == []
    assert data["saltati"] == ["mos/caso_1"]
    assert any("da rivedere" in line for line in lines)


def test_extraction_from_the_pdf_is_measured_against_the_reference_cycle(
    tmp_path: Path,
) -> None:
    suite = company_suite(tmp_path)
    reference = json.loads(example_cycle().model_dump_json())
    (suite / "caso_1" / "ciclo.json").write_text(json.dumps(reference), encoding="utf-8")
    (suite / "caso_1" / "expected.json").write_text(
        '{"profile": "mos", "rows": []}', encoding="utf-8"
    )
    wrong = json.loads(json.dumps(reference))
    wrong["operations"][0]["machine_tag"] = "TM-9999"
    path = run(
        tmp_path, baseline(tmp_path), cases=suite, session_factory=factory(extracting(wrong))
    )
    data = json.loads(path.read_text(encoding="utf-8"))
    (only,) = data["esecuzioni"]
    total = len(reference["operations"])
    assert only["estrazione"]["operazioni"] == [total - 1, total]
    assert data["conoscenza"]["mos"]
    m = measure(data)
    assert m.extraction_accuracy is not None and m.extraction_accuracy < 1.0


def test_runs_on_different_knowledge_are_not_compared(tmp_path: Path) -> None:
    good = [record(1, [])]
    write(tmp_path, "1_baseline", results("baseline", good, conoscenza={"mos": "v1"}))
    write(tmp_path, "2_nuova", results("nuova", good, conoscenza={"mos": "v2"}))
    board = build_leaderboard(tmp_path)[0]
    assert [e.name for e in board.rejected] == ["nuova"]
    assert "conoscenza diversa" in board.rejected[0].reasons[0]


def test_a_variant_that_reads_the_pdf_worse_is_ruled_out(tmp_path: Path) -> None:
    # Stessi esiti, ma un'operazione letta male: su altri cicli diventerebbe un esito sbagliato.
    good = [record(1, [], estrazione={"operazioni": [4, 4], "fonti": [3, 3]})]
    worse = [record(1, [], estrazione={"operazioni": [3, 4], "fonti": [3, 3]})]
    write(tmp_path, "1_baseline", results("baseline", good))
    write(tmp_path, "2_nuova", results("nuova", worse))
    board = build_leaderboard(tmp_path)[0]
    assert [e.name for e in board.rejected] == ["nuova"]
    assert any("estrazione" in reason for reason in board.rejected[0].reasons)


def test_a_snapshot_copies_the_prefixes_and_records_where_they_come_from(
    tmp_path: Path,
) -> None:
    store = InMemoryObjectStore(
        {
            f"{MANUALS}manifest.json": {"format": 1},
            f"{MANUALS}documents/A.md": "testo",
            "structured/TM/tm.json": [{"tag": "TM-1"}],
            "altro/segreto.json": [],
        }
    )
    dest = tmp_path / "foto"
    count = take_snapshot(store, [MANUALS, "structured/TM/"], dest, source="s3://bucket")
    assert count == 3
    copied = LocalDirObjectStore(dest)
    assert copied.get_bytes(f"{MANUALS}documents/A.md") == b"testo"
    assert copied.list_keys("altro/") == []
    info = json.loads((dest / "fotografia.json").read_text(encoding="utf-8"))
    assert info["origine"] == "s3://bucket"
    assert info["oggetti"] == 3
    assert info["versione"]


def test_a_knowledge_folder_that_cannot_be_read_stops_the_run_before_any_model_call(
    tmp_path: Path,
) -> None:
    suite = company_suite(tmp_path)
    shutil.rmtree(tmp_path / "foto" / "structured")
    (suite / "caso_1" / "expected.json").write_text(
        '{"profile": "mos", "rows": []}', encoding="utf-8"
    )
    session = ScriptedSession(extracting({}))
    try:
        run(tmp_path, baseline(tmp_path), cases=suite, session_factory=lambda s, t: session)
    except Exception as error:
        assert "conoscenza" in str(error).lower()
    else:
        raise AssertionError("doveva fermarsi")
    assert session.requests == []
