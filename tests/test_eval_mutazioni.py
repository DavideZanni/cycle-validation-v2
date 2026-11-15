"""Mutazioni: copie di un caso rivisto con un difetto messo apposta, di cui il codice sa l'esito
giusto, e copie con modifiche innocue che non devono cambiare niente."""

import json
from pathlib import Path

import pytest
from test_eval_run import SINTETICI, baseline, run

from cycle_validation.errors import ConfigError
from cycle_validation.evaluation.metrics import measure
from cycle_validation.evaluation.mutations import MUTATIONS, mutate_cases
from cycle_validation.evaluation.run import load_suites


def test_every_mutation_of_the_synthetic_cases_has_the_right_expected_outcome(
    tmp_path: Path,
) -> None:
    out = tmp_path / "mutazioni"
    made = mutate_cases(SINTETICI, out)
    kinds = {name.split("__")[1] for name in made}
    assert kinds == set(MUTATIONS)
    path = run(tmp_path, baseline(tmp_path), cases=out)
    m = measure(json.loads(path.read_text(encoding="utf-8")))
    assert m.concordance == 1.0, m.mismatches
    assert m.failures == 0


def test_a_wrong_machine_is_an_expected_errato(tmp_path: Path) -> None:
    out = tmp_path / "mutazioni"
    mutate_cases(SINTETICI / "mos", out)
    case = out / "mos" / "pulito__targa_non_attiva"
    cycle = json.loads((case / "ciclo.json").read_text(encoding="utf-8"))
    expected = json.loads((case / "expected.json").read_text(encoding="utf-8"))
    info = json.loads((case / "mutazione.json").read_text(encoding="utf-8"))
    operation = info["operazione"]
    assert cycle["operations"][operation]["machine_tag"].endswith("-MUT")
    tag_rows = [
        r for r in expected["rows"] if r["check"] == "machine_tag" and r["index"] == operation
    ]
    assert tag_rows == [
        {
            "check": "machine_tag",
            "kind": "operation",
            "index": operation,
            "verdict": "ERRATO",
            "reason": "MACCHINA_NON_ATTIVA",
        }
    ]
    assert expected["rivisto"] is True and "status" not in expected
    assert "difetto" in info["tipo"]


def test_the_mutated_suite_reads_the_same_knowledge_from_its_new_folder(tmp_path: Path) -> None:
    out = tmp_path / "mutazioni"
    mutate_cases(SINTETICI / "mos", out)
    (suite,) = load_suites(out)
    assert suite.config.estrazione == "ciclo_json"
    assert suite.path(suite.config.conoscenza).is_dir()


def test_only_reviewed_cases_are_mutated(tmp_path: Path) -> None:
    source = tmp_path / "casi" / "mos"
    source.mkdir(parents=True)
    (source / "suite.yaml").write_text(
        (SINTETICI / "mos" / "suite.yaml").read_text(encoding="utf-8"), encoding="utf-8"
    )
    for name in ("pulito", "macchina_non_attiva"):
        case = source / name
        case.mkdir()
        for file in ("ciclo.json", "expected.json"):
            (case / file).write_bytes((SINTETICI / "mos" / name / file).read_bytes())
    draft = json.loads((source / "pulito" / "expected.json").read_text(encoding="utf-8"))
    draft["rivisto"] = False
    (source / "pulito" / "expected.json").write_text(json.dumps(draft), encoding="utf-8")
    # La suite copiata sta altrove: i percorsi relativi non valgono più, si fissano.
    (source / "suite.yaml").write_text(
        (SINTETICI / "mos" / "suite.yaml")
        .read_text(encoding="utf-8")
        .replace("../../../../examples", (SINTETICI.parents[2] / "examples").as_posix()),
        encoding="utf-8",
    )
    made = mutate_cases(tmp_path / "casi", tmp_path / "out")
    assert made and all(name.startswith("mos/macchina_non_attiva__") for name in made)


def test_a_folder_not_made_by_the_generator_is_never_overwritten(tmp_path: Path) -> None:
    out = tmp_path / "mutazioni"
    (out / "mos").mkdir(parents=True)
    (out / "mos" / "mio.txt").write_text("mio", encoding="utf-8")
    with pytest.raises(ConfigError, match="non è stata scritta"):
        mutate_cases(SINTETICI / "mos", out)
    mutate_cases(SINTETICI / "dr", out)
    mutate_cases(SINTETICI / "dr", out)  # la seconda volta sostituisce la prima
