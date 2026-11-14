"""Fabbrica di PDF minimi per i test e per l'esempio sintetico. Nessuna dipendenza esterna."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cycle_validation.domain.cycle import Cycle


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def build_pdf(pages: list[str]) -> bytes:
    """PDF con una pagina per elemento. Stringa vuota = pagina senza testo."""
    objects: list[bytes] = []
    kids = " ".join(f"{4 + 2 * index} 0 R" for index in range(len(pages)))
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objects.append(f"<< /Type /Pages /Kids [{kids}] /Count {len(pages)} >>".encode())
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    for index, text in enumerate(pages):
        operators = ["BT", "/F1 10 Tf", "40 760 Td", "12 TL"]
        operators += [f"({_escape(line)}) Tj T*" for line in text.split("\n")]
        operators.append("ET")
        stream = "\n".join(operators).encode("latin-1") if text else b""
        page = (
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Resources << /Font << /F1 3 0 R >> >> /Contents {5 + 2 * index} 0 R >>"
        )
        objects.append(page.encode())
        objects.append(b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream")

    output = bytearray(b"%PDF-1.4\n")
    offsets: list[int] = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(output))
        output += f"{number} 0 obj\n".encode() + body + b"\nendobj\n"
    xref_offset = len(output)
    output += f"xref\n0 {len(objects) + 1}\n".encode()
    output += b"0000000000 65535 f \n"
    for offset in offsets:
        output += f"{offset:010d} 00000 n \n".encode()
    trailer = f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
    output += (trailer + f"startxref\n{xref_offset}\n%%EOF\n").encode()
    return bytes(output)


def cycle_pdf_text(cycle: "Cycle") -> str:
    """Testo che un PDF di ciclo conterrebbe: ogni valore estratto vi compare."""
    lines = [f"CICLO {cycle.cycle_code} MOTORE {cycle.engine_model}"]
    lines += [f"FONTE {s.manual} TASK {s.task}" for s in cycle.sources]
    for operation in cycle.operations:
        lines.append(f"OPERAZIONE {operation.operation_number} {operation.operation_description}")
        lines.append(f"Targa {operation.machine_tag or '-'} Task {' '.join(operation.task_codes)}")
        if operation.process_sheet:
            lines.append(f"Scheda {operation.process_sheet.code}")
    return "\n".join(lines)


def synthetic_cycle_pdf(cycle: "Cycle") -> bytes:
    return build_pdf([cycle_pdf_text(cycle)])
