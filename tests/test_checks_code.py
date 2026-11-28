from pathlib import Path

import pytest
from kb_fixtures import DOC_72, DOC_75, EXAMPLE_DIR, BrokenKnowledge, memory_knowledge, profile

from cycle_validation.checks.base import CheckContext
from cycle_validation.checks.dr_recommendation import check_dr_recommendation, dr_tasks
from cycle_validation.checks.machine_tag import check_machine_tags
from cycle_validation.checks.process_sheet import (
    check_process_sheets,
    engine_family,
    treatment_for_family,
)
from cycle_validation.checks.source import check_sources
from cycle_validation.checks.task_code import check_task_codes
from cycle_validation.domain.check import CheckResult, Reason, Verdict
from cycle_validation.domain.cycle import Cycle
from cycle_validation.extract.from_file import load_cycle
from cycle_validation.kb.memory import IndexedKnowledgeBase
from cycle_validation.kb.port import (
    DocumentInfo,
    DrRecommendation,
    KnowledgeBase,
    ProcessSheetEntry,
    TaskLocation,
)
from cycle_validation.resolve.dr import (
    DrSelectors,
    SelectorError,
    normalize_conditions,
    parse_selectors,
    serial_in_text,
    with_serial_from_text,
)
from cycle_validation.services.machines import (
    MachineRegistry,
    StaticMachineRegistry,
    UnavailableMachineRegistry,
)
from cycle_validation.verdict.consolidate import is_blocking_failure

ACTIVE = StaticMachineRegistry(["TM-1001", "TM-2002"])


def _ctx(
    cycle: Cycle | None = None,
    *,
    kb: KnowledgeBase | None = None,
    machines: MachineRegistry = ACTIVE,
    profile_name: str = "mos",
    selectors: DrSelectors | None = None,
) -> CheckContext:
    return CheckContext(
        cycle=cycle or load_cycle(EXAMPLE_DIR / "ciclo.json"),
        kb=kb or memory_knowledge(),
        machines=machines,
        profile=profile(profile_name),
        selectors=selectors,
    )


def _reasons(results: list[CheckResult]) -> list[Reason]:
    return [result.reason for result in results]


def test_sources() -> None:
    results = check_sources(_ctx())
    assert _reasons(results) == [Reason.VERIFICATO, Reason.VERIFICATO, Reason.FONTE_ASSENTE]
    evidence = results[1].evidence[0]
    assert (evidence.document_key, evidence.version, evidence.page, evidence.line) == (
        "MAN-DEMO-72",
        "Rev. 12",
        2,
        17,
    )
    assert evidence.quote.startswith("TASK 72-00-01-350-003")
    assert results[2].verdict is Verdict.WARNING


def test_source_task_missing_in_existing_manual() -> None:
    cycle = Cycle.model_validate(
        {"sources": [{"manual": "MD75", "task": "72-00-01-110-001"}], "operations": []}
    )
    result = check_sources(_ctx(cycle))[0]
    assert result.reason is Reason.FONTE_ASSENTE
    assert "MAN-DEMO-75" in result.rationale


def test_source_names_the_chapter_that_holds_the_task(tmp_path: Path) -> None:
    # Manuale diviso in capitoli: stesso codice, la versione è il capitolo (dati inventati).
    def chapter(name: str, text: str) -> DocumentInfo:
        path = tmp_path / f"{name}.md"
        path.write_text(text, "utf-8")
        return DocumentInfo(key=f"MAN_X_{name}", path=path, code="MAN-X", version=name)

    first = chapter("ch10", "<!-- page 1 -->\nTASK 10-00-00-100-001\n1. a\n")
    other = chapter("ch20", "<!-- page 1 -->\naltro\n")
    task = TaskLocation(
        manual_key=first.key, task="10-00-00-100-001", document=first, line_start=2, line_end=3
    )
    kb = IndexedKnowledgeBase("v", documents=[first, other], tasks=[task])
    cycle = Cycle.model_validate(
        {"sources": [{"manual": "MAN-X", "task": "10-00-00-100-001"}], "operations": []}
    )
    result = check_sources(_ctx(cycle, kb=kb))[0]
    assert result.reason is Reason.VERIFICATO
    assert "MAN_X_ch10" in result.rationale


def test_source_without_task_checks_only_the_manual() -> None:
    cycle = Cycle.model_validate({"sources": [{"manual": "MD75"}], "operations": []})
    assert _reasons(check_sources(_ctx(cycle))) == [Reason.VERIFICATO]


def test_task_codes() -> None:
    results = check_task_codes(_ctx())
    assert _reasons(results) == [
        Reason.VERIFICATO,
        Reason.VERIFICATO,
        Reason.VERIFICATO,
        Reason.FONTE_ASSENTE,
    ]
    assert "72-00-01-999-009" in results[3].rationale


def test_task_code_absent_field() -> None:
    cycle = Cycle.model_validate({"operations": [{"operation_number": "1"}]})
    assert _reasons(check_task_codes(_ctx(cycle))) == [Reason.CAMPO_ASSENTE]


def test_task_code_is_searched_in_linked_manuals_only() -> None:
    cycle = Cycle.model_validate(
        {
            "sources": [
                {"manual": "MD72", "repair_code": "R-01"},
                {"manual": "MD75", "repair_code": "R-02"},
            ],
            "operations": [
                {"operation_number": "1", "repair_code": "R-02", "task_codes": "72-00-01-110-001"},
                {"operation_number": "2", "repair_code": "R-09", "task_codes": "72-00-01-110-001"},
            ],
        }
    )
    assert _reasons(check_task_codes(_ctx(cycle))) == [Reason.FONTE_ASSENTE, Reason.VERIFICATO]


def test_machine_tags() -> None:
    results = check_machine_tags(_ctx())
    assert _reasons(results) == [
        Reason.VERIFICATO,
        Reason.VERIFICATO,
        Reason.MACCHINA_NON_ATTIVA,
        Reason.CAMPO_ASSENTE,
    ]
    assert results[2].verdict is Verdict.ERRATO


