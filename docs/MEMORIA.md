# Memoria del progetto

Qui c'è tutto quello che sappiamo già: com'è il PC aziendale, cosa si può fare, come funziona la
v2, il frontend, i problemi già visti e le decisioni prese. Serve a non rifare le stesse analisi.

**Claude la legge prima di ogni lavoro sulle prove e la aggiorna quando impara qualcosa di
nuovo.** Ultimo aggiornamento: 22-11-2026.

Il repository è pubblico: qui non ci sono mai valori veri (bucket, account, host, matricola,
codici di manuali, numeri DR, serial number, part number, codici dei cicli, contenuti EJ200).

Gli altri documenti:

| File | A cosa serve |
|---|---|
| `docs/COPILOT.md` | il file per lavorare sul PC: cosa fare adesso, blocchi da lanciare, domande per Copilot e per le persone |
| `docs/MEMORIA.md` | questo file |
| `docs/MIGLIORIE.md` | cosa migliorare, in che ordine, e il registro delle prove fatte |
| `docs/AZIENDA.md` | guida tecnica: installare, configurare, avviare il servizio, fare esperimenti, formato della conoscenza |

---

## 1. Dove siamo e cosa manca per la consegna (22-11-2026)

**In breve:** la v2 funziona sui cicli veri (MOS e DR) e legge tutte le stampe viste. Per
consegnarla mancano soprattutto **i collegamenti con l'azienda**: accesso degli utenti, macchine
attive, configurazione e pubblicazione. Sono lavori conosciuti, non problemi aperti. La misura
sugli errori veri aspetta i manuali nella conoscenza.

**Chiuso (non si riapre senza un fatto nuovo):**

- **Lettura delle stampe.** Il parser legge tutte le stampe PVRM320 viste (esempi MOS e DR e
  le cartelle `cicli MOS`), anche quelle modificate a mano e quelle con «OPERAZIONE
  EVENTUALE». Una stampa senza layout PVRM320 la legge il modello (sezione 10).
- **Regole DR** (`Accept as is` e `Reject` bloccano; serial number e condition facoltativi) e
  risposta nel formato del frontend di oggi (sezioni 8 e 9).
- **Tempi:** al massimo 131 s su un DR da 9 operazioni, sotto i 600 s del backend.
- **Come funziona la v1 in azienda** (risposte di Copilot C1-C20): frontend, permessi, avvio in
  locale, costruzione dell'immagine (sezione 9).
- **Una sola pipeline** per MOS, DR ed EJ200; il pulsante militare lo decide già il frontend
  con `permissions.json` (sezione 9).

**Da chiudere, in ordine.** Chi: C = Claude, U = utente.

