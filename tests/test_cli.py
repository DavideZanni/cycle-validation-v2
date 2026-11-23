import json
import shutil
from pathlib import Path

import pytest
from fakes import ScriptedSession
from kb_fixtures import EXAMPLE_DIR, EXAMPLE_KB
from support import example_cycle, scripted_judge, write_cycle_pdf
from typer.testing import CliRunner

from cycle_validation import cli

runner = CliRunner()


@pytest.fixture(autouse=True)
def fake_session(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        cli, "make_session", lambda settings, transcripts: ScriptedSession(scripted_judge)
    )


@pytest.fixture
def pdf(tmp_path: Path) -> Path:
    return write_cycle_pdf(tmp_path / "ciclo.pdf", example_cycle())


def base_args(pdf: Path, out: Path) -> list[str]:
    return [
        "run",
        str(pdf),
        "--cycle-json",
        str(EXAMPLE_DIR / "ciclo.json"),
        "--knowledge",
        str(EXAMPLE_KB),
        "--machines",
        str(EXAMPLE_DIR / "macchine_attive.json"),
        "--out",
        str(out),
    ]


def test_kb_check_prints_counts() -> None:
    result = runner.invoke(cli.app, ["kb-check", str(EXAMPLE_KB)])
    assert result.exit_code == 0, result.output
    assert "documenti" in result.output
    assert "sintetico-2026-11" in result.output


def _knowledge_with_doubts(tmp_path: Path, doubts: object) -> Path:
    target = tmp_path / "knowledge"
    shutil.copytree(EXAMPLE_KB, target)
    (target / "uncertainty.json").write_text(json.dumps(doubts), encoding="utf-8")
    return target


def test_kb_check_counts_the_doubtful_entries(tmp_path: Path) -> None:
    knowledge = _knowledge_with_doubts(
        tmp_path,
        {
            "format": 1,
            "machine_tags": {"TM-1001": ["valori_alternativi"]},
            "process_sheets": {"SP-0101": ["da_record_parziale"], "SP-0202": ["x"]},
        },
    )
    result = runner.invoke(cli.app, ["kb-check", str(knowledge)])
    assert result.exit_code == 0, result.output
    assert "targhe_incerte: 1" in result.output
    assert "schede_incerte: 2" in result.output
    assert "recommendation_dr_incerte: 0" in result.output


def test_kb_check_fails_on_an_inconsistent_uncertainty_file(tmp_path: Path) -> None:
    knowledge = _knowledge_with_doubts(
        tmp_path, {"format": 1, "process_sheets": {"SP-9999": ["valori_alternativi"]}}
    )
    result = runner.invoke(cli.app, ["kb-check", str(knowledge)])
    assert result.exit_code == 1
    assert "SP-9999" in result.output


def test_kb_check_reports_a_broken_knowledge_base(tmp_path: Path) -> None:
    result = runner.invoke(cli.app, ["kb-check", str(tmp_path)])
    assert result.exit_code == 1
    assert "manifest" in result.output.lower()


def test_run_writes_the_outputs(pdf: Path, tmp_path: Path) -> None:
    out = tmp_path / "out"
    result = runner.invoke(cli.app, base_args(pdf, out))
    assert result.exit_code == 0, result.output
    assert "completo" in result.output
    payload = json.loads((out / "payload.json").read_text(encoding="utf-8"))
    assert payload["cycle_errors_count"] == 2


def test_run_with_skip_check(pdf: Path, tmp_path: Path) -> None:
    out = tmp_path / "out"
    args = [*base_args(pdf, out), "--skip-check", "operation_description"]
    assert runner.invoke(cli.app, args).exit_code == 0
    payload = json.loads((out / "payload.json").read_text(encoding="utf-8"))
    assert payload["operations"][0]["operationFeedback"] == "N/A"


def test_unknown_skip_check_is_refused(pdf: Path, tmp_path: Path) -> None:
    args = [*base_args(pdf, tmp_path / "o"), "--skip-check", "boh"]
    result = runner.invoke(cli.app, args)
    assert result.exit_code == 2


def test_unknown_profile_is_refused(pdf: Path, tmp_path: Path) -> None:
    args = [*base_args(pdf, tmp_path / "o"), "--profile", "nope"]
    result = runner.invoke(cli.app, args)
    assert result.exit_code == 1
    assert "nope" in result.output


