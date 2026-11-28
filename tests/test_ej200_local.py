"""La prova EJ200 sul PC: conoscenza da S3 (qui uno store in memoria), nessuna traccia."""

import tempfile
from pathlib import Path
from typing import Any

import pytest
from ej200_fixtures import TEXTS, catalog_entries, judge
from fakes import ScriptedSession
from kb_fixtures import EXAMPLE_DIR, EXAMPLE_KB
from support import write_cycle_pdf
from test_ej200 import ej_cycle
from typer.testing import CliRunner

from cycle_validation import cli
from cycle_validation.evaluation import ej200_local
from cycle_validation.kb.stores import InMemoryObjectStore

runner = CliRunner()
POINTER = "k/ej200/current.json"


def published_store() -> InMemoryObjectStore:
    objects: dict[str, Any] = {
        POINTER: {"format": 1, "version": "r1", "path": "v/r1/"},
        "k/ej200/v/r1/catalog.json": catalog_entries(),
    }
    for item in catalog_entries():
        lines = TEXTS[item["document_id"]]
        key = f"k/ej200/v/r1/text/{item['document_id']}/{item['content_hash']}.md"
        objects[key] = "\n".join(lines) + "\n"
    return InMemoryObjectStore(objects)


@pytest.fixture
def temp_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "temp"
    root.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(root))
    monkeypatch.setattr(cli, "make_session", lambda settings, t: ScriptedSession(judge))
    monkeypatch.setattr(cli, "_s3_store", lambda bucket, region: published_store())
    return root


def invoke(tmp_path: Path, *pdfs: Path, pointer: str = POINTER) -> Any:
    cycle_json = tmp_path / "ciclo.json"
    cycle_json.write_text(ej_cycle().model_dump_json(), encoding="utf-8")
    return runner.invoke(
        cli.app,
        [
            "prova-ej200",
            *map(str, pdfs),
            "--bucket",
            "secchio",
            "--conoscenza-ej200",
            pointer,
            "--targhe",
            str(EXAMPLE_KB),
            "--machines",
            str(EXAMPLE_DIR / "macchine_attive.json"),
            "--cycle-json",
            str(cycle_json),
        ],
    )


def files_under(folder: Path) -> set[Path]:
    return set(folder.rglob("*")) if folder.exists() else set()


def test_prints_only_counts_and_leaves_nothing(tmp_path: Path, temp_root: Path) -> None:
    runs_before = files_under(Path("runs"))
    pdf = write_cycle_pdf(tmp_path / "ej.pdf", ej_cycle())
    result = invoke(tmp_path, pdf)
    assert result.exit_code == 0, result.output
    assert f"{ej200_local.fingerprint(pdf)}: " in result.output
    assert "1 errati" in result.output
    assert "ERRATO · operation_description · CONTRADDIZIONE: 1" in result.output
    assert "Cartella temporanea cancellata" in result.output
    # nessun testo, codice o fonte EJ200 a schermo
    for secret in ("RN-100", "EF-200", "RDR-300", "solvente", "45,00", "DMC-"):
        assert secret not in result.output
    assert list(temp_root.iterdir()) == []
    assert files_under(Path("runs")) == runs_before


def test_a_missing_pointer_stops_without_showing_the_key(tmp_path: Path, temp_root: Path) -> None:
    pdf = write_cycle_pdf(tmp_path / "ej.pdf", ej_cycle())
    result = invoke(tmp_path, pdf, pointer="k/assente/current.json")
    assert result.exit_code == 1
    assert "prova non partita (KnowledgeError)" in result.output
    assert "assente" not in result.output
    assert list(temp_root.iterdir()) == []


def test_leftovers_of_an_interrupted_trial_are_removed(tmp_path: Path) -> None:
    old = tmp_path / f"{ej200_local.WORKDIR_PREFIX}vecchia"
    (old / "ej200").mkdir(parents=True)
    (old / "ej200" / "testo.md").write_text("x", encoding="utf-8")
    (tmp_path / "altro").mkdir()
    assert ej200_local.remove_leftovers(tmp_path) == 1
    assert [p.name for p in tmp_path.iterdir()] == ["altro"]


def test_the_workdir_is_removed_after_an_error(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError), ej200_local.temporary_workdir(tmp_path) as folder:
        (folder / "testo.md").write_text("x", encoding="utf-8")
        raise RuntimeError
    assert list(tmp_path.iterdir()) == []


def test_a_failing_cycle_shows_the_error_type_not_the_message(tmp_path: Path) -> None:
    pdf = tmp_path / "a.pdf"
    pdf.write_bytes(b"%PDF-1.4")

    def broken(path: Path) -> Any:
        raise ValueError("RN-100 testo segreto")

    lines = ej200_local.render(ej200_local.run_cycles([pdf], broken))
    assert lines[0].endswith("non validato (ValueError)")
    assert "segreto" not in "\n".join(lines)
    assert lines[-1].startswith("Totale: 0 cicli validati su 1")


def test_the_example_placeholder_is_explained(tmp_path: Path, temp_root: Path) -> None:
    result = invoke(tmp_path, Path("<cartella EJ200>"))
    assert result.exit_code == 1
    assert "è l'esempio del comando" in result.output
    assert "OSError" not in result.output


def test_a_missing_folder_is_named(tmp_path: Path, temp_root: Path) -> None:
    result = invoke(tmp_path, tmp_path / "non-c-e")
    assert result.exit_code == 1
    assert "non esiste" in result.output


def test_an_unreadable_pdf_does_not_stop_the_others(tmp_path: Path) -> None:
    good = tmp_path / "a.pdf"
    good.write_bytes(b"%PDF-1.4")
    missing = tmp_path / "RN-100.pdf"

    def broken(path: Path) -> Any:
        raise ValueError("x")

    outcomes = ej200_local.run_cycles([missing, good], broken)
    assert [o.problem for o in outcomes] == ["FileNotFoundError", "ValueError"]
    assert outcomes[0].fingerprint == "????????"
