# Domande aperte

Decisioni e dati che servono da chi conosce i cicli e l'indice. Per rispondere basta scrivere
sotto ogni domanda. I valori negli esempi sono inventati (il repository è pubblico).
Aggiornato il 20-11-2026, con le risposte ricavate dal servizio precedente e da ingestion_v2
e con le scelte su task mancante, targa sconosciuta e ragionamento ridotto.

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

Come si corregge in knowledge-index, in ordine:

1. **Guardare la fonte.** Aprire il PDF TM alle pagine 14, 17 e 18 e vedere cosa c'è davvero
   nella colonna della funzione per la `90`. Se la frase «la descrizione breve…» è una nota
   a piè di tabella, il parser della tabella la sta prendendo per una riga.
2. **Togliere la nota.** Scartare le righe la cui "funzione" è una frase (molte parole,
   verbi, punto finale) invece di una lavorazione in maiuscolo. Meglio ancora fermare la
   lettura della tabella dove finisce la griglia.
3. **Sistemare gli accenti.** Leggere il testo nella codifica giusta (di solito il PDF dà
   UTF-8 e qualcuno lo rilegge come Latin-1, da cui `Ã¨` al posto di `è`). Un controllo
   semplice: nessun `Ã` o `â€` nei file pubblicati.
4. **Unire le righe ripetute.** Con la stessa targa su più righe, non tenere solo la prima:
   un solo record con le funzioni unite da `; ` senza doppioni
   (`{"tag": "90", "function": "AGGIUSTAGGIO; LAVAGGIO; COLLAUDO DIMENSIONALE"}`). È già la
   forma che il programma legge per le altre targhe.
5. **Se non si fa in tempo.** In `uncertainty.json` della stessa versione:
   `{"format": 1, "machine_tags": {"90": ["da_record_parziale"]}}`. La targa esce WARNING
   `DATO_INCERTO` invece di CORRETTO, finché l'indice non è corretto.
6. **Pubblicare e provare.** Nuova versione con `publish.py`, poi `kb-check` da questo
   programma: deve passare senza avvisi su `uncertainty.json`.

Risposta:

### 16. Task del capitolo 70 cercati nel manuale SPM (scelta da confermare)

