# Formato della conoscenza pubblicata

Com'è fatta la conoscenza che knowledge-index pubblica su S3 e come la legge Cycle Validation.
Confrontato il 20-11-2026 con i file veri della versione di prova (manifest, catalogo EJ200,
schede di processo, recommendation DR, targhe). **I valori qui sotto sono inventati**, ma hanno
la stessa forma di quelli veri: il repository è pubblico, i file veri restano in azienda.
Le domande ancora aperte sono in `docs/DOMANDE_APERTE.md`.

## Dove sta

```
<prefisso>/knowledge/civil/current.json   {"format": 1, "version": "<versione>", "path": "v/<versione>/"}
<prefisso>/knowledge/civil/v/<versione>/  manifest.json, documents/*.md, tasks.json,
                                          machine_tags.json, process_sheets.json,
                                          dr_recommendations.json, uncertainty.json (facoltativo)
<prefisso>/knowledge/ej200/current.json
<prefisso>/knowledge/ej200/v/<versione>/  catalog.json, uncertainty.json (facoltativo)
```

Il bucket e i due `current.json` si danno con le variabili d'ambiente (`BUCKETNAME`,
`CIVIL_KNOWLEDGE_POINTER`, `EJ200_KNOWLEDGE_POINTER`, vedi `docs/AZIENDA.md` 4.2). Il
prefisso predefinito (`Manufacturing AI/cv3/`) non è quello della versione di prova: va
impostato. La versione ha la forma di una data e ora (`20260101T090000Z`).

Esito della verifica, file per file:

| File | Forma vista sui file veri | Esito |
|---|---|---|
| `manifest.json` | sì | va bene |
| `catalog.json` (EJ200) | sì | va bene; la issue dentro `code` ora si gestisce |
| `process_sheets.json` | sì | va bene; `needs_review` prima bloccava il caricamento, ora si ignora |
| `dr_recommendations.json` | sì | va bene |
| `machine_tags.json` | sì | il formato va bene; vedi la domanda sulle targhe |
| `tasks.json`, `current.json` | no | da vedere con `kb-check` |

## Civile

### `manifest.json`

Un documento per voce. Più documenti hanno lo stesso `code`, uno per ogni capitolo di un
manuale: un ciclo che cita il manuale per codice trova il task nel capitolo giusto.

```json
{
  "format": 1,
  "version": "20260101T090000Z",
  "documents": [
    {
      "key": "SPM_GEK0000_pb70-21-00-010_ch1",
      "file": "documents/SPM_GEK0000_pb70-21-00-010_ch1.md",
      "lines": 214,
      "version": "ch1",
      "title": "SPM_GEK0000_pb70-21-00-010_ch1",
      "code": "GEK0000",
      "kind": "SPM"
    },
    {
      "key": "SPM_GEK0000_spm-all-em-ic-70-10-00-010-100_ch1",
      "file": "documents/SPM_GEK0000_spm-all-em-ic-70-10-00-010-100_ch1.md",
      "lines": 388,
      "version": "ch1",
      "title": "SPM_GEK0000_spm-all-em-ic-70-10-00-010-100_ch1",
      "code": "GEK0000",
      "kind": "SPM"
    }
  ]
}
```

### `tasks.json`

`manual` deve essere la `key` di un documento del manifest, non il `code`, altrimenti la
conoscenza non si carica ("il manuale non è nel manifest"). *Non ancora visto sui file veri.*

```json
[
  {"manual": "SPM_GEK0000_pb70-21-00-010_ch1", "task": "70-21-00-200-001", "line_start": 12, "line_end": 40}
]
```

### `machine_tags.json`

`function` elenca le lavorazioni separate da `; `. Le targhe si confrontano senza spazi né
maiuscole (`A 0100` = `A0100`). Anche qui `needs_review` è un promemoria e si ignora.

```json
[
  {"tag": "1200", "function": "ASCIUGATURA; TRATTAMENTO TERMICO; TRATTAMENTO TERMICO LOCALE", "needs_review": true},
  {"tag": "500010", "function": "PROVE NON DISTRUTTIVE", "needs_review": true},
  {"tag": "500020", "function": "LAVAGGIO", "needs_review": true},
  {"tag": "A 0100", "function": "RIPORTO HVOF; RIPORTO PLASMA; RIPORTO FLAME", "needs_review": true},
  {"tag": "A01000", "function": "SABBIATURA", "needs_review": true},
  {"tag": "A01010", "function": "RETTIFICA DI PREPARAZIONE; RETTIFICA DI FINITURA", "needs_review": true}
]
```

