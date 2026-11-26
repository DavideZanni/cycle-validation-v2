"""Errori ciechi: copie dei cicli veri con un errore messo dal programma (dati inventati)."""

import random
from pathlib import Path

import pytest

from cycle_validation.checks.languages import number_mismatches
from cycle_validation.domain.cycle import Cycle, Operation, Source
from cycle_validation.evaluation.blind import KINDS, blind_mutations, mutate
from cycle_validation.kb.local import load_local_knowledge

KNOWLEDGE = Path("examples/sintetico/knowledge")
TASK = "72-00-01-110-001"


def _cycle(description: str, tasks: list[str] | None = None) -> Cycle:
    return Cycle(
        sources=[Source(manual="MAN-DEMO-72", task=TASK, repair_code="R1")],
        operations=[
            Operation(
                operation_number="010",
                operation_description=description,
                repair_code="R1",
                task_codes=tasks if tasks is not None else [TASK],
            ),
            Operation(operation_number="020", operation_description="ALTRO / OTHER"),
        ],
    )


BILINGUAL = (
    "ASCIUGARE A 2 BAR, NON USARE SPAZZOLE, 3 PASSATE / DRY AT 2 BAR, DO NOT USE BRUSHES, 3 PASSES"
)


def _mutated(kind: str, cycle: Cycle, seed: int = 1) -> Operation | None:
    kb = load_local_knowledge(KNOWLEDGE)
    return mutate(cycle, cycle.operations[0], kind, kb, random.Random(seed))


@pytest.mark.parametrize("seed", [1, 2, 3, 4])
def test_a_number_changed_in_one_language_is_seen_by_the_language_check(seed: int) -> None:
    changed = _mutated("numero_una_lingua", _cycle(BILINGUAL), seed)
    assert changed is not None
    assert number_mismatches(changed.operation_description)


def test_a_manual_number_changes_in_both_languages_with_a_value_the_manual_lacks() -> None:
    changed = _mutated("numero_manuale", _cycle(BILINGUAL))
    assert changed is not None
    italian, english = changed.operation_description.split(" / ")
    assert "2 BAR" not in italian and "2 BAR" not in english  # 2 è nel manuale, 3 no
    assert "3 PASSATE" in italian and not number_mismatches(changed.operation_description)
    # senza il numero nel manuale non si applica
    assert _mutated("numero_manuale", _cycle("3 PASSATE / 3 PASSES")) is None


def test_a_negation_is_removed_in_one_language_only() -> None:
    changed = _mutated("negazione_una_lingua", _cycle(BILINGUAL))
    assert changed is not None
    italian, english = changed.operation_description.split(" / ")
    assert ("NON USARE" in italian) != ("DO NOT USE" in english)
    assert _mutated("negazione_una_lingua", _cycle("USARE / USE")) is None


def test_a_task_code_becomes_one_that_no_document_has() -> None:
    changed = _mutated("task_inesistente", _cycle(f"PULIRE SECONDO {TASK} / CLEAN"))
    assert changed is not None
    new = changed.task_codes[0]
    assert new != TASK and new.startswith("72-00-01-110-")
    assert new in changed.operation_description


def test_the_copies_have_one_operation_and_the_same_seed_gives_the_same_errors() -> None:
    kb = load_local_knowledge(KNOWLEDGE)
    cycles = [(f"c{i}", _cycle(BILINGUAL)) for i in range(4)]
    first = blind_mutations(cycles, kb, count=6, seed=7)
    again = blind_mutations(cycles, kb, count=6, seed=7)
    assert [(m.kind, m.source) for m in first] == [(m.kind, m.source) for m in again]
    # una sola operazione con numeri per ciclo: una copia per ciclo
    assert len(first) == 4 and len({m.kind for m in first}) >= 3
    assert {m.kind for m in first} <= set(KINDS)
    assert all(len(m.cycle.operations) == 1 for m in first)
    assert max(sum(m.source == name for m in first) for name, _ in cycles) <= 2


