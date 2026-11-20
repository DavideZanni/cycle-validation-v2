# Domande aperte

Decisioni e dati che servono da chi conosce i cicli e l'indice. Per rispondere basta scrivere
sotto ogni domanda. I valori negli esempi sono inventati (il repository è pubblico).
Aggiornato il 20-11-2026, con le risposte ricavate dal servizio precedente e da ingestion_v2.

## Ancora aperte

### 1. Targhe della stampa e targhe di `machine_tags.json`

Chiarito: la targa è la riga sopra della colonna TARGA (`XX/123`, `PREC01`); la riga sotto
(`AVM700`) è il centro responsabile e non si controlla. Non esiste una tabella di
corrispondenza. Il servizio precedente confrontava la targa stampata con Redshift
(`work_center_cd`) in modo esatto: il programma fa lo stesso (ERRATO se non è attiva), ma senza
badare a spazi e maiuscole.

Resta da vedere sui dati veri: le targhe di `machine_tags.json` hanno forme come `A0100` o
`500010`. Se le targhe stampate non ci sono, ogni operazione riceve un WARNING "targa non
presente nell'indice" (non un ERRATO). Basta contare, su un ciclo vero, quante targhe stampate
si trovano in `machine_tags.json` e quante su Redshift.

Risposta:

### 3. Schede `PG 300` / `300`

Chiarito: nessun codice toglie il prefisso `PG`. Il servizio precedente ignorava i trattini
(`CPEC522-BR` = `CPEC522BR`): ora il programma fa lo stesso, oltre a ignorare spazi e
maiuscole (`PG 300` = `PG300`). Resta da decidere se `PG 300` è la scheda `300`
dell'indice. Per EJ200 non conta: le schede non si verificano.

Risposta:

### 6. DR con `conditions: []`

Chiarito: la lista vuota non vuol dire né "tutte" né "mancante"; il prompt di ingestion dà
`condition_no = null` quando il DR non numera le condition. Il programma si comporta come il
servizio precedente: se il serial number ha una sola recommendation la usa per qualunque
condition; se ne ha più di una, quella con `[]` non viene mai scelta. Resta da decidere se debba
valere per tutte.

Risposta:

### 7. Targa `90` in `machine_tags.json`

Ingestion_v2 scarta solo righe annullate o senza targa e non guarda il contenuto; il campo
`needs_review` lo hanno quasi tutte le targhe. Per capire se è un errore dell'indice: aprire il
record TM di quella riga e guardare `page_number`, `row_index`, `status`, `cell_refs`. Non
cambia niente nel programma.

Risposta:

### 11. `SP.FIAT`

Il vecchio prompt prendeva come codici data-module sia lo `SP.ORIG.` sia lo `SP.FIAT` della
riga SCHEDA. Il programma legge solo lo `SP.ORIG.` e lo mostra sotto la scheda, senza
verificarlo. Lo `SP.FIAT` va letto e mostrato? Questi codici vanno verificati (per esempio nel
catalogo EJ200) o sono solo informativi?

Risposta:

### 12. Paragrafo della fonte citato

Il vecchio prompt estraeva anche il punto citato della fonte (`PAR. 1.1`; un riferimento di
richiesta come `RIF. SD S00/00000` non è un paragrafo). Oggi l'agente riceve tutta la
pubblicazione e trova il punto da solo. Serve estrarre il paragrafo, per indicarlo all'agente e
controllare che esista?

Risposta:

## Risposte date (20-11-2026)

### 2. Registro delle macchine attive

La tabella giusta è quella del vecchio `verify_active_TM`: filtro
`work_center_usage_cd = 'TO'`, targa nella colonna `work_center_cd`. Il nome della tabella va
messo in `MACHINES_QUERY` sul server (non è scritto nel repository, che è pubblico). Differenza
voluta: il vecchio servizio, se la query falliva, saltava il controllo fino al riavvio; qui la
targa esce WARNING "registro non raggiungibile" e la richiesta dopo riprova.

### 4. `current.json`

Esiste: è il puntatore scritto da `publish.py`, con versione, `path`, impronta, conteggi e lo
storico delle ultime tre versioni. Il programma usa solo `version` e `path` e ora accetta il
puntatore anche senza il campo `format`. Nella versione civile ci sono `manifest.json`,
`tasks.json`, `machine_tags.json`, `process_sheets.json`, `dr_recommendations.json` e
`documents/`; in quella EJ200 `catalog.json` e `text/`. Da provare comunque con `kb-check`.

### 5. Fonti EJ200

Anche RN ed EF, con priorità RDR, EF, RN (gli RI nell'indice diventano EF). Il programma ora le
trova nel testo sia con la parola davanti (`DELLA RN RN-EJ-000-0000-01`) sia da sole, perché i
codici cominciano con il tipo (`RN-EJ-…`, `EF000A0000-01`).

### 8. Issue vecchia citata dal ciclo

WARNING. Il ciclo che cita `EJ00020L-01` quando c'è la `-02` riceve sulla fonte "è disponibile
la issue 02, più recente"; il confronto delle operazioni resta sulla issue citata. (Il servizio
precedente confrontava con la più recente: se si preferisce così, è una modifica piccola.)

### 9. Visibilità

Il repository diventa privato (lo fa il proprietario da GitHub).

### 10. Codice vero in un messaggio di commit

Si lascia così: nessuna riscrittura della storia.

## Già decise (per memoria)

- Descrizione: copiata dal PDF così com'è, parole spezzate comprese; nessuna ricucitura.
- Op. `005` (riga NOTE): resta in tabella.
- RC dell'operazione: la `RIPARAZIONE :` della testata della pagina.
- Feedback EJ200: esiti reali; la Scheda è sempre N/A.
- Targa: la riga sopra della colonna TARGA; la riga sotto (centro responsabile) non si verifica.
- `needs_review`: promemoria per chi cura l'indice, ignorato dal programma.
- Il frontend (badge, «-» sotto la scheda, minuscole) lo gestisce un collega.
- Si lavora direttamente su `main`.
