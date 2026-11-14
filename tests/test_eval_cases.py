"""Casi sintetici degli esperimenti: restano allineati alle fixture dei test."""

from pathlib import Path

from ej200_fixtures import make_store

from cycle_validation.kb.stores import LocalDirObjectStore

SINTETICI = Path(__file__).parents[1] / "eval" / "casi" / "sintetici"


def test_exported_ej200_knowledge_matches_the_test_fixtures() -> None:
    expected = make_store()
    exported = LocalDirObjectStore(SINTETICI / "ej200" / "conoscenza")
    assert exported.list_keys("") == expected.list_keys("")
    for key in expected.list_keys(""):
        assert exported.get_bytes(key) == expected.get_bytes(key), key


def test_the_company_suite_templates_are_valid() -> None:
    import yaml

    from cycle_validation.evaluation.run import SuiteConfig

    templates = sorted((SINTETICI.parent.parent / "modelli" / "aziendali").glob("*/suite.yaml"))
    assert [t.parent.name for t in templates] == ["dr", "ej200", "mos"]
    for template in templates:
        config = SuiteConfig.model_validate(yaml.safe_load(template.read_text(encoding="utf-8")))
        assert config.estrazione == "dal_pdf"
        assert config.profilo == template.parent.name