def test_machine_active_but_unknown_to_tm() -> None:
    cycle = Cycle.model_validate({"operations": [{"operation_number": "1", "machine_tag": "X-9"}]})
    ctx = _ctx(cycle, machines=StaticMachineRegistry(["X-9"]))
    assert _reasons(check_machine_tags(ctx)) == [Reason.FONTE_ASSENTE]


def test_a_machine_found_nowhere_is_an_unknown_tag_warning() -> None:
    cycle = Cycle.model_validate({"operations": [{"operation_number": "1", "machine_tag": "X-9"}]})
    (result,) = check_machine_tags(_ctx(cycle, machines=StaticMachineRegistry(["TM-1001"])))
    assert (result.reason, result.verdict) == (Reason.TARGA_SCONOSCIUTA, Verdict.WARNING)
    assert "Targa sconosciuta" in result.rationale and "X-9" in result.rationale


def test_machine_registry_unavailable_is_a_warning() -> None:
    results = check_machine_tags(_ctx(machines=UnavailableMachineRegistry("Redshift giù")))
    assert results[0].reason is Reason.ERRORE_TECNICO
    assert "Redshift giù" in results[0].rationale
    assert results[3].reason is Reason.CAMPO_ASSENTE


def test_machine_registry_switched_off_is_not_applicable() -> None:
    """Sul PC (`MACHINES_SOURCE=nessuna`) il registro è spento: N/A, non WARNING."""
    off = UnavailableMachineRegistry("non collegato", disabled=True)
    results = check_machine_tags(_ctx(machines=off))
    assert (results[0].reason, results[0].verdict) == (
        Reason.CONTROLLO_SPENTO,
        Verdict.NON_APPLICABILE,
    )
    assert "non collegato" in results[0].rationale


def test_process_sheets() -> None:
    results = check_process_sheets(_ctx())
    assert _reasons(results) == [
        Reason.VERIFICATO,
        Reason.ESCLUSO_DA_REGOLA,
        Reason.CAMPO_ASSENTE,
        Reason.SCHEDA_ALTRO_MOTORE,  # H18 nella base dal 27-11 notte
    ]
    assert "LEAP" in results[3].rationale


def test_process_sheet_unknown() -> None:
    """Una scheda che l'indice non ha: ERRATO se l'indice ha altre schede con le stesse lettere
    (H18, nella base dal 27-11 notte), altrimenti WARNING (forse manca dalla conoscenza)."""
    cycle = Cycle.model_validate(
        {"operations": [{"operation_number": "1", "process_sheet": "SP-9999"}]}
    )
    assert _reasons(check_process_sheets(_ctx(cycle))) == [Reason.SCHEDA_INESISTENTE]
    other = Cycle.model_validate(
        {"operations": [{"operation_number": "1", "process_sheet": "QZ-9999"}]}
    )
    assert _reasons(check_process_sheets(_ctx(other))) == [Reason.FONTE_ASSENTE]


def test_a_special_process_without_sheet_is_a_warning_never_an_error() -> None:
    """P6 (26-11, I9): nei processi speciali la scheda è obbligatoria. Senza scheda: WARNING
    «scheda forse mancante», mai ERRATO. Le altre operazioni senza scheda restano N/A."""
    from cycle_validation.config import AgentSettings

    cycle = Cycle.model_validate(
        {
            "operations": [
                {
                    "operation_number": "1",
                    "operation_description": "APPLICARE LUBRIFICANTE SECCO / APPLY DRY FILM",
                },
                {"operation_number": "2", "operation_description": "FPI DELLA ZONA / FPI AREA"},
                {"operation_number": "3", "operation_description": "PULIRE / CLEAN"},
            ]
        }
    )
    results = check_process_sheets(_ctx(cycle))
    assert _reasons(results) == [
        Reason.SCHEDA_FORSE_MANCANTE,
        Reason.SCHEDA_FORSE_MANCANTE,
        Reason.CAMPO_ASSENTE,
    ]
    assert results[0].verdict is Verdict.WARNING
    assert "lubrificante secco" in results[0].rationale.casefold()
    off = CheckContext(
        cycle=cycle,
        kb=memory_knowledge(),
        machines=ACTIVE,
        profile=profile("mos"),
        agent=AgentSettings(special_process_sheet=False),
    )
    assert _reasons(check_process_sheets(off)) == [Reason.CAMPO_ASSENTE] * 3


def test_a_sheet_is_found_without_hyphens_and_spaces() -> None:
    # come nel servizio precedente: CPEC522-BR = CPEC522BR (e gli spazi non contano)
    kb = IndexedKnowledgeBase(
        "t", process_sheets=[ProcessSheetEntry(code="CPEC 522-BR", edition="1", treatment="X")]
    )
    for code in ("CPEC522BR", "CPEC 522-BR", "cpec522-br"):
        assert kb.find_process_sheet(code) is not None, code
    assert kb.find_process_sheet("CPEC523BR") is None


def test_process_sheet_without_engine_model_checks_presence_only() -> None:
    cycle = Cycle.model_validate(
        {"operations": [{"operation_number": "1", "process_sheet": "SP-0202"}]}
    )
    assert _reasons(check_process_sheets(_ctx(cycle))) == [Reason.VERIFICATO]


def test_applicability_is_claimed_only_when_the_engine_family_was_compared() -> None:
    known = check_process_sheets(_ctx())[0]
    assert "applicabile alla famiglia GENX" in known.rationale
    cycle = Cycle.model_validate(
        {
            "engine_model": "MOTORE-SCONOSCIUTO",
            "operations": [{"operation_number": "1", "process_sheet": "SP-0202"}],
        }
    )
    unknown = check_process_sheets(_ctx(cycle))[0]
    assert "applicabilità non verificata" in unknown.rationale
    assert "e applicabile" not in unknown.rationale


def test_process_sheet_not_verified_for_ej200() -> None:
    results = check_process_sheets(_ctx(profile_name="ej200"))
    assert results[0].reason is Reason.NON_VERIFICATO_PER_PROFILO
    assert results[2].reason is Reason.CAMPO_ASSENTE


