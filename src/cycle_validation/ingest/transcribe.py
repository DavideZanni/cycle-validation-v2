"""Trascrizione di immagini di pagina in testo con un modello (Bedrock, es. Haiku).

Serve solo quando l'ingresso non ha un livello di testo: foto, scansioni, PDF di immagini.
Un PDF con testo passa da PDFium e non tocca il modello. Il client Bedrock è iniettato; boto3
si importa solo in `make_transcriber`, senza credenziali nel codice. I test usano un client finto.
Nei log e negli errori non entra mai il testo trascritto.
"""

import time
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Protocol

from cycle_validation.domain.check import Usage
from cycle_validation.errors import IngestError

if TYPE_CHECKING:
    from cycle_validation.config import AgentSettings

TRANSCRIBE_PROMPT = (
    "Trascrivi fedelmente tutto il testo di questa pagina di un ciclo di lavorazione, "
    "riga per riga, mantenendo l'ordine e le colonne (usa gli spazi e il carattere * come "
    "nell'originale). Non tradurre, non correggere, non riassumere e non aggiungere commenti. "
    "Riporta numeri, unità e codici esattamente come sono scritti. Dove un carattere non è "
    "leggibile scrivi [?]. Rispondi solo con la trascrizione."
)

_BEDROCK_FORMATS = {"image/png": "png", "image/jpeg": "jpeg"}
# Errori passeggeri del servizio: si ritenta. Gli altri (richiesta non valida, accesso negato)
# si ripeterebbero identici.
_RETRYABLE = frozenset(
    {
        "ThrottlingException",
        "ModelTimeoutException",
        "ModelNotReadyException",
        "ServiceUnavailableException",
        "InternalServerException",
    }
)


def _error_code(error: Exception) -> str:
    """Codice dell'errore AWS (`ClientError.response`), altrimenti il tipo dell'eccezione.
    Mai il messaggio: può riportare parti della richiesta."""
    response = getattr(error, "response", None)
    code = response.get("Error", {}).get("Code") if isinstance(response, dict) else None
    return str(code) if code else type(error).__name__


class PageTranscriber(Protocol):
    def transcribe(self, image: bytes, media_type: str) -> tuple[str, Usage]: ...


class FakePageTranscriber:
    """Restituisce i testi indicati, uno per chiamata e in ordine. Deterministico."""

    def __init__(self, texts: list[str], usage: Usage | None = None) -> None:
        self._texts = list(texts)
        self._usage = usage or Usage()
        self.calls: list[tuple[bytes, str]] = []

    def transcribe(self, image: bytes, media_type: str) -> tuple[str, Usage]:
        self.calls.append((image, media_type))
        if len(self.calls) > len(self._texts):
            raise IngestError("Trascrizione di prova esaurita.", http_status=502)
        return self._texts[len(self.calls) - 1], self._usage


class BedrockPageTranscriber:
    """Chiama `converse` di Bedrock Runtime. `client` è un `boto3` `bedrock-runtime` o un finto."""

    def __init__(
        self,
        client: Any,
        model_id: str,
        prompt: str = TRANSCRIBE_PROMPT,
        max_tokens: int = 4096,
        *,
        retries: int = 2,
        backoff_s: float = 1.0,
        sleep: Callable[[float], object] = time.sleep,
    ) -> None:
        self._client = client
        self._model_id = model_id
        self._prompt = prompt
        self._max_tokens = max_tokens
        self._retries = retries
        self._backoff_s = backoff_s
        self._sleep = sleep

    def transcribe(self, image: bytes, media_type: str) -> tuple[str, Usage]:
        image_format = _BEDROCK_FORMATS.get(media_type)
        if image_format is None:
            raise IngestError(f"Formato immagine non supportato: {media_type}.", http_status=415)
        request = {
            "modelId": self._model_id,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"image": {"format": image_format, "source": {"bytes": image}}},
                        {"text": self._prompt},
                    ],
                }
            ],
            "inferenceConfig": {"maxTokens": self._max_tokens, "temperature": 0},
        }
        response = self._converse(request)
        try:
            parts = response["output"]["message"]["content"]
            text = "\n".join(part["text"] for part in parts if "text" in part).strip()
            usage = response.get("usage", {})
            used = Usage(
                input_tokens=int(usage.get("inputTokens", 0)),
                output_tokens=int(usage.get("outputTokens", 0)),
                sessions=1,
                turns=1,
            )
        except Exception as exc:
            raise IngestError(
                f"La trascrizione della pagina non è riuscita ({type(exc).__name__}).",
                http_status=502,
            ) from exc
        if response.get("stopReason") == "max_tokens":
            # una pagina tagliata a metà darebbe un ciclo con operazioni mancanti, senza avviso
            raise IngestError(
                f"La trascrizione della pagina è troncata: supera {self._max_tokens} token.",
                http_status=502,
            )
        return text, used

    def _converse(self, request: dict[str, Any]) -> Any:
        attempt = 0
        while True:
            try:
                return self._client.converse(**request)
            except Exception as exc:
                code = _error_code(exc)
                if code in _RETRYABLE and attempt < self._retries:
                    self._sleep(self._backoff_s * 2**attempt)
                    attempt += 1
                    continue
                raise IngestError(
                    f"La trascrizione della pagina non è riuscita ({code}).", http_status=502
                ) from exc


def make_transcriber(settings: "AgentSettings") -> PageTranscriber | None:
    """Trascrittore Bedrock se `transcribe_model` è impostato, altrimenti None.

    boto3 si importa qui, solo se serve: non è una dipendenza obbligatoria. Le credenziali
    vengono dall'ambiente AWS (ruolo, profilo), mai dalla configurazione.
    """
    if not settings.transcribe_model:
        return None
    try:
        import boto3
    except ImportError as exc:
        raise IngestError(
            "La trascrizione richiede boto3, che non è installato.", http_status=500
        ) from exc
    client = boto3.client("bedrock-runtime", region_name=settings.aws_region)
    return BedrockPageTranscriber(client, settings.transcribe_model)
