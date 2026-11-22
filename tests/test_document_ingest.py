"""Ingest di documenti: PDF con testo → PDFium; immagini e PDF scansionati → modello (trascrittore)."""

import io
from pathlib import Path
from typing import Any

import pytest
from pdf_factory import build_pdf
from PIL import Image

from cycle_validation.config import FileLimits
from cycle_validation.domain.check import Usage
from cycle_validation.errors import IngestError
from cycle_validation.ingest.document import read_document, read_document_bytes
from cycle_validation.ingest.transcribe import BedrockPageTranscriber, FakePageTranscriber

LIMITS = FileLimits(min_chars=10)
TEXT = "Operazione 0010 pulire il pezzo con solvente"


def png_bytes() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (40, 30), "white").save(buffer, format="PNG")
    return buffer.getvalue()


def jpeg_bytes() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (40, 30), "white").save(buffer, format="JPEG")
    return buffer.getvalue()


def scanned_pdf(pages: int = 2) -> bytes:
    images = [Image.new("RGB", (200, 100), "white") for _ in range(pages)]
    buffer = io.BytesIO()
    images[0].save(buffer, format="PDF", save_all=True, append_images=images[1:])
    return buffer.getvalue()


def test_pdf_with_text_does_not_call_the_model() -> None:
    fake = FakePageTranscriber([TEXT])
    document, usage = read_document_bytes(build_pdf([TEXT]), "c.pdf", LIMITS, fake)
    assert document.pages[0].text == TEXT
    assert fake.calls == [] and usage == Usage()


@pytest.mark.parametrize(
    ("data", "media"), [(png_bytes(), "image/png"), (jpeg_bytes(), "image/jpeg")]
)
def test_image_is_transcribed_into_a_one_page_document(data: bytes, media: str) -> None:
    fake = FakePageTranscriber([TEXT], usage=Usage(input_tokens=10, output_tokens=5))
    document, usage = read_document_bytes(data, "foto.jpg", LIMITS, fake)
    assert [(p.number, p.text) for p in document.pages] == [(1, TEXT)]
    assert [m for _, m in fake.calls] == [media]
    assert document.name == "foto.jpg" and len(document.sha256) == 64
    assert usage.input_tokens == 10 and usage.output_tokens == 5


def test_scanned_pdf_is_rendered_page_by_page_and_transcribed() -> None:
    fake = FakePageTranscriber([TEXT + " uno", TEXT + " due"], usage=Usage(input_tokens=3))
    document, usage = read_document_bytes(scanned_pdf(2), "scan.pdf", LIMITS, fake)
    assert [(p.number, p.text) for p in document.pages] == [(1, TEXT + " uno"), (2, TEXT + " due")]
    assert all(image.startswith(b"\x89PNG") and media == "image/png" for image, media in fake.calls)
    assert usage.input_tokens == 6


def test_image_without_a_transcriber_is_refused() -> None:
    with pytest.raises(IngestError) as caught:
        read_document_bytes(png_bytes(), "foto.png", LIMITS, None)
    assert caught.value.http_status == 415


def test_scanned_pdf_without_a_transcriber_keeps_the_scan_error() -> None:
    with pytest.raises(IngestError, match="scansione"):
        read_document_bytes(scanned_pdf(1), "scan.pdf", LIMITS, None)


def test_unknown_bytes_are_not_a_supported_file() -> None:
    with pytest.raises(IngestError) as caught:
        read_document_bytes(
            b"MZ\x00\x01 non e' un documento", "x.exe", LIMITS, FakePageTranscriber([])
        )
    assert caught.value.http_status == 415


def test_empty_file_is_400() -> None:
    with pytest.raises(IngestError) as caught:
        read_document_bytes(b"", "x.png", LIMITS, FakePageTranscriber([]))
    assert caught.value.http_status == 400


def test_a_transcription_that_is_too_short_is_an_ingest_error() -> None:
    with pytest.raises(IngestError, match="trascrizione"):
        read_document_bytes(png_bytes(), "foto.png", LIMITS, FakePageTranscriber(["ok"]))


def test_page_limit_applies_to_scanned_pdfs() -> None:
    limits = FileLimits(min_chars=10, max_pages=1)
    with pytest.raises(IngestError, match="pagine"):
        read_document_bytes(scanned_pdf(2), "scan.pdf", limits, FakePageTranscriber([TEXT, TEXT]))


def test_required_text_is_checked_on_the_transcription() -> None:
    limits = FileLimits(min_chars=10, required_text=["PVRM320"])
    with pytest.raises(IngestError, match="PVRM320"):
        read_document_bytes(png_bytes(), "foto.png", limits, FakePageTranscriber([TEXT]))