def test_engine_family() -> None:
    assert engine_family("genx-1b", ["GENX", "LEAP"]) == "GENX"
    assert engine_family("CFM56", ["GENX", "LEAP"]) is None
    assert engine_family(None, ["GENX"]) is None


@pytest.mark.parametrize(
    "check", [check_sources, check_task_codes, check_machine_tags, check_process_sheets]
)
def test_unreachable_knowledge_is_a_warning_not_an_error(check: object) -> None:
    all_active = StaticMachineRegistry(["TM-1001", "TM-2002", "TM-3003"])
    results = check(_ctx(kb=BrokenKnowledge(), machines=all_active))  # type: ignore[operator]
    assert all(result.verdict is not Verdict.ERRATO for result in results)
    assert Reason.ERRORE_TECNICO in _reasons(results)


# --- documenti con stato (pubblicazioni EJ200) ---------------------------------------


def _publications(tmp_path: Path) -> IndexedKnowledgeBase:
    def doc(key: str, **extra: object) -> DocumentInfo:
        path = tmp_path / f"{key}.md"
        path.write_text(f"<!-- page 1 -->\nPubblicazione {key}\nCodice DM-AA-01 citato\n", "utf-8")
        return DocumentInfo(key=key, path=path, **extra)  # type: ignore[arg-type]

    return IndexedKnowledgeBase(
        "pubblicazioni",
        documents=[
            doc("RN-1_i2", code="RN-1", kind="RN", version="002"),
            doc("RN-1_i3", code="RN-1", kind="RN", version="003"),
            doc("EF-7", kind="EF", version="001", partial=True),
            doc("RDR-5", kind="RDR", version="001", published=False),
            doc("RDR-9A", kind="RDR", version="001"),
            doc("RDR-9B", kind="RDR", version="001"),
            doc("RN-2", kind="RN"),
            doc("RN-3", kind="RN", uncertain=("copie_diverse_per_contenuto",)),
            doc("RN-4", kind="RN", uncertain=("copie_diverse_per_tipo",)),
        ],
        aliases={"RDR-9A": ["RDR-9"], "RDR-9B": ["RDR-9"]},
    )


def _source_cycle(manual: str, issue: str | None = None) -> Cycle:
    return Cycle.model_validate({"sources": [{"manual": manual, "issue": issue}], "operations": []})


@pytest.mark.parametrize(
    ("manual", "issue", "reason"),
    [
        ("RN-1", None, Reason.VERIFICATO),
        ("RN-1", "003", Reason.VERIFICATO),
        ("RN-1", "002", Reason.VERSIONE_DIVERSA),
        ("RN-2", "001", Reason.VERSIONE_DIVERSA),
        ("EF-7", None, Reason.PUBBLICAZIONE_PARZIALE),
        ("RDR-5", None, Reason.FONTE_ASSENTE),
        ("RDR-9", None, Reason.RIFERIMENTO_AMBIGUO),
        ("XX-0", None, Reason.FONTE_ASSENTE),
        ("RN-3", None, Reason.DATO_INCERTO),
        ("RN-4", None, Reason.VERIFICATO),
    ],
)
def test_publication_states(tmp_path: Path, manual: str, issue: str | None, reason: Reason) -> None:
    ctx = _ctx(_source_cycle(manual, issue), kb=_publications(tmp_path), profile_name="ej200")
    result = check_sources(ctx)[0]
    assert result.reason is reason
    if reason is Reason.VERIFICATO and manual == "RN-1":
        assert result.evidence[0].document_key == "RN-1_i3"


def test_doubts_on_a_publication_are_written_in_the_rationale(tmp_path: Path) -> None:
    kb = _publications(tmp_path)
    for manual, words in (("RN-3", "contenuto diverso"), ("RN-4", "tipo diverso")):
        ctx = _ctx(_source_cycle(manual), kb=kb, profile_name="ej200")
        assert words in check_sources(ctx)[0].rationale


def test_codes_in_cited_documents(tmp_path: Path) -> None:
    cycle = Cycle.model_validate(
        {
            "sources": [{"manual": "RN-1"}],
            "operations": [
                {"operation_number": "1", "task_codes": ["DM-AA-01"]},
                {"operation_number": "2", "task_codes": ["DM-ZZ-99"]},
            ],
        }
    )
    results = check_task_codes(_ctx(cycle, kb=_publications(tmp_path), profile_name="ej200"))
    assert _reasons(results) == [Reason.VERIFICATO, Reason.EVIDENZA_NON_TROVATA]
    assert results[0].evidence[0].line == 3


@pytest.mark.parametrize(
    ("code", "reason"),
    [
        ("DM-AA-01", Reason.VERIFICATO),
        ("dm - aa - 01", Reason.VERIFICATO),
        ("AA-01", Reason.VERIFICATO),  # componenti intere di un codice più lungo
        ("DM-AA-0", Reason.EVIDENZA_NON_TROVATA),  # pezzo di un codice più lungo
        ("M-AA-01", Reason.EVIDENZA_NON_TROVATA),
        ("A-0", Reason.EVIDENZA_NON_TROVATA),
    ],
)
def test_a_code_is_found_whole_not_as_a_fragment_of_another(
    tmp_path: Path, code: str, reason: Reason
) -> None:
    cycle = Cycle.model_validate(
        {
            "sources": [{"manual": "RN-1"}],
            "operations": [{"operation_number": "1", "task_codes": [code]}],
        }
    )
    results = check_task_codes(_ctx(cycle, kb=_publications(tmp_path), profile_name="ej200"))
    assert _reasons(results) == [reason]


