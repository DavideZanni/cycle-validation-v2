"""Scelta iniziale del ciclo da validare.

Primo passo: ciclo civile o militare. Secondo passo, solo per il civile: MOS o DR.
Il ciclo militare è il profilo EJ200. La regola è qui, in una funzione pura; il frontend
mostra i pulsanti a partire da `selection_options` e manda la scelta con il caricamento.
"""

from typing import Any

from cycle_validation.errors import SelectionError

CIVIL = "civil"
MILITARY = "military"
MOS = "mos"
DR = "dr"
MILITARY_PROFILE = "ej200"

_DOMAIN_ALIASES = {
    "civil": CIVIL,
    "civile": CIVIL,
    "military": MILITARY,
    "militare": MILITARY,
}
_CIVIL_TYPES = (MOS, DR)


def _clean(value: str | None) -> str:
    return (value or "").strip().casefold()


def resolve_profile(domain: str | None, civil_type: str | None) -> str:
    """Profilo della pipeline per la scelta fatta. Solleva SelectionError se è incompleta
    o incoerente: nessun valore viene indovinato."""
    chosen = _DOMAIN_ALIASES.get(_clean(domain))
    if chosen is None:
        raise SelectionError("Scegli il tipo di ciclo: civile o militare.")
    kind = _clean(civil_type)
    if chosen == MILITARY:
        if kind:
            raise SelectionError("La scelta MOS o DR vale solo per i cicli civili.")
        return MILITARY_PROFILE
    if kind not in _CIVIL_TYPES:
        raise SelectionError("Per un ciclo civile scegli MOS o DR.")
    return kind


def selection_options(*, military_enabled: bool) -> dict[str, Any]:
    """Albero delle scelte, nell'ordine in cui il frontend le propone."""
    return {
        "steps": [
            {
                "id": "domain",
                "label": "Che ciclo vuoi validare?",
                "options": [
                    {"value": CIVIL, "label": "Ciclo civile", "enabled": True},
                    {"value": MILITARY, "label": "Ciclo militare", "enabled": military_enabled},
                ],
            },
            {
                "id": "civil_type",
                "label": "Che tipo di ciclo civile?",
                "when": {"domain": CIVIL},
                "options": [
                    {"value": MOS, "label": "Ciclo MOS", "enabled": True},
                    {"value": DR, "label": "Ciclo DR", "enabled": True},
                ],
            },
        ]
    }
