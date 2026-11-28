# Documentazione del progetto

Questo file spiega **tutto il progetto**: a cosa serve, come è fatto, come funziona ogni pezzo,
dove sta il codice, come si prova e come si pubblica. È scritto per chi lo legge la prima
volta e per chi deve ritrovare un dettaglio.

Ultimo aggiornamento: 27-11-2026. Claude lo aggiorna quando cambia il funzionamento del
programma: regole, controlli, comandi, impostazioni.

Gli altri documenti in `docs/`:

| File | A cosa serve |
|---|---|
| `DOCUMENTAZIONE.md` | questo file: com'è fatto e come funziona tutto il progetto |
| `COPILOT.md` | il lavoro sul PC aziendale: cosa fare adesso, i blocchi PowerShell da lanciare |
| `MEMORIA.md` | la storia: cosa si è visto, i problemi già risolti, le decisioni prese |
| `MIGLIORIE.md` | tutte le migliorie, provate e da fare, in una tabella (sigle MG01…) |
| `CONFRONTO_V1_14_CICLI.md` | i risultati della v1 sui 14 cicli con errori noti e il testo originale delle stampe (dati veri: vedi sotto) |

Il repository è pubblico: qui ci sono **solo valori inventati**. Unica eccezione:
`CONFRONTO_V1_14_CICLI.md`, con i codici veri, che il responsabile dell'utente ha permesso di
tenere nel repository pubblico (27-11-2026); è un dato, non si modifica. Niente nomi di bucket,
account, host, matricole, codici di manuali, numeri DR, serial o part number veri, codici dei
cicli, contenuti EJ200.

---

## Indice