def test_a_code_broken_across_two_lines_is_found_with_its_line(tmp_path: Path) -> None:
    kb = _publications(tmp_path)
    path = tmp_path / "RN-2.md"
    path.write_text("<!-- page 1 -->\nVedere il modulo DM-BB-\n02 per i limiti.\n", "utf-8")
    cycle = Cycle.model_validate(
        {
            "sources": [{"manual": "RN-2"}],
            "operations": [{"operation_number": "1", "task_codes": ["DM-BB-02"]}],
        }
    )
    results = check_task_codes(_ctx(cycle, kb=kb, profile_name="ej200"))
    assert _reasons(results) == [Reason.VERIFICATO]
    assert results[0].evidence[0].line == 2


def test_codes_without_available_documents(tmp_path: Path) -> None:
    cycle = Cycle.model_validate(
        {
            "sources": [{"manual": "RDR-5"}],
            "operations": [{"operation_number": "1", "task_codes": ["DM-AA-01"]}],
        }
    )
    results = check_task_codes(_ctx(cycle, kb=_publications(tmp_path), profile_name="ej200"))
    assert _reasons(results) == [Reason.FONTE_ASSENTE]


# --- DR ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("value", "expected"),
    [(1, [1]), ([1, 2], [1, 2]), ("1", [1]), ("1,2", [1, 2]), ("[1, 2]", [1, 2]), ("2, 2", [2])],
)
def test_conditions_are_normalized(value: object, expected: list[int]) -> None:
    assert normalize_conditions(value) == expected


@pytest.mark.parametrize("value", [None, "", "a", "[1", [1, "x"], True, 1.5, []])
def test_invalid_conditions_are_rejected(value: object) -> None:
    with pytest.raises(SelectorError):
        normalize_conditions(value)


@pytest.mark.parametrize("value", ["--1", "1,--2", "²", '["³"]'])
def test_malformed_numbers_are_a_selector_error_not_a_crash(value: str) -> None:
    with pytest.raises(SelectorError):
        normalize_conditions(value)


def test_selectors_policy() -> None:
    assert parse_selectors(is_dr=False) is None
    assert parse_selectors(is_dr=True, serial_number=" SN-1 ", conditions="1,2") == DrSelectors(
        "SN-1", (1, 2)
    )
    with pytest.raises(SelectorError, match="solo per i cicli DR"):
        parse_selectors(is_dr=False, serial_number="SN-1")
    # dal 22-11-2026 serial number e condition sono facoltativi
    assert parse_selectors(is_dr=True) == DrSelectors()
    assert parse_selectors(is_dr=True, conditions=[1]) == DrSelectors(None, (1,))
    assert parse_selectors(is_dr=True, serial_number="SN-1", conditions="") == DrSelectors("SN-1")
    with pytest.raises(SelectorError, match="non valida"):
        parse_selectors(is_dr=True, serial_number="SN-1", conditions="uno")


def test_serial_number_is_read_from_the_print() -> None:
    text = "NOTE\nD.R. CASE #00000001 APPLY ON S/N AAAA1CCC\nS/N DEL PARTICOLARE"
    assert serial_in_text(text) == "AAAA1CCC"
    assert serial_in_text("S/N: \nS/N DEL PARTICOLARE") is None
    # due serial number diversi: non si sceglie
    assert serial_in_text("S/N AAAA1CCC e S/N BBBB2DDD") is None
    assert with_serial_from_text(DrSelectors(None, (2,)), text) == DrSelectors("AAAA1CCC", (2,))
    # quello indicato da chi carica vince sulla stampa
    assert with_serial_from_text(DrSelectors("SN-1"), text) == DrSelectors("SN-1")


@pytest.mark.parametrize(
    "text",
    [
        "APPLY ON S/N:AAAA1CCC",
        "APPLY ON S / N. AAAA1CCC",
        "APPLY ON S/N # AAAA1CCC",
        "APPLY ON S/N\nAAAA1CCC",
    ],
)
def test_serial_number_in_other_spellings(text: str) -> None:
    assert serial_in_text(text) == "AAAA1CCC"


def test_serial_number_with_a_dash_and_dotted_header_field() -> None:
    assert serial_in_text("P/N ......  S/N ......\nAPPLY ON S/N AAAA-1CCC") == "AAAA-1CCC"


def test_more_serial_numbers_keep_the_one_with_recommendations() -> None:
    """Un altro numero dopo la scritta S/N (testata, altre note): vale quello noto al DR."""
    text = "S/N 20261121\nAPPLY ON S/N AAAA1CCC"
    assert serial_in_text(text) is None
    assert serial_in_text(text, lambda serial: serial == "AAAA1CCC") == "AAAA1CCC"
    assert serial_in_text(text, lambda serial: False) is None
    assert serial_in_text(text, lambda serial: True) is None
    found = with_serial_from_text(DrSelectors(None, (1,)), text, lambda s: s == "AAAA1CCC")
    assert found == DrSelectors("AAAA1CCC", (1,))


def _dr(serial: str, *conditions: int, kb: KnowledgeBase | None = None) -> CheckResult:
    ctx = _ctx(kb=kb, profile_name="dr", selectors=DrSelectors(serial, conditions))
    return check_dr_recommendation(ctx)[0]


def test_dr_multiple_recommendations_are_disambiguated_by_condition() -> None:
    result = _dr("SN-DEMO-001", 1)
    assert result.reason is Reason.VERIFICATO
    assert "DR-DEMO-01" in result.rationale


def test_dr_accept_as_is_stops_the_cycle_like_reject() -> None:
    # come nella v1: con "accept as is" un ciclo di riparazione non dovrebbe esistere
    result = _dr("SN-DEMO-001", 2)
    assert (result.reason, result.verdict) == (Reason.DR_NON_APPLICABILE, Verdict.ERRATO)
    assert "così com'è" in result.rationale
    assert is_blocking_failure(result)
    assert dr_tasks(memory_knowledge(), DrSelectors("SN-DEMO-001", (2,))) == []


def test_dr_accept_as_is_written_differently_is_recognised() -> None:
    for written in ("Accept-as-is", "ACCEPT AS IS.", "Use as is"):
        kb = IndexedKnowledgeBase(
            "t",
            dr_recommendations=[
                DrRecommendation(serial_number="SN-X", conditions=(1,), procedure=written)
            ],
        )
        assert _dr("SN-X", 1, kb=kb).reason is Reason.DR_NON_APPLICABILE, written