def test_run_without_cycle_json_extracts_with_the_model(
    pdf: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cycle = example_cycle().model_dump(mode="json")
    for operation in cycle["operations"]:
        operation["process_sheet"] = (
            {"code": operation["process_sheet"]["code"]} if operation["process_sheet"] else None
        )
    for source in cycle["sources"]:
        source.setdefault("issue", None)

    def script(request: object, attempt: int) -> dict[str, object]:
        if getattr(request, "session_id", "") == "extract":
            return cycle
        return scripted_judge(request, attempt)  # type: ignore[arg-type]

    monkeypatch.setattr(cli, "make_session", lambda settings, transcripts: ScriptedSession(script))
    out = tmp_path / "o"
    args = [
        "run",
        str(pdf),
        "--knowledge",
        str(EXAMPLE_KB),
        "--machines",
        str(EXAMPLE_DIR / "macchine_attive.json"),
        "--out",
        str(out),
    ]
    result = runner.invoke(cli.app, args)
    assert result.exit_code == 0, result.output
    payload = json.loads((out / "payload.json").read_text(encoding="utf-8"))
    assert payload["cycleCode"] == "CICLO-DEMO-001"
    assert payload["cycle_errors_count"] == 2


def test_golden_command(tmp_path: Path) -> None:
    from pathlib import Path as P

    golden = P(__file__).parents[1] / "eval" / "casi" / "sintetici" / "mos"
    result = runner.invoke(
        cli.app,
        [
            "golden",
            str(golden),
            "--knowledge",
            str(EXAMPLE_KB),
            "--machines",
            str(EXAMPLE_DIR / "macchine_attive.json"),
        ],
    )
    assert result.exit_code == 0, result.output
    assert "concordanza 100.0%" in result.output


def test_dr_profile_runs_without_serial_number_and_condition(pdf: Path, tmp_path: Path) -> None:
    args = [*base_args(pdf, tmp_path / "o"), "--profile", "dr"]
    result = runner.invoke(cli.app, args)
    assert result.exit_code == 0, result.output
    assert "Ciclo" in result.output


def test_dr_profile_blocks_on_not_applicable_recommendation(pdf: Path, tmp_path: Path) -> None:
    out = tmp_path / "o"
    args = [
        *base_args(pdf, out),
        "--profile",
        "dr",
        "--serial-number",
        "SN-DEMO-002",
        "--condition",
        "1,2",
    ]
    result = runner.invoke(cli.app, args)
    assert result.exit_code == 0, result.output
    assert "bloccato" in result.output


def test_eval_runs_a_variant_and_writes_the_leaderboard(tmp_path: Path) -> None:
    root = Path(__file__).parents[1]
    results = tmp_path / "risultati"
    common = ["--risultati", str(results)]
    for variant in ("baseline", "effort_low"):
        result = runner.invoke(
            cli.app,
            [
                "eval",
                "esegui",
                "--variante",
                str(root / "eval" / "varianti" / f"{variant}.yaml"),
                "--casi",
                str(root / "eval" / "casi" / "sintetici" / "dr"),
                "--ripetizioni",
                "2",
                "--ambiente",
                "prova",
                "--runs",
                str(tmp_path / "runs"),
                *common,
            ],
        )
        assert result.exit_code == 0, result.output
        assert "[10/10]" in result.output
        assert "concordanza 100,0%" in result.output
    out = tmp_path / "classifica.md"
    result = runner.invoke(cli.app, ["eval", "classifica", *common, "--out", str(out)])
    assert result.exit_code == 0, result.output
    text = out.read_text(encoding="utf-8")
    assert "## Ambiente: prova" in text
    assert "`effort_low`" in text and "`baseline`" in text
    assert "Ambiente: prova" in result.output
    # Senza --out la classifica va accanto ai risultati che legge, non in eval/risultati.
    result = runner.invoke(cli.app, ["eval", "classifica", *common])
    assert result.exit_code == 0, result.output
    results = Path(common[common.index("--risultati") + 1])
    assert "## Ambiente: prova" in (results / "classifica.md").read_text(encoding="utf-8")


def test_eval_reports_a_bad_variant_clearly(tmp_path: Path) -> None:
    result = runner.invoke(cli.app, ["eval", "esegui", "--variante", str(tmp_path / "x.yaml")])
    assert result.exit_code == 1
    assert "Variante non trovata" in result.output


def test_eval_pipeline_runs_every_variant_and_writes_the_leaderboard(tmp_path: Path) -> None:
    import shutil

    root = Path(__file__).parents[1]
    variants = tmp_path / "varianti"
    variants.mkdir()
    for name in ("baseline", "effort_low"):
        shutil.copy(root / "eval" / "varianti" / f"{name}.yaml", variants)
    results = tmp_path / "risultati"
    result = runner.invoke(
        cli.app,
        [
            "eval",
            "pipeline",
            "--salta-verifiche",
            "--casi",
            str(root / "eval" / "casi" / "sintetici" / "dr"),
            "--varianti",
            str(variants),
            "--ripetizioni",
            "1",
            "--ambiente",
            "prova",
            "--risultati",
            str(results),
            "--runs",
            str(tmp_path / "runs"),
        ],
    )
    assert result.exit_code == 0, result.output
    assert "2 varianti x 5 casi x 1 ripetizioni (baseline, effort_low)" in result.output
    assert "variante 1/2: baseline" in result.output
    assert "`effort_low`" in (results / "classifica.md").read_text(encoding="utf-8")


def test_eval_pipeline_stops_when_no_case_has_been_reviewed(tmp_path: Path) -> None:
    suite = tmp_path / "s"
    (suite / "c").mkdir(parents=True)
    (suite / "suite.yaml").write_text(f"conoscenza: {EXAMPLE_KB.as_posix()}\n", encoding="utf-8")
    (suite / "c" / "ciclo.json").write_text("{}", encoding="utf-8")
    (suite / "c" / "expected.json").write_text(
        '{"profile": "mos", "rivisto": false, "rows": []}', encoding="utf-8"
    )
    result = runner.invoke(cli.app, ["eval", "pipeline", "--salta-verifiche", "--casi", str(suite)])
    assert result.exit_code == 1
    assert "Nessun caso rivisto" in result.output


def test_eval_prepare_writes_a_draft_to_review(tmp_path: Path) -> None:
    suite = tmp_path / "aziendali"
    case = suite / "caso"
    case.mkdir(parents=True)
    (suite / "suite.yaml").write_text(
        f"conoscenza: {EXAMPLE_KB.as_posix()}\n"
        f"macchine: {(EXAMPLE_DIR / 'macchine_attive.json').as_posix()}\n",
        encoding="utf-8",
    )
    write_cycle_pdf(case / "ciclo.pdf", example_cycle())
    (case / "ciclo.json").write_text(example_cycle().model_dump_json(), encoding="utf-8")
    result = runner.invoke(cli.app, ["eval", "prepara", str(case), "--profilo", "mos"])
    assert result.exit_code == 0, result.output
    assert "Bozza scritta" in result.output
    expected = json.loads((case / "expected.json").read_text(encoding="utf-8"))
    assert expected["rivisto"] is False and expected["rows"]
    again = runner.invoke(cli.app, ["eval", "prepara", str(case)])
    assert again.exit_code == 0  # una bozza non rivista si può rifare
    reviewed = {**expected, "rivisto": True}
    (case / "expected.json").write_text(json.dumps(reviewed), encoding="utf-8")
    refused = runner.invoke(cli.app, ["eval", "prepara", str(case)])
    assert refused.exit_code == 1
    assert "già stato rivisto" in refused.output


def test_eval_mutazioni_writes_the_mutated_suites(tmp_path: Path) -> None:
    root = Path(__file__).parents[1]
    out = tmp_path / "mutazioni"
    result = runner.invoke(
        cli.app,
        ["eval", "mutazioni", "--casi", str(root / "eval/casi/sintetici/mos"), "--out", str(out)],
    )
    assert result.exit_code == 0, result.output
    assert "targa_sconosciuta" in result.output
    assert (out / "mos" / "suite.yaml").is_file()
    assert f"eval pipeline --casi {out}" in result.output


def test_leggi_prints_repair_sources_and_tasks_without_a_model(tmp_path: Path) -> None:
    from pvrm320_report_fixtures import civil_pages

    from cycle_validation.testing.pdf import build_pdf

    printed = tmp_path / "stampa.pdf"
    printed.write_bytes(build_pdf(civil_pages()))
    other = write_cycle_pdf(tmp_path / "altro.pdf", example_cycle())
    result = runner.invoke(cli.app, ["leggi", str(printed), str(other)])
    assert result.exit_code == 0, result.output
    lines = result.output.splitlines()
    assert lines[0] == "stampa.pdf"
    assert "fonti: ABC123456" in lines[1]
    assert lines[2] == "  task: 72-00-00 REPAIR 001"
    assert lines[3] == "altro.pdf"
    assert lines[4].startswith("  non letto dal parser:")


def test_leggi_fonti_prints_sources_without_manual_codes(tmp_path: Path) -> None:
    from pvrm320_report_fixtures import civil_pages

    from cycle_validation.testing.pdf import build_pdf

    printed = tmp_path / "stampa.pdf"
    printed.write_bytes(build_pdf(civil_pages()))
    result = runner.invoke(cli.app, ["leggi", str(printed), "--fonti"])
    assert result.exit_code == 0, result.output
    assert result.output.splitlines()[1:] == [
        "  fonte M1 · task 72-00-00 REPAIR 001 · rc B1",
        "  rc delle operazioni: B1",
        "  OEM nel piè di pagina (forma): AAA999999",
    ]
    assert "ABC123456" not in result.output


def test_leggi_prints_the_requested_page(tmp_path: Path) -> None:
    from pvrm320_report_fixtures import civil_pages

    from cycle_validation.testing.pdf import build_pdf

    printed = tmp_path / "stampa.pdf"
    printed.write_bytes(build_pdf(civil_pages()))
    result = runner.invoke(cli.app, ["leggi", str(printed), "--pagina", "2"])
    assert result.exit_code == 0, result.output
    assert any("|" in line and "C.RESP" in line for line in result.output.splitlines())


def test_leggi_prints_the_dr_case_and_serial_written_in_the_print(tmp_path: Path) -> None:
    from pvrm320_report_fixtures import FOOTER, block, page

    from cycle_validation.testing.pdf import build_pdf

    body = block(
        ["NOTE", "999999"],
        "005",
        [
            "REGISTRARE P/N E S/N DEL PARTICOLARE.",
            "P/N: S/N:",
            "IN D.R. CASE #01000002.",
            "APPLY ON S/N AAAA1CCC",
        ],
    )
    printed = tmp_path / "dr.pdf"
    printed.write_bytes(build_pdf([page(1, body, FOOTER)]))
    result = runner.invoke(cli.app, ["leggi", str(printed), "--profile", "dr"])
    assert result.exit_code == 0, result.output
    assert "  dr: caso 01000002 · S/N AAAA1CCC" in result.output.splitlines()


def test_leggi_prints_the_dr_serial_even_when_the_parser_fails(tmp_path: Path) -> None:
    from pvrm320_report_fixtures import FOOTER, SEP, page, row

    from cycle_validation.testing.pdf import build_pdf

    body = [row("QQ/901", "010", "PRIMA"), row(text="APPLY ON S/N AAAA1CCC"), SEP]
    body += [row(text="TESTO SENZA NUMERO"), SEP]
    printed = tmp_path / "dr.pdf"
    printed.write_bytes(build_pdf([page(1, body, FOOTER)]))
    result = runner.invoke(cli.app, ["leggi", str(printed), "--profile", "dr"])
    lines = result.output.splitlines()
    assert lines[1] == "  dr: caso - · S/N AAAA1CCC"
    assert lines[2].startswith("  non letto dal parser:")


def test_leggi_cerca_prints_matching_lines_with_masked_codes(tmp_path: Path) -> None:
    """Per capire la stampa dalle foto senza far vedere codici veri."""
    from pvrm320_report_fixtures import FOOTER, block, page

    from cycle_validation.testing.pdf import build_pdf

    body = block(
        ["NOTE", "999999"],
        "005",
        ["P/N: S/N:", "IN D.R. CASE #01000002.", "APPLY ON S/N AAAA1CCC"],
    )
    printed = tmp_path / "dr.pdf"
    printed.write_bytes(build_pdf([page(1, body, FOOTER)]))
    result = runner.invoke(cli.app, ["leggi", str(printed), "--profile", "dr", "--cerca", "s/n"])
    assert result.exit_code == 0, result.output
    assert "AAAA1CCC" not in result.output and "01000002" not in result.output
    assert "APPLY ON S/N AAAA9AAA" in result.output
    assert "  serial number trovati: 1 (AAAA9AAA)" in result.output.splitlines()


def test_confronta_says_where_two_prints_of_a_cycle_differ(tmp_path: Path) -> None:
    """Stampa giusta e stampa «con errori»: operazione e campo diversi, codici mascherati."""
    from pvrm320_report_fixtures import civil_pages

    from cycle_validation.testing.pdf import build_pdf

    good = tmp_path / "giusto.pdf"
    good.write_bytes(build_pdf(civil_pages()))
    wrong = tmp_path / "con errori.pdf"
    pages = [text.replace("72-00-00", "72-00-01") for text in civil_pages()]
    wrong.write_bytes(build_pdf(pages))
    result = runner.invoke(cli.app, ["confronta", str(good), str(wrong)])
    assert result.exit_code == 0, result.output
    same = " (stessa forma: cambia qualche lettera o cifra)"
    assert result.output.splitlines() == [
        "operazioni: 5 e 5 · differenze: 3",
        f"  fonte 1, task: 99-99-99 REPAIR 999 → 99-99-99 REPAIR 999{same}",
        "  op 005, descrizione:",
        f"      «99-99-99» → «99-99-99»{same}",
        f"      «99-99-99» → «99-99-99»{same}",
        f"  op 005, task code: 99-99-99 REPAIR 999 → 99-99-99 REPAIR 999{same}",
    ]


def test_confronta_on_the_same_print_finds_no_difference(tmp_path: Path) -> None:
    from pvrm320_report_fixtures import civil_pages

    from cycle_validation.testing.pdf import build_pdf

    good = tmp_path / "giusto.pdf"
    good.write_bytes(build_pdf(civil_pages()))
    result = runner.invoke(cli.app, ["confronta", str(good), str(good)])
    assert result.exit_code == 0, result.output
    assert result.output.splitlines()[0].endswith("differenze: 0")


def test_word_changes_show_only_the_changed_pieces_masked() -> None:
    changes = cli._word_changes("SERRARE A 25 NM CON CHIAVE", "SERRARE A 30 NM CON PINZA")
    assert changes == [
        "«99» → «99» (stessa forma: cambia qualche lettera o cifra)",
        "«CHIAVE» → «PINZA»",
    ]


def test_confronta_says_which_print_the_parser_cannot_read(tmp_path: Path) -> None:
    from pvrm320_report_fixtures import civil_pages

    from cycle_validation.testing.pdf import build_pdf

    good = tmp_path / "giusto.pdf"
    good.write_bytes(build_pdf(civil_pages()))
    other = write_cycle_pdf(tmp_path / "altro.pdf", example_cycle())
    result = runner.invoke(cli.app, ["confronta", str(good), str(other)])
    assert result.exit_code == 0, result.output
    assert result.output.startswith("il secondo (con errori) non è letto dal parser:")


def test_leggi_struttura_shows_the_layout_without_the_text(tmp_path: Path) -> None:
    from pvrm320_report_fixtures import civil_pages

    from cycle_validation.testing.pdf import build_pdf

    printed = tmp_path / "stampa.pdf"
    printed.write_bytes(build_pdf(civil_pages()))
    result = runner.invoke(cli.app, ["leggi", str(printed), "--struttura", "2"])
    assert result.exit_code == 0, result.output
    output = result.output
    assert "op 005, colonna sinistra piena, testo «APPLICARE» + 6 parole" in output
    assert "TRATTEGGIO" in output
    assert output.rstrip().endswith("parser: letto")
    assert "RIVESTIMENTO" not in output  # solo la prima parola del testo


def test_leggi_fonti_shows_codes_in_the_text_that_are_not_tasks(tmp_path: Path) -> None:
    from pvrm320_report_fixtures import FOOTER, block, page

    from cycle_validation.testing.pdf import build_pdf

    body = block(["QQ/901"], "005", ["SECONDO MANUALE ABC123456 SUBTASK 70-11-00-350-035/029"])
    printed = tmp_path / "stampa.pdf"
    printed.write_bytes(build_pdf([page(1, body, FOOTER, note="APPL. LUBRIFIC. SECCO")]))
    result = runner.invoke(cli.app, ["leggi", str(printed), "--fonti"])
    assert result.exit_code == 0, result.output
    assert "  fonte M1 · task - · rc B1" in result.output
    # il SUBTASK è un task citato; la forma con la barra non si legge e resta tra gli altri codici
    assert (
        "op 005 · rc B1 · task 70-11-00-350-035 · altri codici nel testo: "
        "SUBTASK 70-11-00-999-999/999"
    ) in result.output
    assert "ABC123456" not in result.output


def test_leggi_lingue_prints_only_the_numbers_that_differ(tmp_path: Path) -> None:
    from pvrm320_report_fixtures import FOOTER, STARS, block, page

    from cycle_validation.testing.pdf import build_pdf

    body = block(["QQ/901"], "040", ["SPESSORE 13-38 MICRON", STARS, "THICKNESS 13-58 MICRON"])
    body += block(["QQ/902"], "050", ["ASCIUGARE 2 ORE", STARS, "DRY 2 HOURS"])
    printed = tmp_path / "stampa.pdf"
    printed.write_bytes(build_pdf([page(1, body, FOOTER)]))
    result = runner.invoke(cli.app, ["leggi", str(printed), "--lingue"])
    assert result.exit_code == 0, result.output
    assert result.output.splitlines()[1:] == [
        "  op 040: italiano → inglese 38 → 58",
        "  operazioni con le due lingue: 2 su 2",
    ]