def test_code_kinds_are_capped_and_the_room_goes_to_the_model_kinds() -> None:
    kb = load_local_knowledge(KNOWLEDGE)
    # molte operazioni con un numero in tutte e due le lingue e un codice di task
    many = Cycle(
        sources=[Source(manual="MAN-DEMO-72", task=TASK, repair_code="R1")],
        operations=[
            Operation(
                operation_number=f"{10 * i:03d}",
                operation_description=f"{BILINGUAL} SECONDO {TASK}",
                repair_code="R1",
                task_codes=[TASK],
            )
            for i in range(1, 9)
        ],
    )
    cycles = [(f"c{i}", many) for i in range(6)]
    found = blind_mutations(cycles, kb, count=100, seed=3, code_kind_max=2, per_cycle=8)
    counts = {kind: sum(m.kind == kind for m in found) for kind in KINDS}
    assert counts["numero_una_lingua"] <= 2 and counts["task_inesistente"] <= 2
    assert counts["numero_manuale"] > 2 and counts["negazione_una_lingua"] > 2
    assert max(sum(m.source == name for m in found) for name, _ in cycles) <= 8
    narrow = blind_mutations(cycles, kb, count=100, seed=3, per_cycle=1)
    assert len(narrow) == len(cycles)


def test_a_negation_is_removed_in_both_languages() -> None:
    changed = _mutated("negazione_due_lingue", _cycle(BILINGUAL))
    assert changed is not None
    italian, english = changed.operation_description.split(" / ")
    assert "NON USARE" not in italian and "DO NOT USE" not in english
    assert "USARE SPAZZOLE" in italian and "USE BRUSHES" in english
    assert not number_mismatches(changed.operation_description)  # le lingue restano d'accordo


def test_a_limit_is_inverted_in_both_languages() -> None:
    cycle = _cycle(
        "PRESSIONE MASSIMO 2 BAR, ALMENO 3 PASSATE / MAXIMUM PRESSURE 2 BAR, AT LEAST 3 PASSES"
    )
    changed = _mutated("limite_invertito", cycle)
    assert changed is not None
    assert changed.operation_description == (
        "PRESSIONE MINIMO 2 BAR, ALMENO 3 PASSATE / MINIMUM PRESSURE 2 BAR, AT LEAST 3 PASSES"
    )
    assert _mutated("limite_invertito", _cycle("ASCIUGARE / DRY")) is None
    # «min» dentro una parola non è un limite
    assert _mutated("limite_invertito", _cycle("MINUTI 5 / MINUTES 5")) is None


def test_two_prints_of_the_same_cycle_do_not_give_the_same_copy_twice() -> None:
    """24-11: due PDF con lo stesso ciclo davano due copie uguali (stessa impronta): 41 copie
    scritte, 39 diverse. Ora la seconda si salta e il posto va a un'altra copia."""
    kb = load_local_knowledge(KNOWLEDGE)
    twins = [("c1", _cycle(BILINGUAL)), ("c2", _cycle(BILINGUAL))]
    found = blind_mutations(twins, kb, count=10, seed=1, kinds=["negazione_due_lingue"])
    texts = [m.cycle.model_dump_json() for m in found]
    assert len(found) == 1 and len(set(texts)) == len(texts)


def test_model_kinds_go_only_on_operations_the_v2_can_compare() -> None:
    """25-11: 22 dei 26 mai visti mancati della base erano WARNING FONTE_ASSENTE (il task
    citato non è nella conoscenza): nessuno poteva trovarli. I tipi del modello vanno solo su
    operazioni confrontabili; quelli del codice dappertutto."""
    from cycle_validation.evaluation.blind import MODEL_KINDS, comparable

    kb = load_local_knowledge(KNOWLEDGE)
    known = _cycle(BILINGUAL)
    unknown = _cycle(BILINGUAL, tasks=["72-99-99-999-999"])
    assert comparable(known, known.operations[0], kb)
    assert not comparable(unknown, unknown.operations[0], kb)
    assert blind_mutations([("c1", unknown)], kb, count=10, seed=1, kinds=MODEL_KINDS) == []
    assert blind_mutations([("c1", known)], kb, count=10, seed=1, kinds=MODEL_KINDS)
    code = blind_mutations([("c1", unknown)], kb, count=10, seed=1, kinds=["numero_una_lingua"])
    assert len(code) == 1  # i tipi del codice non guardano il manuale
