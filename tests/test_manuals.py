"""`manuali`: quali manuali servono per i cicli di prova (codici inventati)."""

import json
from pathlib import Path

import pytest
from pvrm320_report_fixtures import civil_pages, ej200_pages
from typer.testing import CliRunner

from cycle_validation import cli
from cycle_validation.errors import CycleValidationError
from cycle_validation.kb.local import load_local_knowledge
from cycle_validation.report.manuals import (
    explain_missing,
    file_lines,
    from_report,
    match_files,
    needed_manuals,
    parse_errors,
    screen_lines,
)
from cycle_validation.testing.pdf import build_pdf

KNOWLEDGE = Path("examples/sintetico/knowledge")


def _report(
    sources: list[tuple[str, str, str, str | None]],
    operations: list[tuple[str, str | None, list[str]]],
) -> dict:
    """sources: (manuale, task, esito del controllo della fonte, repair code);
    operations: (numero, repair code, task)."""
    return {
        "cycle": {
            "sources": [
                {"manual": m, "task": t, "issue": "Rev. 3", "repair_code": rc}
                for m, t, _, rc in sources
            ],
            "operations": [
                {"operation_number": number, "repair_code": rc, "task_codes": tasks}
                for number, rc, tasks in operations
            ],
        },
        "results": [
            {"check": "source", "target": {"kind": "source", "index": i}, "reason": reason}
            for i, (_, _, reason, _) in enumerate(sources)
        ]
        + [{"check": "task_code", "target": {"kind": "operation", "index": 0}, "reason": "X"}],
    }


REPORTS = {
    "errori-aaaa1111": _report(
        [
            ("MAN-DEMO-99", "99-20-02-300-004", "FONTE_ASSENTE", "R1"),
            ("MAN-DEMO-72", "72-00-01-110-001", "VERIFICATO", "R2"),
        ],
        [
            ("0005", "R1", ["99-10-01-110-001"]),  # task nella descrizione, non tra le fonti
            ("0010", "R2", ["72-00-01-110-001", "70-00-00-000-001"]),
            ("0035", "R1", []),  # senza task: si confronta con le fonti del suo repair code
        ],
    ),
    "errori-bbbb2222": _report(
        [("man-demo-99", "", "FONTE_ASSENTE", None)],
        [("030", None, ["99-10-01-110-001"])],
    ),
}


def _cycles() -> list:
    return [from_report(name, report) for name, report in REPORTS.items()]


def test_errors_are_hash_and_operations() -> None:
    assert parse_errors(["AAAA1111=005,035", "aaaa1111=40"]) == {"aaaa1111": {"5", "35", "40"}}
    with pytest.raises(CycleValidationError, match="impronta=op"):
        parse_errors(["aaaa1111"])


def test_operation_tasks_go_to_the_manual_of_their_repair_code() -> None:
    errors = parse_errors(["aaaa1111=005,035", "bbbb2222=030"])
    result = needed_manuals(_cycles(), errors)
    first, spm, last = result.manuals
    assert first.code == "MAN-DEMO-99" and first.state == "manca"
    assert first.cycles == {"errori-aaaa1111", "errori-bbbb2222"}  # maiuscole e minuscole
    assert first.tasks == {"99-10-01-110-001", "99-20-02-300-004"}
    assert first.chapters == ["99-10", "99-20"] and first.error_count == 3
    assert first.error_ops == {"errori-aaaa1111": {"5", "35"}, "errori-bbbb2222": {"30"}}
    assert spm.standard_practices and spm.tasks == {"70-00-00-000-001"}
    assert last.code == "MAN-DEMO-72" and last.state == "c'è" and not last.error_ops
    assert last.tasks == {"72-00-01-110-001"}  # il task 70- non è suo
    assert not result.loose_tasks and not result.unmatched


def test_with_the_knowledge_the_state_comes_from_it() -> None:
    cycles = _cycles()
    cycles[0].sources.append({"manual": "MAN-DEMO-72", "task": "72-99-99-999-999"})
    result = needed_manuals(cycles, {}, load_local_knowledge(KNOWLEDGE))
    states = {need.code: need.state for need in result.manuals}
    assert states["MAN-DEMO-99"] == "manca"
    assert states["MAN-DEMO-72"] == "c'è, ma mancano 1 task"


def test_manual_files_on_the_pc_are_matched_by_code_and_chapter() -> None:
    result = needed_manuals(_cycles(), {})
    match_files(
        result,
        [
            "C:/manuali/MAN DEMO 99/cap_99-10 riparazioni.pdf",
            "C:/manuali/MAN-DEMO-99/indice.pdf",
            "C:/manuali/MAN-DEMO-99/cap 99-100.pdf",  # 99-100 non è il capitolo 99-10
            "C:/manuali/SPM/70-00 pratiche.pdf",
            "C:/altro/documento.pdf",
        ],
    )
    first, spm, _ = result.manuals
    assert first.chapter_files == ["C:/manuali/MAN DEMO 99/cap_99-10 riparazioni.pdf"]
    assert len(first.files) == 3
    assert spm.chapter_files == ["C:/manuali/SPM/70-00 pratiche.pdf"]