def test_dr_repair_and_accept_as_is_together_keep_the_repair() -> None:
    kb = IndexedKnowledgeBase(
        "t",
        dr_recommendations=[
            DrRecommendation(
                serial_number="SN-X", conditions=(1,), procedure="Repair", tasks=("70-1",)
            ),
            DrRecommendation(serial_number="SN-X", conditions=(2,), procedure="Accept as is"),
        ],
    )
    result = _dr("SN-X", 1, 2, kb=kb)
    assert result.reason is Reason.VERIFICATO
    assert "Saltata la parte senza riparazione" in result.rationale
    assert dr_tasks(kb, DrSelectors("SN-X", (1, 2))) == [(None, "70-1")]


def _two(second: str) -> IndexedKnowledgeBase:
    return IndexedKnowledgeBase(
        "t",
        dr_recommendations=[
            DrRecommendation(
                serial_number="SN-X", conditions=(1,), procedure="Repair", tasks=("70-1",)
            ),
            DrRecommendation(
                serial_number="SN-X", conditions=(2,), procedure=second, tasks=("70-2",)
            ),
        ],
    )


def test_dr_without_condition_and_only_repairs_uses_them_all() -> None:
    kb = _two("Repair")
    result = _dr("SN-X", kb=kb)
    assert (result.reason, result.verdict) == (Reason.VERIFICATO, Verdict.CORRETTO)
    assert dr_tasks(kb, DrSelectors("SN-X")) == [(None, "70-1"), (None, "70-2")]


@pytest.mark.parametrize("second", ["Accept as is", "Reject"])
def test_dr_without_condition_and_mixed_dispositions_is_a_warning(second: str) -> None:
    kb = _two(second)
    result = _dr("SN-X", kb=kb)
    assert (result.reason, result.verdict) == (Reason.DR_NON_VERIFICATA, Verdict.WARNING)
    assert second in result.rationale
    assert not is_blocking_failure(result)
    # si prosegue con la sola riparazione come riferimento
    assert dr_tasks(kb, DrSelectors("SN-X")) == [(None, "70-1")]


def test_dr_without_condition_and_no_repair_at_all_stops() -> None:
    kb = IndexedKnowledgeBase(
        "t",
        dr_recommendations=[
            DrRecommendation(serial_number="SN-X", conditions=(1,), procedure="Reject"),
            DrRecommendation(serial_number="SN-X", conditions=(2,), procedure="Accept as is"),
        ],
    )
    assert _dr("SN-X", kb=kb).reason is Reason.DR_NON_APPLICABILE


def test_dr_reject_stops_even_with_a_single_recommendation() -> None:
    result = _dr("SN-DEMO-002", 9)
    assert (result.reason, result.verdict) == (Reason.DR_NON_APPLICABILE, Verdict.ERRATO)
    assert is_blocking_failure(result)


def test_dr_no_recommendation_for_serial() -> None:
    assert _dr("SN-ASSENTE", 1).reason is Reason.DR_NESSUNA_CORRISPONDENZA


def test_dr_no_recommendation_for_condition() -> None:
    result = _dr("SN-DEMO-001", 7)
    assert result.reason is Reason.DR_NESSUNA_CORRISPONDENZA
    assert "2 recommendation" in result.rationale


def test_dr_with_an_empty_condition_list_among_several_is_ambiguous_and_stops() -> None:
    kb = IndexedKnowledgeBase(
        "t",
        dr_recommendations=[
            DrRecommendation(serial_number="SN-X", conditions=(1,), procedure="Repair"),
            DrRecommendation(
                serial_number="SN-X", conditions=(), procedure="Repair", reference="DR-VUOTA"
            ),
        ],
    )
    result = _dr("SN-X", 1, kb=kb)
    assert (result.reason, result.verdict) == (Reason.RIFERIMENTO_AMBIGUO, Verdict.WARNING)
    assert "DR-VUOTA" in result.rationale
    assert dr_tasks(kb, DrSelectors("SN-X", (1,))) == []
    # da sola, la recommendation senza condition vale per qualunque condition
    alone = IndexedKnowledgeBase(
        "t",
        dr_recommendations=[
            DrRecommendation(serial_number="SN-Y", conditions=(), procedure="Repair")
        ],
    )
    assert _dr("SN-Y", 3, kb=alone).reason is Reason.VERIFICATO


def test_dr_data_unavailable_is_a_warning() -> None:
    assert _dr("SN-DEMO-001", 1, kb=BrokenKnowledge()).reason is Reason.ERRORE_TECNICO


def test_dr_without_serial_number_is_a_warning_that_does_not_block() -> None:
    for selectors in (None, DrSelectors(None, (1,))):
        result = check_dr_recommendation(_ctx(profile_name="dr", selectors=selectors))[0]
        assert (result.reason, result.verdict) == (Reason.DR_NON_VERIFICATA, Verdict.WARNING)
        assert not is_blocking_failure(result)


def test_dr_tasks_feed_the_context() -> None:
    kb = memory_knowledge()
    assert dr_tasks(kb, DrSelectors("SN-DEMO-001", (1,))) == [("MAN-DEMO-72", "72-00-01-350-003")]
    assert dr_tasks(kb, DrSelectors("SN-DEMO-001", (2,))) == []
    assert dr_tasks(kb, None) == []


# --- voci incerte nell'indice (uncertainty.json di knowledge-index) -------------------