Il controllo della targa usa due sorgenti. Prima il registro delle macchine attive (Redshift
o `MACHINES_FILE`): se la targa non c'è, l'esito è ERRATO. Poi questo file: se la targa non
c'è, l'esito è WARNING.

### `process_sheets.json`

I codici si confrontano senza spazi né maiuscole (`CPEC 100-BR` = `CPEC100-BR`). Con
`engine_families` vuoto la scheda risulta presente, ma l'applicabilità al motore non viene
verificata.

```json
[
  {"code": "10", "edition": "13", "treatment": "POST EMULSIFIED LEV.2", "engine_families": ["GENX"]},
  {"code": "6", "edition": "13", "treatment": "WATER WASHABLE LEV.2", "engine_families": ["GENX"]},
  {"code": "CPEC 100-BR", "edition": "51", "treatment": "ATTACCO LOCALE A TAMPONE SU PARTICOLARI IN LEGA DI MAGNESIO", "engine_families": [], "needs_review": true},
  {"code": "CPEC110-BR", "edition": "51", "treatment": "ATTACCO LOCALE A TAMPONE STAINLESS STEEL ETCHANT", "engine_families": ["LEAP"], "needs_review": true}
]
```

### `dr_recommendations.json`

Con `manual: null` i task si cercano nei manuali citati dal ciclo. Se un serial number ha una
sola recommendation, questa vale per qualunque condition, anche con `conditions: []`. Se ne ha
più di una, valgono quelle con una condition in comune con quelle richieste. `Accept as is` e
`Reject` danno ERRATO (la riparazione non va fatta).

```json
[
  {"serial_number": "AAAA0BBB", "conditions": [1], "procedure": "Repair", "reference": "01000001", "manual": null, "tasks": ["72-56-30-220-100"]},
  {"serial_number": "AAAA0BBB", "conditions": [2], "procedure": "Accept as is", "reference": "01000001", "manual": null, "tasks": ["72-56-30-220-101"]},
  {"serial_number": "AAAA1CCC", "conditions": [], "procedure": "Repair", "reference": "01000002", "manual": null, "tasks": ["72-56-31-200-800", "70-24-00-110-030"]},
  {"serial_number": "BBBB2DDD", "conditions": [3], "procedure": "Reject", "reference": "01000003", "manual": null, "tasks": ["72-56-32-220-180"], "needs_review": true}
]
```

## EJ200

### `catalog.json`

Una voce per issue. Il testo sta in `<document_id>/<content_hash>.md`.

```json
[
  {"code": "EJ00010X-01", "kind": "RDR", "issue": "01", "document_id": "RDR_EJ00010X_-_Housing-0a1b2c3d", "content_hash": "0a1b2c3d4e5f6071", "title": "RDR EJ00010X - Housing", "published": true, "partial": false, "references": ["EJ00010"]},
  {"code": "EJ00020L-01", "kind": "RDR", "issue": "01", "document_id": "EJ00020L-01-1a2b3c4d", "content_hash": "1a2b3c4d5e6f7080", "title": "EJ00020L-01", "published": true, "partial": false, "references": ["EJ00020"]},
  {"code": "EJ00020L-02", "kind": "RDR", "issue": "02", "document_id": "EJ00020L-02-2b3c4d5e", "content_hash": "2b3c4d5e6f708091", "title": "EJ00020L-02", "published": true, "partial": false, "references": ["EJ00020"]}
]
```

Il `code` contiene già la issue (`EJ00020L-02` con `issue: "02"`). Il programma la toglie in
lettura, così le issue della stessa pubblicazione restano una sola pubblicazione. Un ciclo può
citare `EJ00020L-01` (quella issue), oppure `EJ00020L` o `EJ00020` (la issue più recente, la 02).

## `needs_review`

È un promemoria per chi cura l'indice ("da ricontrollare a mano"). Il programma lo accetta su
targhe, schede e recommendation DR e **lo ignora**: la voce vale come le altre, nessun esito
cambia.