def test_the_command_reads_the_prints_and_hides_the_codes(tmp_path: Path) -> None:
    prints = tmp_path / "stampe"
    prints.mkdir()
    pdf = build_pdf(civil_pages())
    (prints / "ciclo.pdf").write_bytes(pdf)
    (prints / "copia dello stesso ciclo.pdf").write_bytes(pdf)
    (prints / "non un ciclo.pdf").write_bytes(build_pdf(["testo qualunque " * 20]))
    military = [page.replace("MOTORE-1/MOTORE-2", "EJ200") for page in ej200_pages()]
    (prints / "militare.pdf").write_bytes(build_pdf(military))
    manual = build_pdf(["pagina di manuale " * 20])
    (prints / "ABC123456 capitolo 72-00.pdf").write_bytes(manual)
    (prints / "ABC123456 indice.pdf").write_bytes(manual + b" ")
    run = tmp_path / "errori-aaaa1111"
    run.mkdir()
    (run / "report.json").write_text(json.dumps(REPORTS["errori-aaaa1111"]), encoding="utf-8")
    out = tmp_path / "manuali.txt"
    result = CliRunner().invoke(
        cli.app,
        [
            "manuali",
            str(prints),
            str(run),
            "--errori",
            "aaaa1111=005",
            "--conoscenza",
            str(KNOWLEDGE),
            "--out",
            str(out),
        ],
    )
    assert result.exit_code == 0, result.output
    assert "Stampe: 6 file, 5 diverse; cicli letti: 3; non lette" in result.output
    for code in ("ABC123456", "MAN-DEMO", "72-00", "ciclo.pdf"):
        assert code not in result.output
    assert "M1: manca · 1 cicli · 2 task in 2 capitoli · serve per 1 errori" in result.output
    assert "PDF sul PC: 2, dei capitoli citati: 1" in result.output  # i file del manuale
    assert "cicli EJ200 lasciati fuori (conoscenza solo su AWS): 1" in result.output
    assert "da ingestionare: 3" in result.output
    text = out.read_text(encoding="utf-8")
    assert "M1  MAN-DEMO-99  (manca)" in text and "capitoli: 99-10, 99-20" in text
    assert "task: 72-00-00 REPAIR 001" in text  # il task della stampa, con gli spazi
    assert "ciclo.pdf | copia dello stesso ciclo.pdf" in text
    assert "non un ciclo.pdf" not in text
    assert "ABC123456 capitolo 72-00.pdf" in text


def test_the_command_stops_without_cycles(tmp_path: Path) -> None:
    result = CliRunner().invoke(cli.app, ["manuali", str(tmp_path)])
    assert result.exit_code == 1 and "Nessun ciclo letto" in result.output


