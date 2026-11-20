# Domande aperte

Decisioni e dati che servono da chi conosce i cicli e l'indice. Per rispondere basta scrivere
sotto ogni domanda. I valori negli esempi sono inventati (il repository è pubblico).
Aggiornato il 20-11-2026, con le risposte ricavate dal servizio precedente e da ingestion_v2.

## Ancora aperte

### 7. Targa `90` in `machine_tags.json` (da correggere nell'indice)

Nell'indice la targa `90` ha come funzione una frase rimasta dal documento («la descrizione
breve può essere scelta…»), con le lettere accentate rovinate. Nel record TM della stessa
ingestion `90` compare in tre righe (pagine 14, 17, 18) con funzioni AGGIUSTAGGIO, LAVAGGIO,
COLLAUDO DIMENSIONALE: sembrano due esecuzioni diverse. Due cose da vedere lato
knowledge-index:

- aprire il PDF TM alle pagine 14, 17 e 18 e il record TM su S3 che ha prodotto il file;
- con una targa ripetuta l'ingestion tiene solo la prima riga: le altre funzioni si perdono.

Perché conta: la funzione della targa arriva all'agente come informazione sull'operazione
("Macchina 90: …"). Una frase sbagliata lì può confonderlo. Il programma non cambia.

Risposta:

## Risposte date (20-11-2026)

### 1. Targhe

La targa è la riga sopra della colonna TARGA; la riga sotto (`AVM700`) è il centro
responsabile e non si controlla. Su un ciclo EJ200 vero le 10 targhe distinte (13 operazioni)
sono tutte in `machine_tags.json` (104 targhe), con corrispondenza esatta: nessun WARNING
atteso. Il registro attivo è Redshift (domanda 2): una targa non attiva dà ERRATO.

### 3. Schede `PG 300`

`PG 300` è un codice a sé: in `process_sheets.json` c'è `PG 300`, non `300` né `PG300`. I
codici solo numerici (`6`, `10`, `16`, …) sono altre schede. Nessun prefisso da togliere: il
programma resta così (spazi, trattini e maiuscole non contano).

### 6. DR con `conditions: []`

Se il serial number ha più recommendation e almeno una ha la lista vuota, il ciclo si ferma
con un WARNING di ambiguità ("va controllato a mano"): né scelta a caso né applicata a tutte.
Una recommendation unica con lista vuota vale per qualunque condition, come prima. Nei dati di
prova (23 righe, 17 serial number, 5 con più recommendation) il caso non c'è: le due righe a
lista vuota sono le uniche del loro serial number.

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
la issue 02, più recente"; il confronto delle operazioni resta sulla issue citata, quella su
cui la riparazione è stata approvata. Il servizio precedente confrontava con la più recente:
scelta cambiata di proposito.

### 11. `SP.ORIG.` e `SP.FIAT`

Come nel servizio precedente: nei cicli EJ200 i codici dopo `SP.ORIG.` e `SP.FIAT` sono i
codici data-module dell'operazione e si verificano come i task code. Si cercano nel testo
delle fonti citate: se mancano, WARNING. Lo SP.FIAT è quasi sempre vuoto; lo SP.ORIG. resta
anche sotto la scheda. Nei cicli civili il task sta nel testo e lo SP.ORIG. non si verifica.
Corretto anche un difetto trovato sulla stampa vera: lo SP.ORIG. in cima alla pagina dopo
"CONTINUA" si perdeva.

### 12. Paragrafo della fonte citato

Si mostra: il punto citato accanto al codice (`EJ00010X-01 PAR. 2.1` oppure
`AL PAR. 2.1 DELLA RDR …`) va nel campo `section` della fonte, nel payload, e arriva all'agente
come informazione ("Il ciclo cita EJ00010X-01, PAR. 2.1."). Non si verifica che il paragrafo
esista.

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