1. [Cos'è, in breve](#1-cosè-in-breve)
2. [Parole da conoscere](#2-parole-da-conoscere)
3. [Chi fa cosa e dove sta il codice](#3-chi-fa-cosa-e-dove-sta-il-codice)
4. [I principi del progetto](#4-i-principi-del-progetto)
5. [La pipeline, passo per passo](#5-la-pipeline-passo-per-passo)
6. [I controlli, uno per uno](#6-i-controlli-uno-per-uno)
7. [Esiti e motivi](#7-esiti-e-motivi)
8. [Stato del ciclo, conteggi, report](#8-stato-del-ciclo-conteggi-report)
9. [Il modello e l'agente](#9-il-modello-e-lagente)
10. [La conoscenza](#10-la-conoscenza)
11. [Le macchine attive](#11-le-macchine-attive)
12. [Impostazioni e profili](#12-impostazioni-e-profili)
13. [Il servizio (API)](#13-il-servizio-api)
14. [I comandi (CLI)](#14-i-comandi-cli)
15. [Misurare la qualità](#15-misurare-la-qualità)
16. [Pubblicare in QA e in produzione](#16-pubblicare-in-qa-e-in-produzione)
17. [Regole sui dati e sicurezza](#17-regole-sui-dati-e-sicurezza)
18. [Le cartelle e i file](#18-le-cartelle-e-i-file)
19. [Test e verifiche](#19-test-e-verifiche)
20. [Limiti noti e regole da rivedere](#20-limiti-noti-e-regole-da-rivedere)
21. [Se qualcosa non va](#21-se-qualcosa-non-va)
22. [Come si aggiorna questo file](#22-come-si-aggiorna-questo-file)

---

## 1. Cos'è, in breve

**Il problema.** In azienda i cicli di riparazione dei motori aeronautici sono stampe PDF
(modulo PVRM320, «CICLO DI LAVORAZIONE»). Ogni ciclo ha una lista di **operazioni**: cosa fare,
su quale macchina, seguendo quale task del manuale, con quale scheda di processo. Un errore nel
ciclo (un numero sbagliato, una macchina dismessa, un task che non esiste) può finire in
officina.

**Cosa fa il programma.** Legge il PDF del ciclo e controlla ogni riga contro i dati
dell'azienda: manuali, elenco delle targhe delle macchine, schede di processo, recommendation
DR, macchine attive. Per ogni controllo dà un esito: **CORRETTO**, **WARNING**, **ERRATO** o
**N/A**. Il risultato va al frontend aziendale, nello stesso formato della versione di oggi.

**v1 e v2.** La v1 è in produzione e non si tocca. La v2 è questo progetto: la sostituisce. La
v2 risponde al frontend come la v1, quindi il frontend non va cambiato.

**I tre tipi di ciclo:**

| Tipo | Cosa è | Profilo | Particolarità |
|---|---|---|---|
| **MOS** | ciclo civile normale (motori GENX, LEAP) | `mos` | i riferimenti sono task dei manuali |
| **DR** | ciclo civile nato da una segnalazione difetti (Departure Recommendation) | `dr` | in più il controllo della recommendation, che può fermare tutto |
| **EJ200** | ciclo militare | `ej200` | i riferimenti sono pubblicazioni intere (RDR, EF, RN); i dati restano su AWS EU |

**Le differenze principali dalla v1:**

- l'esito lo decide il **codice**, non il modello;
- il modello giudica solo la descrizione dell'operazione, e ogni sua citazione viene ricercata
  nel manuale dal codice;
- un guasto tecnico dà sempre WARNING, mai ERRATO;
- la stampa si legge con un parser a regole fisse (zero costo); il modello solo se il parser non
  la riconosce;
- non c'è ricerca per similarità (niente OpenSearch): il codice sa in quale file e a quali righe
  sta ogni task.

---

## 2. Parole da conoscere

| Parola | Cosa vuol dire |
|---|---|
| **Ciclo** | il documento con le operazioni di una riparazione |
| **Stampa PVRM320** | il PDF del ciclo, con testata ripetuta a ogni pagina e una tabella a colonne separate da asterischi |
| **Operazione** | una riga del ciclo: numero (`010`, `020`…), descrizione, targa, task, scheda |
| **Descrizione** | il testo dell'operazione; nelle stampe PVRM320 è in italiano e poi in inglese, divise da una riga di asterischi (nel testo letto: ` / `) |
| **Fonte** | un riferimento del ciclo: un manuale (con task) o una pubblicazione |
| **Manuale** | documento tecnico del costruttore del motore. Nei documenti si chiamano M1…M6, mai con il codice vero |
| **SPM** | Standard Practices Manual, il manuale delle pratiche standard (capitolo 70) |
| **Task** | un paragrafo numerato del manuale, scritto `72-00-01-110-001` (sezione ATA + tipo + numero) o `72-00-01 REPAIR 001` |
| **Sezione ATA** | le prime tre parti del codice (`72-00-01`) |
| **Subtask** | un passo dentro un task: `SUBTASK 70-00-01-350-002` |
| **Famiglia di un task** | il codice senza l'ultimo gruppo (`70-42-00-350`) |
| **Targa** | il codice della macchina dell'operazione (colonna TARGA della stampa) |
| **Dati TM** | l'elenco delle targhe con la funzione di ogni macchina |
| **Macchine attive** | le macchine in uso oggi (da Redshift, in azienda) |
| **Scheda di processo** | il codice dopo `SCHEDA :` (es. `PG 300`); dati SP |
| **DR / recommendation** | per un serial number e una repair condition, cosa fare del pezzo: `Repair`, `Accept as is`, `Reject` |
| **Serial number, condition** | il numero di serie del pezzo e il numero della condizione di riparazione: scelgono la recommendation |
| **Conoscenza** (knowledge base) | i dati di riferimento pubblicati su S3: manuali in markdown, task, targhe, schede, DR |
| **knowledge-index** | il progetto separato che prepara e pubblica la conoscenza |
| **Versione della conoscenza** | una cartella `v/<data e ora>/`; `current.json` dice quale è in uso |
| **Fotografia** | una copia locale di una versione della conoscenza, per le prove |
| **Profilo** | le regole di un tipo di ciclo (`config/profiles/mos.yaml`, `dr.yaml`, `ej200.yaml`) |
| **Esito** (verdict) | CORRETTO, WARNING, ERRATO, NON_APPLICABILE |
| **Motivo** (reason) | il perché dell'esito, per esempio `CONTRADDIZIONE`; ogni motivo ha un solo esito |
| **Sessione** | una conversazione con il modello per un'operazione |
| **In linea / con ricerca** | sessione con il testo del manuale già nel messaggio (niente tool) oppure con i tool Read e Grep |
| **GRASP** | la regola che obbliga il modello a leggere solo una finestra di righe del manuale, mai il file intero |
| **Impronta** | i primi 8 caratteri dell'SHA-256 del PDF: così si chiama un ciclo nei documenti |
| **Variante** | un file `eval/varianti/<nome>.yaml` che cambia una cosa sola delle impostazioni, con la sua proposta (`descrizione`, `ipotesi`, `atteso`) |
| **Prova** | una corsa della v2 su un insieme di cicli, con il punteggio |
| **Copia cieca** | copia di un ciclo vero con un errore messo dal programma, che nessuno vede |

---

## 3. Chi fa cosa e dove sta il codice

| Chi | Fa | Non fa |
|---|---|---|
| **Claude** | cambia codice, test e documenti nel repository personale, solo su `main`; scrive i blocchi di `COPILOT.md`; legge le foto | non entra nel PC aziendale, in AWS, nel frontend o nel repository aziendale |
| **L'utente** | lancia i blocchi di `COPILOT.md` sul PC aziendale e manda le foto; fa commit e push nel repository aziendale | non cambia il codice a mano |
| **Copilot** (sul PC, in modalità **Ask**) | legge il codice e lancia prove e test | non cambia il codice, non legge `data/` |

**I repository:**

- **personale** (pubblico): dove si scrive il codice. Si lavora solo su `main`;
- **aziendale**: la v2 sta nella cartella `app_cycle_validation_v2/`, sul branch
  `feature/cycle-validation-v2`, accanto alla v1 (`app_cycle_validation/`, in produzione). Il
  push lo fa l'utente, mai con `--force`.

**Come arriva una correzione sul PC:** Claude corregge su `main` → l'utente lancia
*Aggiornare* (COPILOT 2.1) → prova → *Salvare* (COPILOT 2.2: commit e push sul branch
aziendale).

**Il PC aziendale:** Windows 11, VS Code, PowerShell 7, Python 3.14 (ogni blocco comincia con
`$env:UV_PYTHON = "3.14"`), `uv`, AWS con SSO. Copilot non legge `data/` per una regola
dell'organizzazione: non si aggira.

---

## 4. I principi del progetto

Sono le scelte che rendono affidabile il risultato. Non si cambiano senza un motivo forte.

1. **Il codice trova il dove, il modello confronta, il codice decide.** Il codice cerca il
   documento e le righe del task. Il modello legge solo quelle righe e dice se la descrizione
   è coerente. Il codice ricerca ogni citazione del modello nel file e dà l'esito.
2. **Ogni esito discende dal suo motivo.** Non si può costruire un esito incoerente (per
   esempio CORRETTO con motivo `CONTRADDIZIONE`): il programma lo rifiuta
   (`domain/check.py`, `REASON_VERDICT`).
3. **Un CORRETTO o un ERRATO deciso dal modello ha sempre una citazione verificata.** Senza
   citazione ritrovata nel file l'esito resta WARNING.
4. **Un guasto dà WARNING, mai ERRATO.** Modello che non risponde, S3 o Redshift
   irraggiungibili, risposta storta: l'operazione esce WARNING `ERRORE_TECNICO` e il ciclo
   `parziale`.
5. **Assente non vuol dire sbagliato.** Un documento che manca nella conoscenza dà WARNING
   `FONTE_ASSENTE`, non ERRATO.
6. **Ogni valore letto dal PDF deve comparire nel PDF.** Se no, l'esito di quel controllo si
   declassa a WARNING `ESTRAZIONE_NON_CONFERMATA`.
7. **Tutto ciò che è esterno sta dietro una porta.** S3, Redshift, Bedrock, la conoscenza: ogni
   servizio ha un'interfaccia e un'implementazione finta per i test. La suite gira offline,
   senza rete e senza credenziali.
8. **Zero token dove si può.** Parser per leggere la stampa, controlli deterministici per
   targhe, task, schede, fonti, lingue. Il modello solo per la descrizione.
9. **Stessa risposta della v1 al frontend.** Stesse rotte, stessi campi, stessi testi a
   prefisso (`No errors found.`, `Warning: …`, `Error found: …`, `N/A`).

---

## 5. La pipeline, passo per passo

Una sola pipeline per MOS, DR ed EJ200 (`src/cycle_validation/pipeline.py`,
`arun_validation`). Cambia solo il profilo.

```
PDF ─► 1 lettura ─► 2 tipo di modulo ─► 3 estrazione ─► 4 integrità ─► 5 controlli ─► 6 consolidamento ─► 7 report
```

### 5.1 Prima di partire

- Il profilo deve essere attivo (`enabled: true`), altrimenti errore `ProfileUnavailableError`.
- Per un DR, serial number e condition sono facoltativi: se mancano si parte vuoti.
- Se la conoscenza si aggiorna da sola (puntatore `current.json`), **la versione si fissa qui**
  e vale per tutta la validazione, anche se a metà ne viene pubblicata una nuova.

### 5.2 Lettura del file (`ingest/`)

- **PDF con testo:** PDFium legge il testo pagina per pagina (`ingest/pdf.py`). Zero token.
- **Foto, scansioni, PDF senza testo:** le pagine diventano PNG e il modello le trascrive
  (`ingest/transcribe.py`), solo se `agent.transcribe_model` è impostato. Al massimo 60 pagine
  trascritte, 4 insieme (`transcribe_concurrency`).
- **Limiti del file** (dal profilo, `file_limits`): file non vuoto (400), deve essere un PDF
  (415), dimensione massima (EJ200: 20 MB, 60 pagine), almeno 100 caratteri di testo
  («meno di 100 caratteri di testo: è una scansione?»), testo obbligatorio (EJ200: la parola
  `EJ200`).

### 5.3 Tipo di modulo (`module_kind.py`)

Dalla testata, senza modello:

- il campo `PROGETTO` dice militare (`EJ200`) o civile (`GENX`, `LEAP`);
- per un civile, i marcatori DR (`module_check.dr_markers`: `\bDR\b`,
  `DEPARTURE RECOMMENDATION`, il numero di segnalazione `Saa/nnnnn` in NOTE) distinguono un DR
  da un MOS.

Se il tipo letto è diverso da quello scelto: errore **«Modulo sbagliato»** (422) prima di
spendere qualcosa. Se la testata non si riconosce, non si blocca nulla.

### 5.4 Estrazione del ciclo (`extract/`)

A cascata (`extract/factory.py`, `extract/composite.py`):

1. **Parser PVRM320** (`extract/pvrm320_report.py`), zero token. Legge la testata (`CICLO :`,
   `DESCR.CICLO :`, `PROGETTO`, `RIPARAZIONE :`, `NOTE`), la tabella a asterischi
   (TARGA, NUM. OPER, DESCRIZIONE), le righe `SCHEDA :` e `SP.ORIG.`, il piè di pagina
   (`RIP: … OEM: …`, il manuale).
2. **Modello** (`extract/llm.py`), solo se il parser non riconosce il layout o non trova
   operazioni. Sessione senza tool, output con schema chiuso (`prompts/extract_cycle.md`,
   `extract_cycle_ej200.md`), ragionamento `high`, al massimo 300 secondi.

**Cosa fa il parser in più:**

- **righe in ordine di posizione:** le stampe modificate a mano hanno in fondo al PDF le righe
  toccate, a volte senza colonne TARGA e NUM. OPER: il parser le rimette al loro posto e le
  attacca all'operazione in corso;
- **operazioni su più pagine:** si uniscono per numero (`*** CONTINUAZIONE DALLA PAGINA
  PRECEDENTE ***`, banner `*** C O N T I N U A ***`). Dal 27-11 notte (MG77) una riga con la
  descrizione a sinistra e «CONTINUA ALLA PAGINA SEGUENTE» a destra tiene la descrizione: prima
  si buttava tutta la riga (298bc28e 035 perdeva proprio la riga cambiata);
- **«OPERAZIONE EVENTUALE»:** il titolo passa all'operazione dopo;
- **una fonte per ogni riparazione:** con la nota della testata delle sue pagine e il manuale
  del piè di pagina. Il task si cerca in tutta la nota (`TASK …`, `CIR <sezione>`,
  `BLENDING <task>`, anche la sola sezione);
- **SUBTASK** letti come task;
- nelle descrizioni si tolgono gli asterischi di cornice e le righe di soli segni;
- un blocco di testo senza numero che non continua nulla è un errore di estrazione (mai righe
  perse in silenzio).

**Dopo l'estrazione:** se il ciclo non ha operazioni, errore. Per un DR senza serial number, il
serial number si prende dalla stampa («APPLY ON S/N …», almeno 6 caratteri con una cifra); se
ce ne sono più d'uno vale quello che ha recommendation nei dati DR.

Il **ciclo estratto** (`domain/cycle.py`) ha: codice e descrizione del ciclo, modello del
motore, tipo di operazione, codice di riparazione, fonti (`manual`, `task`, `repair_code`,
`issue`, `section`), operazioni (`operation_number`, `operation_description`, `repair_code`,
`machine_tag`, `task_codes`, `process_sheet`, e dal 27-11 sera `original_task`, il task della
colonna SP.ORIG, e `other_machine_tags`, le altre targhe della stessa operazione), dati DR. I segnaposto come `-`, `N/A`, `nessuno`
valgono «assente».

### 5.5 Integrità (`extract/integrity.py`)

Ogni valore estratto deve comparire nel testo del PDF, **sulla riga della sua operazione**:

- targa, task code, scheda: se non compaiono, il controllo che li usa non è affidabile;
- descrizione: basta **un numero** che manca dal PDF, oppure più del **20%** delle parole;
- se più del 25% dei codici è fuori riga, il PDF non è impaginato per righe: non si giudica.

I valori non confermati si segnano. Per la descrizione non si chiama nemmeno il modello (il
giudizio verrebbe declassato). Gli altri esiti CORRETTO o ERRATO su valori non confermati
diventano WARNING `ESTRAZIONE_NON_CONFERMATA` al consolidamento.

### 5.6 Controlli

1. Prima i **controlli bloccanti** del profilo (solo DR: `dr_recommendation`).
2. Se uno fallisce (esito diverso da CORRETTO o N/A, tranne `DR_NON_VERIFICATA`), tutti gli
   altri escono WARNING `BLOCCATO_A_MONTE` e il ciclo è `bloccato`.
3. Altrimenti **insieme**: i controlli deterministici (in thread) e le sessioni del modello per
   le descrizioni. Se qualcosa fallisce, le sessioni ancora in corso si fermano (non spendono).

Il dettaglio di ogni controllo è nella sezione 6.

### 5.7 Consolidamento (`verdict/consolidate.py`)

Deterministico: applica l'integrità, conta gli esiti, dà lo stato del ciclo (sezione 8).

Poi le **regole finali** (`verdict/final_rules.py`, dal 28-11 per MG83): regole del codice che
lavorano sugli esiti già fatti del ciclo (per esempio un WARNING del modello su un'operazione
che il codice ha già deciso) e li cambiano. Si accendono per nome con `agent.final_rules`
(vuoto = nessuna; un nome sconosciuto ferma le impostazioni). Le righe della verifica di
integrità non si toccano. Siccome usano solo quello che c'è nel `report.json`, si provano sulle
prove già fatte, senza modello: `eval rigioca` (sezione 15.3).

Le regole (28-11; una variante ciascuna). Nella base dal 28-11: `fonte_assente_una_volta`.

| Nome | Miglioria | Cosa fa |
|---|---|---|
| `fonte_assente_una_volta` | MG83, variante `meno_avvisi` | la fonte assente si dice una volta sola: un WARNING `FONTE_ASSENTE` per ogni avviso diverso del ciclo, con l'elenco delle operazioni («Stesso avviso anche per le operazioni …»). Le altre righe diventano N/A `GIA_SEGNALATO` e dicono in quale operazione guardare. Si uniscono i `FONTE_ASSENTE` della stessa operazione (controlli diversi: la spiegazione dell'altro si aggiunge) e quelli dello stesso controllo con la stessa spiegazione |
| `limite_contro_citazione` | MG87, variante `limiti_citati` | un CORRETTO del modello sulla descrizione diventa ERRATO `LIMITE_CONTRO_CITAZIONE` se la riga del manuale che il modello cita dà lo stesso valore con il limite al contrario («al massimo» contro «almeno»). Il limite si legge prima del numero (come MG75) e anche dopo («0.5 MM MAX», «(0.25 MM) MAX»; «5 MIN» senza unità sono minuti). Conta solo un valore con un verso solo nella descrizione (le due lingue d'accordo) e uno solo nella riga citata |

### 5.8 Report (`report/`)

Tre file nella cartella del run (con la CLI `runs/ultimo`):

- `report.json`: tutto (metadati, ciclo, esiti, conteggi, tempi, consumi, guasti);
- `report.md`: da leggere (riepilogo, fonti, operazioni, dettaglio con le citazioni);
- `payload.json`: quello che riceve il frontend, nel formato della v1 (sezione 13.4).

`report.md` contiene testo dei manuali: **non si manda a Claude**.

---

## 6. I controlli, uno per uno

| Controllo | Su cosa | Chi decide | MOS | DR | EJ200 |
|---|---|---|---|---|---|
| `dr_recommendation` | il ciclo | codice | — | sì, **bloccante** | — |
| `source` | ogni fonte | codice | sì | sì | sì |
| `task_code` | ogni operazione | codice | sì | sì | sì (nel testo) |
| `machine_tag` | ogni operazione | codice | sì | sì | sì |
| `process_sheet` | ogni operazione | codice | sì | sì | N/A |
| `operation_description` | ogni operazione | codice + modello | sì | sì | sì |

Ogni controllo che legge una sorgente esterna passa da `guarded` (`checks/base.py`): se la
sorgente non risponde, l'esito è WARNING `ERRORE_TECNICO`.

### 6.1 `source`: le fonti esistono (`checks/source.py`)

1. Si cerca il documento (`resolve/civil.py`, `resolve_document`):
   - nessun documento: WARNING `FONTE_ASSENTE`. Una procedura DR citata come
     `D.R. CASE #00000000` si cerca anche con il solo numero;
   - il nome corrisponde a più pubblicazioni diverse: WARNING `RIFERIMENTO_AMBIGUO`;
   - nessuno pubblicato: `FONTE_ASSENTE`;
   - si sceglie il pubblicato più recente; se è solo in parte: WARNING
     `PUBBLICAZIONE_PARZIALE`;
   - issue citata diversa da quella disponibile: WARNING `VERSIONE_DIVERSA`;
   - dato incerto nell'indice: WARNING `DATO_INCERTO`.
2. **Profili a task** (MOS, DR) con task citato: il task deve essere nel manuale. Se la fonte
   cita solo la sezione (`CIR 72-00-01`), basta che la sezione ci sia. Task mancante: WARNING
   `FONTE_ASSENTE`.
3. **Profilo a documento** (EJ200): basta il documento. Se esiste una issue più recente di
   quella citata: WARNING `VERSIONE_DIVERSA` (il confronto si fa sulla issue citata).

### 6.2 `task_code`: i task citati esistono (`checks/task_code.py`)

- **Prima di tutto, MOS e DR (H17, dal 27-11 sera):** il task scritto nella colonna SP.ORIG
  accanto all'operazione (`Operation.original_task`, letto dal parser anche quando la colonna
  finisce in fondo a una riga di testo) si confronta con il task della testata della stessa
  riparazione. Se è della **stessa famiglia** (stesse prime quattro parti, per esempio
  `70-11-00-350`) ma **diverso**: ERRATO `TASK_DIVERSO_DALLA_TESTATA`, la stampa si
  contraddice. Un task di un'altra famiglia (attacco chimico, liquidi penetranti, pulizia) è un
  altro processo e non si confronta; senza task in testata non si confronta. Nasce dalla v1
  sugli stessi cicli: il task cambiato di una cifra esiste nel manuale, quindi
  `TASK_INESISTENTE` non lo vedeva.
- **Task di un altro stadio (MG48, dal 28-11, solo con `agent.task_stage_check`, spento nella
  base, variante `altro_stadio`):** lo stadio del ciclo viene dal titolo («... STAGE 7»,
  «STADIO 7»; uno solo, altrimenti non si controlla), quelli del task dalle prime 6 righe del
  task nel manuale («STAGE 6 ... INSPECTION», «STAGES 6 AND 7», «STAGES 1 THRU 7»). Se il task
  dice solo stadi diversi da quello del ciclo: ERRATO `TASK_ALTRO_STADIO`, con la riga del
  manuale come prova. Un'intestazione di un altro modulo (HPT in un ciclo LPT) è un altro pezzo
  e non si confronta. È il controllo che la v1 fa con il modello e la v2 non faceva.
- Nessun task: N/A `CAMPO_ASSENTE`.
- **MOS e DR:** ogni task si cerca nei manuali delle fonti collegate all'operazione (stesso
  repair code; se nessuna, tutte le fonti). I task del **capitolo 70** si cercano **prima
  nell'SPM**.
  - tutti trovati: CORRETTO;
  - un codice completo che **non compare da nessuna parte** nei documenti dove dovrebbe stare,
    mentre lì ci sono task della **stessa famiglia**: ERRATO `TASK_INESISTENTE` (il codice è
    quasi certamente sbagliato; il messaggio elenca i fratelli trovati);
  - altrimenti mancante: WARNING `FONTE_ASSENTE` (il documento può mancare).
- **EJ200:** ogni codice deve comparire per intero nel testo delle pubblicazioni citate
  (`72-31-0` dentro `72-31-00` non vale). Mancante: WARNING `EVIDENZA_NON_TROVATA`.

**Come si trova un task** (`kb/task_text.py`, se l'indice non lo ha):

- una riga apre il task se, tolti spazi, `#`, grassetto e un `TASK` o `CIR` davanti,
  **comincia** con il codice. Dopo la sezione può esserci una virgola
  (`CIR 72-00-01, REPAIR 002`);
- nei documenti SPM basta la sezione (`70-00-01 Pulizia`);
- il task finisce alla riga prima del titolo di un altro task, o a fine documento; se si apre
  in più punti si tiene il blocco più lungo; le righe di sommario non contano;
- un SUBTASK si cerca con la riga che comincia con `SUBTASK <codice>`, fino al prossimo
  SUBTASK o task.

### 6.3 `machine_tag`: la macchina esiste ed è attiva (`checks/machine_tag.py`)

Due elenchi: le **macchine attive** (la fonte che vale, sezione 11) e i **dati TM**. Le targhe
si confrontano senza spazi né maiuscole (`A 0100` = `A0100`).

| Nei dati TM | Tra le attive | Esito |
|---|---|---|
| sì | sì | CORRETTO (WARNING `DATO_INCERTO` se l'indice la segna incerta) |
| sì | no | **ERRATO** `MACCHINA_NON_ATTIVA` |
| no | sì | WARNING `FONTE_ASSENTE` |
| no | no | WARNING `TARGA_SCONOSCIUTA` |

**Prima di tutto (H19, dal 27-11 sera), anche con il registro spento:** se la stessa
operazione ha **targhe diverse su pagine diverse** (il parser le tiene in
`Operation.other_machine_tags`; la stessa targa ripetuta non conta): ERRATO
`MACCHINE_DIVERSE`, la stampa si contraddice.

Nessuna targa: N/A. Elenco delle attive non raggiungibile: WARNING `ERRORE_TECNICO` (mai
ERRATO). La targa è la riga sopra nella colonna TARGA; la riga sotto (centro responsabile) non
si controlla.

### 6.4 `process_sheet`: la scheda esiste (`checks/process_sheet.py`)

- Nessuna scheda: N/A `CAMPO_ASSENTE`. Ma se la descrizione è di un **processo speciale**
  (lubrificante secco, rivestimento, attacco chimico, liquidi penetranti, FPI, in italiano o in
  inglese: `special_process`) è WARNING `SCHEDA_FORSE_MANCANTE` («Scheda mancante: …»), mai
  ERRATO (`agent.special_process_sheet`, accesa nella base dal 27-11; regola P6, MIGLIORIE MG31;
  confermata dall'utente il 27-11 sera: un avviso con il commento «scheda mancante»).
- EJ200: N/A `NON_VERIFICATO_PER_PROFILO`.
- Prefissi esclusi (`SWJ`, `SSS`, `SPS`): N/A `ESCLUSO_DA_REGOLA`.
- I codici si confrontano senza spazi, trattini né maiuscole (`CPEC 100-BR` = `CPEC100BR`).
  `PG 300` è un codice a sé.
- Non trovata: WARNING `FONTE_ASSENTE` (ERRATO se l'indice ha schede con le stesse lettere: H18).
- Trovata ma non per la famiglia del motore (GENX, LEAP): ERRATO `SCHEDA_ALTRO_MOTORE` (H18;
  con H18 spenta WARNING `EVIDENZA_NON_TROVATA`).
- Trovata: CORRETTO. Se la scheda non elenca famiglie o la famiglia non si riconosce, il testo
  dice «applicabilità non verificata».

**La scheda coerente con l'operazione (H18, `agent.sheet_consistency`, accesa nella base dal 27-11 notte;
variante `schede_e_limiti`, 27-11 sera).** Tutto deciso dal codice, senza modello. Nelle stampe
con errori messi a mano la v1 trova le schede cambiate (un'altra lega, un altro motore, una
cifra del task); nelle stampe giuste dello stesso pezzo la coppia scheda e task è sempre la
stessa. Con l'impostazione accesa, in quest'ordine:

1. il task scritto accanto alla scheda (colonna SP.ORIG) non c'è nei manuali collegati (per il
   capitolo 70 anche l'SPM), che hanno però task della stessa famiglia: ERRATO
   `TASK_INESISTENTE`;
2. la scheda non c'è nell'indice, che ha altre schede con le stesse lettere iniziali (per
   esempio `ZZ101-AA` tra `ZZ100-AA` e `ZZ105-AA`): ERRATO `SCHEDA_INESISTENTE`. Con un prefisso
   che l'indice non conosce resta WARNING `FONTE_ASSENTE`;
3. la scheda è di un'altra famiglia di motore: ERRATO `SCHEDA_ALTRO_MOTORE` (spenta: WARNING
   `EVIDENZA_NON_TROVATA`);
4. il materiale scritto nella descrizione dopo «materiale base:» o «base material:» (gamma
   TiAl, titanio, nichel, cobalto, alluminio, acciaio) non ha niente in comune con quello del
   trattamento della scheda: ERRATO `SCHEDA_MATERIALE_DIVERSO`. Gamma TiAl e titanio vanno
   d'accordo. Se uno dei due non dice il materiale, non si giudica.

Le voci incerte dell'indice (`DATO_INCERTO`) non danno mai questi ERRATO.

### 6.5 `operation_description`: la descrizione è d'accordo con il manuale (`checks/operation.py`)

È **l'unico controllo che usa il modello**. Per ogni operazione, in ordine:

1. descrizione vuota: N/A `CAMPO_ASSENTE`;
2. descrizione non confermata dal PDF: WARNING `ESTRAZIONE_NON_CONFERMATA` (niente modello);
3. **le due lingue** (`checks/languages.py`, senza modello): se nello stesso punto l'italiano e
   l'inglese hanno **numeri diversi**: ERRATO `INCOERENZA_LINGUE`. Si conta solo una
   sostituzione (un numero al posto di un altro). Non contano: un numero in una sola lingua,
   le conversioni mm ↔ pollici (2%) e °C ↔ °F (±1). Una conversione scritta in una sola lingua
   («0.38 MM (0.015 IN)», «248 °F (120 °C)») non sposta l'allineamento: di due numeri vicini
   che sono uno la conversione dell'altro resta quello che c'è anche nell'altra lingua (26-11;
   dal 26-11 sera anche con la conversione scritta prima). **Dal 27-11 sera** si confrontano
   anche le descrizioni divise in più di due parti da righe di asterischi dentro il testo
   (`language_blocks`): le parti vicine della stessa lingua si uniscono (la lingua si
   riconosce da parole brevi e frequenti) e il confronto si fa se resta italiano e poi
   inglese. Prima la 010 delle stampe di raccordatura (quattro parti) non si confrontava e i
   limiti cambiati in una lingua sola non si vedevano. Dal 26-11 sera vale anche:
   - due lingue con tanti numeri quanti, uguali tranne uno («50, 25» contro «25, 25»), anche se
     l'allineamento vede un numero tolto e uno aggiunto;
   - i **codici** fatti di cifre (con `/`, o di 5 cifre o più, come i part number) si
     confrontano a parte, come elenco, perché le lingue li scrivono in punti diversi: un codice
     solo in una lingua al posto di uno solo nell'altra è un codice cambiato. Un codice in più
     in una lingua sola non conta.

   Il 26-11 le copie cieche «numero in una lingua» si trovavano 1 su 5: erano su codici e su
   conversioni scritte prima del numero. Un test prova che ogni copia di questo tipo si trova.
   **Dal 27-11 notte:**
   - **rimandi** (MG78): il numero dopo «operazione», «op.», «step», «figura», «pagina»,
     «tabella», «sezione» è un rimando, non un valore. I rimandi si confrontano solo con quelli
     dello stesso tipo dell'altra lingua, e solo se ci sono in tutte e due. Prima «nella
     operazione 70 successiva» contro «refer to figure 903» era un numero cambiato (falso
     errore di 8d3c673c 060 e b1261d11 060, P13);
   - **limiti al contrario** (MG75, `agent.languages_from_code`): lo stesso numero con un limite
     di verso opposto nella stessa frase («superiore a 4X» contro «not to exceed 4X»). Contano
     solo le parole prima del numero; «non inferiore», «no less than» sono un minimo; i numeri
     di un elenco («5)») no. ERRATO `INCOERENZA_LINGUE`;
   - **azione diversa** (MG47, stessa impostazione): rimuovere, raccordare, sostituire,
     lucidare, sabbiare, saldare, pulire. ERRATO solo se ogni lingua ha un'azione che l'altra non
     ha («rimosso» contro «blended»): un'azione in più in una lingua sola non basta.
     Un'azione dopo «durante», «dopo», «prima di» (during, after, before) è una condizione e
     non conta («se danneggiate durante la sabbiatura»); «ripristinare» vale «sostituire»
     («replace the masks»). Così i 4 falsi errori della P15;
   - **massimo contro minimo** (MG81, stessa impostazione): una lingua dice «massimo» (massimo,
     max, maximum) e l'altra «minimo» (minimo, min, minimum), anche senza un numero
     («profondità massima dei difetti» contro «min depth of defects»). Conta solo se ogni lingua
     ha una parola sola delle due; «5 MIN» sono minuti. ERRATO `INCOERENZA_LINGUE`;
   - **numeri e limiti, dettagli** (banco di prova, 27-11 notte): una data («D.T. 01-02-25»,
     spesso in una lingua sola) è un codice, non tre valori; lo stesso numero con un limite
     più volte («massimo 2 … massimo 2») si confronta contando quanti limiti per verso ci sono
     in ogni lingua (l'ordine può cambiare). Limiti noti: un numero scritto due volte per
     sbaglio in una lingua, o un numero in più in una lingua sola, disallineano le lingue e un
     numero cambiato vicino può sfuggire (2 copie su 40 nel banco);
   - **lo stesso DR** (MG76, `agent.dr_consistency`): ogni «D.R. CASE #…» citato deve essere il
     DR del ciclo, quello delle recommendation del serial number (`reference`, P14) o, senza,
     il primo citato nella stampa. Un altro: ERRATO `DR_DIVERSO`.

   Sul testo delle 14 stampe della v1 (`tests/test_real_prints.py`) queste regole trovano 7
   errori in più e nessun ERRATO fuori dagli errori noti. Sul PC, senza modello (27-11 notte):
   0 falsi errori; i 4 ERRATO da verificare nei cicli veri del grande erano falsi errori di
   MG47 (P15), corretti;
4. si cercano i **testi di riferimento** (`context_locations`, sotto); se la sorgente non
   risponde: WARNING `ERRORE_TECNICO`;
5. task citati che il manuale non ha: WARNING `FONTE_ASSENTE` subito, senza modello
   (`skip_missing_task`, acceso);
6. nessun testo trovato: WARNING `FONTE_ASSENTE`;
7. altrimenti una **sessione del modello** (sezione 9).

**Quali testi si danno al modello** (`resolve/civil.py`, `context_locations`), in ordine:

1. i task dell'operazione trovati;
2. se nessuno: i task delle fonti collegate. Una fonte che cita solo la sezione porta tutti i
   task di quella sezione in tutti i documenti del manuale. Una fonte senza task può essere un
   documento tutto intero (LEAP): si prova il codice del documento;
3. per i DR: i task delle recommendation applicabili;
4. se ancora nulla: la procedura DR intera (documenti di tipo `DR_PROC`);
5. se ancora nulla e l'operazione non cita task: i task delle **altre operazioni della stessa
   riparazione**, al massimo 4.

EJ200: i documenti citati interi, in ordine RDR, EF, RN.

**Dal giudizio all'esito** (`decide_operation`):

| Il modello dice | Citazioni ritrovate | Esito |
|---|---|---|
| `non_verificabile` | — | WARNING `EVIDENZA_NON_TROVATA` |
| `fuori_tema` (solo con `agent.out_of_scope`, I16) | — | N/A `FUORI_TEMA` («Niente da confrontare: …»); senza l'impostazione vale come `non_verificabile` |
| `coerente` o `contraddetto` | nessuna | WARNING `CITAZIONE_NON_VERIFICATA` |
| `contraddetto` | almeno una | ERRATO `CONTRADDIZIONE` (da confermare, sotto) |
| `coerente` | almeno una | CORRETTO `VERIFICATO` |
| sessione finita senza risposta (passi esauriti) | — | WARNING `BUDGET_ESAURITO` |
| errore, tempo scaduto, output storto | — | WARNING `ERRORE_TECNICO` |

**Seconda ricerca (`agent.search_when_unverifiable`, spenta nella base; variante
`seconda_ricerca`, 25-11).** Un `non_verificabile` (WARNING `EVIDENZA_NON_TROVATA`) si rifà con
una sessione `-ricerca` che ha Grep e Read su **tutti i documenti citati dal ciclo**, interi
(più quelli del task e, per DR, quelli del profilo), con una nota che dice che il testo del task
non bastava (`checks/operation.py`, `wider_job`; `agent/prompt.py`, `SECOND_SEARCH_NOTE`). Non si
fa se i documenti sono gli stessi e la prima sessione aveva già i tool. Se la seconda dà
CORRETTO o ERRATO con citazione verificata, prende il posto del WARNING e la sua sessione
diventa quella dell'operazione (la conferma G1 si rifà su questa); se no resta il WARNING. Il
costo delle due sessioni si somma.

**Definizioni generali (`agent.general_definitions_note`, spenta nella base; variante
`definizioni_generali`, 26-11).** Alla domanda si aggiunge una nota (`agent/prompt.py`,
`GENERAL_DEFINITIONS_NOTE`): le regole scritte per tutti i casi da un manuale di pratiche
standard valgono solo dove non ci sono limiti specifici, perché il ciclo può prendere i criteri
dal manuale d'ispezione del motore o da una D.R. Se l'unica differenza è con una di queste
definizioni, il modello risponde `non_verificabile` (WARNING `EVIDENZA_NON_TROVATA`). Nasce dal
«4 volte» del ciclo contro il «3 volte» generico dell'SPM (P7, e il ciclo vero 2d724fba).

**Procedura della D.R. insieme ai task (`agent.dr_procedure_always`, accesa nella base dal
27-11; variante `procedura_dr`, 26-11 sera).** Nei cicli DR la procedura della D.R. (documenti
`DR_PROC` delle recommendation applicabili, interi) si aggiunge ai testi trovati, non solo quando
non se ne trova nessuno (`_locations` in `checks/operation.py`). Alla domanda si aggiunge una nota
(`DR_PROCEDURE_NOTE`): la D.R. è una deroga e per quel pezzo vale più del manuale; se il manuale
vieta o manda a sostituire qualcosa che la D.R. autorizza, non è una contraddizione. Nasce da
895167b9 005 (Copilot, 26-11 sera): il manuale manda a sostituire il pezzo, la deroga citata
nella stessa operazione autorizza la raccordatura, ma il modello non l'aveva.

**Sezione d'ispezione del manuale del motore (`agent.inspection_source`, accesa nella base
dal 27-11 sera; variante `fonte_ispezione`, 27-11; I8).** Nelle operazioni d'ispezione e di controllo
(`is_inspection`: ispezione, controllo visivo o dimensionale, liquidi penetranti, FPI,
magnetoscopia, inspect…) che hanno già un testo di riferimento, si aggiunge la sezione
d'ispezione del manuale del motore: per ogni fonte del ciclo che cita una sezione fuori dal
capitolo 70 (`72-00-01 REPAIR 001`), il task `72-00-01 INSPECTION 001` (fino a 003) nello stesso
manuale (`resolve/civil.inspection_locations`, con la ricerca nel testo se l'indice non ha quel
titolo); in più i **task d'ispezione con il codice completo** (terzo gruppo 2xx, per esempio
`72-00-01-200-801`, fuori dal capitolo 70: `is_inspection_task`) citati dalle fonti o da una
qualsiasi operazione del ciclo, cercati nei manuali delle fonti. Questa seconda forma è quella
delle stampe MOS (prove dal frontend del 27-11): la prima operazione cita il task SPM della
raccordatura e il task d'ispezione delle pale, l'ispezione con liquidi penetranti cita solo il
task SPM. Alla domanda si aggiunge una nota (`INSPECTION_NOTE`): per i criteri d'ispezione vale
la sezione del motore, non le definizioni generali di un manuale di pratiche standard. Nasce da
P7 e P8: la stampa giusta 04ecaabe op. 050 e il ciclo vero 2d724fba op. 050 dicono «4 volte»
come il manuale del motore, la v2 confrontava solo con il «3 volte» generico dell'SPM.

**Le due lingue tra loro (`agent.compare_languages`, accesa nella base dal 27-11 sera solo con
la versione stretta; variante `lingue_tra_loro`, 26-11 sera; la versione larga è scartata il
27-11 per i falsi errori).** Per ogni operazione scritta in due lingue (tranne quelle già
ERRATO `INCOERENZA_LINGUE` per i numeri, senza descrizione o non confermate) una sessione corta
chiede al modello se le due lingue danno le stesse istruzioni, **senza manuale**
(`plan_language_checks`; prompt in `agent/prompt.py`, `build_languages_prompt`). Risponde
`diverse` solo per una negazione o un divieto in una lingua sola, un limite al contrario, un
materiale, pezzo, attrezzo o lavorazione diversi, un valore o un codice diversi; non per
traduzioni libere, sinonimi, unità convertite o note in una lingua sola. Con `diverse` deve
copiare le parole che non coincidono: il codice le cerca, ognuna nella sua lingua
(`decide_languages`). Ritrovate, si conferma come gli ERRATO (G1, sotto): se tutte le conferme
dicono `diverse`, l'operazione è ERRATO `INCOERENZA_LINGUE` al posto dell'esito del confronto con
il manuale, con le due citazioni dal ciclo come prova. Vale anche dove il manuale manca
(`FONTE_ASSENTE`). Le sessioni delle lingue girano insieme alle altre; il loro costo va
sull'operazione.

**Versione stretta (`agent.compare_languages_strict`, con `compare_languages`; variante
`finale`, 27-11; I15; accesa nella base dal 27-11 sera).** La domanda chiede solo due tipi di differenza
(`build_strict_languages_prompt`): `negazione` (un divieto o un «non» in una lingua sola) e
`limite` (minimo e massimo, «almeno» e «al massimo», «superiore a» e «not to exceed»). Tutto il
resto non va segnalato: traduzioni libere, titoli, sinonimi, nomi generici e specifici, codici
con o senza lettere, numeri (li controlla già il codice). Lo schema ha in più `kind`
(`negazione`, `limite`, `nessuna`). Il codice accetta il giudizio solo se ritrova la differenza
nelle parole copiate (`checks/languages.strict_difference`): per `negazione`, una parola di
negazione in una citazione sì e nell'altra no (`no.` come abbreviazione di numero non conta);
per `limite`, un limite in tutte e due con verso opposto (`limit_direction`: «non oltre» e «not
to exceed» valgono «al massimo»; un intervallo con minimo e massimo non ha verso). Poi la
conferma G1 come sopra. Nasce dalla campagna del 26-27-11: `lingue_tra_loro` trovava circa 10
errori in più ma prendeva per errore le traduzioni libere (11-13 falsi errori a prova).

**«Fuori tema» (`agent.out_of_scope`, accesa nella base dal 27-11 sera; dentro la variante
`finale`, 27-11; I16).** Lo schema della risposta ammette `fuori_tema` e la domanda ha una nota
(`OUT_OF_SCOPE_NOTE`): se il testo di riferimento non tratta affatto il tipo di operazione (presa
in carico, movimentazione, versamento, preservazione, documenti, mentre il testo parla di una
lavorazione), il modello risponde `fuori_tema` e l'esito è N/A `FUORI_TEMA` con la spiegazione;
`non_verificabile` resta per un testo che parla della stessa lavorazione ma non basta. Mai
`fuori_tema` se il testo dice qualcosa di incompatibile. Nel frontend un N/A con il testo esce
come bollino azzurro «Info». Nasce dalle prove dal frontend del 27-11: 6 operazioni su 9 WARNING
«il testo non ne parla», dove la v1 dice OK senza aver controllato niente. **Dal 27-11 notte**
(MG45, `agent.prudent_out_of_scope`): se la descrizione ha una negazione, un divieto o un
limite, `fuori_tema` non vale: WARNING `EVIDENZA_NON_TROVATA` e una seconda ricerca in tutti i
documenti del ciclo, solo per queste operazioni (una negazione tolta in tutte e due le lingue
finiva N/A).

**Conferma degli ERRATO (regola G1).** Ogni `CONTRADDIZIONE` si rifà con
`confirm_contradiction` sessioni uguali (2). Resta ERRATO solo se **tutte** ritrovano la
contraddizione. Se una la smentisce: WARNING `GIUDIZIO_INSTABILE` («contraddizione ritrovata in
N verifiche su 3»). Se una non si è potuta fare e nessuna smentisce: WARNING `ERRORE_TECNICO`.
Costa solo sugli ERRATO.

**Fatti già risolti dal codice** (dati al modello, da non cercare): le sezioni citate dalle
fonti, la funzione della macchina, il trattamento della scheda per la famiglia del motore.

### 6.6 `dr_recommendation`: la DR permette la riparazione (`checks/dr_recommendation.py`)

Solo per i DR. **Bloccante.** Regole della v1, confermate dall'utente il 22-11-2026.

| Situazione | Esito | Gli altri controlli |
|---|---|---|
| nessun serial number (né dato né nella stampa) | WARNING `DR_NON_VERIFICATA` | vanno avanti; la procedura DR si cerca con il numero «D.R. CASE #…» scritto nella stampa (MG50, 27-11 notte) |
| nessuna recommendation per il serial number | ERRATO `DR_NESSUNA_CORRISPONDENZA` | fermi |
| più recommendation e una senza condition | WARNING `RIFERIMENTO_AMBIGUO` | fermi (è un fallimento bloccante) |
| una sola recommendation | vale per qualunque condition | |
| condition data, nessuna recommendation con quella condition | ERRATO `DR_NESSUNA_CORRISPONDENZA` | fermi |
| `Repair` | CORRETTO | vanno avanti, con i task e la procedura DR come riferimento |
| `Reject` (il pezzo si scarta) | ERRATO `DR_NON_APPLICABILE` | fermi |
| `Accept as is` / `Use as is` (va bene così) | ERRATO `DR_NON_APPLICABILE` | fermi |
| `Repair` e `Accept as is` insieme (condition diverse) | CORRETTO, la parte `Accept as is` si salta | vanno avanti con la sola `Repair` |
| condition non data, più recommendation tutte `Repair` | CORRETTO | valgono tutte |
| condition non data, recommendation diverse | WARNING `DR_NON_VERIFICATA` | vanno avanti con le sole `Repair` |
| condition non data, nessuna `Repair` | ERRATO `DR_NON_APPLICABILE` | fermi |

Le parole si riconoscono senza maiuscole, trattini e punto finale (`Accept-as-is` =
`accept as is`). Le condition si accettano come `1`, `"1,2"`, `"[1,2]"` o una lista.

---

## 7. Esiti e motivi

Ogni motivo ha un solo esito (`domain/check.py`).

| Esito | Motivo | Quando |
|---|---|---|
| **CORRETTO** | `VERIFICATO` | tutto verificato, con una prova |
| **ERRATO** | `CONTRADDIZIONE` | il manuale dice altro (confermata da tutte le verifiche) |
| | `MACCHINA_NON_ATTIVA` | targa nei dati TM ma non tra le attive |
| | `DR_NON_APPLICABILE` | la DR dice `Reject` o `Accept as is` |
| | `DR_NESSUNA_CORRISPONDENZA` | nessuna recommendation per serial number e condition |
| | `TASK_INESISTENTE` | codice completo che non c'è, mentre ci sono i suoi fratelli |
| | `INCOERENZA_LINGUE` | italiano e inglese con numeri o codici diversi, un limite al contrario, «massimo» contro «minimo» o un'azione diversa (dal codice); con `agent.compare_languages` anche negazioni e limiti visti dal modello |
| | `TASK_DIVERSO_DALLA_TESTATA` | il task accanto all'operazione è della stessa famiglia di quello della testata, ma diverso (H17, 27-11 sera) |
| | `MACCHINE_DIVERSE` | la stessa operazione ha targhe diverse su pagine diverse (H19, 27-11 sera) |
| | `DR_DIVERSO` | l'operazione cita un DR diverso da quello del ciclo (MG76, 27-11 notte) |
| | `TASK_ALTRO_STADIO` | il task citato è di un altro stadio del motore (MG48, con `agent.task_stage_check`) |
| | `LIMITE_CONTRO_CITAZIONE` | la riga del manuale citata dal modello dà lo stesso valore con il limite al contrario (MG87, regola finale `limite_contro_citazione`, sezione 5.7) |
| | `SCHEDA_ALTRO_MOTORE` | la scheda è di un'altra famiglia di motore (H18, con `agent.sheet_consistency`) |
| | `SCHEDA_MATERIALE_DIVERSO` | il materiale della scheda non è quello della descrizione (H18) |
| | `SCHEDA_INESISTENTE` | la scheda non è nell'indice, che ha altre schede con lo stesso prefisso (H18) |
| **WARNING** | `FONTE_ASSENTE` | documento, task, targa o scheda non nella conoscenza |
| | `TARGA_SCONOSCIUTA` | targa né nei dati TM né tra le attive |
| | `EVIDENZA_NON_TROVATA` | il testo non basta per decidere |
| | `VERSIONE_DIVERSA` | issue citata diversa da quella disponibile |
| | `PUBBLICAZIONE_PARZIALE` | documento disponibile solo in parte |
| | `DATO_INCERTO` | l'indice segna la voce come incerta |
| | `RIFERIMENTO_AMBIGUO` | il nome corrisponde a più pubblicazioni, o DR senza condition |
| | `CITAZIONE_NON_VERIFICATA` | la citazione del modello non è nel file |
| | `GIUDIZIO_INSTABILE` | una verifica di conferma smentisce la contraddizione |
| | `DR_NON_VERIFICATA` | mancano serial number o condition per scegliere |
| | `SCHEDA_FORSE_MANCANTE` | processo speciale senza scheda di processo: «Scheda mancante» (regola P6) |
| | `ESTRAZIONE_NON_CONFERMATA` | il valore letto non compare nel PDF |
| | `BUDGET_ESAURITO` | la sessione ha finito i passi |
| | `ERRORE_TECNICO` | guasto: modello, rete, sorgente, tempo |
| | `BLOCCATO_A_MONTE` | non eseguito: il controllo DR ha fermato il ciclo |
| **N/A** | `CAMPO_ASSENTE` | il campo non c'è |
| | `ESCLUSO_DA_REGOLA` | escluso da una regola (prefissi delle schede) |
| | `NON_VERIFICATO_PER_PROFILO` | il controllo non vale per questo tipo di ciclo |
| | `CONTROLLO_SPENTO` | controllo spento per configurazione: registro delle macchine non collegato (`MACHINES_SOURCE=nessuna`, sul PC), dal 27-11 |
| | `FUORI_TEMA` | il testo di riferimento non tratta il tipo di operazione: niente da confrontare (I16, con `agent.out_of_scope`) |
| | `GIA_SEGNALATO` | la stessa fonte assente è già in un altro avviso del ciclo, che elenca le operazioni (MG83, regola finale `fonte_assente_una_volta`, sezione 5.7) |

**Due tipi di WARNING (H15, dal 27-11 sera; `warning_kind` in `domain/check.py`).** L'esito
resta WARNING, cambia come si mostra:

- **non controllabile**: il programma non ha potuto controllare (`FONTE_ASSENTE`,
  `EVIDENZA_NON_TROVATA`, `PUBBLICAZIONE_PARZIALE`, `DR_NON_VERIFICATA`, `BUDGET_ESAURITO`,
  `ERRORE_TECNICO`). Di solito manca un documento nella conoscenza;
- **da guardare**: tutti gli altri WARNING, un dubbio vero che una persona deve guardare
  (citazione non ritrovata, giudizio instabile, scheda mancante, dato incerto, targa scritta
  in un altro modo, issue diversa).

---

## 8. Stato del ciclo, conteggi, report

**Stato** (`cycle_status`):

- `bloccato`: un controllo bloccante è fallito;
- `parziale`: c'è un guasto (`ERRORE_TECNICO`, `BUDGET_ESAURITO` o un errore della pipeline).
  Sul PC è quasi sempre così, perché le macchine attive non si raggiungono;
- `completo`: altrimenti.

**Conteggi:** totale, corretti, warning (divisi in `warning_da_guardare` e
`warning_non_controllabili`, H15), errati, N/A, e quota di errori (errati / righe non N/A). Le
righe di integrità non si contano. Nel `report.md` la cella di un WARNING non controllabile
dice `NON CONTROLLABILE`.

**Metadati del run** (`RunMeta`): id del run, data, nome e SHA-256 del PDF, profilo,
selettori DR, versione della conoscenza, modello, impronta dei prompt (`prompt_version`),
versione della v2. Servono a confrontare run diversi.

**Tempi** (`timings_ms`): `ingest`, `extract`, `checks`, `total`. **Consumi** (`usage`):
token di input e output, token letti e scritti nella cache, costo stimato in dollari, tempo
del modello e tempo reale, passi, sessioni. **Modi delle sessioni** (`session_modes`): quante
in linea, con ricerca, di conferma.

---

## 9. Il modello e l'agente

**Dove:** Claude su **Amazon Bedrock** (regione `eu-south-1`), modello Haiku (id del profilo di
inferenza `eu.` scritto in `data/settings.yaml` sul PC). Dal 28-11 la base chiama il modello
**direttamente** (`agent/direct_session.py`, sotto); il **Claude Agent SDK** resta come
seconda strada (`agent.session_backend: sdk`): l'unico modulo che lo importa è
`agent/sdk_session.py`. Il resto del codice parla con la porta
`AgentSession` (`agent/session.py`) e si prova senza rete.

**Due modi di chiamare il modello (`agent.session_backend`, MG54, dal 28-11):**

- `sdk` (la base fino al 28-11): il Claude Agent SDK avvia Claude Code per ogni sessione (circa 3-5 s di
  avvio ciascuna); il costo lo dà l'SDK.
- `diretta` (la base dal 28-11, campagna 4j: stessi errori, costo -37%, tempo -55%): l'SDK `anthropic` (`AsyncAnthropicBedrock`, la stessa
  chiamata `InvokeModel` di Bedrock con le credenziali dell'ambiente) chiama il modello da
  `agent/direct_session.py`, senza avviare niente. Read e Grep li esegue la v2, con le stesse
  regole dell'hook (`agent/hooks.check_tool_call`: solo i file ammessi, lettura a paragrafo).
  La risposta arriva con lo strumento `StructuredOutput` (lo schema della domanda), come fa
  Claude Code. Il costo si calcola dai token con i prezzi in `agent.direct_input_price` e
  `agent.direct_output_price` (listino di Haiku 5.5; la scrittura in cache costa 1,25 volte
  l'ingresso, la lettura 0,1 volte). Id del modello: `agent.direct_model`, vuoto = `agent.model`
  (sul PC è già l'id completo `eu.`). Nessun nuovo tentativo dentro l'SDK: li fa già
  `agent/runner.py`. Provare l'accesso: `eval chiamata-diretta` (una domanda finta, meno di un
  centesimo).
- Il trasporto (`agent.direct_transport`, dal 28-11): `boto3` (predefinito) manda lo stesso
  corpo con `invoke_model` di `bedrock-runtime`, con la rete di boto3 (proxy, `AWS_CA_BUNDLE`,
  credenziali) che sul PC funziona già per S3; un solo client per processo, nessun nuovo
  tentativo dentro boto3. `httpx` usa il client `AsyncAnthropicBedrock` dell'SDK, con il
  certificato di `AWS_CA_BUNDLE` (o `SSL_CERT_FILE`, `REQUESTS_CA_BUNDLE`) se c'è. Il 28-11 sul
  PC il client HTTP dell'SDK ha dato `APIConnectionError`.
- Un errore della sessione diretta dice i tipi della catena delle cause, il codice di AWS e una
  causa probabile (`describe_error`: certificato, accesso scaduto, tempo scaduto, proxy...),
  mai il messaggio (può contenere indirizzi, account o testo del ciclo).
- Con `diretta`: `agent.direct_cache` (MG56; nella base dal 28-11 insieme a `diretta`, perché la
  cache non cambia le risposte, solo il prezzo) mette i punti di cache di
  Bedrock su istruzioni, strumenti e storia della sessione (dal secondo turno la storia si
  rilegge dalla cache); `agent.shared_reference_first` (MG59, variante `testo_comune`, spento:
  nella campagna 4j non ha fatto risparmiare niente rispetto a `diretta`) manda il
  testo del manuale delle sessioni in linea in un blocco a sé prima della domanda, con un punto
  di cache (`SessionRequest.shared_context`): le operazioni che citano lo stesso task lo pagano
  una volta. Con `sdk` il blocco va semplicemente davanti alla domanda.
- `agent.language_batch_size` (MG55, variante `lingue_insieme`; 8 nella base dal 28-11: stessi
  errori, costo -43% sul piccolo e -48% sul grande contro `quasi_finale`): il confronto tra le due lingue
  di più operazioni (al massimo quel numero) in una sessione sola, con un elemento per
  operazione nella risposta. Le citazioni si ritrovano comunque nella lingua giusta di ogni
  operazione, e una differenza si conferma con le sessioni di una sola operazione; un'operazione
  che manca o compare due volte nella risposta resta senza giudizio delle lingue. 0 = spento.

**Ogni sessione è isolata:**

- nessuna impostazione dell'utente, nessun server MCP (`setting_sources=[]`,
  `strict_mcp_config`);
- solo i tool **Read** e **Grep**, e solo sui file ammessi per quella sessione; nelle sessioni
  in linea nessun tool;
- permessi `dontAsk`; output strutturato con schema JSON chiuso;
- `--no-session-persistence`: nessuna chat salvata in `~/.claude/projects`;
- credenziali AWS dell'ambiente (ruolo, profilo), mai nel codice.

**In linea o con ricerca.** Se il testo di riferimento è al massimo `inline_max_lines` righe
(150), va nel messaggio con i numeri di riga: niente tool, al massimo 3 passi. Altrimenti il
messaggio elenca i file e le righe e il modello usa Grep e Read: al massimo 10 passi.

**GRASP** (`agent/hooks.py`): un hook controlla ogni chiamata ai tool **prima** che parta.

- Read: solo su un file ammesso, sempre con `limit` (al massimo 40 righe). Altrimenti la
  chiamata è rifiutata con le istruzioni: `offset = riga del match - 15`, `limit = 30`;
- Grep: solo su un file ammesso, con al massimo 10 righe di contesto;
- ogni altro tool è rifiutato (tranne quello interno dell'output strutturato).

**Il prompt** (`prompts/operation_check.md`): il modello è un verificatore; risponde
`coerente`, `contraddetto` o `non_verificabile` («nel dubbio scegli questo»); un'informazione
assente non è una contraddizione; non usa conoscenze sue; per `coerente` e `contraddetto` dà
almeno una citazione con file, riga e testo copiato alla lettera.

**Le citazioni** (`verdict/citations.py`): il codice riapre il file e cerca il testo
(almeno 8 caratteri, spazi e maiuscole non contano) a partire dalle righe entro
`citation_window` (3) da quella indicata, anche su più righe. Se non lo trova, la citazione non
vale.

**Esecuzione** (`agent/runner.py`):

- fino a `concurrency` (6) sessioni insieme per ciclo;
- guasto tecnico: si riprova `retries` (2) volte, con attesa crescente (`retry_backoff_s` 2 s);
- output non conforme allo schema: si riprova `invalid_output_retries` (1) volta;
- tempo massimo per sessione `session_timeout_s` (90 s): oltre, errore tecnico **senza**
  riprovare;
- tempo massimo di tutte le sessioni di un ciclo `validation_timeout_s` (480 s, sotto i 600 s
  del backend; MG53, 27-11 notte): dopo, nessuna sessione parte e quelle in corso si fermano.
  Diventano WARNING per errore tecnico e il report esce con quello che c'è.

**Ragionamento:** `effort: low` nei controlli (circa -30% di costo), `high` nella lettura del
PDF.

**Transcript:** con `save_transcripts: true` (solo negli esperimenti) il testo di ogni
sessione va in `runs/.../transcripts/`. Contiene cicli e manuali: nel servizio è spento.

---

## 10. La conoscenza

### 10.1 Da dove arriva

La prepara e la pubblica **knowledge-index** su S3. Il formato completo, con esempi inventati,
è nella sezione 10.4.

```
<prefisso>/knowledge/civil/current.json     {"version": "...", "path": "v/<versione>/"}
<prefisso>/knowledge/civil/v/<versione>/    manifest.json, documents/*.md, tasks.json,
                                            machine_tags.json, process_sheets.json,
                                            dr_recommendations.json, uncertainty.json
<prefisso>/knowledge/ej200/v/<versione>/    catalog.json, uncertainty.json, testi
```

- `manifest.json`: un documento per voce (`key`, `file`, `lines`, `version`, `code`, `kind`:
  per esempio `SPM`, `DR_PROC`). Più documenti possono avere lo stesso `code` (un manuale
  diviso in capitoli);
- `documents/*.md`: il testo a righe; `<!-- page N -->` segna l'inizio della pagina N;
- `tasks.json`: dove sta ogni task (`manual` = la `key` del documento, `line_start`,
  `line_end`);
- `machine_tags.json`: le targhe con la funzione; `process_sheets.json`: le schede con
  edizione, trattamento, famiglie di motore; `dr_recommendations.json`: serial number,
  condition, procedura, riferimento, task;
- `uncertainty.json` (facoltativo): le voci incerte con il motivo. Alcuni motivi danno WARNING
  `DATO_INCERTO`, altri solo una nota (`checks/uncertainty.py`). Se il file è incoerente,
  `kb-check` fallisce, ma il servizio lo ignora e lo scrive nel log;
- `needs_review`: un promemoria per chi cura l'indice; il programma lo ignora.

### 10.2 Come la legge la v2 (`kb/`)

- **Porta** (`kb/port.py`, `KnowledgeBase`): le sole domande che i controlli fanno (trova
  manuali, trova task, trova task in un tipo di documento, targa, scheda, recommendation DR).
  Ogni adattatore nuovo deve passare `tests/test_kb_contract.py`.
- **Cartella locale** (`kb/local.py`): la stessa struttura su disco. Ogni difetto dice in
  quale file e in quale voce.
- **Conoscenza pubblicata** (`kb/published.py`): all'avvio scarica la versione di
  `current.json` in una cartella sua; ogni **5 minuti** rilegge il puntatore e, se c'è una
  versione nuova **valida**, passa a quella senza riavvio. Se non è valida resta sulla vecchia.
  Tiene su disco le ultime 3 versioni. All'avvio, se un file della conoscenza civile non è
  valido, il servizio **non parte** e dice quale. Se è la conoscenza **EJ200** a non essere
  valida, dal 27-11 notte (MG44) si spegne solo EJ200: MOS e DR partono, una richiesta EJ200 ha
  la risposta 503 «profilo spento» e alla richiesta dopo si riprova a caricarla.
- **EJ200** (`kb/ej200.py`): catalogo delle pubblicazioni e testi su S3, con cache a tempo. Il
  `code` del catalogo contiene la issue (`EJ00020L-01`): il programma la toglie, così le issue
  della stessa pubblicazione restano una. Un ciclo può citare una issue precisa o solo il
  codice (vale la più recente). **La conoscenza EJ200 non si scarica mai sul PC**: anche la
  prova sul PC (`prova-ej200`, sezione 14.4) legge da S3 e tiene i testi usati solo in una
  cartella temporanea che cancella alla fine.
- **Fotografia** (`evaluation/snapshot.py`): copia locale datata di alcuni prefissi, per le
  prove; si legge con lo stesso codice di produzione.

### 10.3 Regole di ricerca (riassunto)

| Domanda | Regola |
|---|---|
| quale documento per un nome | quello pubblicato con la versione più alta; più pubblicazioni diverse = ambiguo |
| in quali manuali cercare un task | quelli delle fonti con lo stesso repair code dell'operazione; se nessuna, tutte |
| task del capitolo 70 | prima nell'SPM, poi negli altri manuali |
| task che l'indice non ha | nel testo del manuale (`kb/task_text.py`) |
| fonte con la sola sezione | tutti i task di quella sezione, in ogni documento del manuale |
| codice sbagliato o documento mancante | sbagliato se il codice non c'è da nessuna parte e ci sono i fratelli della stessa famiglia |

**Con molti documenti.** La ricerca di un task è un dizionario: non rallenta. Le ricerche nel
testo tengono una cache per documento finché il file non cambia: righe (`kb/documents.py`, 256),
codici di task completi (`full_task_codes`, 512), testo pulito (`resolve/civil.py`, 512). Così i
fratelli di un codice sbagliato del capitolo 70 leggono gli SPM una volta sola. Misura:
`eval scala` (14.3), numeri nella sezione 20.

### 10.4 Il formato, con esempi inventati

Confrontato il 20-11-2026 con i file veri della versione di prova. **I valori sono inventati**,
la forma è quella vera. `tests/test_e2e_formato_reale.py` fa girare tutto (dal PDF al payload
del frontend) con una conoscenza in questo formato.

Bucket e puntatori si danno con `BUCKETNAME`, `CIVIL_KNOWLEDGE_POINTER` ed
`EJ200_KNOWLEDGE_POINTER` (sezione 13.6). La versione ha la forma di una data e ora
(`AAAAMMGGThhmmssZ`). Di `current.json` il programma usa solo `version` e `path`.

**`manifest.json` (civile).** Una voce per documento; più documenti possono avere lo stesso
`code`, uno per capitolo.

```json
{
  "format": 1,
  "version": "AAAAMMGGThhmmssZ",
  "documents": [
    {"key": "SPM_M1_pb70-21-00-010_ch1", "file": "documents/SPM_M1_pb70-21-00-010_ch1.md",
     "lines": 214, "version": "ch1", "title": "SPM_M1_pb70-21-00-010_ch1", "code": "M1", "kind": "SPM"}
  ]
}
```

**`tasks.json`.** `manual` è la `key` di un documento del manifest, non il `code`, altrimenti la
conoscenza non si carica. `line_end` non può superare `lines` del documento.

```json
[
  {"manual": "SPM_M1_pb70-21-00-010_ch1", "task": "70-21-00-110-030", "line_start": 14, "line_end": 45},
  {"manual": "SPM_M1_pb70-21-00-010_ch1", "task": "70-21-00-110-031", "line_start": 46, "line_end": 214}
]
```

**`machine_tags.json`.** `function` elenca le lavorazioni separate da `; `. Le targhe si
confrontano senza spazi né maiuscole (`A 0100` = `A0100`).

```json
[
  {"tag": "1200", "function": "ASCIUGATURA; TRATTAMENTO TERMICO", "needs_review": true},
  {"tag": "A 0100", "function": "RIPORTO HVOF; RIPORTO PLASMA", "needs_review": true}
]
```

**`process_sheets.json`.** I codici si confrontano senza spazi, trattini né maiuscole
(`CPEC 100-BR` = `CPEC100BR`). Con `engine_families` vuoto la scheda risulta presente, ma non
si controlla se vale per il motore.

```json
[
  {"code": "10", "edition": "13", "treatment": "POST EMULSIFIED LEV.2", "engine_families": ["GENX"]},
  {"code": "CPEC 100-BR", "edition": "51", "treatment": "ATTACCO LOCALE A TAMPONE", "engine_families": []}
]
```

**`dr_recommendations.json`.** Con `manual: null` i task si cercano nei manuali citati dal ciclo.

```json
[
  {"serial_number": "AAAA0BBB", "conditions": [1], "procedure": "Repair", "reference": "R-0001", "manual": null, "tasks": ["72-56-30-220-100"]},
  {"serial_number": "AAAA0BBB", "conditions": [2], "procedure": "Accept as is", "reference": "R-0001", "manual": null, "tasks": []}
]
```

**`catalog.json` (EJ200).** Una voce per issue; il testo sta in `<document_id>/<content_hash>.md`.
Il `code` contiene già la issue: il programma la toglie (sezione 10.2).

```json
[
  {"code": "EJ00020L-01", "kind": "RDR", "issue": "01", "document_id": "EJ00020L-01-1a2b3c4d", "content_hash": "1a2b3c4d5e6f7080", "title": "EJ00020L-01", "published": true, "partial": false, "references": ["EJ00020"]}
]
```

Un ciclo EJ200 che cita una issue vecchia: la fonte esce WARNING e le operazioni si confrontano
con la issue citata.

---

## 11. Le macchine attive

L'elenco delle macchine in uso oggi viene da **Redshift**, come nella v1: la tabella della v1,
prima colonna la targa, filtro `work_center_usage_cd = 'TO'`. Su Redshift non si crea niente.

| `MACHINES_SOURCE` | Come | Dove |
|---|---|---|
| `diretta` | `redshift_connector`, con host, porta, utente e password del secret della v1 (riletto a ogni aggiornamento), database da `REDSHIFT_DATABASE`, query da `MACHINES_QUERY`, 20 s per collegarsi | **in servizio** |
| `data_api` | Redshift Data API (HTTPS), con workgroup o cluster | alternativa |
| `file` | `MACHINES_FILE`: JSON con una lista di targhe o `{"active": [...]}` | prove |
| `nessuna` | ogni targa N/A `CONTROLLO_SPENTO` (dal 27-11; prima WARNING) | **sul PC**: dal PC Redshift non si raggiunge |

In servizio l'elenco si rilegge ogni 15 minuti (`MACHINES_TTL_S` = 900). Sul PC il comando
`macchine` prova a scaricarlo in un file, ma oggi la Data API e la connessione diretta sono
bloccate (permessi e rete).

---

## 12. Impostazioni e profili

### 12.1 `config/settings.yaml`

In azienda le impostazioni provate stanno in `data/settings.yaml` (con l'id vero del modello);
nell'immagine del servizio diventano `config/settings.azienda.yaml`.

| Voce | Predefinito | Cosa fa |
|---|---|---|
| `agent.model` | `haiku` | alias o id del profilo di inferenza Bedrock |
| `agent.effort` | `low` | ragionamento nei controlli (`low`, `medium`, `high`, vuoto = del modello) |
| `agent.extraction_effort` | `high` | ragionamento nella lettura del PDF |
| `agent.use_bedrock` | `true` | il modello passa da Bedrock |
| `agent.aws_region` | vuoto | regione di Bedrock; vuoto = quella dell'ambiente |
| `agent.transcribe_model` | vuoto | modello che trascrive foto e scansioni; vuoto = solo PDF con testo |
| `agent.transcribe_concurrency` | 4 | pagine trascritte insieme |
| `agent.max_turns` / `inline_max_turns` / `extraction_max_turns` | 10 / 3 / 3 | passi massimi per sessione con ricerca, in linea, di lettura |
| `agent.concurrency` | 6 | sessioni insieme per ciclo |
| `agent.retries`, `retry_backoff_s`, `invalid_output_retries` | 2, 2.0, 1 | nuovi tentativi |
| `agent.session_timeout_s` / `extraction_timeout_s` | 90 / 300 | tempo massimo |
| `agent.read_limit`, `read_window`, `read_before`, `grep_max_context` | 40, 30, 15, 10 | numeri di GRASP |
| `agent.inline_max_lines` | 150 | fino a quante righe il testo va nel messaggio |
| `agent.citation_window` | 3 | tolleranza in righe per le citazioni |
| `agent.skip_missing_task` | `true` | task citato che manca: WARNING subito, senza modello |
| `agent.missing_task_note` | `false` | (con lo skip spento) dire al modello che il task manca |
| `agent.separate_languages` | `true` (dal 26-11) | descrizione in due lingue: nella domanda al modello la parte italiana e quella inglese separate, con l'istruzione di confrontarle **ognuna** con il testo di riferimento (se una sola dice altro, `contraddetto`). Variante `lingue_separate` |
| `agent.itemized_check` | `true` (dal 26-11) | prima di giudicare il modello scompone la descrizione in elementi tecnici (lavorazione, valori, limiti, divieti, materiali) e li confronta uno per uno; se uno solo è incompatibile, `contraddetto`. Variante `elementi_uno_per_uno`. Le due sono nella base dal 26-11 (campagna del 25-11, variante `elementi_e_lingue`): il valore predefinito nel codice vale anche per `data/settings.yaml` sul PC, che non le nomina |
| `agent.search_when_unverifiable` | `false` | dopo un `non_verificabile`, una seconda sessione cerca in tutti i documenti citati dal ciclo, con i tool. Variante `seconda_ricerca` |
| `agent.general_definitions_note` | `false` | nella domanda al modello: una differenza solo con una **definizione generale** del manuale di pratiche standard (per esempio «indicazione lineare = 3 volte la larghezza») dà `non_verificabile`, non `contraddetto`; resta `contraddetto` con un limite specifico o con una lingua diversa dall'altra. Variante `definizioni_generali` (26-11) |
| `agent.compare_languages` | `true` (dal 27-11 sera, con la versione stretta) | una sessione corta per ogni operazione scritta in due lingue: il modello confronta l'italiano e l'inglese **tra loro**, senza manuale. Una differenza (negazione, limite, materiale, valore) con le citazioni ritrovate e confermata è ERRATO `INCOERENZA_LINGUE`. Variante `lingue_tra_loro` (26-11 sera) |
| `agent.special_process_sheet` | `true` (dal 27-11) | processo speciale senza scheda: WARNING `SCHEDA_FORSE_MANCANTE` («Scheda mancante») invece di N/A (sezione 6.4). Regola P6, I9 |
| `agent.sheet_consistency` | `true` | la scheda coerente con l'operazione, deciso dal codice: altro motore, altro materiale, task della scheda inesistente, scheda inesistente tra altre con lo stesso prefisso danno ERRATO (sezione 6.4). Variante `schede_e_limiti` (H18, 27-11 sera) |
| `agent.boundary_limits_note` | `true` | nella domanda al modello: «almeno N» contro «più di N» (solo il caso uguale a N) non è una contraddizione. Regola decisa dall'utente il 27-11 sera (P12). Variante `schede_e_limiti` |
| `agent.inspection_source` | `true` (dal 27-11 sera) | nelle ispezioni anche la sezione INSPECTION o i task d'ispezione (gruppo 200) del manuale del motore, con una nota (sezione 6.5). Variante `fonte_ispezione` (I8, 27-11) |
| `agent.out_of_scope` | `true` (dal 27-11 sera) | il modello può rispondere `fuori_tema`: N/A `FUORI_TEMA` invece di WARNING quando il testo non tratta il tipo di operazione (sezione 6.5). Variante `finale` (I16, 27-11) |
| `agent.compare_languages_strict` | `true` (dal 27-11 sera) | con `compare_languages`: solo negazioni e limiti al contrario, ritrovati dal codice nelle parole copiate (sezione 6.5). Variante `finale` (I15, 27-11) |
| `agent.dr_procedure_always` | `true` (dal 27-11) | nei cicli DR la procedura della D.R. va al modello insieme ai task trovati, con una nota: per quel pezzo vale più del manuale. Variante `procedura_dr` (26-11 sera), nella base dopo la campagna del 26-27-11 |
| `agent.languages_from_code` | `true` (dal 27-11 notte) | limiti al contrario, «massimo» contro «minimo» e azioni diverse tra le lingue, dal codice: ERRATO `INCOERENZA_LINGUE` (MG75, MG81, MG47; sezione 6.5) |
| `agent.dr_consistency` | `true` (dal 27-11 notte) | tutte le operazioni citano lo stesso DR: un altro è ERRATO `DR_DIVERSO` (MG76; sezione 6.5) |
| `agent.prudent_out_of_scope` | `true` (dal 27-11 notte) | `fuori_tema` non vale se la descrizione ha una negazione o un limite: WARNING e una seconda ricerca (MG45) |
| `agent.validation_timeout_s` | 480 | tempo massimo delle sessioni di un ciclo (MG53; sezione 9) |
| `agent.confirm_contradiction` | 2 | sessioni di conferma per ogni ERRATO del modello |
| `agent.task_stage_check` | `false` | task di un altro stadio: ERRATO `TASK_ALTRO_STADIO` (MG48; sezione 6.2) |
| `agent.session_backend` | `diretta` (dal 28-11) | `diretta`: chiamata diretta a Bedrock senza Claude Code (MG54); `sdk`: Claude Agent SDK (sezione 9) |
| `agent.direct_model` | vuoto | con `diretta`: id del modello su Bedrock (vuoto = `agent.model`) |
| `agent.direct_transport` | `boto3` | con `diretta`: `boto3` (`invoke_model`) o `httpx` (client HTTP dell'SDK) |
| `agent.direct_input_price`, `agent.direct_output_price` | 0,10 e 0,50 | con `diretta`: dollari per milione di token, per il costo nel report |
| `agent.direct_cache` | `true` (dal 28-11) | con `diretta`: punti di cache di Bedrock (MG56) |
| `agent.shared_reference_first` | `false` | il testo del manuale prima della domanda, in un blocco da tenere in cache (MG59) |
| `agent.language_batch_size` | 8 (dal 28-11) | confronto tra le lingue di più operazioni in una sessione (MG55); 0 = spento |
| `agent.final_rules` | `[fonte_assente_una_volta]` (dal 28-11) | regole finali sugli esiti già fatti, per nome: `fonte_assente_una_volta` (MG83), `limite_contro_citazione` (MG87); sezione 5.7 |
| `agent.save_transcripts` | `false` | testo delle sessioni su disco |
| `paths.*` | `config/profiles`, `prompts`, `data/knowledge`, `runs` | cartelle |
| `paths.machines_file` | vuoto | JSON delle macchine attive |
| `module_check.enabled` | `true` | rifiuta il modulo sbagliato |
| `module_check.military_projects` / `civil_projects` | `[EJ200]` / `[GENX, LEAP]` | valori del campo PROGETTO |
| `module_check.dr_markers` | tre espressioni | come si riconosce un DR dalla testata |

Le impostazioni si validano al caricamento: un valore sbagliato dice il file e il campo.

### 12.2 I profili (`config/profiles/`)

| | `mos` | `dr` | `ej200` |
|---|---|---|---|
| controlli | source, task_code, machine_tag, process_sheet, operation_description | gli stessi più `dr_recommendation` (bloccante) | gli stessi di MOS |
| selettori (serial number, condition) | no | sì, facoltativi | no |
| riferimenti | task | task | documento intero, ordine RDR, EF, RN |
| schede | controllate, esclusi `SWJ`, `SSS`, `SPS` | come MOS | N/A |
| famiglie di motore | GENX, LEAP | GENX, LEAP | — |
| limiti del file | PDF, 100 caratteri | come MOS | 20 MB, 60 pagine, parola `EJ200` |
| lettura | parser PVRM320, poi modello | come MOS | come MOS, prompt EJ200 |

---

## 13. Il servizio (API)

### 13.1 Avvio

`uv run uvicorn cycle_validation.api.entry:app --port 8000` (in azienda gunicorn
nell'immagine; in locale sulla porta 8003 al posto della v1). Il servizio si monta da solo
dalle variabili d'ambiente (`api/main.py`, `api/production.py`, `api/settings.py`): prima le
controlla tutte e, se qualcosa non va, le elenca insieme per nome, senza stampare valori di
secret. L'elenco completo delle variabili è nella sezione 13.6.

Con `CV_ENV_SECRET` (lo stesso secret «di ambiente» della v1) le chiavi del secret diventano
variabili, senza sovrascrivere quelle già impostate: la v2 parte con la configurazione della
v1, senza valori nuovi.

### 13.2 Le rotte (prefisso `/cycle_validation`)

| Rotta | Cosa fa |
|---|---|
| `GET /health` | `{"status":"ok","code":200}`, senza login |
| `GET /flow/start` | la domanda «è un DR?» |
| `POST /conversation` | risposta sì/no, poi (facoltativi) serial number e condition |
| `POST /upload` | il PDF civile: `file`, `is_dr`, `dr_serial_number`, `dr_condition` |
| `GET /validation/options` | quali pulsanti mostrare (civile/militare, MOS/DR); il militare solo a chi ha `cv_ej200` o `all` |
| `POST /validation/upload` | caricamento con la scelta: `domain` (`civil`/`military`), `civil_type` (`mos`/`dr`) |
| `GET /ej200/flow/start`, `POST /ej200/upload` | i cicli militari |
| `POST/GET/DELETE /sessions…`, `/ej200/sessions…` | elenco, apertura, salvataggio, cancellazione delle chat (su S3) |
| `POST /feedback`, `/ej200/feedback` | pollice su/giù (un oggetto S3 per feedback) |

Il frontend di oggi usa le rotte storiche (`/conversation`, `/upload`, `/ej200/…`).

### 13.3 La risposta

Successo: `{"state": "succeeded", "result": {"file_name", "payload", "error": null}, "error":
null, "error_info": null}`; per EJ200 anche `job_id` e `finished_at`.

Errore imprevisto sul civile: **200** con `state: failed` (come la v1) e il solo tipo
dell'errore (mai il testo del ciclo). Errori previsti: 400/415 file, 422 scelta, selettori o
«Modulo sbagliato», 503 conoscenza o sorgente non disponibile, 501 EJ200 spento, 401/403
accesso.

Al massimo `API_MAX_WORKERS` (6) validazioni insieme: le altre aspettano. File al massimo
`API_MAX_UPLOAD_MB` (50).

**Risultato già calcolato (MG58, dal 28-11).** Se arriva di nuovo lo stesso file (stessi byte),
con lo stesso profilo, gli stessi serial number e condition, la stessa versione della
conoscenza, lo stesso modello, lo stesso prompt e la stessa versione della v2, il servizio non
rifà la validazione: risponde con gli stessi esiti in meno di un secondo e 0 $. Il run è nuovo
(id, ora e nome del file sono quelli della richiesta); nel log `Risultato riusato (MG58)`. I
risultati stanno in memoria (`api/runner.py`, `ResultCache`): al massimo 200, per 6 ore (le
macchine attive possono cambiare durante il giorno), e si perdono a ogni riavvio. Non si
tengono i risultati con un errore tecnico (rete, servizio): la volta dopo si riprova. Vale
solo per il servizio: i comandi (`validate`, `eval prova`, la campagna) validano sempre.

### 13.4 Il payload per il frontend (`report/legacy_payload.py`)

In alto: `cycleCode`, `cycleDescription`, `engineModel`, `operationType`, `repairCode`,
`cycle_errors_count` (gli ERRATO), `cycle_errors_count_perc`, `cycle_status`,
`_pipeline_errors`, `profile` (i tempi).

- `sources`: `repairCode`, `manual`, `task`, `section`, `sourceFeedback`. L'esito DR va nella
  riga della fonte che cita il DR (con `DRCase` e `serialNumber`); se nessuna lo cita, una riga
  DR in cima. Se la riga ha anche un suo avviso: prima il più grave, poi l'altro, con ` | `;
- `operations`: `operationNumber`, `repairCode`, `operationDescription`, `targaCResp`,
  `taskCodeCited`, `scheda` (`tabNumber` = codice, `task` = codice dopo «SP.ORIG.» nei civili,
  `class` vuoto) e i quattro feedback (`operationFeedback`, `targaCRespFeedback`,
  `taskCodeFeedback`, `schedaFeedback`).

**I testi dei feedback** (il frontend guarda solo l'inizio):

| Esito | Testo | Bollino nel frontend |
|---|---|---|
| CORRETTO | `No errors found.` | OK verde |
| ERRATO | `Error found: <motivazione>` | Error rosso |
| WARNING | `Warning: [da guardare] <motivazione>` oppure `Warning: [non controllabile] <motivazione>` (H15, dal 27-11 sera) | Warning giallo; il tipo tra parentesi quadre il frontend lo può mostrare a parte |
| N/A per campo assente o blocco DR | `N/A` | N/A grigio |
| altro N/A | `N/A - <motivazione>` | Info azzurro |

Intestazione nel frontend: «Validation Failed» se `state: failed`; «Completed with Errors» se
`cycle_errors_count > 0` o ci sono `_pipeline_errors`; altrimenti «Validation Passed», anche
con dei Warning.

### 13.5 Chi è l'utente (`api/auth.py`)

- `API_AUTH=sdk` (in azienda; scelto da solo se c'è `AUTH_INTROSPECT_URL`): gli stessi
  middleware della v1, dalla libreria interna `chatbot_ai_sdk` 0.4.0rc2 `[auth]`. Token dal
  cookie (401 se manca o non vale), permessi da `permissions.json` su S3 (403; sotto
  `/cycle_validation/ej200` serve `cv_ej200`), `Origin` uguale a `FRONTEND_URL`. Senza la
  libreria la v2 non parte;
- `API_AUTH=header` (solo prove): utente e servizi dagli header `X-User` e `X-Services`; il
  backend se ne fida, quindi deve essere raggiungibile solo dal frontend.

L'utente finisce nel percorso S3 di sessioni e feedback: si accettano solo lettere, cifre e
`.`, `_`, `@`, `-`.

### 13.6 Le variabili d'ambiente

Il servizio si monta da solo da queste variabili: non c'è codice da scrivere. In servizio
arrivano quasi tutte dal secret «di ambiente» della v1 (`CV_ENV_SECRET`) e dalle righe `ENV`
del Dockerfile scritto da `qa`.

| Variabile | Obbligatoria | Cosa fa |
|---|---|---|
| `BUCKETNAME`, `REGION_NAME`, `FRONTEND_URL` | sì | bucket S3, regione AWS, indirizzo del frontend |
| `CV_ENV_SECRET` | no | nome del secret «di ambiente» (lo stesso della v1): le sue chiavi diventano variabili, senza sovrascrivere quelle già impostate |
| `MACHINES_SOURCE` | no (dedotta) | `diretta` (come la v1, **in servizio**), `data_api`, `file` o `nessuna` (sezione 11). Senza: `file` se c'è `MACHINES_FILE`, `data_api` se c'è `REDSHIFT_DATABASE` |
| `REDSHIFT_DATABASE` | con `diretta` e `data_api` | il database di Redshift |
| `REDSHIFT_SECRET_NAME` | no | con `diretta`: il secret con host, porta, utente e password. Senza, `SECRET_NAME` come nella v1 |
| `MACHINES_QUERY` | **sì** | prima colonna = targa; la tabella è quella della v1. La predefinita è solo un segnaposto |
| `MACHINES_FILE` | con `file` | JSON delle macchine attive |
| `REDSHIFT_WORKGROUP`, `REDSHIFT_CLUSTER_ID`, `REDSHIFT_DB_USER`, `REDSHIFT_SECRET_ARN` | con `data_api` | workgroup Serverless, oppure cluster con utente IAM o secret |
| `MACHINES_TTL_S` | no | ogni quanti secondi si rilegge Redshift (900) |
| `CIVIL_KNOWLEDGE_POINTER` | no | `current.json` della conoscenza civile |
| `EJ200_KNOWLEDGE_POINTER` | no | `current.json` di EJ200; vuota = catalogo a chiave fissa `EJ200_CATALOG_KEY` |
| `EJ200_VALIDATION_ENABLED` | no | `false` spegne i cicli militari |
| `SECRET_NAME` | no | con `CV_ENV_SECRET`: il secret di Redshift, come nella v1 |
| `KNOWLEDGE_WORKDIR` | no | dove scaricare la conoscenza (predefinita: nella cartella temporanea) |
| `CYCLE_VALIDATION_CONFIG` | no | file delle impostazioni |
| `CLOUDWATCH_METRICS` | no | `false` per non pubblicare il costo su CloudWatch |
| `API_MAX_WORKERS`, `API_MAX_UPLOAD_MB` | no | validazioni insieme (6), dimensione massima del file (50) |
| `API_INCLUDE_TRACEBACK` | no | **in produzione `false`** |
| `API_AUTH` | no | `sdk`, `header` (prove) o `auto` (predefinito: `sdk` se c'è `AUTH_INTROSPECT_URL`) |
| `AUTH_*` | con `sdk` | le variabili della libreria, già nel secret della v1 (`AUTH_INTROSPECT_URL`, `AUTH_CLIENT_ID`, `AUTH_CLIENT_SECRET`, `AUTH_EXPECTED_CLIENT_ID`, `AUTH_SSO_CLAIM`, `AUTH_PERMISSIONS_BUCKET`, `AUTH_PERMISSIONS_KEY`) |
| `API_USER_HEADER`, `API_SERVICES_HEADER` | no | con `header`: gli header con utente e servizi (`X-User`, `X-Services`) |

Con `diretta` serve quello che usa già la v1: leggere il secret di Redshift, arrivare alla
porta del cluster e la libreria `redshift_connector` (extra `redshift`, già nel Dockerfile).
Con `data_api` il ruolo deve poter usare `redshift-data:ExecuteStatement`,
`DescribeStatement` e `GetStatementResult`.

### 13.7 In locale, con login e frontend (provato il 22-11-2026)

Come per la v1, da Run and Debug di VS Code. La v1 in locale gira sulla porta 8003 e il
frontend manda lì `/cycle_validation/`: la v2 si avvia sulla 8003 **al posto** della v1.

1. La libreria di accesso nella v2: la riga dei requirements della v1,
   `chatbot_ai_sdk-0.4.0rc2-py3-none-any.whl[auth]` dalla cartella `vendor` della v1
   (`uv pip install "chatbot_ai_sdk[auth] @ file:///<cartella della v1>/vendor/<file .whl>"`).
   La 0.3.0, nella stessa cartella, non ha i pezzi che servono.
2. In `.vscode/launch.json` una configurazione per la v2 e una voce composta «CV v2» con
   `login`, `app_frontend` e la v2, **senza** il task «Centralizer prerequisites» (sul PC lo
   script non c'è).

```json
{
  "name": "CV v2 (porta 8003)",
  "type": "debugpy",
  "request": "launch",
  "module": "uvicorn",
  "args": ["cycle_validation.api.entry:app", "--port", "8003"],
  "cwd": "${workspaceFolder}/<repository aziendale>/app_cycle_validation_v2",
  "python": "${workspaceFolder}/<repository aziendale>/app_cycle_validation_v2/.venv/Scripts/python.exe",
  "env": {
    "AWS_PROFILE": "<come nella configurazione della v1>",
    "CV_ENV_SECRET": "<identico al nome in load_secrets della v1>",
    "FRONTEND_URL": "http://localhost:3000",
    "CYCLE_VALIDATION_CONFIG": "data/settings.yaml",
    "MACHINES_SOURCE": "nessuna",
    "CIVIL_KNOWLEDGE_POINTER": "<puntatore della conoscenza civile>",
    "EJ200_VALIDATION_ENABLED": "false",
    "CLOUDWATCH_METRICS": "false"
  }
}
```

Perché: con un `CV_ENV_SECRET` diverso dalla v1 la v2 non parte (`ResourceNotFoundException`);
senza `FRONTEND_URL` locale la libreria rifiuta ogni POST con 403 `Origine non ammessa.`;
dal PC Redshift non si raggiunge (`nessuna`: targhe N/A); EJ200 spento perché la sua
conoscenza non deve arrivare sul PC. Aperta direttamente, `http://127.0.0.1:8003/` risponde
401 `Login richiesto.`: è giusto, la prova passa da `http://localhost:3000` dopo il login.

Senza login né frontend basta `uv run uvicorn cycle_validation.api.entry:app --port 8000`
(oppure `docker build -t cycle-validation .` e `docker run -p 8000:8000 --env-file .env
cycle-validation`): `http://127.0.0.1:8000/cycle_validation/health` risponde
`{"status":"ok","code":200}`.

---

## 14. I comandi (CLI)

Tutti con `uv run cycle-validation <comando>`, dalla cartella della v2. `--help` mostra le
opzioni.

### 14.1 Validare e guardare le stampe

| Comando | Cosa fa | Costa |
|---|---|---|
| `run <pdf>` | valida un ciclo e scrive `report.json`, `report.md`, `payload.json` in `runs/ultimo`. Opzioni: `--profile`, `--cycle-json` (ciclo già letto), `--knowledge`, `--machines`, `--config`, `--skip-check`, `--serial-number`, `--condition` | sì |
| `leggi <pdf>…` | legge le stampe con il parser e stampa riparazione, fonti, task. `--breve`, `--pagina N`, `--struttura N`, `--cerca`, `--lingue` (numeri diversi tra le lingue), `--fonti` (manuali come M1, M2…), `--senza-riordino` | no |
| `confronta <giusta> <con errori>` | dice in quali operazioni e campi due stampe sono diverse; codici mascherati | no |
| `kb-check <cartella>` | carica una conoscenza locale, stampa i conteggi e fallisce se un file non va | no |
| `manuali <percorsi>…` | quali manuali servono nella conoscenza per i cicli di prova; con `--conoscenza` quali mancano e perché (il conteggio tiene separati i manuali che mancano del tutto da quelli già dentro a cui mancano dei task: per questi servono altri file, non gli stessi di nuovo); codici veri solo nel file `--out` | no |
| `golden <cartella>` | esegue il golden set (casi con esiti attesi riga per riga) e stampa la concordanza | sì |

### 14.2 Prove sui cicli veri (sezione 15.3)

| Comando | Cosa fa | Costa |
|---|---|---|
| `eval scegli <cartelle>` | sceglie i cicli: prima quelli noti, poi i veri civili con almeno l'80% di operazioni confrontabili (`--copertura`), fino a `--quanti` (0 = tutti). Accanto a ogni ciclo vero scrive se è MOS o DR (dalla testata) e in fondo quanti per tipo | no |
| `eval muta` | fa le copie cieche: `--lista`, `--knowledge`, `--quanti`, `--seme`, `--per-ciclo` (6) | no |
| `eval prova [pdf]…` | valida, confronta con gli errori noti, scrive `prestazioni.md` e `riepilogo.md`. `--nome`, `--variante`, `--lista` (ripetibile), `--attesi` (ripetibile), `--cartella`, `--profile` (predefinito `auto`: MOS o DR ciclo per ciclo, dalla testata, così un DR nella lista non si ferma con «Modulo sbagliato») | sì |
| `eval chiamata-diretta` | prova la chiamata diretta a Bedrock (MG54) con una domanda finta, senza testi aziendali: dice se modello, regione, accesso e strumento di risposta funzionano. `--config` (vuoto = `data/settings.yaml`), `--trasporto` (`boto3` o `httpx`; vuoto = le impostazioni). Se non riesce, dice tipi, codice di AWS e causa probabile. Meno di un centesimo (28-11) | sì |
| `eval senza-modello` | gli stessi cicli della campagna (`--insiemi`, predefinito piccolo e grande), solo con i controlli del codice: al posto del modello una risposta fissa «non verificabile». Dice quanti errori noti trova il codice da solo e se dà falsi errori. Prove in `runs/senza-modello-<insieme>`, fuori dalle cartelle della campagna. I WARNING qui non contano (tutto quello che fa il modello esce WARNING). `--knowledge` (vuoto = ultima fotografia), `--config`, `--cartella`. Serve a provare una regola nuova del codice prima di una campagna (27-11 notte). Con `--variante` (28-11) dopo la base prova anche la variante e stampa la riga `Differenza sul <insieme>`: errori trovati prima e dopo (in più e persi, solo dei cicli noti: delle copie cieche solo il numero), falsi errori, da verificare, e una parola: `da scartare`, `da guardare` (ERRATO nuovi fuori dalla lista), `si può tenere` o `nessuna differenza` | no |
| `eval rigioca` | una regola finale (MG83) sulle prove già fatte (28-11): `--variante` (nome in `eval/varianti`), `--riferimento` (vuoto = quello di `eval/campagna.yaml`), `--insiemi`, `--file`, `--config`, `--cartella`. Rifà il conto delle prove del riferimento dai loro `report.json`, con gli errori noti di adesso (anche copie cieche e gruppo nascosto), e delle stesse prove con le regole della variante; stampa per insieme errori stabili, falsi OK, falsi errori, da verificare e WARNING per ciclo, prima → dopo, e la decisione. Poi, per ogni falso OK delle prove del riferimento (errore noto mancato con CORRETTO), una riga `Falso OK, riga citata: <impronta> <op>: ...` che dice solo sì/no e conteggi sulla riga del manuale citata dal modello (citazioni, limite letto nella descrizione, stesso numero nella riga, parole di limite, verso letto): più il verso letto nella descrizione sullo stesso numero; e una seconda riga `Falso OK, riga citata: <impronta> <op> forma: it «…» · en «…» · riga 1 «…»` con la **forma** della descrizione (per lingua, intorno alla prima parola di limite) e della riga citata (intorno al numero in comune): lettere → `x`, cifre → `9`, leggibili solo le parole di limite e di negazione (`final_rules.text_shape`). Serve a capire perché `limite_contro_citazione` (MG87) non scatta, senza mostrare codici o parole del manuale. Solo per una variante che cambia soltanto `agent.final_rules` (altrimenti si ferma e dice che cosa cambia). Prove in `runs/rigioca-<insieme>`, rifatta da capo ogni volta; le cartelle della campagna non si toccano. 0 $, pochi secondi | no |
| `eval banco` | banco di prova sulle 14 stampe vere di `docs/CONFRONTO_V1_14_CICLI.md`: il programma mette un errore alla volta su ogni operazione possibile (un numero, un limite, «massimo»/«minimo», un'azione in una lingua; il numero del DR) e conta quanti ne trovano i controlli del codice, per tipo, e i falsi allarmi su altre operazioni; poi la lettura della stampa contro la tabella della v1 (operazioni, targhe, schede). `--giri` (5: semi diversi), `--knowledge`, `--config`. 0 $, pochi secondi; a schermo solo impronte, operazioni e conteggi (27-11 notte) | no |
| `eval riepilogo` | riscrive `riepilogo.md` della cartella. Con `--attesi` (ripetibile) prima ricalcola le prove già fatte dai `report.json` dei cicli, con gli errori noti di adesso: solo i cicli che sono in quei file (copie cieche, gruppo nascosto e cicli veri tengono il punteggio e prendono solo i WARNING per operazione, MG83). Serve quando la lista degli errori noti cambia (27-11) | no |
| `eval campagna` | tutte le prove di `eval/campagna.yaml` in fila, per ogni modello e insieme, e il report unico `runs/campagna.md`. `--piano` (gratis), `--solo-report` (gratis: solo il report), `--modelli` (con un solo modello il report è `runs/campagna-<modello>.md`), `--insiemi`, `--varianti`, `--ripetizioni`, `--grande`, `--massimo-dollari`, `--knowledge` (vuoto = ultima fotografia), `--config` (vuoto = `data/settings.yaml` se c'è), `--file`, `--cartella` | sì |

### 14.3 Esperimenti con i casi rivisti (sezione 15.2)

| Comando | Cosa fa |
|---|---|
| `eval fotografia` | copia i prefissi S3 della conoscenza in una cartella datata |
| `eval prepara <caso>` | valida un ciclo vero una volta e scrive la bozza `expected.json` da far rivedere |
| `eval esegui --variante` | esegue una variante su tutti i casi e scrive i risultati grezzi |
| `eval classifica` | mette in classifica le varianti |
| `eval mutazioni` | copie dei casi rivisti con difetti noti o modifiche innocue |
| `eval pipeline` | tutto insieme: verifiche del codice, baseline, varianti, classifica |
| `eval scala` | conoscenza finta di molti documenti in una cartella temporanea: misura avvio, disco, memoria e ricerche, poi la cancella. `--documenti` (2900), `--righe` (3000), `--task` (30), `--spm` (30), `--senza-righe`. Gratis |

### 14.4 Azienda

| Comando | Cosa fa |
|---|---|
| `macchine` | scarica le macchine attive da Redshift in `data/macchine_attive.json` (stampa solo il numero) |
| `qa` | prepara la pubblicazione in QA (sezione 16); `--torna-alla-v1` la annulla |
| `prova-ej200 <pdf o cartelle>…` | cicli EJ200 sul PC senza tracce (autorizzato dal 27-11): catalogo e testi da S3 (`--conoscenza-ej200`, `--bucket`, `--regione`), testi in una cartella temporanea `cv-ej200-…` cancellata alla fine (quelle rimaste si cancellano alla prova dopo); niente `runs/`, report, transcript, log. Targhe da `--targhe` (vuoto = ultima fotografia), macchine da `--machines`. Prima di partire controlla i percorsi: se è rimasto l'esempio `<cartella EJ200>` o il percorso non esiste lo dice in chiaro (28-11: prima usciva solo `prova non partita (OSError)`); un PDF che non si legge non ferma gli altri (impronta `????????`). A schermo solo impronta, stato, conteggi, motivi, costo; un errore solo con il tipo (`evaluation/ej200_local.py`) |

---

## 15. Misurare la qualità

Ci sono tre modi, dal più semplice al più vicino all'uso vero.

### 15.1 Golden set sintetico (`golden.py`, `eval/casi/sintetici/`)

Cicli inventati con l'esito atteso per ogni riga. `golden` stampa la **concordanza** (righe
uguali / righe attese), il costo e i tempi. Serve a vedere che Bedrock risponde e che niente
si è rotto.

### 15.2 Esperimenti con casi rivisti (`evaluation/run.py`, `metrics.py`, `leaderboard.py`)

Per cicli veri con l'esito giusto riga per riga, rivisto da chi conosce il ciclo (`"rivisto":
true`). Le varianti girano sugli stessi casi e sulla stessa fotografia. Una variante è
scartata se ha più ERRATO falsi, più errori mancati, concordanza più bassa, più righe
instabili o più esiti tecnici; tra le ammesse vince la più veloce. La variante `guasti`
simula guasti e **regge** se nessun guasto diventa ERRATO.

Oggi si usano le prove della sezione 15.3; questi esperimenti restano per quando ci saranno casi
rivisti. Come si preparano:

1. `cp -r eval/modelli/aziendali/mos eval/modelli/aziendali/dr eval/casi/aziendali/` e, in ogni
   `suite.yaml`, `conoscenza` = il nome della cartella della fotografia (`eval fotografia`);
2. per ogni ciclo vero una cartella con `ciclo.pdf`, poi `eval prepara <cartella>` (per un DR
   anche `--serial-number`, `--condition`): scrive `ciclo.json`, `expected.json` (esiti
   proposti, `"rivisto": false`) e `revisione.md`;
3. chi conosce il ciclo corregge `verdict` e `reason` sbagliati in `expected.json`, controlla
   `ciclo.json` contro la stampa e mette `"rivisto": true`. Finché è `false` il caso si salta;
4. `eval pipeline --casi eval/casi/aziendali --ripetizioni 3`: verifiche del codice, baseline,
   varianti, classifica in `eval/risultati/classifica.md`. Si confrontano solo prove dello
   stesso ambiente, ogni variante con l'ultima baseline. Per gli errori fabbricati:
   `eval mutazioni`, poi `eval pipeline --casi eval/casi/mutazioni --salta-verifiche`.

Bastano pochi casi ma vari (5-10 MOS, 3-5 DR), con qualche ERRATO vero: sono i più preziosi.

### 15.3 Prove sui cicli veri (`evaluation/trials.py`, `evaluation/blind.py`)

È il sistema usato adesso (COPILOT sezione 3). Non serve rivedere ogni riga: si conoscono solo gli
**errori** di alcuni cicli.

**Tipi di ciclo:**

- `errori`: stampa modificata a mano, con errori noti (`eval/errori-noti.yaml`, per impronta);
- `giusto`: la stampa originale di un ciclo «con errori»: non deve dare ERRATO;
- `vero`: ogni altro ciclo vero: un suo ERRATO è «da verificare».

Un ciclo di `errori-noti.yaml` può avere `in_attesa` (operazione → che cosa aspetta): oggi
quell'operazione non si può giudicare. Un ERRATO lì non conta né come trovato né come falso
errore; un errore noto lì non conta come mancato (è fuori dal totale dei visti). Si vede a parte
(riga «ERRATO in attesa» nel report, sezione «In attesa di una risposta» nel riepilogo, con
tutte le operazioni in attesa e, dal 26-11 sera, in quante prove di ogni variante c'è un
ERRATO). Dal 24-11: op. 050 della stampa giusta `04ecaabe` (domanda P7),
op. 030 di `c5ff3cd6` (scheda tolta, domanda P6), op. 040 di `f355dc3c` (serve un documento che
non è nella conoscenza). I visti contati sono quindi 10.

**Come si leggono i numeri** (dal 24-11 il report li dà separati, perché non si sommano):
**errori visti trovati** (quelli che oggi si possono trovare), **errori mai visti trovati dal
modello** (la generalizzazione), **falsi errori** (devono essere 0); poi i controlli del codice
(copie che il codice trova per costruzione) e il totale, solo per contare. La riga finale di
`eval prova` è `Prova «...»: visti A su B · mai visti per il modello C su D · falsi errori E ·
controlli del codice F su G · da verificare H · in attesa I · costo ... $`. Il report ha anche
**«WARNING per motivo»** (per ciclo senza errori noti: quanti sono targhe, manuali mancanti,
dubbi del modello) e il riepilogo, nella tabella «Errore per errore», l'**ultimo esito** su ogni
errore noto (solo esito e motivo: perché viene mancato).

Le copie cieche si scrivono byte per byte (`\n`), e `eval prova` toglie i `\r` prima di
calcolare l'impronta di un file `.json`: su Windows prima del 24-11 l'impronta del file non era
quella di `errori.yaml` e le copie uscivano come cicli veri.

Per una copia cieca `eval prova` **non** fa il controllo di integrità contro il PDF
(`RunRequest.check_integrity=False`): il ciclo viene dal file con l'errore messo apposta, e il
valore cambiato per costruzione non è nel PDF originale. Con il controllo, ogni ERRATO sul
numero o sul codice cambiato diventava WARNING `ESTRAZIONE_NON_CONFERMATA` (prova del 24-11:
mai visti per il modello 0 su 21, per il codice 4 su 10).

**Errori visti e mai visti:**

- **visti**: i 12 errori noti. Chi scrive le migliorie li conosce: una miglioria può
  «impararli a memoria»;
- **mai visti**: misurano se la v2 **generalizza**:
  - **copie cieche** (`eval muta`): da ogni ciclo vero il programma fa copie con **una sola**
    operazione cambiata, al massimo 6 copie per ciclo (`--per-ciclo`; erano 2 fino al 24-11),
    sempre le stesse per lo stesso seme. I tipi «codice» si fermano a 5 copie ciascuno
    (`CODE_KIND_MAX`): il resto del posto va ai tipi «modello». I tipi:

    | Tipo | Cosa cambia | Chi lo deve trovare |
    |---|---|---|
    | `numero_una_lingua` | un numero, solo in italiano o solo in inglese | **codice** (`INCOERENZA_LINGUE`) |
    | `numero_manuale` | un numero che c'è nelle due lingue e nel manuale, cambiato in tutte e due con un valore che il manuale non ha | **modello** |
    | `negazione_una_lingua` | un «non» / «not» tolto in una lingua sola | **modello** |
    | `task_inesistente` | l'ultimo gruppo di un task cambiato in uno che non c'è, mentre i fratelli ci sono | **codice** (`TASK_INESISTENTE`) |
    | `negazione_due_lingue` | un «non» / «not» tolto in tutte e due le lingue | **modello** |
    | `limite_invertito` | minimo ↔ massimo, almeno ↔ al massimo (e min ↔ max), in tutte e due le lingue | **modello** |

    I tipi «codice» li trova il codice con la stessa regola che li ha messi: dicono solo che
    non si è rotto niente. **La generalizzazione la misurano i tipi «modello» e il gruppo
    nascosto** (`CODE_KINDS` in `blind.py`);
  - **gruppo nascosto**: stampe con errori messi a mano dall'utente o da un collega, in
    `data/nascosti`, con gli errori in `data/errori-nascosti.yaml`. Claude non li vede mai.

  I report dei mai visti danno **solo i conteggi per tipo**, mai quali sono. Non si mandano
  foto di `runs/mutazioni/errori.yaml`, `data/errori-nascosti.yaml` o delle stampe nascoste.

**Due insiemi:**

- **piccolo** (`runs/prove-piccolo`): i 10 cicli noti, le copie cieche, il gruppo nascosto.
  Ogni miglioria passa da qui;
- **grande** (`runs/prove-grande`): i 10 noti più tutti i cicli veri civili confrontabili. Per
  i falsi errori; solo per le migliorie che si tengono sul piccolo.

Le prove si confrontano solo sugli stessi cicli: il riepilogo mostra l'impronta dell'insieme
(colonna «Cicli») e avvisa se in una cartella sono diversi. Quando cambiano il seme o la
conoscenza, le prove vecchie si archiviano.

**La variante e la sua proposta.** Ogni file di `eval/varianti/` dice, oltre a cosa cambia
nelle impostazioni:

```yaml
nome: effort_medio
descrizione: ragionamento medium nei controlli invece di low      # cosa cambia
ipotesi: "con low il modello a volte non vede le frasi al contrario"  # perché dovrebbe migliorare
atteso: "più errori stabili; costo sotto il doppio della base"     # cosa deve cambiare nei numeri
base: baseline
agent:
  effort: medium
```

Un valore con `: ` dentro va tra virgolette. Un test controlla che ogni variante del
repository abbia tutti e tre i campi. `eval prova --variante` copia la proposta nella prova
(`prova.json`, campo `proposal`):

- in cima a `prestazioni.md`, sezione «La proposta» (senza variante, per esempio la base:
  «Nessuna variante»);
- nel `riepilogo.md`, tabella «Le proposte e la decisione»: per ogni variante cosa cambia,
  ipotesi, atteso e la decisione della regola.

Il `riepilogo.md` ha anche (dal 26-11) la tabella **«ERRATO da verificare»**: gli ERRATO fuori
dalla lista nei cicli veri e nei cicli con errori, per ciclo e operazione, con in quante prove
di ogni variante sono usciti e il motivo (dal 27-11 notte, MG82: per esempio
`INCOERENZA_LINGUE`, `DR_DIVERSO`). Solo impronta, operazione, motivo e numeri, senza testo: si
fotografa, e una persona guarda quelle operazioni sul ciclo (errore vero o falso errore). Anche
a schermo, nella riga di ogni ciclo, accanto a ogni `ERRATO in più` c'è il motivo:
`ERRATO in più 050 (INCOERENZA_LINGUE)`.

Dal 27-11 notte il `riepilogo.md` ha anche le **«Metriche di controllo»**, per variante su
tutte le sue prove: **falsi OK** (errori noti mancati con CORRETTO: i più pericolosi, devono
essere 0), errori mancati come WARNING e come N/A, **esiti decisi** (nei cicli giusti e veri,
la parte dei controlli con OK o ERRATO; il resto è lavoro a mano), **errori tecnici** del
modello, ciclo più lento e più caro. Si calcolano da `prova.json`: ricalcolando il riepilogo
escono anche per le prove vecchie.

Le **considerazioni** (cosa si è capito, cosa fare dopo) le scrive Claude nel registro di
`MEMORIA.md` (sezione 16), quando la variante è decisa. Così proposta, risultati
e decisione stanno sul PC in `runs/` (che git ignora), e nel repository restano solo la
proposta e le conclusioni, senza dati veri.

**La campagna** (`eval campagna`, `evaluation/campaign.py`, COPILOT 3.5). Lancia da sola
tutte le prove dell'elenco `eval/campagna.yaml`:

```yaml
varianti: [elementi_uno_per_uno, lingue_separate, ...]  # la base si fa sempre per prima
ripetizioni: 3
modelli: {haiku: }    # vuoto = quello delle impostazioni; sonnet: eu.anthropic.claude-sonnet-5-5
insiemi: [piccolo, grande]
grande: se_si_tiene   # sempre | mai
massimo_dollari: 15
riferimento: quasi_finale   # facoltativo: la variante con cui si confrontano le altre
```

- **Il riferimento (dal 28-11).** Le decisioni («si tiene», «non si tiene») si prendono contro
  la base, oppure contro la variante scritta in `riferimento`. La campagna lo scrive in
  `riferimento.txt` nelle cartelle delle prove, così anche `riepilogo.md` lo usa; senza il
  campo il file si toglie e si torna alla base. Serve quando la base ha prove fatte con il
  codice di prima (28-11: le prove di `quasi_finale` sono quelle di oggi).

- Per ogni modello, in ordine: base e varianti sul piccolo; poi sul grande la base e le varianti
  che sul piccolo «si tengono» (`se_si_tiene`). Il modello della campagna sostituisce
  `agent.model` di base e varianti.
- Cartelle: il primo modello del file usa `runs/prove-<insieme>` (contano anche le prove fatte a
  mano), gli altri `runs/prove-<insieme>-<modello>`, con una base loro: una variante si
  confronta solo con la base dello stesso modello.
- Insiemi come la prova a mano (COPILOT 3.7): il grande è `runs/prove-grande/cicli.txt` (3.2); il piccolo
  sono i cicli di quella lista che sono in `eval/errori-noti.yaml`, più le copie cieche
  (`runs/mutazioni`) e il gruppo nascosto (`data/nascosti`), se ci sono. La conoscenza è
  l'ultima fotografia (`eval/casi/aziendali/conoscenza/foto-*`, `.../civil/current.json`).
- Le prove già fatte (stesso nome nella cartella) si contano e non si rifanno: una campagna
  interrotta, rilanciata, riparte da dove era.
- Si ferma da sola al tetto di spesa (somma dei costi delle prove), se una prova non esegue
  nessun ciclo (la prova si cancella: di solito l'accesso AWS è scaduto) o con Ctrl+C; in ogni
  caso scrive il report.
- **Prova in cui il modello non ha risposto** (25-11): con l'accesso AWS scaduto i cicli
  girano lo stesso, ma ogni controllo del modello finisce in WARNING `ERRORE_TECNICO` e la
  prova costa 0 $. Una prova così non misura niente: `Trial.unusable` è vera se almeno 5
  controlli del modello (`decided_by` agent) e più del 20% di quelli della prova sono finiti
  in errore tecnico. Gli errori tecnici del codice (una fonte, un servizio) non contano. Una
  prova così non entra nel riepilogo né nel conto delle prove fatte (`load_trials` la salta);
  la campagna la cancella appena finita e si ferma con «il modello non ha risposto (N
  controlli …) · Primo errore: …» (il primo guasto, senza ARN né numeri di account); al lancio
  dopo cancella quelle rimaste e le rifà. Per le prove scritte prima del 25-11, che non hanno
  il conto dei controlli del modello, non vale solo una prova a zero token con almeno 5 WARNING
  `ERRORE_TECNICO` (dal 26-11: il 25-11 la regola contava tutti i WARNING per errore tecnico,
  e sul PC le targhe ne danno circa 8 per ciclo perché Redshift non si raggiunge; così le prove
  buone del 24-11 di Haiku sono state cancellate). Un ciclo **non eseguito** non ha il conto
  dei controlli ma non fa della prova una prova vecchia (dal 27-11: prima una prova con un ciclo
  non eseguito e il modello che non rispondeva restava buona, e la variante risultava scartata
  invece di rifare la prova). `eval prova` scrive `ATTENZIONE: prova non valida` in fondo.
- Il report `runs/campagna.md`: per ogni modello e insieme la scelta migliore e la classifica
  (prove, stabili, mai visti per il modello stabili, falsi errori, falsi OK a prova (dal
  28-11), da verificare, costo e tempo per ciclo, decisione); i modelli a confronto, variante per variante; gli errori mai
  visti per tipo, con cosa ha risposto la v2 sui mancati, e i WARNING per motivo, tutti e due
  nell'ultima prova della scelta migliore di ogni insieme (piccolo e grande). Fino al 28-11
  guardavano l'ultima base sul piccolo, anche quando le prove della base erano fatte con il
  codice di prima. Poi (MG83, 28-11) i WARNING operazione per operazione nei cicli senza errori
  noti: impronta, numero dell'operazione, controllo e motivo (`CycleScore.warning_ops`): da qui
  si sceglie che cosa tagliare. Le prove scritte prima li prendono dal loro `report.json` con
  `eval riepilogo --attesi`.
- Le cartelle delle prove hanno i secondi nel nome (`AAAAMMGG-HHMMSS-<nome>`, con `-2`, `-3`
  se due prove partono nello stesso secondo).
- **Due modelli insieme** (24-11): con `--modelli haiku` in un terminale e `--modelli sonnet`
  in un altro le due campagne girano in parallelo. Non condividono niente: cartelle diverse e
  report diversi (lanciata con `--modelli` o `--insiemi`, la campagna scrive
  `runs/campagna-<modelli>-<insiemi>.md` invece di `runs/campagna.md`). Il file `prova.json` si
  scrive accanto e poi si rinomina, e `load_trials` salta un file che non si legge: un
  terminale che legge mentre l'altro scrive non si ferma. Ogni report mostra tutti i modelli del file, con le prove che
  c'erano quando è stato scritto; la riga «Lanciati ora» dice quali modelli ha fatto girare e
  quanto ha speso. Il tetto di spesa vale per ogni terminale. `--solo-report` scrive
  `runs/campagna.md` con tutte le prove che ci sono, senza lanciarne (gratis): si usa quando
  tutti e due i terminali hanno finito.
  Sconsigliati quattro terminali (modello × insieme): il grande con `se_si_tiene` legge il
  piccolo quando parte e farebbe solo la base; due processi con lo stesso modello si dividono la
  quota Bedrock, e i controlli che vanno oltre `session_timeout_s` o finiscono i `retries`
  diventano WARNING per errore tecnico (numeri peggiori, senza crash).

**Metriche di una prova** (`prestazioni.md`):

| Metrica | Cosa misura |
|---|---|
| Trovati | errori noti con un ERRATO sulla loro operazione, a parte visti, mai visti per il modello e mai visti per il codice |
| Mancati | errori noti senza ERRATO, con quello che ha detto la v2 |
| Falsi errori | ERRATO nelle stampe giuste: deve essere 0 (non contano le operazioni `in_attesa`) |
| Da verificare | ERRATO fuori lista, nei cicli con errori e nei cicli veri |
| Precisione | trovati / tutti gli ERRATO |
| Warning per ciclo senza errori | lavoro a mano che resta sui cicli giusti e veri |
| Costo e tempo per ciclo | medi, più il ciclo più lento |
| Token riletti dalla cache | per capire se la cache dei prompt funziona (costano circa un decimo) |
| Non eseguiti | cicli andati in errore |

**Regola di scelta** (`riepilogo.md`, su una variante = prove con lo stesso nome):

1. **scartata** se: un falso errore, un ciclo non eseguito, un ciclo oltre 10 minuti, costo per
   ciclo oltre 2 volte la base;
2. **da ripetere** se ha meno di 2 prove;
3. **non si tiene** se dà più **falsi OK** della base (errori noti mancati con CORRETTO, in
   media per prova; dal 28-11, per MG83: togliere WARNING non deve far dire OK a un errore);
4. **classifica**: errori stabili (trovati in tutte le prove), trovati minimo, trovati medio,
   meno da verificare, meno warning, meno costo, meno tempo;
5. **si tiene** se non perde errori stabili, **non perde errori mai visti per il modello
   stabili** (altrimenti «non generalizza») e: trova **più errori stabili** della base, oppure
   trova gli stessi con un **risparmio vero** (costo per ciclo almeno 10% in meno, tempo almeno
   20% in meno o almeno 1 WARNING per ciclo in meno: `MIN_COST_SAVING`, `MIN_TIME_SAVING`,
   `MIN_WARNING_SAVING`). Con gli stessi errori e differenze più piccole è **«pari alla
   base»** e non si tiene (dal 24-11 sera: prima bastava stare sopra la base in classifica, e
   quattro varianti «si tenevano» per 0,2 WARNING o il 3% di costo, finendo anche sul grande).

**Provare una miglioria senza campagna** (28-11). Una campagna serve solo se la miglioria
cambia quello che fa il modello. Per il resto:

| La miglioria cambia | Come si prova | Costo |
|---|---|---|
| solo il codice dei controlli (per esempio MG48) | `eval senza-modello --variante`: gli errori che il codice trova senza modello li trova in ogni prova | 0 $, minuti |
| solo gli esiti già fatti (regole finali, MG83) | `eval rigioca`: le stesse risposte del modello delle prove di riferimento, con la regola in più | 0 $, secondi |
| il modo di chiamare il modello, con le stesse risposte (per esempio la cache) | una prova sola (`eval campagna --varianti X --insiemi piccolo --ripetizioni 1`): costo e tempo cambiano poco da una prova all'altra | una prova |
| il modello, il prompt o le sessioni | la campagna, 3 prove: le risposte cambiano da una prova all'altra | 3 prove per insieme |

Una prova sola conta come la prima delle tre: la campagna dopo fa solo quelle che mancano.

Le copie cieche (`eval muta`) sono tutte diverse: se due stampe dello stesso ciclo danno la
stessa copia, la seconda si salta (24-11: 41 copie scritte ma 39 diverse, perché due avevano
la stessa impronta).

I tipi del modello (`numero_manuale`, le negazioni, `limite_invertito`) si mettono solo su
operazioni che la v2 può confrontare con il manuale (`blind.comparable`, dal 26-11): i task
citati sono nella conoscenza e c'è un testo di riferimento, guardando l'operazione da sola come
nella copia. Il 25-11, 22 dei 26 mai visti mancati della base uscivano WARNING `FONTE_ASSENTE`:
erano su operazioni il cui task non è nella conoscenza, e nessuno poteva trovarli. I tipi del
codice si mettono dappertutto. Con lo stesso seme le copie cambiano rispetto a prima del 26-11:
si rifanno con un seme nuovo.

**Come si scelgono le migliorie (dal 23-11):** non dagli errori noti che mancano. Si fa la
base, si guarda nel report la tabella «Errori mai visti, per tipo» (trovati per tipo e, sui
mancati, cosa ha risposto la v2: solo esito e motivo contati, per esempio `CORRETTO 12`, mai
l'operazione o la spiegazione) e si sceglie una miglioria
per il tipo «modello» trovato peggio. Le varianti pronte sono in `eval/varianti/`; la lista è
in `MIGLIORIE.md` (stato ⬜).

---

## 16. Pubblicare in QA e in produzione

- `buildspec.yml` (nella radice del repository aziendale) costruisce l'immagine di una
  cartella. Oggi è quella della v1. develop = QA, main = produzione.
- **`cycle-validation qa`** (`deploy.py`), sul PC, dalla cartella della v2:
  - legge dalla v1 la riga `FROM` e le istruzioni sui certificati del Dockerfile, il `.whl` di
    `chatbot_ai_sdk` dei requirements (copiato in `vendor/`), il nome del secret di ambiente,
    il database e la tabella delle macchine;
  - scrive il Dockerfile della v2 con le righe `ENV` (`CV_ENV_SECRET`, `MACHINES_SOURCE=diretta`,
    `REDSHIFT_DATABASE`, `MACHINES_QUERY`, `CYCLE_VALIDATION_CONFIG`, i puntatori della
    conoscenza, `EJ200_VALIDATION_ENABLED`, `API_INCLUDE_TRACEBACK=false`);
  - copia `data/settings.yaml` in `config/settings.azienda.yaml` con i transcript spenti;
  - sposta ogni percorso del buildspec sulla cartella della v2; `--torna-alla-v1` lo rimette.
- Primo passaggio **con EJ200 spento**: la conoscenza EJ200 non si può controllare dal PC.
- La **pull request** verso `develop` fa passare QA alla v2. Quando il ramo arriva su `main`
  anche la produzione passa alla v2: **prima serve una prova QA riuscita.**
- Il Dockerfile del repository personale resta generico (Python 3.14, gunicorn, extra `aws` e
  `redshift`): in azienda vale quello scritto da `qa`.

I passi da fare sono in `COPILOT.md`, sezione 7.

---

## 17. Regole sui dati e sicurezza

- **EJ200:** documenti e output restano su AWS EU. Nessuna copia della conoscenza EJ200 sul
  PC; nei documenti nessun contenuto EJ200. Dal 27-11 l'utente è autorizzato a provare i cicli
  EJ200 sul suo PC, **solo** con `prova-ej200` (sezione 14.4): testi in una cartella temporanea
  cancellata alla fine, niente in `runs/`, a schermo solo esiti e conteggi.
- **Repository pubblico:** mai bucket, account, host, ARN, nomi o valori di secret, matricola o
  utente Windows, codici di manuali (si scrivono M1…M6), numeri DR, serial o part number,
  codici dei cicli, profilo AWS, database, tabella delle macchine, repository aziendale.
  Negli esempi valori inventati. Si possono scrivere: capitoli, sezioni e task (`72-56-32`),
  impronte dei PDF.
- **Dati veri solo in cartelle che git ignora:** `data/`, `runs/`, `eval/casi/aziendali/`,
  `eval/casi/mutazioni/`, `eval/risultati/`, `.env`, e tutta `docs/` tranne
  `DOCUMENTAZIONE.md` (esempi, foto, materiale di lavoro). Gli altri tre file di `docs/`
  erano già in git e restano seguiti: la regola vale per i file nuovi.
- **Nelle foto** possono comparire bucket, codici, percorsi con la matricola: Claude non li
  ripete. `report.md` non si manda (contiene i testi dei manuali).
- **Nei log e negli errori** del programma: mai valori di secret, mai testo del ciclo o dei
  manuali (al client va solo il tipo dell'errore; i guasti della pipeline non portano testo).
- **Copilot** in modalità Ask; non legge `data/`; la regola non si aggira.
- Prima di ogni commit Claude controlla il diff: numeri di 6 cifre o più, codici di manuali.

---

## 18. Le cartelle e i file

```
config/settings.yaml            impostazioni (sezione 12)
config/profiles/                mos.yaml, dr.yaml, ej200.yaml
prompts/                        operation_check.md, extract_cycle.md, extract_cycle_ej200.md
eval/errori-noti.yaml           errori noti dei cicli di prova (per impronta, senza codici veri)
eval/varianti/                  le varianti (baseline, effort_*, conferme_1, testo_lungo, ...)
eval/casi/sintetici/            golden set inventato (mos, dr)
eval/modelli/aziendali/         modelli di suite per i casi veri
examples/sintetico/             un ciclo e una conoscenza inventati, per provare tutto offline
tests/                          la suite (offline), con finti per ogni servizio
Dockerfile                      immagine generica
src/cycle_validation/
├── cli.py                      tutti i comandi (sezione 14)
├── pipeline.py                 la pipeline (sezione 5)
├── config.py                   impostazioni e profili, validati
├── errors.py                   errori con messaggi leggibili
├── module_kind.py              MOS, DR o militare dalla testata
├── selection.py                scelta iniziale civile/militare, MOS/DR
├── golden.py                   golden set e concordanza
├── deploy.py                   comando qa
├── text.py                     normalizzazione di codici e testi
├── domain/                     ciclo, esiti e motivi, report
├── ingest/                     PDF (PDFium), immagini e scansioni (trascrizione)
├── extract/                    parser PVRM320, estrazione con il modello, integrità
├── resolve/                    dove stanno documenti e task (civile, DR)
├── kb/                         conoscenza: porta, locale, pubblicata, EJ200, testo dei task
├── checks/                     i controlli (sezione 6)
├── agent/                      porta, SDK, runner, hook GRASP, prompt
├── verdict/                    citazioni e consolidamento
├── report/                     report.json, report.md, payload, lista dei manuali
├── services/                   macchine attive, Redshift
├── api/                        servizio FastAPI, accesso, sessioni e feedback su S3
├── evaluation/                 esperimenti, prove, copie cieche, fotografie
└── testing/                    PDF sintetici per i test
```

Sul PC, in più (ignorate da git): `data/` (impostazioni vere, conoscenza scaricata, macchine,
gruppo nascosto), `runs/` (risultati, prove, copie cieche, liste dei cicli).

---

## 19. Test e verifiche

```bash
uv sync --all-groups --extra aws
uv run pytest -q              # la suite, offline
uv run ruff check .           # stile
uv run ruff format --check .  # formato
uv run mypy src               # tipi (strict)
```

Si lanciano tutte e quattro prima di ogni commit. `tests/test_copilot_blocks.py` controlla
che i blocchi *Aggiornare* e *Salvare* di `COPILOT.md` portino sul PC e mettano in git tutto
quello che il codice e i test leggono (`src`, `tests`, `prompts`, `config`, `examples`,
`eval/errori-noti.yaml`, le cartelle di `eval/`, `pyproject.toml`, `uv.lock`). La suite non usa rete né credenziali: ogni
servizio esterno ha un finto (`tests/fakes.py`). Due test si saltano da soli: la prova con il
modello vero (`pytest -m live`, solo dove ci sono le credenziali) e quella sulle stampe di
esempio in `docs/Esempio*/` (solo se le cartelle ci sono).

Test importanti da conoscere:

- `test_kb_contract.py`: ogni adattatore della conoscenza deve rispettare la porta;
- `test_e2e_formato_reale.py`: dal PDF al payload del frontend, con una conoscenza nel formato
  vero (valori inventati);
- `test_e2e_mos.py`, `test_e2e_dr.py`: i due flussi civili per intero;
- `test_hooks.py`: le regole GRASP;
- `test_eval_guasti.py`: un guasto non diventa mai ERRATO.

Python: il progetto chiede 3.12 o più; sul PC si usa 3.14. `.python-version` chiede 3.13:
con un altro Python si scrive, in ogni terminale nuovo, `$env:UV_PYTHON = "3.14"`
(altrimenti uv risponde `No interpreter found for Python 3.13`).

**Prima prova con Bedrock, sui dati inventati** (dice una cosa sola: il modello risponde):

```bash
uv run cycle-validation kb-check examples/sintetico/knowledge
uv run cycle-validation run examples/sintetico/ciclo.pdf --cycle-json examples/sintetico/ciclo.json --knowledge examples/sintetico/knowledge --machines examples/sintetico/macchine_attive.json --config config/settings.yaml
uv run cycle-validation golden eval/casi/sintetici/mos --knowledge examples/sintetico/knowledge --machines examples/sintetico/macchine_attive.json --config config/settings.yaml
uv run pytest -m live
```

Deve uscire: un elenco che finisce con `recommendation_dr_incerte: 0`; `Ciclo completo: ...`
in 10-20 secondi; la concordanza del golden set; `1 passed`. Se **tutte** le operazioni escono
«errore tecnico», il modello non risponde: accesso AWS, regione, `agent.model`.

---

## 20. Limiti noti e regole da rivedere

**Cose che oggi mancano** (non sono difetti del codice):

- alcuni manuali e capitoli non sono nella conoscenza: le righe che ne hanno bisogno escono
  WARNING `FONTE_ASSENTE`, ed è giusto;
- sul PC le macchine attive non si leggono: le targhe escono N/A `CONTROLLO_SPENTO` (dal 27-11;
  prima WARNING e il ciclo `parziale`);
- EJ200 non è mai stato provato con i servizi veri: si prova sul PC con `prova-ej200` (dal
  27-11), poi in QA;
- il modello non risponde sempre uguale sullo stesso testo: per questo c'è la conferma degli
  ERRATO e le prove si ripetono almeno 2 volte.

**Con 2900 documenti** (`eval scala`, conoscenza finta, 27-11; sul PC e in AWS i tempi cambiano):

| | 75 documenti | 2900 documenti | 2900, manifest senza righe |
|---|---|---|---|
| Disco | 14 MB | 559 MB | 559 MB |
| Avvio (copia e lettura) | 0,1 s | 4,2 s | 7,7 s |
| Riavvio con la versione su disco | 0,0 s | 1,0 s | 2,5 s |
| Memoria | 4 MB | 164 MB | 248 MB |
| Task dell'indice | 3 µs | 6-9 µs | 6-9 µs |
| Task fuori indice (testo) | 18 ms | 25 ms | 25 ms |
| Fratelli di un codice del capitolo 70 | | 0,7 s la prima volta, 0,07 s dopo | |

Non misurati: il download da S3 e la qualità dell'ingestion (task tagliati male portano falsi
errori: per questo la prova di controllo sul grande).

**Regole scelte senza tutti i dati veri, da rivedere con chi conosce i cicli:**

| Regola di oggi | Se è sbagliata |
|---|---|
| DR: un serial number con una sola recommendation vale per qualunque condition | si applica una recommendation a una condition non prevista |
| DR: `Accept as is` (anche `Accept-as-is`, `Use as is`) e `Reject` riconosciuti per nome | un'altra parola per la stessa disposizione passa come riparazione normale |
| DR: `Reject` e `Accept as is` = ERRATO e ciclo bloccato, come nella v1 | un ciclo con `Accept as is` che contiene solo ispezioni esce ERRATO lo stesso |
| DR: serial number non indicato = quello scritto nella stampa (`APPLY ON S/N`), se ce n'è uno solo | un altro numero scritto dopo `S/N` viene preso per serial number |
| DR: condition non indicata e recommendation diverse per lo stesso serial number = WARNING `DR_NON_VERIFICATA`, si prosegue con le sole `Repair` | un pezzo da scartare passa con un WARNING invece di un ERRATO |
| DR: nessuna recommendation trovata = ERRATO | dati DR incompleti danno ERRATO invece di WARNING |
| Scheda presente ma famiglia del motore non riconosciuta = CORRETTO, con nota | passa una scheda di un'altra famiglia |
| MOS: la fonte è l'OEM del piè di pagina più il task letto dalle NOTE | note scritte in altro modo danno fonti mancanti |
| EJ200: le fonti sono i codici RDR, RN ed EF nel testo (dopo la sigla, o RN/EF da soli) | una fonte scritta in un altro modo non viene trovata |
| Stesso numero di operazione = stessa operazione, anche su pagine diverse | due operazioni distinte diventano una |
| Si leggono solo la prima SCHEDA e il primo SP.ORIG / SP.FIAT di ogni operazione | le successive non vengono controllate |
| EJ200: il paragrafo citato si legge solo accanto al codice (`PAR.`, `FIG.`, `TAB.`, `STEP`…) | un paragrafo scritto altrove non viene mostrato |
| PDF misto testo e scansione: si legge solo il testo | le operazioni delle pagine scansionate mancano, senza avviso |
| Oltre il 20% di parole della descrizione assenti dal PDF: niente modello, WARNING | soglia da tarare sui PDF veri |
| Chi ha solo `cv_ej200` può usare anche le rotte civili | come nella v1: chi vede i militari vede anche i civili |
| Elenco delle macchine attive vuoto = «registro non disponibile» (WARNING) | è voluto: un guasto non diventa ERRATO |

**Cose scritte senza dati veri, da guardare una volta:**

| Cosa | Dove si corregge | Come ti accorgi che è sbagliata |
|---|---|---|
| Id del modello | `agent.model` | tutte le operazioni «errore tecnico» |
| Come si riconosce un DR dalla testata | `module_check.dr_markers`; `[]` smette di distinguere MOS da DR | i DR veri rifiutati come «ciclo civile MOS» |
| Query delle macchine attive | `MACHINES_QUERY` | targhe giuste segnate «non attiva» (ERRATO) |
| La colonna TARGA della stampa è la targa da verificare | `extract/pvrm320_report.py` | esiti sulla macchina sbagliata |
| Nomi con cui i cicli citano manuali e documenti (LEAP compresi) | `aliases.json` accanto a `current.json`, lato knowledge-index | fonti valide segnate «non trovate» |

**Attenzione alle targhe:** una targa che non è tra le macchine attive dà ERRATO. Se l'elenco
delle attive è incompleto escono ERRATO falsi: i primi risultati in servizio vanno guardati a
mano.

**Domande aperte alle persone:** in `COPILOT.md`, sezione 6.1.

---

## 21. Se qualcosa non va

| Cosa vedi | Causa probabile | Cosa fare |
|---|---|---|
| il servizio non parte e nomina una variabile | variabile mancante o sbagliata | sezione 13.6 |
| `Configurazione di produzione non valida` | manca la sorgente delle macchine o una variabile Redshift | sezione 13.6 |
| `boto3 non è installato` | installato senza `--extra aws` | `uv sync --all-groups --extra aws` |
| il servizio non parte e nomina un file della conoscenza | pubblicazione non valida | `kb-check` sulla versione |
| EJ200 risponde 503 «profilo spento», MOS e DR vanno | conoscenza EJ200 non valida (MG44) | `kb-check` sulla versione EJ200, poi ripubblicare |
| tutte le operazioni «errore tecnico» | Bedrock non risponde | `aws sso login`, regione, `agent.model` |
| «meno di 100 caratteri di testo (è una scansione?)» | il PDF è una foto | `agent.transcribe_model` |
| «Modulo sbagliato» su un file giusto | marcatori DR | `module_check.dr_markers` |
| molte targhe ERRATO | elenco macchine incompleto o scritto diverso | sezione 20, «Attenzione alle targhe» |
| molte targhe WARNING «Registro macchine non raggiungibile» | Redshift non risponde o query sbagliata | con `diretta`: secret, rete verso il cluster, `REDSHIFT_DATABASE`, `MACHINES_QUERY`; con `data_api`: permessi `redshift-data`. Intanto `MACHINES_FILE` |
| `MACHINES_SOURCE=diretta: serve redshift_connector` | installato senza l'extra `redshift` | `uv sync --extra aws --extra redshift` |
| `Nessun caso rivisto` | casi ancora in bozza | revisione (sezione 15.2) |
| `verifiche del codice fallite` | test, ruff o mypy rossi | il dettaglio è stampato sopra; nessuna prova è partita |
| `NON regge` sotto i guasti | un guasto è diventato ERRATO | difetto del codice: tenere il file dei risultati |

Gli errori visti sul PC aziendale, con la soluzione, sono in `MEMORIA.md`, sezione 11.

**Cosa non toccare.** Rendono affidabile il risultato e costano millisecondi: la verifica che i
valori letti compaiano nel PDF, la verifica che ogni citazione del modello esista nel manuale a
quella riga, l'esito deciso dal codice e non dal modello, un guasto che dà WARNING e mai ERRATO.

---

## 22. Come si aggiorna questo file

- Claude lo aggiorna **nello stesso commit** in cui cambia una regola, un controllo, un
  comando, un'impostazione o una rotta.
- Qui va **come funziona**. La storia (cosa si è visto, quando, perché) va in `MEMORIA.md`;
  cosa fare sul PC in `COPILOT.md`; le idee in `MIGLIORIE.md`.
- Solo valori inventati. Prima del commit: le quattro verifiche della sezione 19 e il
  controllo del diff della sezione 17.
