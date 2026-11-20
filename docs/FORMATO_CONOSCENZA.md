# Formato della conoscenza pubblicata

Com'è fatta la conoscenza che knowledge-index pubblica su S3 e come la legge Cycle Validation.
Confrontato il 20-11-2026 con i file veri della versione di prova (manifest, catalogo EJ200,
schede di processo, recommendation DR). **Tutti i valori qui sotto sono inventati**: il
repository è pubblico, i file veri restano in azienda.

## Dove sta

```
<prefisso>/knowledge/civil/current.json   {"format": 1, "version": "<versione>", "path": "v/<versione>/"}
<prefisso>/knowledge/civil/v/<versione>/  manifest.json, documents/*.md, tasks.json, ...
<prefisso>/knowledge/ej200/current.json
<prefisso>/knowledge/ej200/v/<versione>/  catalog.json, uncertainty.json (facoltativo)
```

Il bucket e i due `current.json` si danno con le variabili d'ambiente (`BUCKETNAME`,
`CIVIL_KNOWLEDGE_POINTER`, `EJ200_KNOWLEDGE_POINTER`, vedi `docs/AZIENDA.md` 4.2). Il
prefisso predefinito (`Manufacturing AI/cv3/`) non è quello della versione di prova: va
impostato. Se manca `current.json` il servizio non trova la conoscenza.

## Civile

**`manifest.json`**: un documento per voce. Più documenti possono avere lo stesso `code`
(tutti i capitoli di un manuale): un ciclo che cita il manuale per codice trova il task nel
capitolo giusto.

```json
{"format": 1, "version": "20260101T000000Z", "documents": [
  {"key": "SPM_MAN0001_pb70-00-00-000_ch1", "file": "documents/SPM_MAN0001_pb70-00-00-000_ch1.md",
   "lines": 120, "version": "ch1", "title": "SPM_MAN0001_pb70-00-00-000_ch1",
   "code": "MAN0001", "kind": "SPM"}
]}
```

**`tasks.json`**: `manual` deve essere la `key` di un documento del manifest, non il `code`.
Altrimenti la conoscenza non si carica ("il manuale non è nel manifest"). *Non ancora visto
sui file veri.*

```json
[{"manual": "SPM_MAN0001_pb70-00-00-000_ch1", "task": "70-00-00-200-001", "line_start": 10, "line_end": 25}]
```

**`process_sheets.json`**: i codici si confrontano senza spazi né maiuscole
(`CPEC 000-BR` = `CPEC000-BR`). Con `engine_families` vuoto la scheda risulta presente, ma
l'applicabilità al motore non è verificata.

```json
[{"code": "CPEC 000-BR", "edition": "51", "treatment": "TRATTAMENTO DI PROVA",
  "engine_families": ["GENX"], "needs_review": true}]
```

**`dr_recommendations.json`**: con `manual: null` i task si cercano nei manuali citati dal
ciclo. Se un serial number ha una sola recommendation, questa vale per qualunque condition
(anche con `conditions: []`). Se ne ha più di una, valgono quelle con una condition in comune
con quelle richieste.

```json
[{"serial_number": "SN00000", "conditions": [1], "procedure": "Repair", "reference": "00000000",
  "manual": null, "tasks": ["72-00-00-200-001"], "needs_review": true}]
```

**`machine_tags.json`**: `{"tag": ..., "function": ...}`. *Non ancora visto sui file veri.*

## EJ200

**`catalog.json`**: una voce per issue. Il testo sta in `<document_id>/<content_hash>.md`.

```json
[{"code": "EJ00000X-02", "kind": "RDR", "issue": "02", "document_id": "EJ00000X-02-0000abcd",
  "content_hash": "0000000000000000", "title": "EJ00000X-02", "published": true,
  "partial": false, "references": ["EJ00000"]}]
```

Il `code` contiene già la issue (`EJ00000X-02` con `issue: "02"`). Il programma la toglie in
lettura, così le issue della stessa pubblicazione restano una sola pubblicazione. Un ciclo può
citare `EJ00000X-02` (quella issue), oppure `EJ00000X` o `EJ00000` (la issue più recente).

## `needs_review`

È un promemoria per chi cura l'indice ("da ricontrollare a mano"). Il programma lo accetta su
schede, targhe e recommendation DR e **lo ignora**: la voce vale come tutte le altre e nessun
esito cambia.

## Ancora da verificare

- `tasks.json` e `machine_tags.json` veri: con `kb-check` sulla fotografia (guida, 6.1);
- presenza di `current.json` nelle due cartelle `knowledge/`;
- schede dei cicli MOS: una scheda stampata `PG 300` corrisponde nell'indice al codice
  `PG 300` o `300`? Se è `300`, oggi risulta "non presente".
