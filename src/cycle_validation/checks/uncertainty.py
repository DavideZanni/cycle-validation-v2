"""Voci che l'indice della conoscenza segnala come incerte (`uncertainty.json`).

Due tipi di motivo:

- il dato stesso può essere sbagliato (record letto solo in parte, edizione precedente
  perché la più recente è bloccata): il controllo che lo usa diventa un warning;
- il dato c'è ed è affidabile per ciò che il controllo verifica, ma ha una particolarità
  (valori alternativi, manuale collegato in dubbio): l'esito resta, con una nota.

Un motivo che questo codice non conosce vale come il primo tipo: meglio un warning in più
che un esito pieno su un dato di cui non sappiamo dire nulla.
"""

from collections.abc import Sequence

_LABELS = {
    "valori_alternativi": "valori alternativi tra più righe con lo stesso codice",
    "da_record_parziale": "dato da un record letto solo in parte",
    "edizione_precedente_per_blocco": "edizione precedente (la più recente è bloccata)",
    "manuale_parziale": "manuale collegato disponibile solo in parte",
    "manuale_indicato_contraddetto": "manuale indicato dalla fonte contraddetto dai task",
    "manuale_indicato_non_pubblicato": "manuale indicato dalla fonte non pubblicato",
    "manuale_indicato_assente": "manuale indicato dalla fonte assente dall'indice",
    "task_non_nel_manuale_indicato": "task non trovati nel manuale indicato dalla fonte",
    "copie_diverse_per_contenuto": "copie con contenuto diverso per lo stesso codice e issue",
    "copie_diverse_per_tipo": "copie con tipo diverso (tenuta quella con il tipo confermato)",
    "copie_diverse_per_pubblicazione": "copie con stato diverso (tenuta quella pubblicata)",
    "copie_diverse_per_completezza": "copie con completezza diversa (tenuta quella completa)",
    "da_rivedere": "voce segnata da rivedere (needs_review)",
}

# Motivi che non mettono in dubbio presenza e valore del dato verificato.
NOTE_ONLY = frozenset(
    {
        "valori_alternativi",
        "manuale_parziale",
        "manuale_indicato_contraddetto",
        "manuale_indicato_non_pubblicato",
        "manuale_indicato_assente",
        "task_non_nel_manuale_indicato",
        "copie_diverse_per_tipo",
        "copie_diverse_per_pubblicazione",
        "copie_diverse_per_completezza",
    }
)


def is_doubtful(reasons: Sequence[str]) -> bool:
    """Vero se almeno un motivo mette in dubbio il dato stesso."""
    return any(reason not in NOTE_ONLY for reason in reasons)


def describe(reasons: Sequence[str]) -> str:
    """Nota da aggiungere alla motivazione; vuota se la voce è certa."""
    if not reasons:
        return ""
    labels = ", ".join(_LABELS.get(reason, reason) for reason in reasons)
    return f" Dato incerto nell'indice: {labels}."