# --- adattatore Bedrock, con client finto -------------------------------------------------


class FakeBedrockClient:
    def __init__(self, text: str = "testo trascritto") -> None:
        self.text = text
        self.requests: list[dict[str, Any]] = []

    def converse(self, **request: Any) -> dict[str, Any]:
        self.requests.append(request)
        return {
            "output": {"message": {"role": "assistant", "content": [{"text": self.text}]}},
            "usage": {"inputTokens": 120, "outputTokens": 40},
        }


def test_bedrock_adapter_sends_the_image_and_returns_text_and_usage() -> None:
    client = FakeBedrockClient()
    transcriber = BedrockPageTranscriber(client, "modello-test", "Trascrivi.")
    text, usage = transcriber.transcribe(png_bytes(), "image/png")
    assert text == "testo trascritto"
    assert (usage.input_tokens, usage.output_tokens, usage.sessions) == (120, 40, 1)
    request = client.requests[0]
    assert request["modelId"] == "modello-test"
    content = request["messages"][0]["content"]
    assert content[0]["image"]["format"] == "png"
    assert content[0]["image"]["source"]["bytes"] == png_bytes()
    assert content[1] == {"text": "Trascrivi."}
    assert request["inferenceConfig"]["temperature"] == 0


def test_bedrock_adapter_maps_jpeg_format() -> None:
    client = FakeBedrockClient()
    BedrockPageTranscriber(client, "m", "p").transcribe(jpeg_bytes(), "image/jpeg")
    assert client.requests[0]["messages"][0]["content"][0]["image"]["format"] == "jpeg"


def test_bedrock_adapter_failure_is_an_ingest_error_without_leaking_content() -> None:
    class Broken:
        def converse(self, **_: Any) -> dict[str, Any]:
            raise RuntimeError("throttled")

    with pytest.raises(IngestError, match="trascrizione"):
        BedrockPageTranscriber(Broken(), "m", "p").transcribe(png_bytes(), "image/png")


# --- pipeline -----------------------------------------------------------------------------


def test_pipeline_validates_an_image_through_the_transcriber_and_counts_its_usage() -> None:
    import dataclasses

    from support import EXAMPLE_DIR, make_deps

    from cycle_validation.domain.cycle import Cycle
    from cycle_validation.golden import synthetic_cycle_pdf
    from cycle_validation.ingest.pdf import read_pdf_bytes
    from cycle_validation.pipeline import RunRequest, run_validation

    cycle = Cycle.model_validate_json((EXAMPLE_DIR / "ciclo.json").read_text(encoding="utf-8"))
    text = read_pdf_bytes(synthetic_cycle_pdf(cycle), "c.pdf", FileLimits(min_chars=10)).text
    deps, _ = make_deps()
    fake = FakePageTranscriber([text], usage=Usage(input_tokens=700, output_tokens=300, sessions=1))
    deps = dataclasses.replace(deps, transcriber=fake)

    report = run_validation(RunRequest(pdf_bytes=png_bytes(), pdf_name="foto.png"), deps)

    assert len(fake.calls) == 1
    assert report.usage.input_tokens >= 700 and report.usage.output_tokens >= 300


# --- configurazione -----------------------------------------------------------------------


def test_transcriber_is_off_unless_a_model_is_configured() -> None:
    from cycle_validation.config import AgentSettings
    from cycle_validation.ingest.transcribe import make_transcriber

    assert make_transcriber(AgentSettings()) is None


def test_transcriber_is_built_from_settings_with_a_lazily_imported_client(monkeypatch) -> None:
    import sys
    import types

    from cycle_validation.config import AgentSettings
    from cycle_validation.ingest.transcribe import make_transcriber

    created: list[tuple[str, str | None]] = []
    fake_boto3 = types.SimpleNamespace(
        client=lambda service, region_name=None: created.append((service, region_name)) or object()
    )
    monkeypatch.setitem(sys.modules, "boto3", fake_boto3)
    transcriber = make_transcriber(
        AgentSettings(transcribe_model="eu.anthropic.haiku-test", aws_region="eu-south-1")
    )
    assert isinstance(transcriber, BedrockPageTranscriber)
    assert created == [("bedrock-runtime", "eu-south-1")]


def test_missing_boto3_gives_a_clear_error(monkeypatch) -> None:
    import sys

    from cycle_validation.config import AgentSettings
    from cycle_validation.ingest.transcribe import make_transcriber

    monkeypatch.setitem(sys.modules, "boto3", None)
    with pytest.raises(IngestError, match="boto3"):
        make_transcriber(AgentSettings(transcribe_model="m"))


