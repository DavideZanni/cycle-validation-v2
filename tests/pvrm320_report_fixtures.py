"""Stampa PVRM320 sintetica nel formato reale (colonne TARGA / NUM. OPER / DESCRIZIONE).

Il contenuto è inventato: il formato è quello della stampa PVRM320 (testata ripetuta a ogni pagina,
righe con colonne separate da `*`, descrizione italiana e inglese divise da una riga di
asterischi, continuazioni tra pagine, piè di pagina con OEM e firme), il testo no.
"""

from cycle_validation.ingest.pdf import PdfDocument, PdfPage

SEP = "-" * 90
STARS = "* " * 20
CONT = "*** CONTINUAZIONE DALLA PAGINA PRECEDENTE ***"
NEXT = "*******  CONTINUA ALLA PAGINA SEGUENTE  ******"


def header(page: int, note: str = "72-00-00 REPAIR 001", repair: str = "B1") -> list[str]:
    return [
        " Azienda",
        " PGM PVRM320",
        f"  ** C I C L O   D I   L A V O R A Z I O N E **        DATA STAMPA 01-01-2030 PAG. {page:>3}",
        "                                                        *** STAMPA DI PROVA ***",
        "CICLO :   ABCD-12345678A100-1                DESCR.CICLO : TEST BLADE STAGE 1",
        "",
        "TIPO CICLO : NORMALE                         PROGETTO...   MOTORE-1/MOTORE-2",
        "CAMPO A..                                    CAMPO B...   X",
        "CAMPO C. VALORE                              NOTE.......",
        f"RIPARAZIONE : {repair}".ljust(46) + note,
        "=" * 90,
    ]


TABLE = [
    "=" * 90,
    "TARGA       * NUM.   *    DESCRIZIONE  OPERAZIONE                      *",
    "C.RESP.     * OPER   *                                                 * PRE",
    SEP,
]


def row(left: str = "", num: str = "", text: str = "") -> str:
    return f"{left:<12}* {num:<5} *  {text:<58}*"


def block(
    left: list[str], num: str, text: list[str], date: str | None = None, closed: bool = True
) -> list[str]:
    out = [row(text=f"D.T.   {date}".rjust(58) if date else "")]
    for index, line in enumerate(text):
        out.append(row(left[index] if index < len(left) else "", num if index == 0 else "", line))
    return out + ([SEP] if closed else [])


def page(number: int, body: list[str], footer: list[str] | None = None, **head: str) -> str:
    return "\n".join(header(number, **head) + TABLE + body + (footer or []))


FOOTER = [
    "RIP: B1 OEM: ABC123456".ljust(46) + "CHANGE: 7",
    "FIRMA A".ljust(32) + "NOME COGNOME".ljust(24) + "01-01-2030",
    "FIRMA B",
]


def civil_pages() -> list[str]:
    first = ["", "** PRIMA PAGINA SENZA TABELLA **"]
    body2 = block(
        ["NOTE", "000000"],
        "005",
        [
            "APPLICARE IL RIVESTIMENTO DI PROVA SUL PEZZO",
            "",
            "SECONDO MANUALE ABC123456 TASK 72-00-00 REPAIR 001",
            "",
            STARS,
            "",
            "APPLY THE TEST COATING ON THE PART",
            "",
            "I.A.W. ABC123456  TASK 72-00-00 REPAIR 001",
        ],
    )
    body2 += block(
        ["QQ/901", "RSP002"],
        "010",
        [
            "RITIRO E MARCATURA DEL PEZZO DI PROVA",
            "P/N ..................  S/N ..............",
            STARS,
            "PICK UP AND MARK THE TEST PART",
        ],
    )
    body2 += block(
        ["700001", "RSP001"],
        "040",
        [
            "PULIRE A SECCO LE ZONE INDICATE",
            "NOTA: COMPLETARE ENTRO TRE GIORNI",
            "DATA: ................  ORA: ................",
            STARS,
            "DRY CLEAN THE MARKED ZONES",
            NEXT,
        ],
        date="01-02-30",
        closed=False,
    )
    body3 = [row(text=CONT)]
    body3 += [
        row("700001", "040", "."),
        row("SCHEDA : SSS-900", "", "SP.ORIG. 11-22-33-444-555     SP.XXXX"),
        row("", "", "* ATTREZZATURA PREVISTA *"),
        row("", "", "Z0000001         ATTREZZO DI PROVA"),
        SEP,
    ]
    body3 += block(
        ["QQ/902", "RSP001"],
        "050",
        [
            "***** NOTA DI PROVA *****",
            "ASCIUGARE IL PEZZO DI PROVA",
            STARS,
            "DRY THE TEST PART",
        ],
        date="03-04-30",
    )
    body3 += [row(left="", num="", text=""), "", " " * 30 + "*** C O N T I N U A ***"]
    body4 = [
        row(text=CONT),
        *block(
            ["QQ/904", "RSP00A"],
            "100",
            ["VERIFICA CONCLUSIVA DI PROVA", "DO THE CLOSING TEST CHECK"],
            closed=False,
        ),
    ]
    return [
        "\n".join(header(1) + first),
        page(2, body2),
        page(3, body3),
        page(4, body4, FOOTER),
        "\n".join([*header(5), "ULTIMA PAGINA SENZA TABELLA", " ELENCO DI PROVA"]),
    ]


def ej200_pages() -> list[str]:
    note = "S26/00001"
    body = block(
        ["NOTE", "000000"],
        "005",
        [
            "QUESTO CICLO DI PROVA DESCRIVE COME",
            "SISTEMARE UN SEGNO.",
            "LAVORO DA FARE COME INDICATO NELLA RDR",
            "EJ000001R-01 (RIF. SD S26/00001).",
        ],
    )
    body += block(
        ["QQ/903", "RSP003"],
        "020",
        ["TOGLIERE IL SEGNO CON LA LIMA DI PROVA.", "MASSIMO 0.99MM;", NEXT],
        date="05-06-30",
        closed=False,
    )
    next_body = [row(text=CONT), row(text="SP.ORIG. X1Y22300001Z999ZZ     SP.XXXX"), SEP]
    next_body += [
        row("TG0001", "030", "PULIZIA DEL PEZZO SECONDO SCHEDA DI PROVA."),
        row("RSP004"),
        row("SCHEDA : PG 900", "", "SP.ORIG. X1Y22300002Z999ZZ     SP.XXXX"),
        SEP,
    ]
    footer = [
        "RIP: A3 OEM: AA/BB/CCC".ljust(46) + "CHANGE: 0",
        "FIRMA C".ljust(32) + "NOME COGNOME",
    ]
    return [
        page(1, body, repair="A3", note=note),
        page(2, next_body, footer, repair="A3", note=note),
    ]


def as_document(pages: list[str], name: str = "ciclo.pdf") -> PdfDocument:
    return PdfDocument(
        name=name,
        sha256="0" * 64,
        size_bytes=1,
        pages=tuple(PdfPage(number=i + 1, text=text) for i, text in enumerate(pages)),
    )