def test_missing_tasks_say_why(tmp_path: Path) -> None:
    """Un task che manca: scritto nel testo ma non come titolo, solo la sezione, assente, o
    citato in una forma che non è un task."""
    kb_dir = tmp_path / "kb"
    (kb_dir / "documents").mkdir(parents=True)
    (kb_dir / "documents" / "m99.md").write_text(
        "# 99-10-01-110-001 Pulizia\n"
        "testo\n"
        "Vedi anche 99-20-02-300-004 per i limiti.\n"  # citato, ma non come titolo
        "Figura 99-30-05 pagina 3\n",  # solo la sezione
        encoding="utf-8",
    )
    (kb_dir / "documents" / "spm.md").write_text("# 70-00-00-000-001 Pratiche\n", encoding="utf-8")
    manifest = {
        "version": "prova",
        "documents": [
            {"key": "MAN-DEMO-99", "file": "documents/m99.md"},
            {"key": "SPM-DEMO", "file": "documents/spm.md", "kind": "SPM"},
        ],
    }
    (kb_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    kb = load_local_knowledge(kb_dir)
    cycles = _cycles()
    cycles[0].sources += [
        {"manual": "MAN-DEMO-99", "task": "99-30-05-200-001", "repair_code": "R1"},
        {"manual": "MAN-DEMO-99", "task": "99-40-01-100-001", "repair_code": "R1"},
        {"manual": "MAN-DEMO-99", "task": "REPAIR 007", "repair_code": "R1"},
    ]
    cycles[0].operations.append(
        {"operation_number": "0040", "repair_code": None, "task_codes": ["70-23-23-000-001"]}
    )
    result = needed_manuals(cycles, {}, kb)
    explain_missing(result, kb)
    need = next(m for m in result.manuals if m.code == "MAN-DEMO-99")
    why = {task: reason for task, (reason, _) in need.missing_why.items()}
    assert why == {
        "99-20-02-300-004": "testo",
        "99-30-05-200-001": "sezione",
        "99-40-01-100-001": "assente",
        "REPAIR 007": "forma",
    }
    assert need.missing_why["99-20-02-300-004"][1] == [
        "MAN-DEMO-99 riga 3: Vedi anche 99-20-02-300-004 per i limiti."
    ]
    spm = next(m for m in result.manuals if m.standard_practices)
    assert spm.missing_why == {"70-23-23-000-001": ("assente", [])}
    screen = "\n".join(screen_lines(result))
    assert (
        "(task mancanti: nel testo ma non come titolo 1, solo la sezione nel testo 1, "
        "non nel testo 1, forma non da task 1)" in screen
    )
    assert "99-" not in screen
    text = "\n".join(file_lines(result))
    assert "99-30-05-200-001: nel testo c'è solo la sua sezione" in text
    assert "MAN-DEMO-99 riga 4: Figura 99-30-05 pagina 3" in text


def test_coverage_counts_the_operations_the_v2_can_compare() -> None:
    from cycle_validation.report.manuals import cycle_coverage

    kb = load_local_knowledge(KNOWLEDGE)
    seen = from_report(
        "x",
        _report(
            [("MAN-DEMO-72", "72-00-01-110-001", "VERIFICATO", "R2")],
            [
                ("010", "R2", ["72-00-01-110-001"]),  # nella conoscenza
                ("020", "R2", []),  # senza task: il manuale della fonte c'è
                ("030", "R2", ["72-99-99-999-999"]),  # task che non c'è
            ],
        ),
    )
    assert cycle_coverage(seen, kb) == (2, 3)
    missing = from_report("y", REPORTS["errori-bbbb2222"])
    assert cycle_coverage(missing, kb) == (0, 1)


def test_choose_puts_the_known_cycles_first_and_adds_real_ones(tmp_path: Path) -> None:
    import hashlib

    prints = tmp_path / "stampe"
    prints.mkdir()
    known_pdf = build_pdf(civil_pages())
    other = build_pdf([p.replace("B1", "B2") for p in civil_pages()])
    (prints / "noto.pdf").write_bytes(known_pdf)
    (prints / "copia.pdf").write_bytes(known_pdf)
    (prints / "vero.pdf").write_bytes(other)
    military = [page.replace("MOTORE-1/MOTORE-2", "EJ200") for page in ej200_pages()]
    (prints / "militare.pdf").write_bytes(build_pdf(military))
    noted = hashlib.sha256(known_pdf).hexdigest()[:8]
    attesi = tmp_path / "attesi.yaml"
    attesi.write_text(f"cicli:\n  '{noted}':\n    giusto: true\n  ffff0000:\n    giusto: true\n")
    out = tmp_path / "cicli.txt"
    args = ["eval", "scegli", str(prints), "--knowledge", str(KNOWLEDGE), "--attesi", str(attesi)]
    result = CliRunner().invoke(cli.app, [*args, "--copertura", "0", "--out", str(out)])
    assert result.exit_code == 0, result.output
    assert "Scelti 2: noti 1, veri 1." in result.output
    assert "lasciati fuori (EJ200 (la sua conoscenza resta su AWS)): 1" in result.output
    assert "non trovati: ffff0000" in result.output
    assert "vero.pdf" not in result.output  # sullo schermo solo impronte
    lines = out.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2 and lines[0].endswith(("noto.pdf", "copia.pdf"))
    assert lines[1].endswith("vero.pdf")
    result = CliRunner().invoke(cli.app, [*args, "--quanti", "1", "--out", str(out)])
    assert "Scelti 1: noti 1, veri 0." in result.output
    everything = [*args, "--quanti", "0", "--copertura", "0", "--out", str(out)]
    assert "Scelti 2: noti 1, veri 1." in CliRunner().invoke(cli.app, everything).output


def test_trial_needs_a_name_or_a_variant(tmp_path: Path) -> None:
    pdf = tmp_path / "c.pdf"
    pdf.write_bytes(build_pdf(civil_pages()))
    result = CliRunner().invoke(cli.app, ["eval", "prova", str(pdf), "--knowledge", str(KNOWLEDGE)])
    assert result.exit_code == 1 and "Manca --nome" in result.output
    empty = tmp_path / "vuota.txt"
    empty.write_text("\n")
    result = CliRunner().invoke(
        cli.app, ["eval", "prova", "--lista", str(empty), "--nome", "x", "--knowledge", "k"]
    )
    assert result.exit_code == 1 and "Nessun PDF" in result.output


def test_trial_with_a_missing_variant_fails_clearly(tmp_path: Path) -> None:
    pdf = tmp_path / "c.pdf"
    pdf.write_bytes(build_pdf(civil_pages()))
    result = CliRunner().invoke(
        cli.app,
        ["eval", "prova", str(pdf), "--knowledge", "k", "--variante", str(tmp_path / "x.yaml")],
    )
    assert result.exit_code == 1 and "Variante non trovata" in result.output


def test_every_variant_file_loads() -> None:
    from cycle_validation.evaluation.variant import load_variant

    for path in sorted(Path("eval/varianti").glob("*.yaml")):
        variant = load_variant(path)
        assert variant.name == path.stem