def _doubtful(
    *,
    tags: dict[str, tuple[str, ...]] | None = None,
    sheets: dict[str, tuple[str, ...]] | None = None,
    dr: dict[tuple[str, tuple[int, ...]], tuple[str, ...]] | None = None,
) -> IndexedKnowledgeBase:
    """La knowledge base dell'esempio con alcuni motivi di incertezza sulle voci."""
    base = memory_knowledge()
    tags, sheets, dr = tags or {}, sheets or {}, dr or {}
    return IndexedKnowledgeBase(
        base.version,
        documents=[DOC_72, DOC_75],
        tasks=[base.find_task("MAN-DEMO-72", "72-00-01-350-003")],  # type: ignore[list-item]
        machine_tags=[
            item.model_copy(update={"uncertain": tags.get(item.tag, ())})
            for item in base.machine_tags()
        ],
        process_sheets=[
            item.model_copy(update={"uncertain": sheets.get(code, ())})
            for code in ("SP-0101", "SP-0202")
            if (item := base.find_process_sheet(code)) is not None
        ],
        dr_recommendations=[
            item.model_copy(update={"uncertain": dr.get((serial, item.conditions), ())})
            for serial in ("SN-DEMO-001", "SN-DEMO-002")
            for item in base.find_dr_recommendations(serial)
        ],
    )


def test_tag_from_a_partial_record_is_a_warning() -> None:
    kb = _doubtful(tags={"TM-1001": ("da_record_parziale",)})
    result = check_machine_tags(_ctx(kb=kb))[0]
    assert result.reason is Reason.DATO_INCERTO
    assert result.verdict is Verdict.WARNING
    assert "letto solo in parte" in result.rationale


def test_tag_with_alternative_functions_exists_but_says_so() -> None:
    kb = _doubtful(tags={"TM-1001": ("valori_alternativi",)})
    result = check_machine_tags(_ctx(kb=kb))[0]
    assert result.reason is Reason.VERIFICATO
    assert "valori alternativi" in result.rationale


def test_sheet_from_a_previous_edition_is_a_warning() -> None:
    kb = _doubtful(sheets={"SP-0101": ("edizione_precedente_per_blocco",)})
    result = check_process_sheets(_ctx(kb=kb))[0]
    assert result.reason is Reason.DATO_INCERTO
    assert "edizione precedente" in result.rationale


def test_sheet_with_alternative_values_is_verified_with_a_note() -> None:
    kb = _doubtful(sheets={"SP-0101": ("valori_alternativi",)})
    result = check_process_sheets(_ctx(kb=kb))[0]
    assert result.reason is Reason.VERIFICATO
    assert "valori alternativi" in result.rationale


def test_unknown_doubt_is_treated_as_a_warning() -> None:
    kb = _doubtful(sheets={"SP-0101": ("motivo_nuovo",)})
    result = check_process_sheets(_ctx(kb=kb))[0]
    assert result.reason is Reason.DATO_INCERTO
    assert "motivo_nuovo" in result.rationale


def test_inapplicable_sheet_stays_inapplicable_even_if_doubtful() -> None:
    kb = _doubtful(sheets={"SP-0202": ("da_record_parziale",)})
    assert check_process_sheets(_ctx(kb=kb))[3].reason is Reason.EVIDENZA_NON_TROVATA


def test_doubtful_dr_does_not_block_the_cycle_but_says_so() -> None:
    kb = _doubtful(dr={("SN-DEMO-001", (1,)): ("da_record_parziale", "manuale_parziale")})
    result = _dr("SN-DEMO-001", 1, kb=kb)
    assert result.reason is Reason.VERIFICATO
    assert "letto solo in parte" in result.rationale
    assert "manuale collegato" in result.rationale


@pytest.mark.parametrize(
    ("treatment", "family", "expected"),
    [
        ("A [GENX]; B [LEAP]", "GENX", "A"),
        ("A [GENX, LEAP]; B [LEAP]", "genx", "A"),
        ("A [GENX] (ed. 2); B [LEAP] (ed. 1)", "LEAP", "B (ed. 1)"),
        ("A [GENX]; B [GENX]; C [LEAP]", "GENX", "A; B"),
        ("A [GENX]; B [LEAP]", None, "A [GENX]; B [LEAP]"),
        ("A [GENX]; B [LEAP]", "CFM56", "A [GENX]; B [LEAP]"),
        ("A; B", "GENX", "A; B"),
        ("Lavaggio [fase 2]", "GENX", "Lavaggio [fase 2]"),
    ],
)
def test_treatment_for_family(treatment: str, family: str | None, expected: str) -> None:
    assert treatment_for_family(treatment, family) == expected


def test_a_task_code_missing_where_its_family_is_is_errato(tmp_path: Path) -> None:
    from cycle_validation.domain.check import Verdict
    from cycle_validation.kb.memory import IndexedKnowledgeBase
    from cycle_validation.kb.port import DocumentInfo

    path = tmp_path / "spm.md"
    path.write_text(
        "TASK 70-11-00-350-002 Raccordatura\n(1) SUBTASK 70-11-00-350-029 Rimozione\nTesto.\n",
        "utf-8",
    )
    kb = IndexedKnowledgeBase(
        "v", documents=[DocumentInfo(key="spm", path=path, code="SPM-X", kind="SPM")]
    )
    cycle = Cycle.model_validate(
        {
            "sources": [{"manual": "MAN-X"}],
            "operations": [
                {"operation_number": "1", "task_codes": ["70-11-00-350-029"]},
                {"operation_number": "2", "task_codes": ["70-11-00-350-035"]},
                {"operation_number": "3", "task_codes": ["70-99-00-350-001"]},
            ],
        }
    )
    results = check_task_codes(_ctx(cycle, kb=kb))
    assert _reasons(results) == [
        Reason.VERIFICATO,
        Reason.TASK_INESISTENTE,
        Reason.FONTE_ASSENTE,
    ]
    assert results[1].verdict == Verdict.ERRATO
    assert "70-11-00-350-029" in results[1].rationale


def test_the_same_operation_with_two_machines_is_errato_even_with_the_registry_off() -> None:
    """H19 (27-11 sera): la stessa operazione con targhe diverse su due pagine; vale anche sul
    PC, dove il registro delle macchine è spento."""
    cycle = load_cycle(EXAMPLE_DIR / "ciclo.json")
    first = cycle.operations[0].model_copy(update={"other_machine_tags": ["TM-9999"]})
    cycle = cycle.model_copy(update={"operations": [first, *cycle.operations[1:]]})
    off = UnavailableMachineRegistry("non collegato", disabled=True)
    results = check_machine_tags(_ctx(cycle, machines=off))
    assert (results[0].reason, results[0].verdict) == (Reason.MACCHINE_DIVERSE, Verdict.ERRATO)
    assert "TM-9999" in results[0].rationale
    assert results[1].reason is Reason.CONTROLLO_SPENTO


