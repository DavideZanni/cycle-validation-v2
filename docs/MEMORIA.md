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

## 1. Chi fa cosa

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

## 2. Il PC aziendale

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

## 3. Copilot

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

## 4. I servizi

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
- **Macchine attive**: in azienda vengono da Redshift. Non sono ancora collegate, quindi le
  targhe escono WARNING `ERRORE_TECNICO` e il ciclo è `parziale`. La v1 le legge in
  `verify_active_TM` con `redshift_connector` (porta 5439): colonne `work_center_cd` (la
  targa) e `work_center_usage_cd`, filtro `work_center_usage_cd = 'TO'`. Le credenziali
  vengono da `get_db_credentials()`, in un file che Copilot non può leggere; `config.py` ha una
  variabile `SECRET_NAME` sotto «Redshift Configuration». Se la query fallisce, la v1 salta il
  controllo (la v2 invece dà WARNING: più prudente). La v2 non usa la connessione diretta ma la
  Redshift Data API (`AZIENDA.md`). Il nome della tabella va in `MACHINES_QUERY` sul server
  (non nel repository).
- **Frontend**: il gateway QA aziendale (pagina *Cycle Validation*) oggi parla con la v1. La v2
  non è ancora collegata.

## 5. La conoscenza di prova

È stato ingestionato solo un pezzo (i file sono circa 2000, tutti costerebbero troppo):

- 8 capitoli del manuale SPM (capitolo 70);
- 2 procedure DR;
- 104 targhe, 94 schede;
- 23 recommendation DR (17 serial number, 5 con più recommendation).

I **manuali dei motori non ci sono**: le righe che ne hanno bisogno escono WARNING
`FONTE_ASSENTE`, ed è giusto. **Decisione del 21-11-2026: per ora non si ingestiona altro.**

