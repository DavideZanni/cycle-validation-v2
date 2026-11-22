# Memoria del progetto: PC aziendale, prove, problemi già risolti

Da leggere **prima** di ogni lavoro sulle prove aziendali, e da aggiornare quando si impara
qualcosa di nuovo (un problema, una regola, un comportamento del frontend). Serve a non rifare
le stesse analisi. Aggiornata il 22-11-2026.

Niente valori veri qui (il repository è pubblico): bucket, account, host, matricola, codici di
manuali, numeri DR, serial number, part number, codici dei cicli e contenuti EJ200 restano solo
sul PC.

Indice: [Chi fa cosa](#chi-fa-cosa) · [Il PC](#il-pc) · [Copilot](#copilot) ·
[I servizi](#i-servizi) · [La conoscenza di prova](#la-conoscenza-di-prova) ·
[Regole sui dati](#regole-sui-dati) · [La pipeline in breve](#la-pipeline-v2-in-breve) ·
[Il frontend](#il-frontend-della-v1-gateway-qa) · [Stato delle prove](#stato-delle-prove) ·
[Problemi già visti](#problemi-già-visti-e-cosa-fare) · [COPILOT.md](#come-si-scrive-docscopilotmd) ·
[Le stampe](#le-stampe-pvrm320-viste-finora) · [Dove sta cosa](#dove-sta-cosa)

---

## Chi fa cosa

| Chi | Cosa fa | Cosa non fa |
|---|---|---|
| Claude | modifica codice, test e documenti nel repository personale (`main`, nessun branch); scrive in `docs/COPILOT.md` i blocchi da lanciare; legge le foto | non ha accesso al PC aziendale, ad AWS, al frontend né al repository aziendale: vede solo le foto |
| L'utente | lancia i blocchi di `docs/COPILOT.md` nel terminale di VS Code e manda le foto; fa commit **e push** nel repository aziendale con i blocchi di `COPILOT.md` | non modifica il codice a mano |
| Copilot (sul PC) | può **leggere** il codice e **lanciare** prove e test | **non modifica il codice** (regola dell'utente, 21-11-2026) e non legge `data/` (vedi [Copilot](#copilot)) |

Flusso di una correzione: Claude corregge su `main` → l'utente lancia **Aggiornare il codice sul
PC** (clone temporaneo, `robocopy` di `src/`, `tests/`, `docs/`, `eval\casi\sintetici`, poi
`pytest`) → prova → **Salvare le correzioni** (commit, poi push con controllo del branch).

Repository aziendale: la v2 sta in `app_cycle_validation_v2/`, branch
`feature/cycle-validation-v2`. La v1 (`app_cycle_validation/`) è in produzione e **non si
tocca**. Il push lo fa l'utente; mai `--force`.

## Il PC

- Windows 11, VS Code, terminale **PowerShell 7** (`pwsh`): i comandi sono PowerShell, non bash.
  Il terminale sta in `app_cycle_validation_v2` (il prompt finisce con `app_cycle_validation_v2>`).
- Python di sistema 3.14 (il progetto dice 3.13): **ogni blocco comincia con
  `$env:UV_PYTHON = "3.14"`**. Si usa `uv`.
- `git clone` da github.com funziona (repository personale pubblico). I commit aziendali usano
  l'email aziendale.
- AWS CLI con SSO, regione `eu-south-1`. Token scaduto: `aws sso login`.
- Proxy Zscaler: finora nessun errore di certificati con Bedrock e S3. Se capita:
  `zscaler.pem` della v1 in `NODE_EXTRA_CA_CERTS` e `AWS_CA_BUNDLE` (il comando è in
  `COPILOT.md`).
- Antivirus e indicizzatore tengono aperti per un attimo i file appena scritti: una rinomina
  subito dopo può fallire con `PermissionError [WinError 5] Accesso negato`. Il codice riprova
  (`rename_when_free` in `kb/published.py`); il test
  `test_a_new_version_is_picked_up_after_the_check_interval` può comunque fallire una volta:
  si rilancia.
- **Incollare nel terminale esegue le righe una alla volta.** Un `if` su più righe si rompe se
  `} elseif (...) {` o `} else {` stanno su una riga a parte: vanno sulla stessa riga della `}`
  che chiude (errore visto il 21-11-2026 sul blocco del push). Meglio blocchi corti, un passo
  per blocco (commit e push separati).
- Nel container di Claude `pwsh` non si installa: i blocchi si rileggono a occhio prima di
  darli.

## Copilot

- La *content exclusion* dell'organizzazione GitHub vieta a Copilot `data/` e gli URI S3 che ne
  vengono: rifiuta. **Non si aggira** (niente rinomine o spostamenti): solo gli amministratori
  possono cambiarla. Per questo i comandi li lancia l'utente, non Copilot.
- Copilot può leggere il codice del repository aziendale (anche il frontend, se è lì): utile
  per domande tipo «trova la funzione che fa X e incollala». Nella domanda scrivere sempre
  «Non modificare niente».

## I servizi

- **Bedrock** (`eu-south-1`): in uso `eu.anthropic.claude-haiku-5-5` per `model` e
  `transcribe_model` in `data/settings.yaml`; disponibili anche i profili `eu.` di Sonnet 5.5 e
  Opus 5.5. Il costo nel report è la stima del claude-agent-sdk sui prezzi Anthropic: su
  Bedrock può essere un po' diverso.
- **S3**: il nome del bucket è in `data/bucket.txt` (git lo ignora). I comandi lo leggono con
  `$(Get-Content data/bucket.txt)` e non lo stampano. Sotto `Manufacturing AI/`:
  - `cicli MOS/` e `cicli DR/`: i PDF veri dei cicli;
  - `ingestion-v2-test-qa-output/knowledge/civil/` e `.../ej200/`: la conoscenza della v2,
    **versione di prova su un sottoinsieme** (sotto);
  - `cv3/knowledge/`: vuoto (è il prefisso predefinito nel codice, da cambiare con
    `CIVIL_KNOWLEDGE_POINTER` quando si configura il servizio);
  - `retrieval_output/`: la conoscenza della v1.
- **Macchine attive**: in azienda vengono da Redshift; non ancora collegate, quindi le righe
  `machine_tag` escono WARNING `ERRORE_TECNICO` e lo stato del ciclo è `parziale`.
- **Frontend**: il gateway QA aziendale (pagina *Cycle Validation*) oggi parla con la v1. La
  v2 non è ancora dietro il gateway.

## La conoscenza di prova

L'utente ha ingestionato solo un sottoinsieme (i file sono circa 2000, tutti costerebbero
troppo): 8 capitoli del manuale SPM (capitolo 70), 2 procedure DR, 104 targhe, 94 schede,
23 recommendation DR (17 serial number, 5 con più recommendation). I manuali dei motori
**non** ci sono: le righe che ne dipendono escono WARNING `FONTE_ASSENTE`, ed è giusto.
**Decisione del 21-11-2026: per ora non si ingestiona altro**, si prova solo con questo
sottoinsieme. Il comando per trovare i sorgenti da aggiungere è in fondo a `COPILOT.md`.

La copia locale (solo `civil/`) è in `eval/casi/aziendali/conoscenza/foto-20261121/`; i PDF
dei cicli in `docs\Esempio ciclo mos\` e `docs\Esempio ciclo dr\` (git li ignora).

## Regole sui dati

- Guida aziendale (`Guida_test_QA_SageMaker.md`): *«Non caricare o spostare documenti per fare
  il test. I documenti e gli output EJ200 restano su AWS EU; non copiarli nella repository o
  fuori dall'ambiente autorizzato.»* Quindi: **nessuna copia locale della conoscenza EJ200**
  (quella scaricata per errore è stata cancellata il 21-11-2026), la fotografia si fa solo di
  `civil/`, e **un ciclo EJ200 non si prova sul PC** (l'output finirebbe in `runs\`): va
  provato dentro AWS, per esempio con la v2 dietro il gateway QA. Nei documenti non si
  scrivono contenuti EJ200 visti nelle foto.
- I dati veri stanno solo in cartelle che git ignora: `data/`, `runs/`, `eval/casi/aziendali/`,
  `docs/Esempio*/`.
- Nel repository personale non vanno mai: nome del bucket, account AWS, host, ARN, nomi dei
  segreti, matricola o utente Windows, codici dei manuali, numeri delle procedure DR, serial
  number, part number, codici dei cicli. Negli esempi e nei test: valori inventati. I comandi
  di `COPILOT.md` prendono i codici veri dai file sul PC (conoscenza, PDF, output di `leggi`).
- Le foto possono mostrare il nome del bucket, un codice di ciclo, il percorso Windows con la
  matricola, un caso DR, codici di manuali o task: **non ripeterli** né in chat né nei
  documenti.
- `report.md` non si manda a Claude (contiene le citazioni dei manuali): bastano le righe di
  riepilogo stampate dai blocchi; i giudizi l'utente li dà a parole.

---

## La pipeline v2 in breve

Dettagli in `docs/MIGLIORIE.md` («Come è fatto») e `docs/AZIENDA.md`.

1. **Lettura del PDF**: il parser di layout PVRM320 (zero token) per MOS, DR ed EJ200; se non
   riconosce il layout, l'estrazione col modello. Il parser è più stabile e costa meno (prova
   del 21-11-2026): si tiene.
2. **Integrità**: ogni valore letto deve comparire nel testo del PDF, altrimenti
   `ESTRAZIONE_NON_CONFERMATA` (WARNING).
3. **Controlli**, scelti dal profilo `config/profiles/mos|dr|ej200.yaml`: `dr_recommendation`
   (solo DR, **bloccante**), `source`, `task_code`, `machine_tag`, `process_sheet`,
   `operation_description`. Per EJ200 le schede non si verificano (N/A).
4. **Esito per riga**, deciso dal codice (`domain/check.py`, motivo → esito):
   - CORRETTO: `VERIFICATO`;
   - ERRATO: `CONTRADDIZIONE`, `MACCHINA_NON_ATTIVA`, `DR_NON_APPLICABILE`,
     `DR_NESSUNA_CORRISPONDENZA`;
   - NON_APPLICABILE: `CAMPO_ASSENTE`, `ESCLUSO_DA_REGOLA`, `NON_VERIFICATO_PER_PROFILO`;
   - WARNING: tutto il resto (`FONTE_ASSENTE`, `EVIDENZA_NON_TROVATA`, `ERRORE_TECNICO`,
     `GIUDIZIO_INSTABILE`, `DR_SENZA_RIPARAZIONE`, ...). Un guasto dà WARNING, mai ERRATO.
5. Il modello giudica **solo** la descrizione dell'operazione contro il testo della fonte, e
   ogni citazione viene ritrovata dal codice; se non c'è, `CITAZIONE_NON_VERIFICATA`. Un ERRATO
   della descrizione si rifà con 2 sessioni: resta ERRATO solo se lo ritrovano tutte,
   altrimenti `GIUDIZIO_INSTABILE` (G1).
6. **Stato del ciclo**: `bloccato` se un controllo bloccante fallisce; `parziale` con
   `ERRORE_TECNICO` o `BUDGET_ESAURITO` (oggi sempre, per il registro macchine); altrimenti
   `completo`.
7. **Output**: `report.json`, `report.md`, e `payload.json` nel formato che il frontend riceve
   oggi (`report/legacy_payload.py`).

**Regole DR** (domanda 17, da confermare):

| Disposizione della recommendation | `dr_recommendation` | Gli altri controlli |
|---|---|---|
| `Repair` | CORRETTO | proseguono, con task e procedura DR come riferimento |
| `Accept as is` / `Use as is` | WARNING `DR_SENZA_RIPARAZIONE` | proseguono, senza la procedura di riparazione |
| `Reject` | ERRATO `DR_NON_APPLICABILE` | bloccati |
| `Repair` + `Accept as is` | CORRETTO con nota | solo la `Repair` come riferimento |

Il serial number cerca la recommendation; la condition sceglie tra più recommendation dello
stesso serial number. Oggi sono obbligatori tutti e due (domanda 18: si possono rendere
facoltativi).

## Il frontend della v1 (gateway QA)

Visto dalle foto il 22-11-2026.

- **Percorso**: «Which cycle do you want to validate?» → *Civil cycle (DR/MOS)* o *EJ200 cycle
  (military)*. Civile → «Devi validare un ciclo DR?» → *Yes – DR* chiede `Serial Number (S/N)`
  e `DR Condition Numbers` (una o più, separate da virgole), poi il PDF; *No – MOS* chiede
  subito il PDF. EJ200 chiede subito il PDF. Durante la validazione: «Validating...».
- **Esito**: intestazione con il nome del file e le etichette (codice ciclo, descrizione,
  tipo, `RC`, tipo di ciclo). Tabella *Sources*: Repair Code, Type, Reference, Task, Feedback.
  Tabella *Operations*: Op #, Description (con `RC`), Targa C.Resp, Task Code, Scheda,
  Op. Feedback, TM Feedback, Task Code Feedback, Scheda Feedback. Pulsante di download, pollice
  su/giù, «New validation».
- **Intestazione**: «Validation Passed» (verde) se non ci sono errori, **anche con dei
  Warning**; «Completed with Errors» (arancione) con «N errors» se ce n'è almeno uno, e «1 err»
  accanto all'operazione.
- **Bollini**: `OK` + «No errors found»; `Warning` giallo con il testo; `Error` rosso con
  «Error found: ...»; `N/A` grigio senza testo; `Info` azzurro con un testo («N/A, non
  verificato per EJ200»).
- La v2 manda gli stessi campi e gli stessi prefissi («No errors found.», «Warning: ...»,
  «Error found: ...»). **Aperto**: la v2 manda `N/A - <motivo>` per ogni N/A; se il frontend fa
  `Info` di ogni N/A con testo, le celle vuote diventano `Info`. Serve la regola del frontend
  (da chiedere a Copilot).
- **La v1 non è un riferimento**: dà falsi positivi (su un ciclo EJ200 due «Error» con valori
  che rispettano il limite) e giudizi incoerenti (stesso task, pezzi dello stesso tipo: OK in
  un ciclo, Warning nell'altro). Per giudicare la v2 serve la risposta giusta di chi conosce i
  cicli, non l'esito della v1.

## Stato delle prove

Al 22-11-2026, con Bedrock Haiku 5.5 e la conoscenza di prova:

- **MOS**: terzo ciclo `7 corretti, 16 warning, 0 errati, 14 non applicabili`, 0,0058 USD. I
  WARNING vengono dal manuale del motore assente e dal registro macchine.
- **DR**: le tre condition del ciclo vero danno l'esito atteso: `Repair` 5 corretti, 0 errati,
  0,006-0,011 USD e 9-11 sessioni per run; `Accept as is` WARNING `DR_SENZA_RIPARAZIONE`,
  0 errati, 0 USD.
- **EJ200**: mai provato con servizi veri (va fatto in AWS, vedi regole sui dati).
- **Ciclo MOS «con errori»** (dato già segnato come errato): blocco pronto in `COPILOT.md`;
  manca la risposta su quali siano gli errori.

## Problemi già visti e cosa fare

| Sintomo | Causa | Cosa fare |
|---|---|---|
| Molti WARNING `FONTE_ASSENTE` | manuali dei motori non ingestionati | niente: è giusto; si risolve con l'ingestion, quando si decide |
| Stato `parziale`, targhe WARNING `ERRORE_TECNICO` | registro macchine (Redshift) non collegato | niente finché non si collega |
| La stessa descrizione esce a volte ERRATO, a volte CORRETTO | il modello oscilla (op. 060 del ciclo DR: ERRATO 2 volte su 3) | G1: un ERRATO si conferma con 2 sessioni, altrimenti `GIUDIZIO_INSTABILE`. Prima di «correggere» un ERRATO, ripetere il run 3 volte |
| Esiti diversi tra ciclo letto dal modello e dal parser | il modello legge in modo diverso (repair code mancante, fonti in più) | usare il parser per le stampe PVRM320 |
| `Accept as is` bloccava tutto il DR | le procedure DR pubblicate sono solo di riparazione: «accept as is» non c'è mai | regola G2 (tabella DR sopra) |
| Una ricerca nel testo della conoscenza non trova niente | si cercava riga per riga e le frasi vanno a capo | cercare sul testo intero (`Get-Content -Raw`) e contare |
| Previsto «completo», uscito `parziale` | dimenticato il registro macchine | ogni previsione di stato tiene conto di `ERRORE_TECNICO` |
| Test degli esiti attesi falliti sul PC | `eval\casi\sintetici` non copiata | il blocco di aggiornamento la copia (dal 21-11-2026) |
| Blocco del push fallito a metà | righe incollate una alla volta, `else` su riga a parte | `} else {` sulla stessa riga della `}`; commit e push in blocchi separati |
| `PermissionError [WinError 5]` | antivirus o indicizzatore | il codice riprova; un test può fallire una volta: si rilancia |
| Copilot rifiuta un comando o un file | content exclusion su `data/` | lancia l'utente; non aggirare |
| Il bucket si vede in una foto | scheda di `data/bucket.txt` aperta | non ripeterlo, chiedere di chiudere la scheda |
| Un esito della v1 sembra sbagliato | la v1 è meno affidabile | non usarla come riferimento: chiedere a chi conosce i cicli |

## Come si scrive `docs/COPILOT.md`

- Blocchi PowerShell da copiare così come sono, senza niente da sostituire; ogni blocco comincia
  con `$env:UV_PYTHON = "3.14"`.
- Dopo ogni blocco: **Deve uscire** (cosa aspettarsi) e **Manda a Claude** (cosa fotografare).
- Se un blocco costa (Bedrock), dirlo. Per esplorare a costo zero c'è `cycle-validation leggi`
  (parser, nessun modello; `--pagina N` stampa il testo di una pagina).
- Un blocco che può fare danni (push) si protegge con un controllo che stampa `FERMO: ...` e
  non fa niente se qualcosa non torna (branch sbagliato, file fuori dalle cartelle previste).
- Le parti fatte si riducono a un riassunto di poche righe (l'utente vuole il file pulito);
  restano: *Se qualcosa va storto*, *Dove siamo*, *Aggiornare il codice sul PC*, *Fatto
  finora*, *Da fare nei prossimi giorni*, *Ancora aperte*, *Salvare le correzioni*, *Più
  avanti*.
- Accorgimenti PowerShell: nei pattern di `Select-String` usare `\S+` al posto di caratteri come
  `·`; `Get-Content -Raw` prima di `ConvertFrom-Json`; in `aws s3 ls` il nome del file comincia
  alla colonna 31; i PDF si cercano per nome parziale (`Get-ChildItem -Filter`), mai con il
  codice vero nel blocco.

## Le stampe PVRM320 viste finora

- MOS e DR hanno lo stesso modulo: testata ripetuta a ogni pagina, tabella a colonne con
  asterischi, manuale OEM nel piè. Il parser di layout le legge a zero token; se non ci riesce,
  `run` passa all'estrazione con il modello.
- I task stanno nel testo come `TASK 70-xx-xx-xxx-xxx` e si leggono per intero. I task del
  capitolo 70 si cercano anche nel manuale SPM (scelta da confermare, domanda 16 in
  `DOMANDE_APERTE.md`).
- Stampe DR: un'operazione può avere in tabella solo la prima riga, a metà frase (la NOTE
  op. 005 a pagina 2, l'op. 050 a pagina 5); il seguito, con l'inglese ed eventualmente la riga
  `SCHEDA`, sta dopo il banner di fine pagina `*** C O N T I N U A ***`. Il parser lo attacca
  all'unica operazione della pagina rimasta a metà; se non è una sola, si ferma (e `run` passa
  al modello).
- Una delle stampe DR scrive nel testo il caso DR e il serial number del pezzo («D.R. CASE #…»,
  «APPLY ON S/N …»); `leggi` li stampa. Le altre no. La condition non è mai nella stampa. I
  cicli DR non citano task: i task vengono dalla recommendation.
- Stampe EJ200 (viste solo nel frontend della v1): descrizioni in italiano maiuscolo, fonti
  RDR/RN/EF, schede `PG ...`.

## Dove sta cosa

| File | Cosa contiene |
|---|---|
| `CLAUDE.md` | le regole che non si discutono |
| `docs/AMBIENTE_AZIENDALE.md` | questa memoria |
| `docs/COPILOT.md` | i blocchi da lanciare sul PC, lo stato del lavoro, le cose da fare |
| `docs/DOMANDE_APERTE.md` | le domande per chi conosce i cicli, con le risposte |
| `docs/MIGLIORIE.md` | com'è fatto il codice, cosa resta da costruire, registro degli esperimenti |
| `docs/AZIENDA.md` | installazione, configurazione, servizio, esperimenti in azienda |
| `docs/FORMATO_CONOSCENZA.md` | il formato della conoscenza pubblicata, confrontato con i file veri |
| `docs/IMPORTAZIONE.md` | come la v2 è entrata nel repository aziendale |