def _with_header_task(header: str | None, original: str | None) -> Cycle:
    from cycle_validation.domain.cycle import Operation, Source

    return Cycle(
        repair_code="A1",
        sources=[Source(manual="SPM-DEMO", task=header, repair_code="A1")],
        operations=[
            Operation(
                operation_number="030",
                operation_description="RACCORDARE / BLEND",
                repair_code="A1",
                original_task=original,
            )
        ],
    )


@pytest.mark.parametrize(
    ("header", "original", "expected"),
    [
        # stessa famiglia, ultima parte diversa: la stampa si contraddice
        ("70-11-00-350-002", "70-11-00-350-003", Reason.TASK_DIVERSO_DALLA_TESTATA),
        # uguale alla testata, o di un altro processo (attacco chimico), o incompleto: niente
        ("70-11-00-350-002", "70-11-00-350-002", Reason.CAMPO_ASSENTE),
        ("70-11-00-350-002", "70-99-00-110-001", Reason.CAMPO_ASSENTE),
        ("70-11-00-350-002", "70-11-00", Reason.CAMPO_ASSENTE),
        # testata senza task: niente da confrontare
        (None, "70-11-00-350-003", Reason.CAMPO_ASSENTE),
    ],
)
def test_the_task_next_to_the_operation_is_compared_with_the_header(
    header: str | None, original: str | None, expected: Reason
) -> None:
    """H17 (27-11 sera): nelle stampe con errori il task della colonna SP.ORIG era cambiato di
    una cifra; esiste nel manuale, quindi «task inesistente» non lo vedeva."""
    results = check_task_codes(_ctx(_with_header_task(header, original)))
    assert results[0].reason is expected
    if expected is Reason.TASK_DIVERSO_DALLA_TESTATA:
        assert results[0].verdict is Verdict.ERRATO
        assert "70-11-00-350-003" in results[0].rationale


def test_the_header_task_of_another_repair_is_not_compared() -> None:
    cycle = _with_header_task("70-11-00-350-002", "70-11-00-350-003")
    other = cycle.operations[0].model_copy(update={"repair_code": "A3"})
    results = check_task_codes(_ctx(cycle.model_copy(update={"operations": [other]})))
    assert results[0].reason is Reason.CAMPO_ASSENTE


# H18 (27-11 sera): la scheda coerente con l'operazione, con `sheet_consistency`. Codici e
# trattamenti inventati.
def _sheet_ctx(cycle: Cycle, kb: KnowledgeBase, *, strict: bool = True) -> CheckContext:
    from cycle_validation.config import AgentSettings

    return CheckContext(
        cycle=cycle,
        kb=kb,
        machines=ACTIVE,
        profile=profile("mos"),
        agent=AgentSettings(sheet_consistency=strict),
    )


def _sheet_cycle(description: str, sheet: str, task: str | None = None) -> Cycle:
    return Cycle.model_validate(
        {
            "engine_model": "GENX-1B",
            "sources": [{"manual": "MAN-X", "task": "70-11-00-350-001"}],
            "operations": [
                {
                    "operation_number": "040",
                    "operation_description": description,
                    "process_sheet": sheet,
                    "original_task": task,
                }
            ],
        }
    )


SHEETS = [
    ProcessSheetEntry(code="ZZ100-AA", treatment="etch gamma TiAl class I", engine_families=()),
    ProcessSheetEntry(code="ZZ105-AA", treatment="etch nickel-based alloys", engine_families=()),
    ProcessSheetEntry(code="QQ-05", treatment="penetrant level 3", engine_families=("GENX",)),
    ProcessSheetEntry(code="QQ-06", treatment="penetrant level 4", engine_families=("LEAP",)),
]
ETCH = "ATTACCO CHIMICO A TAMPONE. MATERIALE BASE: GAMMA TIAL / SWAB ETCH. BASE MATERIAL: TIAL"


def test_a_sheet_for_another_material_is_an_error() -> None:
    kb = IndexedKnowledgeBase("t", process_sheets=SHEETS)
    [right] = check_process_sheets(_sheet_ctx(_sheet_cycle(ETCH, "ZZ100-AA"), kb))
    assert right.reason is Reason.VERIFICATO
    [wrong] = check_process_sheets(_sheet_ctx(_sheet_cycle(ETCH, "ZZ105-AA"), kb))
    assert wrong.reason is Reason.SCHEDA_MATERIALE_DIVERSO
    assert wrong.verdict is Verdict.ERRATO
    assert "nichel" in wrong.rationale and "gamma TiAl" in wrong.rationale
    # spento (la base oggi): solo la presenza
    [off] = check_process_sheets(_sheet_ctx(_sheet_cycle(ETCH, "ZZ105-AA"), kb, strict=False))
    assert off.reason is Reason.VERIFICATO


def test_the_material_counts_only_where_the_description_states_it() -> None:
    kb = IndexedKnowledgeBase("t", process_sheets=SHEETS)
    other = "ATTACCO CHIMICO. NON USARE ATTREZZI IN ACCIAIO / SWAB ETCH"
    [result] = check_process_sheets(_sheet_ctx(_sheet_cycle(other, "ZZ105-AA"), kb))
    assert result.reason is Reason.VERIFICATO


def test_a_sheet_for_another_engine_is_an_error() -> None:
    kb = IndexedKnowledgeBase("t", process_sheets=SHEETS)
    fpi = "FPI LOCALE / LOCAL FPI"
    [right] = check_process_sheets(_sheet_ctx(_sheet_cycle(fpi, "QQ-05"), kb))
    assert right.reason is Reason.VERIFICATO
    [wrong] = check_process_sheets(_sheet_ctx(_sheet_cycle(fpi, "QQ-06"), kb))
    assert wrong.reason is Reason.SCHEDA_ALTRO_MOTORE
    [off] = check_process_sheets(_sheet_ctx(_sheet_cycle(fpi, "QQ-06"), kb, strict=False))
    assert off.reason is Reason.EVIDENZA_NON_TROVATA