Sul PC la copia della parte civile è in `eval/casi/aziendali/conoscenza/foto-20261121/`; i PDF
dei cicli in `docs\Esempio ciclo mos\` e `docs\Esempio ciclo dr\` (git li ignora).

## 6. Regole sui dati

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

## 7. Come funziona la v2, in breve

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
spento se sono vuote: sezione 8); finché le fa, i valori dati si usano come prima. Il serial
number è scritto solo in alcune stampe; la condition mai.

## 8. Il frontend della v1

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

**Come gira la v1.** Nel repository c'è solo la costruzione dell'immagine: `buildspec.yml`
(immagine Docker pubblicata in ECR, tag del commit e `latest`), `Dockerfile` (Python 3.14,
gunicorn `app_backend:app` sulla porta 8000), `app_backend.py` (all'avvio legge le variabili da
Secrets Manager), `vite.config.ts` (solo in locale manda `/cycle_validation/` alla porta
8003). **Il deploy (ECS o altro) e il gateway che collega `/cycle_validation` non sono nel
repository**: vanno chiesti a chi li gestisce (P5).

## 9. Stato delle prove (22-11-2026)

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
  `ProgettoDocumenti` (una cartella di esempi e il corpus delle prove di ingestion). Chi li ha
  dati non ha detto quali sono gli errori, e l'utente non lo sa. Il comando `confronta`
  (stampa giusta contro stampa «con errori», zero token, codici mascherati) serve a trovarli.
  - Prima prova (il ciclo «applicazione lubrificante»): ciclo parziale, 2 corretti, 15
    warning, 0 errati, 16 N/A. La fonte è WARNING `FONTE_ASSENTE`: il manuale citato non è
    nella conoscenza di prova, quindi la v2 non può confrontare le operazioni. Un solo task
    code citato (op. 005), trovato.
  - Da fare: confronto e prova sui tre cicli (COPILOT 5.1).
- **Frontend:** Copilot ha letto il codice del frontend e della v1 il 22-11-2026 (domande
  C1-C14, sezione 8). La v2 è stata adattata. Mancano: la modifica del pulsante Confirm
  (collega) e dove gira la v1 (P5).
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
- **Tempi:** vedi sezione 8, «Tempi massimi».
- **Salvataggio:** il lavoro fino al 22-11-2026 (regole DR, risposta adattata al frontend,
  documenti riorganizzati) è nel ramo `feature/cycle-validation-v2` del repository aziendale.
  Il comando `confronta` è da salvare.

## 10. Problemi già visti e cosa fare

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

### Accesso ai cicli militari (22-11-2026)

Cosa vuole l'utente: chi entra con l'SSO ed è autorizzato ai cicli militari vede i pulsanti
civile (MOS, DR) e militare (EJ200). Gli altri vedono solo MOS e DR. La pipeline è la stessa per
tutti e tre.

- **Pipeline:** è già la stessa (`run_validation`). Cambiano solo le impostazioni del profilo:
  - EJ200 cita pubblicazioni intere, non task di un manuale;
  - le schede EJ200 non si verificano;
  - la conoscenza EJ200 resta su AWS EU;
  - il DR aggiunge il controllo della recommendation, che blocca.
- **Permessi nella v2:**
  - il backend legge utente e servizi da due header messi dal frontend (`API_USER_HEADER`,
    `API_SERVICES_HEADER`);
  - EJ200 chiede il servizio `cv_ej200` o `all`;
  - `GET /validation/options` mostra il pulsante militare solo a chi ha uno dei due servizi.
- **Da sapere (C15-C17):**
  - come il frontend decide chi vede il pulsante EJ200;
  - se manda un header con i servizi (oggi sappiamo solo di `sso`);
  - se la v1 controlla i permessi.

  Se il frontend manda solo `sso`, la v2 risponde 403 a tutti finché non si decide da dove
  prendere i servizi.

## 11. Decisioni prese

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
  manca (sezione 7). Chi carica un DR li conosce, ma le domande rendono il frontend
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
  oggi (sezione 8): `N/A` grigio per i campi vuoti, esito DR nella riga della fonte DR.
- **DR nella v1** (per confronto): serial number letto anche dal PDF, ma sostituito da quello
  scritto dall'utente; con più recommendation tiene quelle con almeno una condition in comune,
  se non ne resta nessuna si ferma con errore; con una sola recommendation la usa senza
  guardare la condition. La v2 fa lo stesso, e in più funziona senza serial number e
  condition.
- **Repository:** si lavora su `main`; un codice vero rimasto in un vecchio messaggio di commit
  si lascia così (nessuna riscrittura della storia).

## 12. Da correggere nell'indice (knowledge-index)

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

## 13. Come si scrive `COPILOT.md`

- Blocchi PowerShell da copiare così come sono, senza niente da cambiare; ognuno comincia con
  `$env:UV_PYTHON = "3.14"` (tranne quelli di solo git).
- Dopo ogni blocco: **Deve uscire** e **Manda a Claude**.
- Se un blocco costa (Bedrock), dirlo. Per guardare un PDF senza spendere c'è
  `cycle-validation leggi` (`--pagina N` stampa il testo di una pagina).
- Un blocco che può fare danni (push) ha un controllo che scrive `FERMO` e non fa niente se
  qualcosa non torna.
- Le cose fatte si tolgono (l'utente vuole il file pulito): il riassunto va qui in `MEMORIA.md`,
  sezione 9.
- Scrivere tutto in modo molto semplice.
- Accorgimenti PowerShell: in `Select-String` usare `\S+` al posto di caratteri come `·`;
  `Get-Content -Raw` prima di `ConvertFrom-Json`; in `aws s3 ls` il nome del file comincia alla
  colonna 31; i PDF si cercano con una parte del nome (`Get-ChildItem -Filter`), mai con il
  codice vero nel blocco.
- Un file tolto da `docs/` va aggiunto alla riga `Remove-Item` del blocco di aggiornamento,
  perché `robocopy` non cancella.

## 14. Le stampe PVRM320 viste finora

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
