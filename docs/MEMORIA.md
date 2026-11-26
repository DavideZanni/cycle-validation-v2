# Memoria del progetto

Qui c'è tutto quello che sappiamo già: com'è il PC aziendale, cosa si può fare, come funziona la
v2, il frontend, i problemi già visti e le decisioni prese. Serve a non rifare le stesse analisi.

**Claude la legge prima di ogni lavoro sulle prove e la aggiorna quando impara qualcosa di
nuovo.** Ultimo aggiornamento: 22-11-2026 (notte).

Il repository è pubblico: qui non ci sono mai valori veri (bucket, account, host, matricola,
codici di manuali, numeri DR, serial number, part number, codici dei cicli, contenuti EJ200).

Gli altri documenti:

| File | A cosa serve |
|---|---|
| `docs/DOCUMENTAZIONE.md` | com'è fatto e come funziona tutto il progetto, nei dettagli |
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
- **Macchine attive dal PC: non si leggono** (prova del 22-11 notte). La Data API risponde
  `AccessDeniedException` su `ExecuteStatement` (il ruolo SSO non ha il permesso) e la
  connessione diretta dà `OperationalError` (il PC non arriva al cluster; i tunnel di
  centralizer non c'entrano). In locale la v2 parte con `MACHINES_SOURCE=nessuna` (targhe
  WARNING); in servizio legge Redshift come la v1 (`MACHINES_SOURCE=diretta`, sezione 5).

**Da chiudere, in ordine.** Chi: C = Claude, U = utente.

| # | Cosa | Perché serve | Come si chiude | Chi |
|---|---|---|---|---|
| 1 | Misura sugli errori veri | 23-11 sera: 3 degli 8 errori noti trovati in modo stabile, più uno per ciascuno degli altri 4 cicli; 0 falsi errori nei 3 cicli giusti | ingestion del manuale principale fatta il 23-11 (10 manuali); due correzioni nel 23-11 (titoli `CIR`, fonti con la sola sezione). Mancano i file di due REPAIR e il capitolo 70-23 dell'SPM (non sul PC); poi COPILOT 2.1 e 2.1b, Claude confronta con i 10 errori | U, poi C |
| 2 | Accesso degli utenti come la v1 | il frontend manda solo il cookie con il token | **fatto nel codice** (22-11 sera): `API_AUTH=sdk`, scelto da solo quando c'è `AUTH_INTROSPECT_URL`, con gli stessi middleware della v1 (sezione 9). Provato in locale il 22-11 (punto 4); da provare in QA | U |
| 3 | Stessa configurazione della v1 | in servizio la v2 deve partire con lo stesso secret «di ambiente» della v1, senza chiavi nuove | **fatto nel codice**: `CV_ENV_SECRET` = nome del secret di ambiente, letto come `load_secrets` (22-11 sera); macchine attive come la v1 con `MACHINES_SOURCE=diretta`: `redshift_connector` con il secret `SECRET_NAME` (22-11 notte). Da provare in QA | C, poi U |
| 4 | Prova in locale | è il passo prima di develop | **fatto** (22-11 notte): login, frontend e v2 da Run and Debug; ciclo MOS di esempio `Validation Passed` in circa 20 s, con accesso e permessi della v1. Configurazione in `AZIENDA.md`, sezione 7 | — |
| 5 | Pubblicazione in QA | oggi `buildspec.yml` costruisce solo la cartella della v1: un push della v2 su develop non cambia il servizio | **pronto nel codice** (22-11 notte): `cycle-validation qa` sul PC scrive il Dockerfile della v2 da quello della v1 (base, certificati), copia la libreria in `vendor/`, mette i valori aziendali nelle righe `ENV`, copia le impostazioni in `config/settings.azienda.yaml` e sposta il buildspec sulla v2. Primo passaggio con EJ200 spento. Dockerfile e buildspec scritti sul PC e controllati (22-11). Manca la pull request verso develop: COPILOT 4 | U |
| 6 | Pulsante Confirm | per usare DR senza serial number e condition | messaggio COPILOT 6.2 | U |
| 7 | Prova in QA: EJ200 e targhe | i dati EJ200 non escono da AWS; Redshift si raggiunge solo da AWS | dopo il punto 5, dal frontend QA | U |
| 8 | Domande agli esperti | P1-P9 chiuse il 26-11 (Copilot sui dati, regola prudente) | fatto | U |

**Decisioni da prendere:**