def test_a_sheet_missing_among_others_with_the_same_prefix_is_an_error() -> None:
    kb = IndexedKnowledgeBase("t", process_sheets=SHEETS)
    [wrong] = check_process_sheets(_sheet_ctx(_sheet_cycle(ETCH, "ZZ101-AA"), kb))
    assert wrong.reason is Reason.SCHEDA_INESISTENTE
    assert "ZZ100-AA" in wrong.rationale
    [unknown] = check_process_sheets(_sheet_ctx(_sheet_cycle(ETCH, "WW-01"), kb))
    assert unknown.reason is Reason.FONTE_ASSENTE


def test_a_sheet_task_the_manual_does_not_have_is_an_error(tmp_path: Path) -> None:
    path = tmp_path / "man.md"
    path.write_text(
        "<!-- page 1 -->\nTASK 70-11-00-350-001\n1. a\nTASK 70-91-00-110-001\n2. b\n", "utf-8"
    )
    document = DocumentInfo(key="MAN_X", path=path, code="MAN-X", version="1")
    task = TaskLocation(
        manual_key="MAN_X", task="70-91-00-110-001", document=document, line_start=4, line_end=5
    )
    kb = IndexedKnowledgeBase("t", documents=[document], tasks=[task], process_sheets=SHEETS)
    good = _sheet_cycle(ETCH, "ZZ100-AA", "70-91-00-110-001")
    assert _reasons(check_process_sheets(_sheet_ctx(good, kb))) == [Reason.VERIFICATO]
    bad = _sheet_cycle(ETCH, "ZZ100-AA", "70-91-00-110-009")
    [wrong] = check_process_sheets(_sheet_ctx(bad, kb))
    assert wrong.reason is Reason.TASK_INESISTENTE
    assert "70-91-00-110-001" in wrong.rationale
    # un'altra famiglia, che il manuale non ha per niente: non si giudica
    other = _sheet_cycle(ETCH, "ZZ100-AA", "70-99-00-110-001")
    assert _reasons(check_process_sheets(_sheet_ctx(other, kb))) == [Reason.VERIFICATO]


def test_a_missing_sheet_says_it_is_missing() -> None:
    cycle = Cycle.model_validate(
        {"operations": [{"operation_number": "1", "operation_description": "FPI / FPI"}]}
    )
    [result] = check_process_sheets(_ctx(cycle))
    assert result.verdict is Verdict.WARNING
    assert result.rationale.startswith("Scheda mancante")


# MG48 (28-11): il task citato è di un altro stadio. Manuale e codici inventati.
def _stage_kb(tmp_path: Path, heading: str) -> KnowledgeBase:
    path = tmp_path / "MAN-ST.md"
    path.write_text(
        f"indice\nTASK 10-00-00-200-801\n{heading}\n1. Ispezionare le pale.\n", encoding="utf-8"
    )
    document = DocumentInfo(key="MAN-ST", path=path)
    task = TaskLocation(
        manual_key="MAN-ST", task="10-00-00-200-801", document=document, line_start=2, line_end=4
    )
    return IndexedKnowledgeBase("v", documents=[document], tasks=[task])


def _stage_cycle(title: str) -> Cycle:
    return Cycle.model_validate(
        {
            "cycle_description": title,
            "sources": [{"manual": "MAN-ST", "task": "10-00-00-200-801"}],
            "operations": [
                {"operation_number": "050", "task_codes": ["10-00-00-200-801"]},
            ],
        }
    )


@pytest.mark.parametrize(
    ("title", "heading", "expected"),
    [
        ("DEMO LPT BLADE STAGE 7", "STAGE 6 LPT BLADES - INSPECTION", Reason.TASK_ALTRO_STADIO),
        ("DEMO LPT BLADE STAGE 7", "STAGE 7 LPT BLADES - INSPECTION", Reason.VERIFICATO),
        ("DEMO LPT BLADE STAGE 7", "LPT BLADES STAGES 1 THRU 7", Reason.VERIFICATO),
        ("DEMO LPT BLADE STAGE 7", "LPT BLADES STAGES 6 AND 7", Reason.VERIFICATO),
        ("DEMO LPT BLADE STAGE 7", "LPT BLADES STAGES 1-4", Reason.TASK_ALTRO_STADIO),
        # un altro modulo (un altro pezzo) o un'intestazione senza stadi: non si confronta
        ("DEMO LPT BLADE STAGE 7", "HPT STAGE 1 NOZZLE", Reason.VERIFICATO),
        ("DEMO LPT BLADE STAGE 7", "LPT BLADES - INSPECTION", Reason.VERIFICATO),
        # ciclo senza stadio, o con due: non si controlla
        ("DEMO LPT BLADE", "STAGE 6 LPT BLADES", Reason.VERIFICATO),
        ("DEMO LPT BLADE STAGE 6 E STAGE 7", "STAGE 5 LPT BLADES", Reason.VERIFICATO),
    ],
)
def test_a_task_of_another_stage_is_errato(
    tmp_path: Path, title: str, heading: str, expected: Reason
) -> None:
    from cycle_validation.config import AgentSettings

    kb = _stage_kb(tmp_path, heading)
    ctx = _ctx(_stage_cycle(title), kb=kb)
    on = CheckContext(**{**ctx.__dict__, "agent": AgentSettings(task_stage_check=True)})
    result = check_task_codes(on)[0]
    assert result.reason is expected, result.rationale
    if expected is Reason.TASK_ALTRO_STADIO:
        assert result.verdict is Verdict.ERRATO and "stadio 7" in result.rationale
        assert result.evidence[0].line == 3
    # spento (la base): mai
    assert check_task_codes(ctx)[0].reason is Reason.VERIFICATO