# --- limiti e file malformati prima di spendere una chiamata ---------------------------------


def big_page_pdf(side_pt: int) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (side_pt, side_pt), "white").save(buffer, format="PDF", resolution=72.0)
    return buffer.getvalue()


def noise_png(width: int, height: int) -> bytes:
    import random

    pixels = random.Random(0).randbytes(width * height * 3)
    buffer = io.BytesIO()
    Image.frombytes("RGB", (width, height), pixels).save(buffer, format="PNG")
    return buffer.getvalue()


def test_scanned_pdfs_have_a_page_cap_even_when_the_profile_sets_none() -> None:
    # MOS e DR non hanno max_pages: senza un tetto una scansione di mille pagine sarebbero
    # mille pagine renderizzate e mille chiamate al modello
    limits = FileLimits(min_chars=10, max_transcribed_pages=2)
    fake = FakePageTranscriber([TEXT] * 3)
    with pytest.raises(IngestError, match="trascri") as caught:
        read_document_bytes(scanned_pdf(3), "scan.pdf", limits, fake)
    assert caught.value.http_status == 413
    assert fake.calls == []


def test_the_default_page_cap_for_transcription_is_sixty() -> None:
    assert FileLimits().max_transcribed_pages == 60


def test_a_huge_page_is_rendered_within_a_pixel_cap() -> None:
    fake = FakePageTranscriber([TEXT])
    read_document_bytes(big_page_pdf(2000), "scan.pdf", LIMITS, fake)
    image, media_type = fake.calls[0]
    assert media_type in ("image/png", "image/jpeg")
    assert max(Image.open(io.BytesIO(image)).size) <= 3000


def test_an_ordinary_page_keeps_the_full_render_scale() -> None:
    fake = FakePageTranscriber([TEXT])
    read_document_bytes(big_page_pdf(600), "scan.pdf", LIMITS, fake)
    assert Image.open(io.BytesIO(fake.calls[0][0])).size == (1500, 1500)


def test_a_file_that_only_looks_like_an_image_is_refused_before_the_model() -> None:
    fake = FakePageTranscriber([TEXT])
    with pytest.raises(IngestError, match="non è leggibile") as caught:
        read_document_bytes(b"\x89PNG\r\n\x1a\n" + b"non-una-immagine" * 10, "x.png", LIMITS, fake)
    assert caught.value.http_status == 422
    assert fake.calls == []


def test_an_image_with_too_many_pixels_is_refused_without_decoding_it() -> None:
    buffer = io.BytesIO()
    Image.new("1", (9000, 9000)).save(buffer, format="PNG")  # 81 megapixel in pochi kB
    fake = FakePageTranscriber([TEXT])
    with pytest.raises(IngestError, match="pixel") as caught:
        read_document_bytes(buffer.getvalue(), "x.png", LIMITS, fake)
    assert caught.value.http_status == 413
    assert fake.calls == []


def test_an_image_too_heavy_for_the_model_is_re_encoded_under_the_limit() -> None:
    heavy = noise_png(1400, 1000)
    assert len(heavy) > 3_750_000
    fake = FakePageTranscriber([TEXT])
    read_document_bytes(heavy, "foto.png", LIMITS, fake)
    image, media_type = fake.calls[0]
    assert len(image) <= 3_750_000
    assert media_type == "image/jpeg"
    assert Image.open(io.BytesIO(image)).format == "JPEG"


def test_a_small_image_is_sent_as_it_is() -> None:
    fake = FakePageTranscriber([TEXT])
    read_document_bytes(png_bytes(), "foto.png", LIMITS, fake)
    assert fake.calls == [(png_bytes(), "image/png")]


