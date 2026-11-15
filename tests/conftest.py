from collections.abc import Callable
from pathlib import Path

import pytest
from pdf_factory import build_pdf

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture
def make_pdf(tmp_path: Path) -> Callable[..., Path]:
    def _make(pages: list[str], name: str = "ciclo.pdf") -> Path:
        path = tmp_path / name
        path.write_bytes(build_pdf(pages))
        return path

    return _make


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Le prove `live` chiamano il modello vero: partono solo se chieste con `-m live`."""
    if "live" in (config.getoption("markexpr") or ""):
        return
    skip = pytest.mark.skip(reason="prova con il modello vero: lanciala con `pytest -m live`")
    for item in items:
        if "live" in item.keywords:
            item.add_marker(skip)