| # | Cosa | Perché serve | Come si chiude | Chi |
|---|---|---|---|---|
| 1 | Macchine attive sul PC | senza, tutte le targhe escono `ERRORE_TECNICO` e il ciclo è `parziale` | COPILOT 5.1: il comando ora segue il database fino a `get_db_credentials` della v1 | U |
| 2 | Misura sugli errori veri | oggi la v2 trova 0 dei 10 errori dei cicli «con errori», perché mancano i manuali | ingestion del manuale citato, poi COPILOT 5.3; Claude confronta con i 10 errori | U, poi C |
| 3 | Accesso degli utenti come la v1 | il frontend manda solo il cookie con il token | **fatto nel codice** (22-11 sera): `API_AUTH=sdk`, scelto da solo quando c'è `AUTH_INTROSPECT_URL`, con gli stessi middleware della v1 (sezione 9). Da provare: COPILOT 5.2 | U |
| 4 | Stessa configurazione della v1 | in servizio la v2 deve partire con lo stesso secret «di ambiente» della v1, senza chiavi nuove | **fatto per l'avvio** (22-11 sera): `CV_ENV_SECRET` = nome del secret di ambiente, letto come `load_secrets`. Manca Redshift in servizio: come la v1, con `SECRET_NAME`, `get_db_credentials` e `redshift_connector` (stessa rete, nessun permesso nuovo), dopo 5.1 | C |
| 5 | Prova in locale | è il passo prima di develop | COPILOT 5.2: libreria nella v2, configurazione in `launch.json`, prova dal frontend con login | U |
| 6 | Pubblicazione in QA | oggi `buildspec.yml` costruisce solo la cartella della v1: un push della v2 su develop non cambia il servizio | Dockerfile della v2 come quello della v1 (Python 3.14, certificato, libreria in `vendor/`); su develop `cd app_cycle_validation_v2` nel buildspec. Per tornare indietro si rimette la riga | C, poi U |
| 7 | Pulsante Confirm | per usare DR senza serial number e condition | messaggio COPILOT 4.1 | U |
| 8 | Prova EJ200 | i dati EJ200 non escono da AWS | dopo il punto 6, dal frontend QA | U |
| 9 | Domande agli esperti | P1, P2, P6 (P4 per chi cura l'indice) | quando capita | U |

**Decisioni da prendere:**

- **D1. Dove scrivere il nome del secret «di ambiente» per la v2.** Nella v1 è scritto nel
  codice; nel repository personale (pubblico) non si può. Fatto così (22-11 sera, da
  confermare dall'utente): la v2 lo legge dalla variabile `CV_ENV_SECRET`; in locale la mette
  `launch.json`, nel container una riga `ENV` nel Dockerfile della copia aziendale (il blocco
  di aggiornamento non copia il Dockerfile).
- **D2. Quando passare a QA.** Proposta: dopo i punti 1-5 e una prova in locale riuscita con
  centralizer e login.

**Non serve per la consegna** (`MIGLIORIE.md`, «Da fare»): chiamata diretta a Bedrock (B1), più
concorrenza (B4), varianti proposte dal modello (E1), togliere le rotte storiche (D).

---

## 2. Chi fa cosa

| Chi | Cosa fa | Cosa non fa |
|---|---|---|
| **Claude** | cambia codice, test e documenti nel repository personale, solo su `main`; scrive i blocchi in `COPILOT.md`; legge le foto | non entra nel PC aziendale, in AWS, nel frontend né nel repository aziendale: vede solo le foto |
| **L'utente** | lancia i blocchi di `COPILOT.md` e manda le foto; fa commit e push nel repository aziendale | non cambia il codice a mano |
| **Copilot** (sul PC) | legge il codice e lancia prove e test | **non cambia il codice** e non legge `data/` |

**Come arriva una correzione sul PC:** Claude corregge su `main` → l'utente lancia *Aggiornare
il codice sul PC* → prova → *Salvare nel repository aziendale* (commit, poi push).

**Il repository aziendale:** la v2 sta nella cartella `app_cycle_validation_v2/`, sul branch
`feature/cycle-validation-v2`. La v1 (`app_cycle_validation/`) è in produzione e **non si
tocca**. Il push lo fa l'utente, mai con `--force`. Il README della radice del repository
aziendale descrive le due cartelle. Come è stata fatta l'importazione: storia git,
`docs/IMPORTAZIONE.md` al commit `e2da808`.

## 3. Il PC aziendale

- Windows 11, VS Code, terminale **PowerShell 7**: i comandi sono PowerShell, non bash.
- Il terminale deve stare nella cartella `app_cycle_validation_v2`.
- Python 3.14 (il progetto chiede 3.13): **ogni blocco comincia con
  `$env:UV_PYTHON = "3.14"`**. Si usa `uv`.
- `git clone` da GitHub funziona. I commit aziendali usano l'email aziendale.
- AWS con SSO, regione `eu-south-1`. Se il token scade: `aws sso login`.
- Proxy Zscaler: finora nessun problema di certificati. Se capita, la riga che lo risolve è
  in cima a `COPILOT.md`.
- L'antivirus tiene aperti per un attimo i file appena scritti: a volte esce
  `PermissionError [WinError 5]`. Il codice riprova da solo; un test può fallire una volta: si
  rilancia.
- **Quando incolli un blocco, il terminale esegue una riga alla volta.** In un `if` su più
  righe, `} elseif (...) {` e `} else {` devono stare sulla stessa riga della `}` che chiude,
  altrimenti si rompe. Meglio blocchi corti, un passo per blocco.
- Nel computer di Claude PowerShell non si installa: Claude rilegge i blocchi a occhio prima
  di darli.

## 4. Copilot

- Va usato in modalità **Ask** (in basso nella chat). In **Agent** può modificare file e
  lanciare comandi: non deve.
- Non può leggere `data/` né gli indirizzi S3 che ne vengono: è un blocco
  dell'organizzazione GitHub. **Non si aggira** (niente rinomine o spostamenti). Per questo i
  comandi li lancia l'utente.
- Può leggere il codice del repository aziendale: è utile per domande tipo «trova la funzione
  che fa X e incollala». Nel messaggio scrivere sempre «non modificare niente».
- Allega da solo il file aperto nell'editor: se è un file con accessi o password, va tolto
  dalla chat (la **x**) prima di scrivere.
- Se gli si incolla un testo senza domande, lo spiega e basta: le domande vanno scritte chiare
  (vedi la sezione 3 di `COPILOT.md`).

## 5. I servizi

- **Bedrock** (`eu-south-1`): modello `eu.anthropic.claude-haiku-5-5`, scritto in
  `data/settings.yaml`. Ci sono anche Sonnet 5.5 e Opus 5.5. Il costo nel report è una stima.
- **S3**: il nome del bucket è in `data/bucket.txt` (git lo ignora); i comandi lo leggono da lì
  e non lo stampano. Sotto `Manufacturing AI/`:
  - `cicli MOS/` e `cicli DR/`: i PDF veri dei cicli;
  - `ingestion-v2-test-qa-output/knowledge/civil/` e `.../ej200/`: la conoscenza di prova della
    v2;
  - `cv3/knowledge/`: vuota (è il percorso predefinito nel codice, da cambiare con
    `CIVIL_KNOWLEDGE_POINTER` quando si configura il servizio);
  - `retrieval_output/`: la conoscenza della v1.
- **Macchine attive**: in azienda vengono da Redshift (il database aziendale con l'elenco
  delle macchine). Su Redshift non si crea niente: si legge la tabella che legge la v1. La v1
  la legge in `verify_active_TM` con `redshift_connector` (porta 5439): colonne
  `work_center_cd` (la targa) e `work_center_usage_cd`, filtro `= 'TO'`. Le credenziali sono
  in un secret di Secrets Manager (`SECRET_NAME` in `config.py`). Se la query fallisce la v1
  salta il controllo; la v2 dà WARNING `ERRORE_TECNICO` e il ciclo è `parziale`.
  - **In servizio** la v2 usa la Data API (`REDSHIFT_*`, `MACHINES_QUERY`, `AZIENDA.md`).
  - **Sul PC** (dal 22-11): `cycle-validation macchine --v1 ..\app_cycle_validation`
    scrive `data\macchine_attive.json`; poi `run --machines data\macchine_attive.json`.
    Nella v1 il nome del secret di Redshift non è nel codice: `config.py` ha
    `SECRET_NAME = os.getenv("SECRET_NAME")`, e all'avvio `app_backend.py` chiama
    `load_secrets("<secret di ambiente>")` che mette le chiavi del secret di ambiente nelle
    variabili d'ambiente (`secret_loader.py`). Il comando fa lo stesso: legge il secret di
    ambiente, prende `SECRET_NAME`, legge il secret di Redshift, fa la query con la Data API.
    Stampa solo il numero di macchine.
  - **Il secret di Redshift** (prova del 22-11) ha i campi `dbClusterIdentifier`, `engine`,
    `host`, `password`, `port`, `username`: è un cluster, e **il database non c'è**.
  - **Da dove la v1 prende il database (C21):** in `verify_active_TM`
    `REDSHIFT_HOST, REDSHIFT_USER, REDSHIFT_PWD, REDSHIFT_DBNAME = get_db_credentials()`, poi
    `RedshiftConnector(host=..., port=5439, database=REDSHIFT_DBNAME, ...)`, che passa i
    valori a `redshift_connector.connect`. `get_db_credentials` sta in
    `src/config/credentials.py`, che Copilot non può leggere (esclusione dell'organizzazione).
    Il comando `macchine` segue il valore fino a quella funzione (analisi del codice Python, solo
    la struttura) e trova la chiave che legge; poi cerca la chiave nei due secret e
    nell'ambiente. Stampa solo il nome della chiave. Se non basta: `--database`.
  - **Perché Redshift e non il documento delle targhe su S3:** il documento dice se una targa
    esiste e che macchina è; Redshift dice se la macchina è in uso oggi. Una macchina dismessa
    che è ancora nel documento è un errore. Alternativa possibile: l'ingestion copia ogni
    giorno l'elenco delle attive su S3 e la v2 lo legge con `MACHINES_FILE`.
- **Frontend**: il gateway QA aziendale (pagina *Cycle Validation*) oggi parla con la v1. La v2
  non è ancora collegata.

## 6. La conoscenza di prova

È stato ingestionato solo un pezzo (i file sono circa 2000, tutti costerebbero troppo):

- 8 capitoli del manuale SPM (capitolo 70);
- 2 procedure DR;
- 104 targhe, 94 schede;
- 23 recommendation DR (17 serial number, 5 con più recommendation).

I **manuali dei motori non ci sono**: le righe che ne hanno bisogno escono WARNING
`FONTE_ASSENTE`, ed è giusto. **Decisione del 21-11-2026: per ora non si ingestiona altro.**

Sul PC la copia della parte civile è in `eval/casi/aziendali/conoscenza/foto-20261121/`; i PDF
dei cicli in `docs\Esempio ciclo mos\` e `docs\Esempio ciclo dr\` (git li ignora).

## 7. Regole sui dati

- La guida aziendale dice: *«I documenti e gli output EJ200 restano su AWS EU; non copiarli
  nella repository o fuori dall'ambiente autorizzato.»* Quindi:
  - nessuna copia della conoscenza EJ200 sul PC (quella scaricata per errore è stata cancellata
    il 21-11-2026);
  - **un ciclo EJ200 non si prova sul PC**, perché il risultato finirebbe in `runs\`. Va
    provato dentro AWS, per esempio con la v2 dietro il gateway QA;
  - nei documenti non si scrivono contenuti EJ200 visti nelle foto.
- I dati veri stanno solo in cartelle che git ignora: `data/`, `runs/`, `eval/casi/aziendali/`,
  `docs/Esempio*/`.
- Nel repository personale non vanno mai: bucket, account AWS, host, ARN, nomi dei segreti,
  matricola o utente Windows, codici dei manuali, numeri DR, serial number, part number, codici
  dei cicli. Negli esempi: valori inventati. I comandi prendono i codici veri dai file sul PC.
- Nelle foto possono comparire bucket, codici, percorsi con la matricola: Claude **non li
  ripete**, né in chat né nei documenti.
- `report.md` non si manda a Claude (contiene i testi dei manuali). Bastano le righe di
  riepilogo; i giudizi l'utente li dà a parole.

---

## 8. Come funziona la v2, in breve

Più dettagli in `MIGLIORIE.md` e `AZIENDA.md`.

1. **Legge il PDF.** Prima prova il lettore a regole fisse (il "parser"), che non costa niente;
   se non riconosce la stampa, usa il modello. Il parser è più stabile: si tiene.
2. **Controlla la lettura.** Ogni valore letto deve comparire nel PDF; se no, WARNING
   `ESTRAZIONE_NON_CONFERMATA`.
3. **Fa i controlli** previsti per il tipo di ciclo (`config/profiles/mos|dr|ej200.yaml`):
   - `dr_recommendation` (solo DR): se fallisce, gli altri controlli non partono;
   - `source`: le fonti citate esistono;
   - `task_code`: i task citati esistono;
   - `machine_tag`: la targa esiste ed è attiva;
   - `process_sheet`: la scheda esiste (per EJ200 non si controlla: N/A);
   - `operation_description`: la descrizione dell'operazione è d'accordo con la fonte.
4. **Decide l'esito con il codice**, non con il modello:
   - CORRETTO: tutto verificato;
   - ERRATO: una contraddizione, una macchina non attiva, una DR che non si applica;
   - N/A: il campo non c'è o il controllo non vale per quel ciclo;
   - WARNING: tutto il resto (fonte mancante, prova non trovata, guasto, giudizio incerto…).
     **Un guasto dà sempre WARNING, mai ERRATO.**
5. **Il modello giudica solo la descrizione**, confrontandola con il testo della fonte. Ogni
   sua citazione viene ricercata dal codice; se non c'è, WARNING. Se dice ERRATO, la domanda si
   rifà 2 volte: resta ERRATO solo se lo ridicono tutte, altrimenti WARNING
   `GIUDIZIO_INSTABILE`.
6. **Stato del ciclo:** `bloccato` se fallisce il controllo DR; `parziale` se c'è un guasto
   (oggi sempre, per le macchine attive); altrimenti `completo`.
7. **Risultato:** `report.json`, `report.md` e `payload.json` (lo stesso formato che il frontend
   riceve oggi dalla v1).

**Regole per i DR:**

| La DR dice | Esito del controllo DR | Gli altri controlli |
|---|---|---|
| `Repair` (ripara) | CORRETTO | vanno avanti, con i task e la procedura DR come riferimento |
| `Accept as is` / `Use as is` (va bene così) | ERRATO: un ciclo di riparazione non dovrebbe esistere | si fermano |
| `Reject` (scarta) | ERRATO | si fermano |
| `Repair` e `Accept as is` insieme (condition diverse) | CORRETTO, la parte `Accept as is` si salta | solo la `Repair` come riferimento |

È la regola della v1, confermata dall'utente il 22-11-2026 (prima, dal 21-11, `Accept as is`
dava solo un WARNING).

**Serial number e condition sono facoltativi** (decisione del 22-11-2026, per rendere il
frontend meno macchinoso):

| Cosa c'è | Cosa succede |
|---|---|
| serial number dato da chi carica | si usa quello |
| serial number non dato, ma scritto nella stampa («APPLY ON S/N …») | si prende dalla stampa |
| nessun serial number | WARNING `DR_NON_VERIFICATA`; gli altri controlli vanno avanti, senza la procedura DR |
| condition non data, una sola recommendation | si usa quella |
| condition non data, più recommendation tutte `Repair` | valgono tutte |
| condition non data, recommendation diverse (`Repair` e `Accept as is`/`Reject`) | WARNING `DR_NON_VERIFICATA`; si va avanti con le sole `Repair` |
| condition non data, nessuna `Repair` | ERRATO, ciclo bloccato |

Il frontend può quindi togliere l'obbligo delle due domande (oggi il pulsante Confirm resta
spento se sono vuote: sezione 9); finché le fa, i valori dati si usano come prima. Il serial
number è scritto solo in alcune stampe; la condition mai.

## 9. Il frontend della v1

Visto dalle foto e dal codice (risposte di Copilot, 22-11-2026).

**Dove sta.** Non nel repository della v1: è nel repository del frontend del collega. La
pagina con le domande è `CycleValidationPage.tsx`, i risultati li mostra
`CycleValidationResultDisplay.tsx`. L'indirizzo del backend viene dalla variabile
`VITE_BACKEND_URL`.

**Percorso.** «Which cycle do you want to validate?» → *Civil cycle (DR/MOS)* oppure *EJ200
cycle (military)*.

- Civile: `GET /cycle_validation/flow/start?session_id=…`, poi «Devi validare un ciclo DR?»
  → `POST /cycle_validation/conversation` con `{answer: "yes"|"no"}`. Se è DR, chiede
  `Serial Number (S/N)` e `DR Condition Numbers` e li manda con un secondo
  `POST /cycle_validation/conversation` `{dr_serial_number, dr_condition: [1, 2]}`.
- Poi il PDF: `POST /cycle_validation/upload?session_id=…`, form con `file`, `is_dr`,
  `dr_serial_number`, `dr_condition` (qui come testo `"1,2"`).
- **Il pulsante Confirm resta spento se serial number o condition sono vuoti.** Per togliere
  le due domande il collega deve cambiare questo (messaggio pronto in `COPILOT.md`). La v2 è
  già pronta: accetta i due campi vuoti in tutti e due i passi.
- EJ200: rotte sotto `/cycle_validation/ej200/…`; l'upload ha solo `file`.
- Altre rotte: elenco, apertura, salvataggio e cancellazione delle chat
  (`/cycle_validation/sessions…`), pollice su/giù (`POST /cycle_validation/feedback`).
  L'header `sso` porta l'utente.

**Risposta letta.** `{state, result: {file_name, payload, error}, error, error_info,
finished_at, job_id}`. Dal `payload`:

- in alto: `cycleCode`, `cycleDescription`, `operationType`, `repairCode`,
  `cycle_errors_count`, `_pipeline_errors`;
- `sources`: `repairCode`, `DRCase`, `manual`, `serialNumber`, `task`, `sourceFeedback`. La
  colonna *Type* dice «DR Case» se la riga ha `DRCase`, altrimenti «Manual»;
- `operations`: `operationNumber`, `operationDescription`, `repairCode`, `targaCResp`,
  `taskCodeCited`, `scheda.tabNumber`, `scheda.task`, `scheda.class` e i quattro feedback;
- **non legge** `cycle_status` né `drRecommendationFeedback`. `_pipeline_errors` va nel
  riquadro «Pipeline issues»;
- l'etichetta «MOS Cycle», «DR Cycle», «EJ200 Cycle» la sceglie il frontend dal percorso.

**Bollini** (funzione `feedbackSeverity`, guarda solo l'inizio del testo, maiuscole non
contano):

| Testo | Bollino |
|---|---|
| vuoto, oppure esattamente `N/A` | `N/A` grigio |
| comincia con `error` | `Error` rosso |
| comincia con `warning` | `Warning` giallo |
| comincia con `no error` | `OK` verde |
| qualsiasi altro testo (anche `N/A - motivo`) | `Info` azzurro |

**Intestazione.** «Validation Failed» se `state` è `failed`. «Completed with Errors» se
`cycle_errors_count > 0` oppure `_pipeline_errors` non è vuoto. Altrimenti «Validation
Passed», **anche con dei Warning**. Il «N errors» in alto è `cycle_errors_count`; il «1 err»
vicino all'operazione lo conta il frontend (feedback dell'operazione che cominciano con
`error`). Nella v1, quando il DR ferma il ciclo, `cycle_errors_count = 1`.

**Download.** Un CSV fatto dal browser (`cycle_validation_<nome>_<data>.csv`): metadati, fonti,
operazioni. Il backend non è chiamato.

**Tempi massimi.** Frontend: 300 s per le chiamate normali, **660 s per l'upload**. Backend v1:
gunicorn con `--timeout 600`. Un commento parla di 650 s nel gateway nginx, ma nei file non
c'è. **La v2 deve finire una validazione in meno di 10 minuti.** Misurato il 22-11-2026 sui
cicli DR da 9 operazioni: al massimo 131 s (con la lettura del PDF fatta dal modello), di solito
12-30 s; 0 s quando nessun controllo chiama il modello (ciclo bloccato, o DR senza riferimento).
Un ciclo MOS lungo è ancora da misurare.

**«N/A, non verificato per EJ200».** Nasce nel backend v1 (`ej200/validation.py`) e va in
`schedaFeedback` quando un'operazione EJ200 ha una scheda. Il frontend lo mostra `Info`
azzurro perché non è esattamente `N/A`.

**Come la v2 si adatta** (dal 22-11-2026, `report/legacy_payload.py`):

- `N/A` esatto (grigio) quando il campo manca o il controllo non è partito perché il DR ha
  fermato il ciclo; `N/A - motivo` (azzurro) quando il controllo è escluso per una regola o
  per il tipo di ciclo, come fa la v1 con le schede EJ200;
- l'esito DR va nella riga della fonte che cita il DR (con `DRCase` e `serialNumber`); se
  nessuna fonte lo cita, si aggiunge una riga DR in cima alle fonti. Se la fonte ha anche un
  suo avviso, si mostra prima il più grave e poi l'altro, separati da ` | `;
- la scheda ha i campi che il frontend mostra, riempiti come nella v1: `tabNumber` = il codice;
  `task` = il codice dopo «SP.ORIG.» nei cicli civili, vuoto negli EJ200; `class` vuoto (la v2
  non la legge).

**La scheda nella v1** (risposta C13). Civile: il modello legge solo la riga dopo `SCHEDA`
(prompt `cycle_extraction.yaml`): `tabNumber` il codice, `task` il codice sulla stessa riga
(senza «SP.ORIG.»/«SP.FIAT»), `class` la lettera dopo «Class». I task dopo `SCHEDA` non vanno
in `taskCodeCited`; se manca il codice ma c'è un task, `check_task_codes` sposta il task in
`taskCodeCited` e la scheda diventa vuota. EJ200 (`ej200_cycle_extraction.yaml`, `_scheda`):
solo `tabNumber`; `task` e `class` sempre vuoti; le righe SCHEDA si tolgono dalla descrizione.

**DR fermo nella v1** (risposta C14, `DR_source_validation`, `process_single_cycle_bytes`):

- il motivo va in `sources[0].sourceFeedback`, in inglese, uno per caso (`Accept as is`,
  `Reject`, nessuna recommendation: «Error found: no matching DR data found…», serial number e
  condition mancanti). Il frontend lo mostra nella riga «DR Case»;
- ogni operazione riceve `fallbackFeedback: "Error during validation."` (il frontend non lo
  mostra); `_pipeline_errors` riceve un messaggio generico «Attenzione: validazione
  bloccata…»;
- `DRCase` lo legge il modello dalla prima operazione (la NOTE, di solito 005/010);
  `serialNumber` è quello scritto dall'utente, in maiuscolo (sovrascrive quello letto dal PDF).
  Per un DR serial number e condition sono obbligatori (`_enforce_dr_policy`);
- **se il modello non trova il `DRCase`, la v1 salta del tutto la validazione DR.** La v2 no:
  senza riferimento dà WARNING `DR_NON_VERIFICATA`.

**La v1 non è un riferimento.** Dà errori falsi (su un ciclo EJ200, due «Error» con valori che
rispettano il limite) e giudizi diversi per casi uguali. Per sapere se la v2 ha ragione serve
chi conosce i cicli.

### Come si prova e si pubblica la v1 (risposte C18-C20, 22-11-2026)

**L'utente:** in locale si avviano da Run and Debug centralizer, login e il backend da provare;
quando funziona, push su `develop` (QA) e poi su `main` (produzione).

**In locale.** Un solo `launch.json`, nella radice del workspace. La configurazione composta
«CV» avvia insieme login, backend della v1 e frontend; prima lancia il task «Centralizer
prerequisites» (`tasks.json`, lo script che apre i tunnel verso OpenSearch).

| | Backend v1 | Login | Frontend (centralizer) |
|---|---|---|---|
| Comando | debugpy, modulo `uvicorn app_backend:app --reload --port 8003` | debugpy, `uvicorn app_backend:app --reload --port 8000` | `npm run dev` (vite) |
| Cartella | `app_cycle_validation` | la cartella del login | la cartella del frontend React |
| Python | `.venv` della cartella | `.venv` della cartella | — |
| Porta | 8003 | 8000 | 3000 |
| Variabili nel launch | `AWS_PROFILE` | `AWS_PROFILE`, `REDIRECT_URI`, `FRONTEND_URL` | nessuna (`.env.development`) |
| Configurazione | all'avvio `load_secrets("<secret di ambiente>")` copia le chiavi di un secret AWS in `os.environ` | allo stesso modo, con il suo secret | `.env.development` |

`VITE_BACKEND_URL` è vuota: il frontend chiama indirizzi relativi e il proxy di vite manda
`/login` alla porta 8000 e `/cycle_validation/` alla 8003. Per provare la v2 basta avviarla
sulla porta 8003 al posto della v1.

Variabili della v1 (solo i nomi, da `config.py`, `app_backend.py`, `logger.py`): API e log
(`API_MAX_WORKERS`, `API_INCLUDE_TRACEBACK`, `FRONTEND_URL`, `ENVIRONMENT`, `LOG_LEVEL`);
OpenSearch e RAG (`OPENSEARCH_HOST`, `OPENSEARCH_KNOWLEDGE_BASE_INDEX`, `RAG_TOP_K`,
`CHUNK_*`); modello (`EMBEDDING_*`, `LOCAL_MODEL_*`, `MODEL_ID`, `BEDROCK_MODEL_ID`, costi dei
token); S3 e AWS (`BUCKETNAME`, `REGION_NAME`, `SECRET_NAME`, `RAW_PATH`, `TM_STRUCTURED_PATH`,
`SP_STRUCTURED_PATH`, `DR_STRUCTURED_PATH`, `CA_BUNDLE_PATH`); EJ200 (`EJ200_OPENSEARCH_INDEX`,
`EJ200_CATALOG_KEY`, `EJ200_VALIDATION_ENABLED`); accesso (`AUTH_INTROSPECT_URL`,
`AUTH_CLIENT_ID`, `AUTH_CLIENT_SECRET`, `AUTH_EXPECTED_CLIENT_ID`, `AUTH_SSO_CLAIM`,
`AUTH_PERMISSIONS_BUCKET`, `AUTH_PERMISSIONS_KEY`, `AUTH_CACHE_TTL_S`).

**Costruzione e pubblicazione.** `buildspec.yml` sta nella radice del repository aziendale e fa
`cd app_cycle_validation`, poi `docker build`: **costruisce solo la v1**. La v2 ha un suo
Dockerfile, ma oggi nessuno lo costruisce: un push della v2 su develop o main non cambia il
servizio. Il Dockerfile della v1: Python `3.14.10-slim`, copia `ca-certificates.crt` (lo prende
la macchina di CodeBuild), installa AWS CLI, torch solo CPU, `requirements.txt` con la libreria
in `vendor/`, gunicorn con 1 worker sulla porta 8000. Immagine in ECR con due tag: i primi 7
caratteri del commit e `latest`. Nel buildspec non c'è nessuna regola sui branch: quale branch
fa partire la build si decide in CodeBuild/CodePipeline, fuori dal repository (la documentazione
dice develop = QA, main = produzione). Le variabili di CodeBuild: `AWS_REGION`,
`AWS_ACCOUNT_ID`, `ECR_REPO_NAME`, `CODEBUILD_RESOLVED_SOURCE_VERSION`. La configurazione non è
nell'immagine: arriva dal secret letto da `load_secrets`, con lo stesso nome nei due ambienti
(cambia l'account AWS).

### Accesso ai cicli militari (22-11-2026, risposte C15-C17)

Cosa vuole l'utente: chi entra ed è autorizzato ai cicli militari vede i pulsanti civile (MOS,
DR) e militare (EJ200); gli altri vedono solo MOS e DR. Una sola pipeline per i tre.

- **Pipeline:** è già la stessa (`run_validation`). Cambiano solo le impostazioni del profilo:
  EJ200 cita pubblicazioni intere, le schede EJ200 non si verificano, la conoscenza EJ200 resta
  su AWS EU, il DR aggiunge la recommendation che blocca.
- **Come fa oggi il frontend (C15):** il pulsante militare (`ScopeChooser`) compare solo se
  l'utente è nella lista `cv_ej200` o `all` di `permissions.json` su S3. Il frontend la riceve
  da `GET {BACKEND_URL}/login/permissions` (servizio di login, `get_s3_permissions`, cache 10
  minuti, solo le voci dell'utente verificato dal token). Non viene dai gruppi SSO. Chi è in
  `cv_ej200` vede anche il civile. Quello che l'utente vuole **c'è già** nel frontend.
- **Cosa manda il frontend (C16):** solo l'header `sso` (nome utente), `Content-Type` e il
  cookie di sessione HttpOnly con il token. **Nessun header con i permessi.** Chiavi dei
  servizi: `all`, `cv`, `cv_ej200` e altre di altri progetti.
- **Come controlla la v1 (C17):** middleware della libreria interna `chatbot_ai_sdk` (file
  `.whl` in `vendor/`): `AuthMiddleware` con `IntrospectionValidator` (token del cookie,
  pubblica solo `/cycle_validation/health`) e `ServiceAccessMiddleware` (servizi `cv`,
  `cv_ej200`; sotto `/cycle_validation/ej200` solo `cv_ej200`; permessi da
  `S3PermissionsSource.from_env()`). In più `Depends(current_user)` sul router EJ200. L'utente
  viene dal token (`current_user(request).sso`), non dall'header `sso`. Risposte: 401 token
  mancante o non valido; 403 senza permesso; 503 se il provider d'identità o
  `permissions.json` non rispondono.
- **Come controlla il token (C19).** In `app_backend.py`:
  `AuthMiddleware(validator=IntrospectionValidator(AuthSettings.from_env()),
  public_paths={"/cycle_validation/health"}, allowed_origins=[FRONTEND_URL])` e
  `ServiceAccessMiddleware(..., permissions=S3PermissionsSource.from_env())`. Il token arriva
  dal cookie HttpOnly del login (vale anche `Authorization: Bearer`); l'`Origin` deve essere
  `FRONTEND_URL`. `IntrospectionValidator` chiede all'identity provider SSO se il token è
  valido (`AUTH_INTROSPECT_URL` e gli altri `AUTH_*`). **In locale è uguale**: niente token
  finti. `permissions.json` si legge sempre da S3 (`AUTH_PERMISSIONS_BUCKET`,
  `AUTH_PERMISSIONS_KEY`); se non si legge, 503.
- **La libreria (prova sul PC, 22-11):** `chatbot_ai_sdk.auth.middleware.AuthMiddleware(app,
  validator, public_paths, allowed_origins)` (tutto protetto per default, tranne i preflight
  CORS; l'utente va in `request.state.user`); `chatbot_ai_sdk.auth.middleware.current_user(request)
  -> VerifiedUser`; `chatbot_ai_sdk.auth.validator.IntrospectionValidator(settings, *,
  transport, clock)`. Variabili lette direttamente: `AUTH_CACHE_TTL_S`, `ENVIRONMENT`,
  `LOG_LEVEL`. `ServiceAccessMiddleware` e `S3PermissionsSource` non sono usciti: COPILOT 5.2.
- **Come la v1 usa la libreria (C21).** Import: `from chatbot_ai_sdk.auth import
  AuthMiddleware, AuthSettings, IntrospectionValidator, current_user, ServiceAccessMiddleware,
  S3PermissionsSource` (in `routes.py` anche `VerifiedUser`). Chiamata:
  `app.add_middleware(ServiceAccessMiddleware, service_keys={"cv", "cv_ej200"},
  path_service_keys={"/cycle_validation/ej200": {"cv_ej200"}},
  permissions=S3PermissionsSource.from_env())`. Le rotte civili leggono solo
  `username = current_user(request).sso`; il router EJ200 ha
  `dependencies=[Depends(current_user)]` e usa `user.sso`. `VerifiedUser` ha `sso` e
  `client_id`. **Nessuna rotta legge i servizi dell'utente** e non c'è `request.state` nel
  codice: il permesso lo controlla solo il middleware.
- **Cosa fa la v2 (dal 22-11 sera, `api/auth.py`).** `API_AUTH=sdk` (scelto da solo se c'è
  `AUTH_INTROSPECT_URL`, cioè con il secret della v1): gli stessi tre pezzi della v1 (token,
  permessi, utente) con gli stessi parametri; l'utente delle sessioni e dei feedback è
  `current_user(request).sso`. I servizi non arrivano alle rotte, quindi la v2 li deduce dal
  percorso, già controllato dalla libreria. Conseguenza: le rotte nuove
  `validation/options` e `validation/upload` non offrono il militare; i cicli militari passano
  da `/cycle_validation/ej200/...`, come nel frontend di oggi. Senza la libreria installata la
  v2 non parte (meglio che partire senza controllo). `API_AUTH=header` resta per le prove.
- La libreria nella v2: `uv pip install` del `.whl` della v1 (COPILOT 5.2). `uv run` la
  lascia; `uv sync` la toglierebbe (va reinstallata).
- `GET /validation/options` della v2 mostra il pulsante militare solo a chi ha `cv_ej200` o
  `all` (per un frontend futuro; quello di oggi usa `/login/permissions`).

## 10. Stato delle prove (22-11-2026)

Con Bedrock Haiku 5.5 e la conoscenza di prova:

- **MOS:** terzo ciclo con 7 corretti, 16 warning, 0 errati, 14 N/A, 0,0058 USD. I warning
  vengono dai manuali dei motori che mancano e dalle macchine attive non collegate.
- **DR:** le tre condition del ciclo vero danno l'esito atteso.
  - `Repair`: 5 corretti, 0 errati, 0,006-0,011 USD, 9-11 chiamate al modello per prova.
  - `Accept as is`: provata il 21-11 con la regola di allora (WARNING); dal 22-11 dà ERRATO
    e ciclo bloccato. Da riprovare sul PC insieme al DR senza serial number e condition.
  - Descrizioni: 4 CORRETTO, 5 WARNING `EVIDENZA_NON_TROVATA`; la scheda dell'op. 050 non è
    tra le 94 schede.
- **EJ200:** mai provato con i servizi veri (va fatto dentro AWS).
- **Cicli MOS «con errori» (22-11):** sono 3 cicli diversi, ognuno in due cartelle di
  `ProgettoDocumenti`; si chiamano con le prime 8 lettere dell'impronta SHA-256. Sono stampe
  modificate a mano: l'editor mette in fondo al PDF le righe toccate e a volte toglie loro le
  colonne TARGA e NUM. OPER. Dal 22-11 la lettura rimette le righe in ordine di posizione e
  attacca all'operazione in corso le righe senza colonne (solo nelle pagine rimesse in
  ordine).
  - **Errori trovati con `confronta`** (stampa giusta contro «con errori»):
    - `298bc28e` (giusta `4e64d49a`): op. 005 un codice cambiato nella descrizione; op. 035
      parole cambiate nella descrizione.
    - `c5ff3cd6` (giusta `8bdb25d5`): op. 030 scheda tolta; op. 040 un numero cambiato.
    - `f355dc3c` (giusta `04ecaabe`): op. 010 tre numeri cambiati; op. 030 numeri e parole
      cambiati; op. 040 una lettera cambiata (la classe); op. 050 una frase sostituita (dice
      il contrario della giusta).
  - **La v2 non ne trova nessuno** (prova del 22-11 sera, righe in ordine): 0 errati in tutti
    e tre. Motivo: i manuali citati non sono nella conoscenza di prova (fonti `FONTE_ASSENTE`,
    descrizioni non confrontate). La scheda tolta esce N/A come nella v1 (P6). Per misurare la
    v2 su questi errori servono quei manuali nella conoscenza.
  - Gli `ERRORE_TECNICO` (7-9 per ciclo) sono tutti sulla targa: sul PC il registro delle
    macchine non è collegato. Dal 22-11 c'è il comando `macchine` (COPILOT 5.1).
  - **Lettura di tutte le stampe** (esempi MOS e DR e cartelle `cicli MOS`, `leggi --breve`,
    22-11): **il parser le legge tutte**, tranne `8e6c9c8d` che non ha il layout PVRM320 (la
    legge il modello). Il riordino fa leggere `298bc28e`, `38960731`, `5ff17062`, `f355dc3c`
    (e la stampa con «AREE RIPARATE…»); il titolo «OPERAZIONE EVENTUALE» passato
    all'operazione dopo fa leggere `b1261d11` e `d206cc9c`. Dove il riordino non serviva per
    leggere (`c5ff3cd6`, `e9b74c84`, `298bc28e`) le letture con e senza riordino sono uguali.
  - **Stampe DR** (`22f586bb`, `895167b9`): tutte le pagine rimesse in ordine, stesse 9
    operazioni, 4 differenze. Il riordino **aggiunge testo che prima si perdeva**: nella 005
    il testo della procedura (riferimento alla SA e al caso DR), nella 030 «BLOW THE PART WITH
    CLEAN AND DRY AIR». Erano righe in fondo al PDF. Dal 22-11 pomeriggio nelle descrizioni si
    tolgono gli asterischi di cornice e le righe di soli segni (trattini, «/ .»).
  - **Caratteri strani nei blocchi** («À» al posto di «·»): l'output di Python passato in una
    pipe di PowerShell usa un'altra codifica. Nei blocchi che leggono l'output:
    `[Console]::OutputEncoding = [Text.Encoding]::UTF8; $env:PYTHONIOENCODING = "utf-8"`.
- **Frontend:** Copilot ha letto il codice del frontend e della v1 il 22-11-2026 (domande
  C1-C20, sezione 9). La v2 è stata adattata. Mancano: la modifica del pulsante Confirm
  (collega) e la prova in locale insieme a centralizer e login (sezione 1, punto 5).
- **DR senza serial number e condition (22-11): riuscita.**
  - Stampa «SENZA sn» (campo `S/N:` vuoto): nessun serial number trovato, e nessuno preso per
    sbaglio dalle frasi «REGISTRARE P/N E S/N...». WARNING `DR_NON_VERIFICATA`, ciclo non
    bloccato, anche con condition 2.
  - Stampa «CON sn»: `leggi --cerca "S/N"` trova un solo serial number (riga «APPLY ON S/N»).
    - senza condition: ciclo parziale, 4 corretti, 16 warning, 0 errati, 18 N/A, DR WARNING
      `DR_NON_VERIFICATA` (il serial number ha recommendation diverse, non si sa quale vale);
    - condition 2: ciclo bloccato, 0 corretti, 37 warning, 1 errato, DR ERRATO
      `DR_NON_APPLICABILE`. I 37 warning sono i controlli fermati (`BLOCCATO_A_MONTE`): il
      frontend li mostra come `N/A` grigio e il motivo sta nella riga «DR Case» delle fonti.
- **Tempi:** vedi sezione 9, «Tempi massimi».
- **Salvataggio:** il lavoro fino al 22-11-2026 mattina (regole DR, risposta adattata al
  frontend) è nel ramo `feature/cycle-validation-v2` del repository aziendale. Da salvare:
  riordino delle stampe, `confronta`, `macchine`, documenti riordinati (COPILOT 6).

## 11. Problemi già visti e cosa fare

| Cosa si vede | Perché | Cosa fare |
|---|---|---|
| Tanti WARNING `FONTE_ASSENTE` | i manuali dei motori non sono ingestionati | niente: è giusto |
| Stato `parziale`, targhe WARNING `ERRORE_TECNICO` | macchine attive (Redshift) non collegate | niente, finché non si collegano |
| La stessa descrizione a volte ERRATO, a volte CORRETTO | il modello non risponde sempre uguale (op. 060 del DR: ERRATO 2 volte su 3) | c'è già la conferma con 2 domande in più. Prima di «correggere» un ERRATO, rifare la prova 3 volte |
| Esiti diversi tra lettura del modello e del parser | il modello legge il PDF in modo diverso | usare il parser |
| Dubbio: `Accept as is` deve bloccare il DR? | le procedure DR pubblicate parlano solo di riparazione | sì: la guida della v1 dice che con `Accept as is` o `Reject` un ciclo di riparazione è sbagliato. Confermato dall'utente il 22-11-2026 |
| Una ricerca nel testo della conoscenza non trova niente | si cercava riga per riga e le frasi vanno a capo | cercare nel testo intero (`Get-Content -Raw`) |
| Previsto «completo», uscito `parziale` | dimenticate le macchine attive | ricordarsi che oggi è sempre `parziale` |
| Test degli esiti attesi falliti sul PC | mancava la copia di `eval\casi\sintetici` | il blocco di aggiornamento la copia |
| Il blocco del push si è rotto a metà | righe eseguite una alla volta, `else` su una riga a parte | `} else {` sulla stessa riga; commit e push in due blocchi |
| `PermissionError [WinError 5]` | antivirus | il codice riprova; un test può fallire una volta: si rilancia |
| Copilot rifiuta un comando o un file | blocco su `data/` | lancia l'utente, non aggirare |
| Copilot spiega invece di rispondere | gli è stato incollato un testo senza domande | usare il messaggio pronto in `COPILOT.md` |
| Copilot in modalità Agent (anche con «Allow all» acceso) | scelta in basso nella chat | passare ad Ask. Il 22-11 ha risposto alle domande in Agent senza cambiare niente, ma in Agent potrebbe |
| Il bucket si vede in una foto | è aperto `data/bucket.txt` | non ripeterlo; chiedere di chiudere il file |
| Un esito della v1 sembra sbagliato | la v1 sbaglia | non usarla come riferimento |
| DR senza dati: `serial number trovato: no` | il blocco ha preso la stampa «SENZA sn» (`*sn.pdf` ne trova due), oppure il serial number è scritto in un modo non previsto | usare `*CON sn.pdf`; `leggi <pdf> --profile dr --cerca "S/N"` mostra le righe con i codici mascherati |
| Un blocco va avanti anche se il file non c'è (`Missing argument 'pdf'`) | le righe incollate partono una alla volta | mettere il comando dentro `if ($ciclo) { ... }` sulla stessa riga |
| I documenti tolti restano sul PC | `robocopy` copia ma non cancella | il blocco di aggiornamento li cancella per nome |
| `macchine`: «Nel secret mancano host o database» | il secret di Redshift della v1 non ha il database: la v1 lo scrive nella connessione | il comando lo cerca nel codice della v1; se no `--database` |
| Un blocco Python si ferma su un modulo della libreria standard | un file con lo stesso nome (`inspect.py`) nella cartella TEMP | lo script gira in una cartella sua con `python -I` |
| Blocco della libreria: mancano delle classi | probabilmente ha preso un altro `.whl` | usare quello in `app_cycle_validation\vendor` (COPILOT 5.2) |

## 12. Decisioni prese

Le risposte già date. Le domande ancora aperte sono in `COPILOT.md` (sezioni 3 e 4).

- **Task citato che il manuale non ha:** WARNING `FONTE_ASSENTE` subito, senza chiamare il
  modello (interruttore `agent.skip_missing_task`, acceso).
- **Task del capitolo 70:** se non sono nei manuali citati, si cercano nel manuale SPM. Da
  confermare (P1).
- **Targa che non c'è da nessuna parte:** WARNING `TARGA_SCONOSCIUTA`. ERRATO solo per una
  targa che è nei dati TM ma non è attiva.
- **Targa:** è la riga sopra nella colonna TARGA; la riga sotto (centro responsabile) non si
  controlla.
- **Schede:** `PG 300` è un codice a sé; i codici solo numerici sono altre schede. Spazi,
  trattini e maiuscole non contano.
- **Ragionamento ridotto:** acceso (`effort: low` nei controlli, `high` nella lettura del PDF,
  circa -30% di costo). Da confermare su Bedrock; per tornare indietro si svuotano i due campi
  in `config/settings.yaml`.
- **DR con `conditions: []`:** se il serial number ha più recommendation e una ha la lista
  vuota, WARNING «da controllare a mano». Una recommendation unica vale per ogni condition.
- **DR `Accept as is`:** ERRATO e ciclo bloccato, come `Reject` (regola della v1, confermata il
  22-11-2026).
- **DR, serial number e condition:** facoltativi; il serial number si prende dalla stampa se
  manca (sezione 8). Chi carica un DR li conosce, ma le domande rendono il frontend
  macchinoso.
- **`current.json`:** è il puntatore scritto da `publish.py`; il programma usa solo `version` e
  `path`.
- **Fonti EJ200:** RDR, EF, RN, in quest'ordine. Si trovano con la sigla davanti o da sole.
- **Issue vecchia citata da un ciclo EJ200:** WARNING sulla fonte («c'è una issue più
  recente»), ma le operazioni si confrontano con la issue citata.
- **`SP.ORIG.` e `SP.FIAT` (EJ200):** sono i codici dell'operazione e si controllano come i
  task. Nei cicli civili no.
- **Paragrafo citato (EJ200):** si mostra, non si verifica.
- **Descrizione:** copiata dal PDF così com'è. L'op. 005 (riga NOTE) resta. L'RC
  dell'operazione è quello della testata della pagina.
- **`needs_review` nell'indice:** è un promemoria per chi cura l'indice; il programma lo ignora.
- **Frontend:** lo gestisce un collega. La v2 manda i testi come li vuole il frontend di
  oggi (sezione 9): `N/A` grigio per i campi vuoti, esito DR nella riga della fonte DR.
- **DR nella v1** (per confronto): serial number letto anche dal PDF, ma sostituito da quello
  scritto dall'utente; con più recommendation tiene quelle con almeno una condition in comune,
  se non ne resta nessuna si ferma con errore; con una sola recommendation la usa senza
  guardare la condition. La v2 fa lo stesso, e in più funziona senza serial number e
  condition.
- **Repository:** si lavora su `main`; un codice vero rimasto in un vecchio messaggio di commit
  si lascia così (nessuna riscrittura della storia).

## 13. Da correggere nell'indice (knowledge-index)

**Targa `90`.** Nel file delle targhe la `90` ha come funzione una frase rimasta dal documento
(«la descrizione breve può essere scelta…») con le lettere accentate rovinate. Nei dati TM la
stessa targa compare in tre righe (pagine 14, 17, 18) con funzioni diverse. Come correggere:

1. aprire il PDF TM alle pagine 14, 17 e 18 e guardare la colonna della funzione;
2. scartare le righe dove la "funzione" è una frase (è una nota della tabella);
3. leggere il testo con la codifica giusta: nei file pubblicati non devono esserci `Ã` o `â€`;
4. con la stessa targa su più righe, unire le funzioni con `; ` invece di tenere solo la prima;
5. se non c'è tempo: in `uncertainty.json` scrivere
   `{"format": 1, "machine_tags": {"90": ["da_record_parziale"]}}` (la targa esce WARNING
   finché non si corregge);
6. pubblicare la nuova versione e lanciare `kb-check`.

## 14. Come si scrive `COPILOT.md`

- Blocchi PowerShell da copiare così come sono, senza niente da cambiare; ognuno comincia con
  `$env:UV_PYTHON = "3.14"` (tranne quelli di solo git).
- Dopo ogni blocco: **Deve uscire** e **Manda a Claude**.
- Se un blocco costa (Bedrock), dirlo. Per guardare un PDF senza spendere c'è
  `cycle-validation leggi` (`--pagina N` stampa il testo di una pagina).
- Un blocco che può fare danni (push) ha un controllo che scrive `FERMO` e non fa niente se
  qualcosa non torna.
- Le cose fatte si tolgono (l'utente vuole il file pulito): il riassunto va qui in `MEMORIA.md`,
  sezione 10.
- Scrivere tutto in modo molto semplice.
- Accorgimenti PowerShell: in `Select-String` usare `\S+` al posto di caratteri come `·`;
  `Get-Content -Raw` prima di `ConvertFrom-Json`; in `aws s3 ls` il nome del file comincia alla
  colonna 31; i PDF si cercano con una parte del nome (`Get-ChildItem -Filter`), mai con il
  codice vero nel blocco.
- Un file tolto da `docs/` va aggiunto alla riga `Remove-Item` del blocco di aggiornamento,
  perché `robocopy` non cancella.

## 15. Le stampe PVRM320 viste finora

- MOS e DR hanno lo stesso modulo: testata ripetuta a ogni pagina, tabella con asterischi,
  manuale del motore nel piè di pagina. Il parser le legge senza costi.
- I task sono scritti come `TASK 70-xx-xx-xxx-xxx`.
- Nelle stampe DR un'operazione può continuare dopo il banner `*** C O N T I N U A ***` alla
  pagina dopo. Il parser la ricuce se in quella pagina c'è una sola operazione a metà;
  altrimenti si ferma e passa al modello.
- Una delle stampe DR scrive il caso DR e il serial number («D.R. CASE #…», «APPLY ON S/N …»);
  `leggi` li stampa. Le altre no. La condition non c'è mai. I cicli DR non citano task: i task
  vengono dalla recommendation.
- Stampe EJ200 (viste solo nel frontend della v1): descrizioni in italiano maiuscolo, fonti
  RDR/RN/EF, schede `PG …`.