def test_pdfium_is_never_entered_by_two_threads_at_once(monkeypatch: pytest.MonkeyPatch) -> None:
    # PDFium non è thread-safe e l'ingest gira in un thread per richiesta
    import threading
    import time

    from cycle_validation.ingest import pdf as pdf_module

    state = {"active": 0, "max": 0}
    guard = threading.Lock()

    class FakeTextPage:
        def get_text_bounded(self) -> str:
            return TEXT

        def count_chars(self) -> int:
            return 0

        def close(self) -> None:
            return None

    class FakePage:
        def get_textpage(self) -> FakeTextPage:
            return FakeTextPage()

        def close(self) -> None:
            return None

    class FakeDocument:
        def __init__(self, data: bytes) -> None:
            with guard:
                state["active"] += 1
                state["max"] = max(state["max"], state["active"])
            time.sleep(0.05)

        def __len__(self) -> int:
            return 1

        def __getitem__(self, index: int) -> FakePage:
            return FakePage()

        def close(self) -> None:
            with guard:
                state["active"] -= 1

    monkeypatch.setattr(pdf_module.pdfium, "PdfDocument", FakeDocument)
    threads = [
        threading.Thread(target=pdf_module.read_pdf_bytes, args=(b"%PDF-1.4 x", "c.pdf", LIMITS))
        for _ in range(4)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert state["max"] == 1


# --- risposte anomale di Bedrock ----------------------------------------------------------


class Throttled(Exception):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.response = {"Error": {"Code": code}}


class FlakyBedrockClient(FakeBedrockClient):
    def __init__(self, failures: list[Exception], stop_reason: str = "end_turn") -> None:
        super().__init__()
        self.failures = list(failures)
        self.stop_reason = stop_reason

    def converse(self, **request: Any) -> dict[str, Any]:
        if self.failures:
            self.requests.append(request)
            raise self.failures.pop(0)
        return {**super().converse(**request), "stopReason": self.stop_reason}


def test_a_transcription_cut_by_the_token_limit_is_an_error_not_a_shorter_page() -> None:
    client = FlakyBedrockClient([], stop_reason="max_tokens")
    with pytest.raises(IngestError, match="troncata") as caught:
        BedrockPageTranscriber(client, "m", "p").transcribe(png_bytes(), "image/png")
    assert caught.value.http_status == 502


def test_throttling_is_retried_with_backoff_and_then_succeeds() -> None:
    delays: list[float] = []
    client = FlakyBedrockClient(
        [Throttled("ThrottlingException"), Throttled("ModelTimeoutException")]
    )
    transcriber = BedrockPageTranscriber(client, "m", "p", retries=2, sleep=delays.append)
    text, _ = transcriber.transcribe(png_bytes(), "image/png")
    assert text == "testo trascritto"
    assert len(client.requests) == 3
    assert delays == [1.0, 2.0]


def test_throttling_gives_up_after_the_retries() -> None:
    client = FlakyBedrockClient([Throttled("ThrottlingException")] * 3)
    transcriber = BedrockPageTranscriber(client, "m", "p", retries=2, sleep=lambda _: None)
    with pytest.raises(IngestError, match="ThrottlingException"):
        transcriber.transcribe(png_bytes(), "image/png")
    assert len(client.requests) == 3


def test_a_request_the_service_rejects_is_not_retried() -> None:
    client = FlakyBedrockClient(
        [Throttled("ValidationException"), Throttled("ValidationException")]
    )
    transcriber = BedrockPageTranscriber(client, "m", "p", retries=2, sleep=lambda _: None)
    with pytest.raises(IngestError, match="ValidationException"):
        transcriber.transcribe(png_bytes(), "image/png")
    assert len(client.requests) == 1


def test_a_reply_without_text_blocks_is_an_empty_page_not_a_crash() -> None:
    class NoText(FakeBedrockClient):
        def converse(self, **request: Any) -> dict[str, Any]:
            return {"output": {"message": {"content": [{"reasoningContent": {}}]}}, "usage": {}}

    text, usage = BedrockPageTranscriber(NoText(), "m", "p").transcribe(png_bytes(), "image/png")
    assert text == "" and usage.sessions == 1


# --- limiti e letture non riuscite -----------------------------------------------------------


def test_a_file_over_the_profile_size_limit_is_413_before_the_model() -> None:
    fake = FakePageTranscriber([TEXT])
    limits = LIMITS.model_copy(update={"max_bytes": 50})
    for data, name in [(png_bytes(), "foto.png"), (scanned_pdf(), "scansione.pdf")]:
        with pytest.raises(IngestError) as caught:
            read_document_bytes(data, name, limits, fake)
        assert caught.value.http_status == 413
    assert fake.calls == []


def test_a_file_that_cannot_be_opened_is_400(tmp_path: Path) -> None:
    with pytest.raises(IngestError) as caught:
        read_document(tmp_path / "manca.pdf", LIMITS, None)
    assert caught.value.http_status == 400


def test_a_rendered_page_too_heavy_for_the_model_is_sent_as_a_lighter_jpeg(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from cycle_validation.ingest import document

    noisy = Image.open(io.BytesIO(noise_png(300, 200)))
    buffer = io.BytesIO()
    noisy.save(buffer, format="PDF")
    limit = 120_000  # il PNG e il primo JPEG della pagina di rumore pesano di più
    monkeypatch.setattr(document, "_MODEL_IMAGE_BYTES", limit)
    fake = FakePageTranscriber([TEXT])
    read_document_bytes(buffer.getvalue(), "scansione.pdf", LIMITS, fake)
    image, media_type = fake.calls[0]
    assert media_type == "image/jpeg" and len(image) <= limit
    assert Image.open(io.BytesIO(image)).format == "JPEG"


def test_bedrock_adapter_refuses_a_format_it_cannot_send() -> None:
    client = FakeBedrockClient()
    with pytest.raises(IngestError) as caught:
        BedrockPageTranscriber(client, "m", "p").transcribe(b"GIF89a", "image/gif")
    assert caught.value.http_status == 415
    assert client.requests == []


COLORS = ["red", "green", "blue", "yellow", "white", "black"]


def colored_scan(colors: list[str]) -> bytes:
    images = [Image.new("RGB", (200, 100), color) for color in colors]
    buffer = io.BytesIO()
    images[0].save(buffer, format="PDF", save_all=True, append_images=images[1:])
    return buffer.getvalue()


class ColorTranscriber:
    """Riconosce la pagina dal colore, aspetta che tutte le pagine siano in volo e risponde
    prima dalle ultime: se la trascrizione fosse in fila, la barriera scadrebbe."""

    def __init__(self, in_flight: int, fail_on: str | None = None) -> None:
        import threading

        self.barrier = threading.Barrier(in_flight, timeout=5)
        self.fail_on = fail_on
        self.seen: list[str] = []
        self._lock = threading.Lock()

    def transcribe(self, image: bytes, media_type: str) -> tuple[str, Usage]:
        import time

        # la pagina passa da un JPEG dentro il PDF: il colore torna vicino, non identico
        rgb = Image.open(io.BytesIO(image)).convert("RGB").getpixel((5, 5))

        def distance(name: str) -> int:
            ref = Image.new("RGB", (1, 1), name).getpixel((0, 0))
            return sum((a - b) ** 2 for a, b in zip(rgb, ref, strict=True))  # type: ignore[arg-type]

        color = min(COLORS, key=distance)
        with self._lock:
            self.seen.append(color)
        if color == self.fail_on:
            raise IngestError("pagina illeggibile", http_status=502)
        if self.fail_on is None:
            self.barrier.wait()
            time.sleep(0.01 * (len(COLORS) - COLORS.index(color)))
        return f"{TEXT} {color}", Usage(input_tokens=1)


def test_scanned_pages_are_transcribed_together_and_keep_their_order() -> None:
    # MIGLIORIE B3: 3 pagine da 5 s fanno 5 s, non 15 s
    colors = COLORS[:3]
    transcriber = ColorTranscriber(in_flight=3)
    document, usage = read_document_bytes(
        colored_scan(colors), "scan.pdf", LIMITS, transcriber, concurrency=3
    )
    assert [page.text for page in document.pages] == [f"{TEXT} {c}" for c in colors]
    assert [page.number for page in document.pages] == [1, 2, 3]
    assert usage.input_tokens == 3


def test_a_page_that_cannot_be_transcribed_stops_the_others() -> None:
    # le pagine oltre quelle in volo non si renderizzano né si mandano al modello
    transcriber = ColorTranscriber(in_flight=2, fail_on="red")
    with pytest.raises(IngestError, match="illeggibile"):
        read_document_bytes(colored_scan(COLORS), "scan.pdf", LIMITS, transcriber, concurrency=2)
    assert len(transcriber.seen) <= 3


def test_pages_are_transcribed_four_at_a_time_by_default() -> None:
    from cycle_validation.config import AgentSettings

    assert AgentSettings().transcribe_concurrency == 4


def test_the_pipeline_transcribes_with_the_configured_concurrency(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import dataclasses

    from support import make_deps

    from cycle_validation import pipeline
    from cycle_validation.pipeline import RunRequest, run_validation

    seen: list[int] = []

    def fake_read(*args: Any, concurrency: int = 1) -> Any:
        seen.append(concurrency)
        raise IngestError("fermo qui", http_status=400)

    monkeypatch.setattr(pipeline, "read_document_bytes", fake_read)
    deps, _ = make_deps()
    agent = deps.settings.agent.model_copy(update={"transcribe_concurrency": 7})
    deps = dataclasses.replace(deps, settings=deps.settings.model_copy(update={"agent": agent}))
    with pytest.raises(IngestError):
        run_validation(RunRequest(pdf_bytes=png_bytes(), pdf_name="foto.png"), deps)
    assert seen == [7]
