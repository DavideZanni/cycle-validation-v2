"""I blocchi di `docs/COPILOT.md` portano sul PC e salvano tutto quello che serve ai test.

Il 24-11-2026 `eval/errori-noti.yaml` non arrivava sul PC: il blocco Aggiornare copiava solo
alcune cartelle, e tre test fallivano.
"""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
COPILOT = ROOT / "docs" / "COPILOT.md"
# Quello che il codice e i test leggono dal repository (oltre a docs/).
NEEDED = (
    "src",
    "tests",
    "prompts",
    "config",
    "examples",
    "eval/casi/sintetici",
    "eval/varianti",
    "eval/modelli",
    "eval/errori-noti.yaml",
    "eval/campagna.yaml",
    "pyproject.toml",
    "uv.lock",
)


def _block(title: str) -> str:
    if not COPILOT.is_file():
        pytest.skip("docs/COPILOT.md non c'è")
    text = COPILOT.read_text("utf-8")
    start = text.index(title)
    code = re.search(r"```powershell\n(.*?)```", text[start:], re.S)
    assert code is not None, title
    return code.group(1).replace("\\", "/")


def test_the_update_block_copies_everything_the_tests_need() -> None:
    block = _block("### 2.1 Aggiornare")
    for path in NEEDED:
        assert path in block, f"Aggiornare non copia {path}"


def test_the_save_block_commits_everything_the_tests_need() -> None:
    block = _block("### 2.2 Salvare")
    for path in NEEDED:
        assert path in block, f"Salvare non mette in git {path}"
