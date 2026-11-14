"""Lettura dei prompt YAML del sistema attuale (`prompts/use_cases/*.yaml`).

Serve a due cose: leggere e documentare cosa giudica ciascun caso d'uso (per decidere cosa
deve valutare la sessione per operazione) e riusare le regole di dominio dei prompt senza
ricopiarle a mano. La struttura è letta in modo tollerante: i nomi dei campi alternativi più
comuni sono accettati e ciò che manca ha un valore predefinito.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from cycle_validation.errors import ConfigError

_SYSTEM_KEYS = ("system", "system_prompt")
_TEMPLATE_KEYS = ("prompt", "template", "user_prompt")
_VARIABLE_KEYS = ("variables", "input_variables")
_PLACEHOLDER = re.compile(r"{([A-Za-z_][A-Za-z0-9_]*)}")


@dataclass(frozen=True)
class UseCase:
    name: str
    system: str
    template: str
    variables: tuple[str, ...]
    temperature: float = 0.0
    max_tokens: int = 7000

    def render(self, values: dict[str, object]) -> str:
        """Riempie i segnaposto. Un valore mancante è un errore che nomina la variabile."""
        missing = [name for name in self.variables if name not in values]
        if missing:
            raise ConfigError(f"Caso d'uso {self.name}: variabili mancanti: {', '.join(missing)}.")
        return _PLACEHOLDER.sub(lambda m: str(values.get(m.group(1), m.group(0))), self.template)


def _first(data: dict[str, Any], keys: tuple[str, ...]) -> Any:
    return next((data[key] for key in keys if key in data), None)


def load_use_case(path: Path) -> UseCase:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ConfigError(f"Prompt non leggibile: {path} ({exc})") from exc
    if not isinstance(data, dict):
        raise ConfigError(f"{path}: attesa una mappa chiave: valore.")
    template = _first(data, _TEMPLATE_KEYS)
    if not isinstance(template, str) or not template.strip():
        raise ConfigError(
            f"{path}: manca il testo del prompt (campi: {', '.join(_TEMPLATE_KEYS)})."
        )
    declared = _first(data, _VARIABLE_KEYS)
    variables = (
        tuple(str(item) for item in declared)
        if isinstance(declared, list)
        else tuple(dict.fromkeys(_PLACEHOLDER.findall(template)))
    )
    return UseCase(
        name=path.stem,
        system=str(_first(data, _SYSTEM_KEYS) or "").strip(),
        template=template,
        variables=variables,
        temperature=float(data.get("temperature", 0.0)),
        max_tokens=int(data.get("max_tokens", 7000)),
    )


def load_use_cases(directory: Path) -> dict[str, UseCase]:
    if not directory.is_dir():
        raise ConfigError(f"Cartella dei prompt non trovata: {directory}")
    return {path.stem: load_use_case(path) for path in sorted(directory.glob("*.yaml"))}


def describe_use_cases(cases: dict[str, UseCase]) -> str:
    """Tabella Markdown dei casi d'uso: nome, variabili, prima riga del prompt di sistema."""
    lines = ["| Caso d'uso | Variabili | Ruolo |", "|---|---|---|"]
    for name, case in cases.items():
        role = (case.system.splitlines() or [""])[0]
        lines.append(f"| {name} | {', '.join(case.variables)} | {role} |")
    return "\n".join(lines)
