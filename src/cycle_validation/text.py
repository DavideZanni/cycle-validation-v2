"""Normalizzazione del testo per confronti esatti tra ciclo, PDF e documenti."""

import re
import unicodedata

_WHITESPACE = re.compile(r"\s+")
_DASHES = str.maketrans(dict.fromkeys("‐‑‒–—−", "-"))
_QUOTES = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"'})


def _fold(value: str) -> str:
    folded = unicodedata.normalize("NFKC", value)
    return folded.translate(_DASHES).translate(_QUOTES)


def normalize_code(value: str) -> str:
    """Forma canonica di un codice: maiuscole, senza spazi, trattini unificati."""
    return _WHITESPACE.sub("", _fold(value)).upper()


def sheet_key(value: str) -> str:
    """Codice di una scheda di processo per il confronto: come `normalize_code` e senza
    trattini, come nel servizio precedente (`CPEC522-BR` = `CPEC522BR`)."""
    return normalize_code(value).replace("-", "")


def squash(value: str) -> str:
    """Testo senza spazi e senza maiuscole, per cercare un valore dentro un testo impaginato."""
    return _WHITESPACE.sub("", _fold(value)).casefold()


def normalize_quote(value: str) -> str:
    """Testo con spazi compressi e senza maiuscole, per confrontare citazioni."""
    return _WHITESPACE.sub(" ", _fold(value)).strip().casefold()