Prova del 21-11-2026 su un ciclo MOS vero: il ciclo cita come fonte solo il manuale del motore
(l'OEM del piè di pagina), ma nel testo scrive anche task del capitolo 70
(`TASK 70-11-00-350-002`, valori inventati), che stanno nel manuale delle pratiche standard
(SPM, `kind: SPM` nel manifest). Prima il programma li cercava solo nel manuale citato e non li
trovava mai; lo stesso per i task delle recommendation DR con `manual: null`.

Scelta fatta: un task che comincia con `70-` e non è nei manuali citati si cerca nei documenti
con `kind: SPM`. Gli altri capitoli no. La citazione resta verificata sul testo dell'SPM.
Da confermare: il capitolo 70 è sempre e solo l'SPM? C'è un altro capitolo con la stessa
regola?

Risposta:

### 17. DR con `Accept as is`: scelta fatta, da confermare

Regola di prima, scelta all'inizio senza dati veri: con `Accept as is` (o `Reject`)
`dr_recommendation` usciva ERRATO e gli altri controlli non partivano, senza guardare le
operazioni. Dubbio dell'utente (21-11-2026): «Accept as is» non vuol dire «non si fa nulla».

Cosa si è visto sui dati veri (21-11-2026, messaggi 16 e 17):

- le 2 procedure DR pubblicate sono solo **procedure di riparazione** (16 righe, circa 1.250
  caratteri ciascuna: rimozione del difetto, raccordatura, ispezione visiva, attacco chimico,
  penetranti). «Accept as is», «reject», «condition» non ci sono mai;
- la disposizione per condition (`Repair`, `Accept as is`, `Reject`) sta quindi solo nelle
  recommendation dell'indice, non nel testo della procedura.

Nella prassi aeronautica «use/accept as is» vuol dire che il pezzo non conforme si usa senza
ripararlo, perché l'ingegneria l'ha giudicato accettabile; la decisione si registra e il pezzo
prosegue con ispezioni e documenti fino al rilascio.

**Scelta fatta (21-11-2026):**

| Disposizione | Esito di `dr_recommendation` | Gli altri controlli |
|---|---|---|
| `Repair` | CORRETTO | proseguono con i task e la procedura DR come riferimento |
| `Accept as is` (anche `Accept-as-is`, `Use as is`) | WARNING `DR_SENZA_RIPARAZIONE`: il pezzo si accetta senza riparazione, da controllare a mano che il ciclo non contenga le lavorazioni della procedura di riparazione | proseguono, **senza** la procedura DR come riferimento: una raccordatura nel ciclo non deve risultare giusta perché la procedura di riparazione la descrive |
| `Reject` | ERRATO `DR_NON_APPLICABILE` (il pezzo si scarta) | bloccati |
| più condition, una `Repair` e una `Accept as is` | CORRETTO, con una nota | proseguono con la sola `Repair` come riferimento |

Il programma non decide da solo se un'operazione è una riparazione: lo dice il WARNING e lo
guarda una persona. Provato sul ciclo DR vero (messaggio 18): WARNING, 0 errati, nessuna
sessione del modello; tutte le descrizioni `FONTE_ASSENTE`, perché senza la procedura di
riparazione resta solo il manuale del motore, che non è nella conoscenza. Da confermare con chi conosce i DR:

- per una condition `Accept as is` esiste un ciclo DR, e con quali operazioni?
- con `Reject` un ciclo di riparazione è sempre sbagliato?
- i task delle recommendation `Accept as is`, quando ci sono, che cosa sono? Oggi non si usano.

Risposta:

### 18. DR: serial number e condition chiesti a chi carica il ciclo

Il frontend (visto il 22-11-2026), dopo «Yes — DR cycle», chiede `Serial Number (S/N)` e
`DR Condition Numbers` (una o più, separate da virgole) prima del PDF. Dubbio dell'utente: si
possono togliere?

A cosa servono nella v2:

- il **serial number** è la chiave con cui si cerca la recommendation nell'indice. Senza, il
  controllo `dr_recommendation` non sa quale recommendation guardare, e i task e la procedura DR
  da usare come riferimento vengono da lì. Nella stampa c'è solo a volte: una delle stampe DR
  viste lo scrive («APPLY ON S/N …»), le altre no;
- la **condition** non è mai scritta nella stampa. Serve solo quando il serial number ha più di
  una recommendation (nei dati di prova 5 serial number su 17): sceglie quale vale, e quindi se
  la disposizione è `Repair`, `Accept as is` o `Reject`. Con una sola recommendation oggi la
  condition c'è ma non cambia niente.

Proposta, da decidere con chi usa il frontend:

| Campo | Proposta |
|---|---|
| serial number | facoltativo: se è vuoto si prende dalla stampa («APPLY ON S/N»); se non c'è neanche lì, il ciclo si ferma con un messaggio che lo chiede |
| condition | facoltativa: se il serial number ha una sola recommendation non serve; se ne ha più di una e manca, `dr_recommendation` esce WARNING ed elenca le condition possibili |

Il frontend può restare com'è: i campi restano, solo non più obbligatori. Da chiedere: chi
carica un ciclo DR il serial number e la condition li sa sempre? Dove li legge?

Risposta:

## Risposte date (20-11-2026)

### 13. Task citato che il manuale non ha

WARNING `FONTE_ASSENTE` subito, senza chiamare il modello: "I task citati (…) non sono nel
manuale: descrizione non confrontata". Prima il modello confrontava la descrizione con il testo
delle altre fonti del ciclo e l'esito cambiava da un giro all'altro. Interruttore:
`agent.skip_missing_task` (acceso). Per i cicli EJ200, che citano documenti e non task, non
cambia niente.

### 14. Targa che non c'è da nessuna parte

WARNING `TARGA_SCONOSCIUTA` ("va controllato come è scritta"), non più ERRATO. ERRATO resta
per una targa dei dati TM che non è tra le macchine attive.

### 15. Ragionamento ridotto

Acceso: `effort: low` nei controlli, `high` nella lettura del PDF (circa -30% di costo sui
casi di prova). Da confermare su Bedrock con la variante `effort_pieno`; per tornare indietro
basta lasciare vuoti i due campi in `config/settings.yaml`.

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