- **D1. Dove scrivere il nome del secret «di ambiente» per la v2.** **Confermato dall'utente
  (22-11 notte).** Nella v1 è scritto nel
  codice; nel repository personale (pubblico) non si può. Fatto così (22-11 sera, da
  confermare dall'utente): la v2 lo legge dalla variabile `CV_ENV_SECRET`; in locale la mette
  `launch.json`, nel container una riga `ENV` nel Dockerfile della copia aziendale (il blocco
  di aggiornamento non copia il Dockerfile). Nello stesso Dockerfile vanno anche
  `MACHINES_SOURCE=diretta`, `REDSHIFT_DATABASE` (il database scritto nel file delle credenziali
  della v1) e `MACHINES_QUERY` (la query di `verify_active_TM`), a meno che non stiano già nel
  secret di ambiente.
- **D2. Quando passare a QA.** **Deciso dall'utente (22-11 notte):** prima altre prove in
  locale dal frontend (COPILOT sezione 4), poi QA quando lo dice lui. Il comando `qa` e il salvataggio
  sul ramo `feature/cycle-validation-v2` si fanno subito; solo la pull request verso `develop`
  aspetta (è quella che fa passare QA alla v2). La misura sugli errori (punto 1) può andare avanti in parallelo.

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
  («Rispondi solo leggendo il codice, senza modificare né eseguire niente», poi la domanda).

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
  - **In servizio** la v2 fa come la v1 (dal 22-11 notte): `MACHINES_SOURCE=diretta`,
    `redshift_connector` con host, porta, utente e password del secret `SECRET_NAME` (riletto
    a ogni aggiornamento dell'elenco, ogni 15 minuti), database da `REDSHIFT_DATABASE`, query
    da `MACHINES_QUERY`, 20 secondi al massimo per collegarsi. Resta possibile la Data API
    (`MACHINES_SOURCE=data_api`, `AZIENDA.md`).
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
  - **Il file delle credenziali (visto dall'utente, 22-11 sera):** `get_db_credentials` legge
    il secret `SECRET_NAME` (regione `REGION_NAME`), costruisce un dizionario con `host`,
    `username`, `password` presi dal secret e **`database` scritto nel codice**, e restituisce
    i quattro valori. Il comando segue anche il dizionario. Se il database non si trova, prova
    quello creato con il cluster (`describe_clusters`, `DBName`).
  - **Dal PC non si legge (prova del 22-11 notte).** Il comando trova tutto (secret, tabella,
    database scritto nel codice), ma la Data API risponde `AccessDeniedException` su
    `ExecuteStatement` (manca il permesso al ruolo SSO: P7, facoltativa) e la connessione
    diretta (`macchine --diretto`) dà `OperationalError`: il PC non arriva alla porta del
    cluster. Copilot ha controllato: lo script dei tunnel di centralizer non c'è nel workspace e
    comunque apre solo i tunnel di OpenSearch. La v1 legge Redshift solo quando gira su AWS.
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
`FONTE_ASSENTE`, ed è giusto. Decisione del 21-11-2026: per ora non si ingestiona altro.
**Cambiata il 22-11 notte:** l'utente ingestiona i manuali (solo i capitoli citati) di tutti i
cicli di prova sul PC. La lista la fa il comando `manuali` (COPILOT sezione 5): legge con il parser
tutte le stampe di `ProgettoDocumenti`, confronta con l'ultima fotografia della conoscenza e mette
in cima i manuali che servono per i 10 errori noti. Codici veri solo nel file sul PC
(`runs/manuali-da-ingestionare.txt`).
**Lista del 23-11** (29 cicli letti su circa 2500 PDF; codici solo nel file sul PC): 6 manuali.
M1 (manuale del motore, manca) capitolo 72-56: serve a 20 cicli e a tutti e 7 gli errori dei
tre cicli «con errori» legati a un manuale; sul PC 7 file nella cartella del corpus
dell'ingestion (più copie vecchie in `Extra\storico\old`, da non usare). SPM: c'è, manca solo il
task del capitolo 70-23 (nessun file sul PC). M3 (altro manuale motore, manca) capitolo 72-56:
3 file, 3 cicli (due con «errori» nel nome). M4 e M5 (senza task, 3 cicli): nessun file sul PC.
M6 è EJ200 (una guida d'esempio non riconosciuta come EJ200): non va nell'ingestion civile. I
cicli con «errori» nel nome sono 7, non 3: il blocco dei cicli con errori (COPILOT 2.1) li prende tutti.
**Ingestion del 23-11** (fatta dall'utente): 10 manuali nuovi, 21 file già presenti saltati,
versione pubblicata. Il controllo di Copilot sull'indice diceva che mancano alcuni task (tipo
`REPAIR 00N` di M1, uno del capitolo 72-56 e quello del 70-23), ma guardava solo l'indice: la v2,
se l'indice non ha un task, lo cerca nel testo del manuale (`kb/task_text.py`). Per sapere
quali mancano davvero alla v2 c'è il blocco COPILOT sezione 5 B: `manuali` con la fotografia nuova, che
per ogni task mancante dice perché (nel testo ma non come titolo, solo la sezione, non nel
testo, forma non da task) e nel file sul PC scrive le righe del manuale dove compare. Dal codice di
`knowledge-index` (repository personale, collegato il 23-11): l'indice registra come titolo di
un task solo il codice completo (`codice_task` in `regole.json`), quindi i titoli `REPAIR 00N`
non li ha mai; i «conflitti» del report dell'indice sono targhe e schede con lo stesso codice
e valori diversi (si uniscono con «; »), non riguardano i manuali. I 44 c'erano già prima.
**Prova del 23-11 pomeriggio** (versione `v/20261123T142517Z/`, 20 documenti, 28 task):
i 7 cicli con «errori» danno tutti 0 errati. M1 c'è, ma mancano 7 task. La risposta di Copilot
(in sola lettura) spiega perché:
- due REPAIR hanno il titolo `CIR <sezione>, REPAIR 00N`, con `CIR` davanti e una virgola. La
  ricerca nel testo della v2 non lo riconosceva: corretto il 23-11 (`kb/task_text.py`);
- due citazioni sono la sola sezione: non sono task;
- due REPAIR sono nominati solo in una frase («Refer to TASK <codice completo> (<sezione>,
  REPAIR 00N)»): sono task di altri file del manuale, non ingestionati. I file del manuale
  hanno nel nome la sezione e `-09-` con il numero del REPAIR;
- il task SPM del capitolo 70-23 è citato con la sola sezione: adesso la v2 lo accetta nei
  documenti SPM, ma il capitolo 70-23 dell'SPM non è nella conoscenza.
Dopo la correzione (lista delle 16:00) M1 ha 5 task mancanti: le 2 sezioni e i 2 REPAIR della
sezione 72-56-31 citati solo in una frase (più il codice completo di uno dei due). I loro PDF
(`-09-001`, `-09-003`) **non sono sul PC**: vanno presi dalla fonte dei manuali.
I 7 cicli con la correzione (16:15): ancora 0 errati in tutti (2-6 corretti, 15-24 warning).
Il controllo della descrizione, se un task citato dall'operazione manca, non confronta niente
(`skip_missing_task`, FONTE_ASSENTE): per capire quale controllo ferma gli errori noti c'è il
blocco COPILOT 2.1b.
**2.1b del 23-11 (16:40)** sui tre cicli «con errori»:
- 298bc28e op 035, c5ff3cd6 op 030 e 040, f355dc3c op 030: nessun task citato e nessun testo
  delle fonti collegate (FONTE_ASSENTE). Causa probabile: le fonti citano solo la sezione
  (`CIR <sezione>`). Corretto il 23-11 (`section_locations` in `resolve/civil.py`): una fonte con
  la sola sezione porta i task di quella sezione in tutti i documenti del manuale; anche il
  controllo `source` e il comando `manuali` la danno trovata;
- 298bc28e op 005 e f355dc3c op 010: il modello ha avuto il task d'ispezione della sezione
  72-56-32 e ha risposto EVIDENZA_NON_TROVATA (op 005: errore in un codice; op 010: tre numeri
  cambiati). Da capire con la spiegazione intera (2.1b allungato);
- f355dc3c op 040 e 050: fuori dalla foto.

**2.3, 2.1 e 2.1b del 23-11 (16:50)**, dopo la correzione delle sezioni: M1 ha 3 task mancanti
(nel testo, ma non come titolo), M2 uno. I 7 cicli: ancora 0 errati. In 2.1b la fonte risulta
**senza task** (rc A1) e le operazioni 035 (rc A3), c5ff3cd6 030/040 (rc A2) e f355dc3c
030/040/050 (rc A1) restano FONTE_ASSENTE. Causa trovata nel parser della stampa: la fonte era
una sola, con la riparazione e la nota della **prima** pagina, e il task veniva preso dalla nota
solo se cominciava con le cifre (una nota `CIR <sezione>` dava task vuoto). Corretto il 23-11
(17:10, `extract/pvrm320_report.py`): una fonte per ogni riparazione, con la nota della testata
delle sue pagine e il manuale del piè di pagina; la nota può cominciare con `CIR` o `TASK` e
avere la virgola dopo la sezione. `leggi --fonti` stampa le fonti senza codici di manuali
(COPILOT 2.0). Non ancora visto sui PDF veri: la forma della nota è un'ipotesi da confermare con
2.0. Le spiegazioni di op 005 e op 010 (task d'ispezione 72-56-32): il testo dell'ispezione non
parla di rimozione del metallo né dei limiti di numero delle raccordature; quelle cose stanno nei
REPAIR, quindi senza i REPAIR giusti il modello non può trovare l'errore.

**2.0 del 23-11 (17:00)**, con le fonti per riparazione: c5ff3cd6 ha una sola riparazione (A2)
con nota `APPL. LUBRIFIC. SECCO` (una descrizione, nessun task); f355dc3c una sola (A1) con nota
`BLENDING <task completo>` (parola prima del codice: corretto alle 17:20, il task si cerca in
tutta la nota). 298bc28e in 2.1b non ha **nessuna** fonte (OEM del piè di pagina assente o con
`/`?): da vedere con 2.0. op 005 di 298bc28e cita dei subtask SPM della sezione 70-42-00 in una
forma che la v2 non legge come task (non c'è la parola TASK davanti): `leggi --fonti` ora stampa
questi codici, per capire la forma prima di leggerli. Rilanciati i 7 cicli (17:02): ancora 0
errati.

**2.0 del 23-11 (17:10)**, con il parser nuovo: tutti e tre i cicli hanno una fonte (M1, OEM
nel piè di pagina). 298bc28e (rc A3) e c5ff3cd6 (rc A2): nota senza task. f355dc3c (rc A1):
task della nota = un task SPM della sezione 70-42-00 (raccordatura), quindi le sue operazioni
030/040/050 ora hanno un testo. Codici non letti come task: `SUBTASK <codice completo>` (op 005
di 298bc28e, sezione 70-42-00; op 005 di c5ff3cd6, sezione 72-56-31). Corretto (17:30): SUBTASK
è letto come task code; nel manuale, se il codice non apre un task, si cerca la riga che comincia
con `SUBTASK <codice>` (anche dopo «(1)») fino al prossimo SUBTASK o task. L'indice non registra
i SUBTASK e non serve cambiarlo. Per c5ff3cd6 030/040 resta il problema: nessun task né nella
nota né nell'operazione (domanda alle persone: quale task vale per quella riparazione?).

**2.3, 2.1 e 2.1b del 23-11 (17:20)**, con i SUBTASK: M2 (SPM) ha 1 task «non nel testo», che
serve per 298bc28e op 005. I 7 cicli: ancora 0 errati. Analisi dei 8 errori dei tre cicli:
- 298bc28e op 005 (codice cambiato): ora i subtask SPM 70-42-00 sono letti. Uno dei due non è
  da nessuna parte nel testo SPM, dove ci sono i suoi fratelli: è il codice sbagliato. Il
  modello giudica solo la descrizione e ha detto CORRETTO. Corretto (17:50): `task_code` dà
  ERRATO `TASK_INESISTENTE` se un codice completo non compare in nessun punto dei documenti
  dove dovrebbe stare e lì ci sono task della stessa famiglia (stesse prime quattro parti).
  Se la famiglia non c'è (documento mancante), resta FONTE_ASSENTE;
- f355dc3c op 030/040/050: la fonte (task SPM 70-42-00 della nota) veniva presa dal manuale del
  motore, che la cita su una riga a sé: la ricerca nel testo la scambiava per il titolo. Il
  modello ha detto «il testo del task non è presente». Corretto (17:50): i task del capitolo 70
  si cercano prima nell'SPM. op 040 (la classe, un attacco chimico a tampone) sta
  probabilmente nel capitolo 70-23 dell'SPM, che manca; op 050 (frase al contrario): con il
  testo SPM giusto forse si trova;
- 298bc28e op 035 e c5ff3cd6 op 040: nessun task né nell'operazione né nella testata. Corretto
  (17:50): si usano i task citati dalle altre operazioni della stessa riparazione (al massimo
  4). Più chiamate al modello per ciclo;
- f355dc3c op 010 (tre numeri): i limiti di numero delle raccordature non sono nel task
  d'ispezione citato; stanno in un altro task (forse un REPAIR della sezione 72-56-32). Aperto;
- c5ff3cd6 op 030 (scheda tolta): regola P6. Aperto.
Per i falsi errori c'è COPILOT 2.1c (le tre stampe giuste: non devono dare ERRATO).

**2.1, 2.1b e 2.1c del 23-11 (17:30)**, con le correzioni delle 17:50:
- 7 cicli con errori: 298bc28e 0 errati; 5ff17062 **2 errati** (op 030 e 050,
  CONTRADDIZIONE: da vedere se veri); f355dc3c **1 errato** (op 050). Cicli giusti: 4e64d49a 0,
  8bdb25d5 0, 04ecaabe **1** (op 050, stessa spiegazione di f355dc3c: il ciclo dice indicazione
  lineare «almeno 4 volte la larghezza», l'SPM «3 volte o più»). Quindi f355dc3c op 050 non è
  l'errore messo apposta: è una differenza che c'è anche nella stampa vera (domanda P7);
- 298bc28e op 005: i due subtask SPM ci sono tutti e due (il 035 parla di raccordatura del
  titanio su parti rotanti); `TASK_INESISTENTE` non scatta. Il codice cambiato va visto
  confrontando i task dell'op. 005 nella stampa giusta (COPILOT 2.0);
- 298bc28e op 035 e c5ff3cd6 op 030/040: ora confrontate con i task della stessa riparazione,
  ma sono task d'altro (lubrificante, raccordatura): EVIDENZA_NON_TROVATA. In c5ff3cd6 op 040 il
  modello ha notato che **l'italiano dice 13-38 micron e l'inglese 13-58**: è il numero cambiato;
- f355dc3c op 030: CONTRADDIZIONE alla prima risposta (il ciclo dice raccordatura lunga almeno
  30 volte la profondità, l'SPM 10 volte), non ritrovata nelle due verifiche: GIUDIZIO_INSTABILE;
- f355dc3c op 010 e 040: EVIDENZA_NON_TROVATA (limiti in un altro task; classe d'attacco nel
  capitolo 70-23 o nel manuale d'ispezione del motore).
Corretto il 23-11 (18:10): controllo senza modello delle **due lingue** (`checks/languages.py`):
se nello stesso punto la descrizione italiana e quella inglese hanno numeri diversi (non una
conversione mm/pollici o °C/°F), ERRATO `INCOERENZA_LINGUE`. Misura gratis con `leggi --lingue`
(COPILOT 2.0) sui 10 cicli, prima di rilanciare.

**2.0 del 23-11 (17:40)**, `leggi --lingue` sui 10 cicli (prima versione):
- con errori: f355dc3c op 030 `30 → 10, 0,5 → 1,5` (**è l'errore messo apposta**: in italiano
  30 volte, in inglese 10; la verifica che diceva «corretto» aveva letto l'inglese); 5ff17062
  op 030 `30 → 2, 0,5 → 1,5`; 38960731 op 050 `4 → 2`; 8d3c673c op 140 `32 → 31`; e9b74c84 op
  025 `500 → 60` (questi quattro cicli non hanno la stampa giusta conosciuta: probabili errori
  messi apposta, da confermare); c5ff3cd6: niente (il modello aveva visto 13-38 / 13-58);
- giusti: 4e64d49a niente; **8bdb25d5 op 040: falso errore** (un part number scritto in punti
  diversi nelle due lingue spostava l'allineamento dei numeri). Corretto (17:55): i codici fatti
  di cifre (con `/`, o di 5 cifre o più) restano fuori dal confronto. Con questo anche c5ff3cd6
  op 040 dovrebbe uscire. 298bc28e e 04ecaabe fuori dalla foto;
- 298bc28e op 005: nella stampa giusta i task sono il subtask SPM 029 e l'ispezione; in quella
  con errori c'è **in più il subtask 035** (raccordatura del titanio su parti rotanti): il codice
  cambiato è un subtask che esiste, ma è un altro lavoro. Né `TASK_INESISTENTE` né il modello lo
  vedono: serve chi conosce il pezzo (domanda P9);
- 5ff17062 op 030 ERRATO dal modello: l'inglese dice di usare abrasivi a matrice vetrificata,
  l'italiano di non usarli e il manuale li vieta: **vero errore**. op 050: stesso «4 volte
  contro 3 volte» della domanda P7;
- f355dc3c op 030: verifica 1 CONTRADDIZIONE, verifiche 2 e 3 VERIFICATO (hanno letto il «10
  volte» inglese): ora la prende il controllo delle due lingue.

**2.0 del 23-11 (17:49)**, `leggi --lingue` con i part number fuori dal confronto: i tre cicli
giusti (04ecaabe, 4e64d49a, 8bdb25d5) **puliti**. Trovati: 298bc28e op 005 `035 → 029` (il
codice cambiato è il subtask, cambiato **solo in italiano**: la domanda P9 non serve più),
c5ff3cd6 op 040 `38 → 58`, f355dc3c op 030 `30 → 10, 0,5 → 1,5`; e negli altri cicli 5ff17062
op 030, 38960731 op 050, 8d3c673c op 140, e9b74c84 op 025. Dei 8 errori noti dei tre cicli: 3
trovati senza modello (005, c5ff3cd6 040, f355dc3c 030). Restano: 298bc28e op 035 (parole),
c5ff3cd6 op 030 (scheda, P6), f355dc3c op 010 (numeri cambiati in tutte e due le lingue), 040
(classe), 050 (frase).

**2.1, 2.1b e 2.1c del 23-11 (17:58)**, con tutte le correzioni:
- i 7 cicli con errori: un ERRATO `INCOERENZA_LINGUE` in ognuno (298bc28e op 005, 38960731 op
  050, 5ff17062 op 030, 8d3c673c op 140, c5ff3cd6 op 040, e9b74c84 op 025, f355dc3c op 030);
  in più CONTRADDIZIONE del modello in 5ff17062 op 050 e f355dc3c op 050 («4 volte» contro i
  «3 volte» dell'SPM, domanda P7);
- i 3 cicli giusti: **0 errati** (04ecaabe questa volta non ha dato l'op. 050: il giudizio del
  modello su quel punto cambia da una prova all'altra);
- dei 8 errori noti dei tre cicli: **3 trovati in modo stabile** (298bc28e 005, c5ff3cd6 040,
  f355dc3c 030); f355dc3c 050 segnato, ma per il «4 volte» che c'è anche nella stampa giusta.
  Restano 298bc28e 035 (parole: confrontata con i task della riparazione, nessun collaudo
  visivo), c5ff3cd6 030 (scheda tolta, P6; la descrizione esce CORRETTO), f355dc3c 010 (limiti
  delle raccordature in un altro task), 040 (classe d'attacco: l'SPM rimanda al manuale
  d'ispezione del motore, che non è nella conoscenza), 050 (frase al contrario).

**COPILOT riordinato (23-11 sera).** Tolti i blocchi di analisi già fatti (2.0 lingue, 2.1 cicli
con errori, 2.1b, 2.1c cicli giusti): li sostituisce la prova con metriche (`eval prova`, ora
COPILOT 2.3). Nuova numerazione: 2.1 Aggiornare, 2.2 Salvare, 2.3 Prove delle migliorie, 2.4
Frontend, 2.5 Dopo una nuova ingestion (fotografia e lista dei manuali). Nelle note sopra i
numeri dei blocchi sono quelli vecchi. Metriche e regola di scelta: `MIGLIORIE.md`.

**Due insiemi di prova (23-11 sera).** L'utente vuole provare le migliorie anche su più cicli.
Insieme **piccolo** = i 10 cicli noti (`runs/prove-piccolo`); insieme **grande** = i 10 più 20
cicli veri civili con almeno l'80% delle operazioni confrontabili con la conoscenza, scelti da
`eval scegli` (zero token, lista dei percorsi in `runs/prove-grande/cicli.txt`, solo sul PC).
Un ciclo vero non ha errori noti: tipo `vero`, i suoi ERRATO sono «da verificare», i suoi
WARNING contano nel lavoro a mano. Si confrontano solo prove sullo stesso insieme (colonna
«Cicli» con l'impronta dell'insieme nel riepilogo). Una miglioria con file
`eval/varianti/<nome>.yaml` si lancia con `eval prova --variante`; il blocco della prova a mano (COPILOT 3.7) lo fa da
solo. La lista delle migliorie da provare è in `MIGLIORIE.md`, «Da provare».

**Errori mai visti (23-11 sera).** L'utente vuole sapere se la v2 generalizza o ha imparato la
lista dei 12 errori (che Claude conosce). Fatto: `eval muta` (copie cieche dai cicli veri, un
errore per copia, quattro tipi, seme; `runs/mutazioni` sul PC), gruppo nascosto facoltativo in
`data/nascosti` + `data/errori-nascosti.yaml` (Claude non lo vede mai), `visto: false` negli
attesi. I report danno visti e mai visti a parte, i mai visti solo per tipo; la regola non tiene
una variante che perde errori mai visti stabili. Il piccolo ora = 10 noti + copie cieche +
nascosti; il grande = 10 noti + tutti i cicli veri confrontabili (`--quanti 0`). Quando cambia
il seme o la conoscenza, le prove si archiviano (COPILOT 3.8). Non chiedere mai foto degli
errori ciechi o nascosti.

**Migliorie scelte sui mai visti (23-11 notte).** Decisione dell'utente: le migliorie non si
scelgono più dagli errori noti mancati (erano fatte su misura, cioè «imparare la lista»). Tolte
`negazioni_lingue` (I1), `classi_lingue` (I2), `prompt_confronto` (I3), `contesto_sezione` (I5),
`fatti_incerti` (F5), `modello_grande_sui_dubbi` (I6); resta solo `numeri_manuale` (I4). Dopo la
base si guarda la tabella «Errori mai visti, per tipo» e si sceglie sul tipo «modello» trovato
peggio. Corretto anche un errore di misura: i tipi ciechi `numero_una_lingua` e
`task_inesistente` li trova il codice con la stessa regola che li mette (`CODE_KINDS`), quindi
non contano nella generalizzazione né nella regola; si vedono a parte come controllo.

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
prerequisites» (`tasks.json`, lo script che apre i tunnel verso OpenSearch). Copilot (22-11
notte): lo script `scripts\ensure-opensearch-tunnels.ps1` non c'è nel workspace, è solo
descritto in una guida; comunque apre solo OpenSearch, non Redshift.

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

### Come si pubblica la v2 in QA (deciso il 22-11-2026, notte)

- **Il comando `cycle-validation qa`** (`src/cycle_validation/deploy.py`) gira sul PC nella
  cartella della v2 e legge la v1: dal suo Dockerfile la riga `FROM` e le istruzioni sui
  certificati; dai requirements il `.whl` di `chatbot_ai_sdk` con le aggiunte; dal codice il
  nome del secret di ambiente, il database e la tabella (come il comando `macchine`). Scrive il
  Dockerfile della copia aziendale con le righe `ENV` (`CV_ENV_SECRET`,
  `MACHINES_SOURCE=diretta`, `REDSHIFT_DATABASE`, `MACHINES_QUERY`, `CYCLE_VALIDATION_CONFIG`,
  i due puntatori della conoscenza, `EJ200_VALIDATION_ENABLED`, `API_INCLUDE_TRACEBACK=false`),
  copia `data/settings.yaml` in `config/settings.azienda.yaml` e cambia nel buildspec
  `cd app_cycle_validation` in `cd app_cycle_validation_v2`. Stampa il Dockerfile con i tre
  valori aziendali coperti. `--torna-alla-v1` rimette il buildspec com'era.
- **Prima prova del comando (22-11 notte):** dalla v1 base
  `public.ecr.aws/docker/library/python:3.14.10-slim` e 2 istruzioni sui certificati (`COPY
  ca-certificates.crt /etc/ssl/certs/ca-certificates.crt` e un `ENV` con `SSL_CERT_FILE` e
  `REQUESTS_CA_BUNDLE`); libreria 0.4.0rc2 `[auth]`; secret, database e tabella trovati; modello
  `eu.anthropic.claude-haiku-5-5`. Il buildspec copia il certificato della macchina di build con
  `cp ... app_cycle_validation/ca-certificates.crt` **prima** del `cd`: la prima versione del
  comando cambiava solo il `cd`, e il certificato sarebbe finito nella cartella della v1
  (build della v2 fallita su `COPY ca-certificates.crt`). Corretto: ora cambia ogni percorso
  con la cartella. Le impostazioni del PC avevano `save_transcripts: true`: nella copia per il
  servizio il comando lo spegne.
- **Seconda prova (22-11 notte): giusta.** `buildspec: percorsi spostati sulla v2: 1` (la copia
  del certificato), tutte le righe del buildspec con `app_cycle_validation_v2`; impostazioni
  copiate con i testi su disco spenti; Dockerfile come previsto. Da salvare sul ramo feature.
- **Pulizia del progetto (22-11 notte).** Tolti dal codice due pezzi mai usati
  (`RemoteKnowledge.structured`, il contatore `text_reads` di EJ200). `COPILOT.md` riscritto corto:
  solo il punto in cui siamo, cosa manca e i blocchi; sezioni nuove: 2 Aggiornare, 3 Salvare, 4
  prove in locale, 5 domande e messaggio, 6 QA (il 23-11 riordinato: 1 cosa fare, 2 blocchi, 3 persone, 4 QA). Il blocco
  Aggiornare ora toglie sul PC i file che nel repository personale non ci sono più (prima
  `robocopy /E` copiava e basta, quindi i file vecchi restavano e finivano nel commit) e copia
  anche `eval/varianti`, `eval/modelli` e `.gitignore`.
- **Perché così:** il repository personale è pubblico; la configurazione resta quella della v1
  (stesso secret di ambiente, stesso nome in QA e in produzione); nessun valore nuovo da
  chiedere a nessuno.
- **Il Dockerfile del repository personale** resta generico (Python 3.14, senza certificati e
  senza libreria di accesso): in azienda vale quello scritto da `qa`. Il blocco di
  aggiornamento ora copia anche `config/`, `prompts/`, `pyproject.toml`, `uv.lock`, `README.md`.
- **EJ200 spento al primo passaggio:** all'avvio la v2 scarica la conoscenza pubblicata e, se un
  file non è valido, non parte. La conoscenza EJ200 non si può controllare dal PC (resta su
  AWS), quindi prima si prova il civile, poi si accende EJ200 (COPILOT 4, punto 3).
- **Produzione:** passa alla v2 quando il ramo arriva su `main`. Prima serve una prova QA
  riuscita.
- **Da verificare in QA:** che il ruolo del servizio possa usare Bedrock con il modello delle
  impostazioni e leggere i prefissi della conoscenza v2 su S3; che `uvicorn.workers` ci sia
  nella versione di uvicorn installata.

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
  `LOG_LEVEL`.
- **Le versioni della libreria (22-11 notte).** In `vendor` della v1 ci sono
  `chatbot_ai_sdk-0.3.0` e `chatbot_ai_sdk-0.4.0rc2`. I requirements della v1 (quindi il
  servizio) usano `./vendor/chatbot_ai_sdk-0.4.0rc2-py3-none-any.whl[auth]`. Solo la 0.4.0rc2
  ha `ServiceAccessMiddleware` e `S3PermissionsSource`; la 0.3.0 no. Sul PC il `.venv` della
  v1 ha ancora la 0.3.0 (non aggiornato dai requirements): il backend v1 in locale con quel
  `.venv` non ha i pezzi che importa. La v2 installa la riga dei requirements della v1
  (`AZIENDA.md`, sezione 7) e nel Dockerfile farà lo stesso.
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
- **Prima prova completa in locale (22-11 notte).** Dopo aver messo `FRONTEND_URL` =
  `http://localhost:3000` nella configurazione della v2, dal frontend: sessioni, conversazione
  e caricamento rispondono 200, il ciclo MOS di esempio esce `Validation Passed` in circa 20
  secondi. Il frontend chiede spesso `POST /cycle_validation/sessions`: è il suo aggiornamento
  dell'elenco, non un errore.
- **Prima partenza della v2 in locale (22-11 notte).** Con la libreria 0.4.0rc2 `[auth]`, il
  secret di ambiente della v1 in `CV_ENV_SECRET` e `MACHINES_SOURCE=nessuna` la v2 parte sulla
  porta 8003. Aperta direttamente nel browser risponde 401 `Login richiesto.` e nel log
  `chatbot_ai_sdk.auth.middleware ... Request rejected on /: no access token`: l'accesso
  funziona come nella v1. La prova vera passa dal frontend (porta 3000) dopo il login.
- **Cosa fa la v2 (dal 22-11 sera, `api/auth.py`).** `API_AUTH=sdk` (scelto da solo se c'è
  `AUTH_INTROSPECT_URL`, cioè con il secret della v1): gli stessi tre pezzi della v1 (token,
  permessi, utente) con gli stessi parametri; l'utente delle sessioni e dei feedback è
  `current_user(request).sso`. I servizi non arrivano alle rotte, quindi la v2 li deduce dal
  percorso, già controllato dalla libreria. Conseguenza: le rotte nuove
  `validation/options` e `validation/upload` non offrono il militare; i cicli militari passano
  da `/cycle_validation/ej200/...`, come nel frontend di oggi. Senza la libreria installata la
  v2 non parte (meglio che partire senza controllo). `API_AUTH=header` resta per le prove.
- La libreria nella v2: `uv pip install` del `.whl` della v1 (`AZIENDA.md`, sezione 7). `uv run` la
  lascia; `uv sync` la toglierebbe (va reinstallata).
- `GET /validation/options` della v2 mostra il pulsante militare solo a chi ha `cv_ej200` o
  `all` (per un frontend futuro; quello di oggi usa `/login/permissions`).

## 10. Stato delle prove (22-11-2026)

- **24-11, cicli dell'insieme grande (`eval scegli`, COPILOT 3.2):** sotto
  `ProgettoDocumenti` ci sono 2600 PDF; 29 sono cicli PVRM320 diversi, gli altri 2531 sono
  manuali o altri documenti. Scelti 23: i 10 noti e 13 veri (dalle 9 alle 21 operazioni, quasi
  tutte confrontabili). Lasciati fuori 1 EJ200 e 5 con poche operazioni confrontabili. Il
  grande è piccolo: 23 cicli, nessun limite da mettere.
- **24-11, copie cieche (`eval muta`, seme 1, primo giro):** 16 cicli letti (13 veri e 3
  giusti), 32 copie: `numero_una_lingua` 11, `numero_manuale` 3, `negazione_una_lingua` 11,
  `task_inesistente` 7. Il tetto di 2 copie per ciclo si era riempito (16 × 2) e i tipi del
  codice, che servono solo come controllo, prendevano metà del posto. Cambiato: 6 copie per
  ciclo (`--per-ciclo`) e al massimo 5 per tipo del codice. Da rifare con lo stesso seme.
- **24-11, MOS e DR nelle prove:** `eval scegli` lasciava fuori solo gli EJ200, quindi nella
  lista potevano esserci stampe DR; `eval prova` le avrebbe lanciate tutte come MOS, fermandole
  con «Modulo sbagliato» (ciclo non eseguito = variante scartata). Ora `eval prova` sceglie il
  profilo ciclo per ciclo dalla testata (`--profile auto`, predefinito) e `eval scegli` scrive
  MOS o DR accanto a ogni ciclo. A0 da rifare per vedere quanti DR ci sono.
- **24-11, secondo giro (dopo le correzioni):** A0 di nuovo 23 cicli, **MOS 17, DR 6** (i 6 DR
  sono tra i 13 veri). A1, seme 1: 16 cicli, **31 copie**: `numero_una_lingua` 5,
  `numero_manuale` 3, `negazione_una_lingua` 18, `task_inesistente` 5. Mai visti per il
  modello: 21. `numero_manuale` resta a 3 anche con 6 copie per ciclo: il limite ora sono le
  operazioni adatte (un numero nelle due lingue e nel testo del task del manuale), non il
  tetto. Un seme nuovo non ne aggiunge (stesse operazioni adatte). Per misurare bene
  `numeri_manuale` servono errori di quel tipo nel gruppo nascosto.
- **24-11, prime due prove `base` sul piccolo (14:41 e 14:47):** visti trovati 8 e 7 su 12,
  costo 0,16 e 0,14 $. Due problemi, corretti lo stesso giorno: (1) le 31 copie cieche uscivano
  come cicli «vero» (`mai visti 0 su 0`): `eval muta` le scriveva con `write_text`, che su
  Windows mette `\r\n`, quindi l'impronta del file non era quella di `errori.yaml`. Ora le
  scrive byte per byte ed `eval prova` toglie i `\r` prima dell'impronta (le copie già fatte
  vanno bene). Nelle due prove 4-5 copie avevano un ERRATO (contato come «da verificare»).
  (2) 1 falso errore su `04ecaabe` op. 050, la stampa giusta di f355dc3c: è P7 («4 volte»
  contro «3 volte» dell'SPM). Nuovo campo `in_attesa` in `errori-noti.yaml`: un ERRATO lì non
  conta finché P7 non ha risposta. Le due prove si cancellano e la base si rifà.
- **24-11 ore 14:57, terza prova `base`:** copie riconosciute, ma mai visti per il modello
  **0 su 21** e per il codice **4 su 10**; visti 8 su 12, 0 falsi errori, 0,16 $. Causa: il
  controllo di integrità confrontava la copia con il PDF originale, dove il valore cambiato non
  c'è, e declassava ogni ERRATO a WARNING `ESTRAZIONE_NON_CONFERMATA`. Le negazioni tolte non
  aggiungono valori, quindi passavano il controllo: per loro lo 0 su 18 sembra un limite vero
  del modello (da rivedere dopo la base corretta). Ora per le copie il controllo si salta
  (`RunRequest.check_integrity`). Anche questa prova si cancella.
- **24-11 ore 15:08, prima prova `base` valida (piccolo):** visti **8 su 12**; mai visti per il
  modello **1 su 21**; per il codice **9 su 10**; **0 falsi errori** (op. 050 di 04ecaabe «in
  attesa»); 1 ERRATO da verificare (5ff17062 op. 050); 0,17 $. Grande distanza tra visti (67%)
  e mai visti per il modello (5%): sulle negazioni tolte in una lingua sola il modello quasi
  non vede l'errore. Per capire il perché senza vedere gli errori, il report dà ora sui
  mancati mai visti esito e motivo contati per tipo.
- **24-11 ore 16:09, campagna partita** (dopo aver azzerato le prove): le due prove `base`
  Haiku sul piccolo sono uguali: visti **8 su 12**, mai visti per il modello **2 su 21**, per il
  codice **9 su 10**, **0 falsi errori**, 1 ERRATO da verificare, 0,16 $ ciascuna (circa 5
  minuti a prova). È il riferimento stabile della base Haiku.
- **24-11 ore 17:17, campagna Haiku sul piccolo quasi finita** (13 prove, manca la seconda di
  `concorrenza_12`): nessuna variante si tiene; decisioni e considerazioni nel registro di
  `MIGLIORIE.md`. I 12 visti sono identici in tutte le prove (8 sempre, 4 mai). Il costo per
  ciclo usciva `0.00 $` (circa 0,004 $ arrotondato): ora i report lo danno con 4 decimali.
- **24-11 sera, campagna fermata dall'utente** per sistemare prima le migliorie. Perché il
  modello manca le negazioni: il prompt chiede solo «la descrizione è coerente con il
  manuale?» e una lingua giusta copre l'altra. Nuova variante `lingue_separate`
  (`agent.separate_languages`), aggiunta alla campagna; la base non cambia, quindi le 13 prove
  restano valide. `numeri_manuale` rimandata: troverebbe le copie «numero del manuale» per
  costruzione (vedi MIGLIORIE 7.3).
- **24-11 sera, rianalisi da capo (richiesta dell'utente: «metriche molto basse»).** Cosa non
  andava e cosa è cambiato:
  1. il numero in evidenza («19 su 43, 44%») sommava cose diverse (visti, mai visti per il
     modello, controlli del codice): ora il report e la riga finale danno separati visti, mai
     visti per il modello, falsi errori; il totale solo per ultimo;
  2. 2 errori visti oggi non si possono trovare (c5ff3cd6 030 = P6; f355dc3c 040 = documento
     mancante): ora sono `in_attesa` e fuori dal conto. Visti contati: 10 (la base ne trova 8;
     mancati sempre 298bc28e 035 e f355dc3c 010);
  3. i mai visti per il modello erano 21, 18 dello stesso tipo: due tipi nuovi di copie
     cieche, `negazione_due_lingue` e `limite_invertito` (si vedono solo con il manuale);
  4. i 14 WARNING per ciclo non si sapeva da dove venissero: ora il report li conta per motivo;
  5. per i visti mancati il riepilogo dà l'ultimo esito (solo esito e motivo);
  6. due migliorie sul metodo: `lingue_separate` e `elementi_uno_per_uno`;
  7. domanda nuova P9: 5ff17062 op. 050, ERRATO in tutte le prove ma non nella lista.
  Le copie cieche cambiano: si azzera e si rifà tutto (COPILOT, tappa 2).

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
    macchine non è collegato. Dal 22-11 c'è il comando `macchine`
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
  (collega). La prova in locale insieme a centralizer e login è riuscita il 22-11 notte
  (sezione 1, punto 4).
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
  riordino delle stampe, `confronta`, `macchine`, documenti riordinati.

- **Tre cicli «con errori», 22-11 sera (oggi COPILOT 2.1, senza ingestion nuova).** Fotografia del
  22-11 (16 oggetti), poi i tre cicli: 0 errati in tutti e tre (0-3 corretti, 16-19 warning,
  15-18 non applicabili), come prima. Il blocco non fa l'ingestion: ora stampa la versione
  pubblicata accanto a quella del 21-11 per vedere se l'ingestion è arrivata.

## 11. Problemi già visti e cosa fare

| Cosa si vede | Perché | Cosa fare |
|---|---|---|
| Dopo Aggiornare 3 test `failed` con `No such file or directory: 'eval\\errori-noti.yaml'` (24-11) | il blocco 2.1 copiava solo alcune cartelle: `eval/errori-noti.yaml` (nato il 23-11) e `examples/` non arrivavano | corretto il 24-11: 2.1 copia anche quei due, 2.2 li mette in git; un test (`test_copilot_blocks.py`) controlla che i blocchi portino tutto quello che serve ai test. Rilanciare 2.1 |
| Dopo Aggiornare i test di `test_campaign.py` danno `ERROR at setup` con `WinError 1314` (24-11) | i test creavano collegamenti simbolici, che su Windows chiedono permessi da amministratore | corretto il 24-11: i test copiano le cartelle. Regola: nei test niente `symlink_to`, solo copie |
| Tanti WARNING `FONTE_ASSENTE` | i manuali dei motori non sono ingestionati | niente: è giusto |
| Stato `parziale`, targhe WARNING `ERRORE_TECNICO` | macchine attive (Redshift) non collegate: dal PC Redshift non si raggiunge | niente: in locale è giusto. In QA la v2 legge Redshift come la v1 |
| `macchine`: `AccessDeniedException, ExecuteStatement` e poi `OperationalError` con `--diretto` | dal PC: manca il permesso della Data API e la rete non arriva al cluster | niente da fare sul PC (P7 facoltativa). I tunnel di centralizer non c'entrano |
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
| Dal frontend locale ogni POST della v2 dà 403 `Origine non ammessa.` (log: `cookie sent from a foreign origin`) | la libreria accetta solo l'`Origin` uguale a `FRONTEND_URL`; dal secret arriva l'indirizzo del servizio, in locale il frontend è `http://localhost:3000` | `FRONTEND_URL` nella configurazione CV v2 di `launch.json` (`AZIENDA.md`, sezione 7) |
| Nel terminale del frontend: `[vite] http proxy error: /prc/sessions/...`, `/mrb/...`, `/me/...`, `/psr/...` `ECONNREFUSED` | il frontend chiede le sessioni anche ai backend di altri progetti, che in locale non sono accesi | niente: non riguarda Cycle Validation |
| `git status` mostra `?? ../src/`, `../tests/`, `../docs/`, `../eval/` | un blocco di aggiornamento lanciato dalla radice del repository invece che dalla cartella della v2 | tolte il 22-11 (blocco Pulizia); ora il blocco Aggiornare si ferma con `FERMO` se il terminale non è nella cartella della v2; controllare sempre che il terminale finisca con `app_cycle_validation_v2>` |
| Avviando una voce composta: `ensure-opensearch-tunnels.ps1 ... non esiste`, exit code 1 | il task «Centralizer prerequisites» chiama uno script che sul PC non c'è | la voce «CV v2» senza il task (`AZIENDA.md`, sezione 7); oppure avviare le voci una per una |
| Avviando «CV» partono v1 e v2 insieme | la v2 aggiunta alla voce composta della v1: tutte e due sulla porta 8003 | voce composta a parte «CV v2» (login, frontend, v2): `AZIENDA.md`, sezione 7 |
| Avvio della v2 in locale: `Secret '...' non leggibile o non valido (ResourceNotFoundException)` | in `CV_ENV_SECRET` un nome diverso da quello della v1 (per esempio con `_v2` in fondo) | lo stesso nome di `load_secrets` della v1: `AZIENDA.md`, sezione 7 |
| Nel pannello di Claude in VS Code tante chat con i nomi delle operazioni dei cicli | il Claude Agent SDK (le sessioni della v2, con Bedrock) salva ogni sessione in `~/.claude/projects` come una chat di Claude Code; il pannello le mostra. Non sono Copilot e non sono chat dell'utente | dal 23-11 la v2 passa `--no-session-persistence` (provato: nessun file scritto); le vecchie (167 chat) spostate il 23-11 in `.claude\chat-validazioni-v2`; il blocco è tolto da COPILOT |
| In una prova della campagna `costo 0.00 $`, nel riepilogo `WARNING ERRORE_TECNICO` come ultimo esito e «mai visti 0 su 29» (25-11 mattina) | l'accesso AWS (SSO) della sera prima era scaduto: i cicli girano, ma ogni chiamata al modello fallisce; la prova contava come fatta | dal 25-11 una prova così non conta (`Trial.unusable`): la campagna si ferma con «il modello non ha risposto» e al lancio dopo la toglie e la rifà. Prima di una campagna: `aws sso login` |
| Blocco della libreria: mancano delle classi (`libreria pronta: False`) | in `vendor` ci sono la 0.3.0 e la 0.4.0rc2; era stata presa la 0.3.0 | installare la riga dei requirements della v1, 0.4.0rc2 con `[auth]` (`AZIENDA.md`, sezione 7) |

## 12. Decisioni prese

Le risposte già date. Le domande ancora aperte sono in `COPILOT.md` (sezione 6.1).

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
- **Proposte delle migliorie (24-11-2026):** niente cartelle con un report per variante in
  `eval/` (il repository è pubblico e i risultati veri restano in `runs/`). Ogni variante ha
  `descrizione`, `ipotesi` e `atteso`; `eval prova` li mette in cima a `prestazioni.md` e nella
  tabella «Le proposte e la decisione» del riepilogo. Le considerazioni le scrive Claude nel
  registro di `MIGLIORIE.md`, colonna «Considerazioni».
- **Campagna di prove (24-11-2026, richiesta dell'utente):** «lanciare tutti gli esperimenti
  in automatico, prima con Haiku e poi con Sonnet, sul piccolo e sul grande; io leggo solo i
  risultati finali», e poterne lanciare anche solo una parte. Fatto con `eval campagna` ed
  `eval/campagna.yaml` (lo aggiorna Claude). Sonnet ha cartelle e base sue. Le prove fatte si
  saltano; tetto di spesa 60 $. Report unico `runs/campagna.md`.
- 24-11 sera, l'utente: Haiku e Sonnet in parallelo, un terminale ciascuno. Si può: cartelle
  diverse, nessun file in comune tranne il report, che ora con `--modelli` è
  `runs/campagna-<modello>.md`; alla fine `--solo-report` fa `runs/campagna.md` (gratis). Il
  tetto vale per terminale: COPILOT dà 10 $ a Haiku e 50 $ a Sonnet. Se escono «cicli non
  eseguiti» (troppe richieste ad AWS insieme), Sonnet si rifà da solo dopo Haiku.
- 24-11 sera, l'utente: quattro terminali (modello × insieme)? Sconsigliato: il grande dipende
  dal piccolo (farebbe solo la base) e due terminali dello stesso modello si dividono la quota
  AWS (WARNING per errore tecnico, numeri falsati). Sistemato comunque: report con anche
  l'insieme nel nome, `prova.json` scritto e poi rinominato, prove illeggibili saltate.
- 24-11 sera, passi 1–4 fatti. Copie cieche nuove (seme 1): 41 su 100 chieste, sei tipi:
  numero_una_lingua 5, numero_manuale 3, negazione_una_lingua 9, task_inesistente 5,
  negazione_due_lingue 9, limite_invertito 10 (mai visti per il modello 31, del codice 10;
  prima 21 e 10). Piano: piccolo 51 cicli e copie, grande 23, tutto `2 da fare`, grande solo
  base (dipende dal piccolo). Sonnet sul piccolo potrebbe stare vicino al tetto di 50 $.
- **24-11 sera, campagna sul piccolo finita** (Sonnet 19:20-21:12, Haiku 19:20-21:22, in
  parallelo senza problemi). Cicli 49 (non 51): due copie cieche erano doppie (due stampe dello
  stesso ciclo, stessa copia, stessa impronta); corretto in `blind_mutations`, vale dalle
  prossime copie. Haiku: base 19 stabili (visti 8 su 10, mai visti 2 su 29, codice 9 su 10),
  `elementi_uno_per_uno` 21 (mai visti 4), `lingue_separate` 20 (4). Sonnet: base 18 (mai
  visti 1), `lingue_separate` 19, costo ×12. Visti mancati sempre 298bc28e 035 e f355dc3c 010,
  con `EVIDENZA_NON_TROVATA`: il testo del manuale giusto non arriva al modello. Regola «si
  tiene» resa più severa (serve più errori o un risparmio vero): quattro varianti per
  differenze di rumore finivano anche sul grande. Registro e considerazioni in MIGLIORIE 13.
- **24-11 notte, preparato il 25-11** (richiesta: «risolvi tutti i problemi», domani si
  rilancia). Nuova miglioria `seconda_ricerca` (`agent.search_when_unverifiable`): dopo un
  «non verificabile» una seconda sessione cerca con i tool in tutti i documenti del ciclo
  (ipotesi: il testo del task arriva spesso nel messaggio, senza tool, e il passo giusto è
  altrove). Varianti `elementi_e_lingue` e `tutto_insieme`. Campagna: solo Haiku (Sonnet tolto),
  solo le migliorie, 3 prove, tetto 15 $. Copie cieche **non** rifatte (restano le 39 diverse):
  le prove del 24-11 valgono ancora. COPILOT sezione 1: tappa 3, passi Aggiornare, piano,
  campagna, report (con «Errori mai visti per tipo» e «WARNING per motivo», che mancano ancora).
- **25-11 mattina, tappa 3.** Aggiornare e piano a posto (piccolo come previsto; grande 3 da
  fare per base, elementi e lingue: la sera del 24-11 Haiku non era arrivato al grande). La
  campagna partita con l'accesso AWS scaduto: prova «base» con `costo 0.00 $`, visti 7 su 10
  (solo i controlli del codice), mai visti 0 su 29. Il riepilogo **non sovrascrive**: ogni
  prova è una colonna in più (da 18 a 19), «Ultimo esito» è quello dell'ultima prova. Corretto:
  le prove senza risposte del modello non contano, la campagna si ferma e le rifà.
- **25-11 mezzogiorno.** Piccolo finito (12 prove, circa 4 $); l'utente ferma con Ctrl+C alla
  prima riga del grande, stacca il PC per il pranzo e rilancia lo stesso blocco: il piccolo si
  salta da solo (prove già fatte), una prova interrotta non conta. Prima prova di
  `tutto_insieme`: mai visti 5 su 29 ma 0,37 $ a prova (×2,2 la base: rischio «scartata» per
  costo). `COPILOT.md` riscritto corto (stesse sezioni 0-7, stessi blocchi); `MIGLIORIE.md` con
  «In breve», regola della prova non valida e registro del 25-11.
- **25-11, risposte di Copilot alle domande** (chat in modalità *Agent* con «Allow all»:
  ricordato all'utente di tornare in **Ask**; Copilot si offriva di cambiare
  `eval/errori-noti.yaml`, lo fa Claude). P1 chiusa (capitolo 70 civile = SPM). P4 confermata
  (lettere rovinate in `�`). P6, P7, P8 proposte da confermare (COPILOT 6.1). P7: il «4 volte»
  viene dalla sezione d'ispezione del manuale del motore citato in testata → l'ERRATO della v2
  sulla stampa giusta sarebbe un **falso errore**: la v2 confronta solo con il task SPM. P9:
  5ff17062 sarebbe una copia di 04ecaabe con 010, 030, 040, 050 cambiate (come f355dc3c):
  da verificare con `confronta`. La lista degli errori noti **non** si cambia durante la
  campagna: si cambia quando la base cambia (prove archiviate, seme nuovo).
- **26-11, report della campagna del 25-11** (piccolo e grande, 33 prove, 4,13 $). Scelta:
  `elementi_e_lingue` nella base (valori predefiniti nel codice: `data/settings.yaml` sul PC
  non li nomina, quindi la base nuova vale anche lì; il passo 2 di COPILOT lo controlla).
  `tutto_insieme` 22 stabili e 5 mai visti ma ×2,2 il costo: si riprova come `seconda_ricerca`
  sopra la base nuova. Scoperto: 22 dei 26 mai visti mancati erano su operazioni senza task
  nella conoscenza (FONTE_ASSENTE) → copie cieche del modello solo su operazioni confrontabili;
  ERRORE_TECNICO 7,7 per ciclo sul PC = targhe. **Errore di Claude:** la regola «prova non
  valida» per le prove vecchie contava tutti i WARNING tecnici e al rilancio del 25-11 ha
  cancellato le prove buone di Haiku del 24-11 (Sonnet intatto; i numeri restano nel registro
  di MIGLIORIE). Corretta: per le prove vecchie solo zero token. Nuovo nel riepilogo: «ERRATO da
  verificare» per ciclo e operazione. Prossimo giro: archiviare, seme 2, campagna base nuova
  contro `seconda_ricerca`. Il blocco Archiviare ora rimette la lista dei cicli scelti.
- **26-11, secondo giro.** Due riavvii del PC (problema del computer): la campagna riparte da
  sola dalle prove mancanti (una prova scrive il suo file solo alla fine; quella interrotta non
  conta e si rifà). Piano dopo il secondo riavvio: piccolo finito, `seconda_ricerca` **si
  tiene** sul piccolo, sul grande mancano le sue 3 prove.
- **26-11, domande P1-P9 chiuse** (decise da Copilot sui dati, senza referente; dove i dati non
  bastano: regola prudente, WARNING e mai ERRATO). P2: l'ERRATO del ciclo DR era un giudizio
  instabile, G1 lo evita già. P6: scheda obbligatoria solo nei processi speciali → WARNING
  «scheda forse mancante» (I9 da scrivere). P7: vale il manuale del motore, l'ERRATO su
  04ecaabe 050 è un falso errore (I8 `fonte_ispezione` da scrivere; fino ad allora resta in
  attesa). P8: operazioni senza task → task della prima riga di note, per le ispezioni anche la
  sezione d'ispezione del manuale del motore. P9 verificata con `confronta`: 5ff17062 ha 010,
  030, 040, 050 cambiate; `eval/errori-noti.yaml` aggiornato, vale dal giro dopo questa
  campagna (non aggiornare il PC mentre la campagna gira).
- **26-11, report della campagna** (seme 2): `seconda_ricerca` stessi errori della base (14 su
  25 sul piccolo, 7 su 10 sul grande), costo ×2,1 sul grande → non entra; la base resta.
  Scoperte: i 7 visti stabili li trova tutti il controllo delle lingue (il modello ne aggiunge
  pochi); le copie «numero in una lingua» trovate 1 su 5 → corretto il controllo delle lingue
  (I10: conversione in una lingua sola). Da verificare sul grande: 895167b9 010/030/060,
  2d724fba 050 (domanda a Copilot in COPILOT sezione 1). Prossimo: ingestion del manuale del
  motore, `fonte_ispezione`, regola della scheda.
- **26-11, richiesta nuova:** in azienda chiedono una guida agli unit test (Python, backend del
  chatbot, forse il frontend) per gli sviluppatori dei vari use case, che sono data scientist.
- **`.gitignore` di `docs/` (24-11-2026):** in git entra solo `DOCUMENTAZIONE.md`; gli altri
  quattro file erano già seguiti e restano (servono al blocco Aggiornare e alla memoria).
- **26-11 sera, ERRATO da verificare del grande (Copilot, che era di nuovo in Agent: ricordare
  Ask).** 895167b9 è una copia modificata, non un ciclo vero (come 5ff17062): 4 errori, ora in
  `eval/errori-noti.yaml`. 2d724fba 050 è un falso errore su un ciclo vero, causa P7 («4 volte»
  contro la definizione generica di «3 volte» dell'SPM): 2d724fba è ora una stampa giusta con
  la 050 in attesa. Tre errori veri la v2 li trova per il motivo sbagliato. Scritta la variante
  `definizioni_generali` (I11); campagna base contro questa, `grande: sempre`. Da chiedere a
  Copilot: l'impronta della stampa originale di 895167b9 e se nella lista del grande ci sono
  altre copie modificate.

## 13. Da correggere nell'indice (knowledge-index)

**Titoli dei task GE.** `regole.json` (`codice_task`) riconosce solo il codice completo
(`72-00-01-110-001`). I titoli `72-00-01 REPAIR 001` e `CIR 72-00-01, REPAIR 001` l'indice non
li registra: la v2 li trova nel testo, ma l'indice potrebbe registrarli (con la stessa regola di
`kb/task_text.py`), così anche il controllo di Copilot li vedrebbe.

**Targa `90`.** Nel file delle targhe la `90` ha come funzione una frase rimasta dal documento
(«la descrizione breve può essere scelta…») con le lettere accentate rovinate. Nei dati TM la
stessa targa compare in tre righe (pagine 14, 17, 18) con funzioni diverse. Come correggere:

1. aprire il PDF TM alle pagine 14, 17 e 18 e guardare la colonna della funzione;
2. scartare le righe dove la "funzione" è una frase (è una nota della tabella);
3. leggere il testo con la codifica giusta: nei file pubblicati non devono esserci `Ã`, `â€`
   né `�` (25-11: nel file delle targhe le lettere accentate sono diventate `�`);
4. con la stessa targa su più righe, unire le funzioni con `; ` invece di tenere solo la prima;
5. se non c'è tempo: in `uncertainty.json` scrivere
   `{"format": 1, "machine_tags": {"90": ["da_record_parziale"]}}` (la targa esce WARNING
   finché non si corregge);
6. pubblicare la nuova versione e lanciare `kb-check`.

## 14. Come si scrive `COPILOT.md`

- Struttura (riscritta il 24-11-2026, su richiesta dell'utente: «estremamente semplice, non
  dare per scontato nulla»): 0 prima di iniziare (parole, come si lancia un blocco, regole,
  cosa fare se va storto), 1 cosa fare adesso (dal 24-11: la strada con tutte le tappe e ✅ fatta,
  👉 adesso, ⬜ dopo; «dove siamo» in tre righe; i passi di adesso uno per uno, ognuno con titolo,
  costo e tempo, il comando da copiare o il link al blocco, «Deve uscire» e «Mandami»; poi le
  tappe dopo e «Quando hai tempo»),
  2 aggiornare e salvare (2.1, 2.2), 3 le prove (3.1 come funzionano, 3.2 cicli veri, 3.3
  copie cieche, 3.4 gruppo nascosto, 3.5 campagna, 3.6 leggere i risultati, 3.7 prova a mano,
  3.8 togliere, azzerare, archiviare), 4 frontend, 5 ingestion, 6 persone, 7 QA. Riordinato il
  24-11: se si cambia la numerazione, aggiornare i rimandi negli altri documenti e nel codice.
  In «Dove siamo» solo lo stato di oggi: la storia va qui in MEMORIA.
- Prima di ogni blocco: **a cosa serve**, **quando**, se **costa**; per i blocchi lunghi anche
  cosa fa passo per passo.
- Blocchi PowerShell da copiare così come sono, senza niente da cambiare; ognuno comincia con
  `$env:UV_PYTHON = "3.14"` (tranne quelli di solo git o solo apertura di file).
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
- Il blocco di aggiornamento toglie da solo sul PC i file che nel repository personale non ci
  sono più (`src`, `tests`, `prompts`, `examples`, `eval/casi/sintetici`, `eval/varianti` e i
  `.md` di `docs`); copia anche `eval/errori-noti.yaml` (dal 24-11): un file tolto qui sparisce anche lì al primo aggiornamento, e Salvare lo registra come
  `D`. Il blocco si ferma (`FERMO`) se il download non riesce o il terminale non è nella cartella
  della v2.

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
