# Documentazione del progetto

Questo file spiega **tutto il progetto**: a cosa serve, come è fatto, come funziona ogni pezzo,
dove sta il codice, come si prova e come si pubblica. È scritto per chi lo legge la prima
volta e per chi deve ritrovare un dettaglio.

Ultimo aggiornamento: 24-11-2026. Claude lo aggiorna quando cambia il funzionamento del
programma: regole, controlli, comandi, impostazioni.

Gli altri documenti in `docs/`:

| File | A cosa serve |
|---|---|
| `DOCUMENTAZIONE.md` | questo file: com'è fatto e come funziona tutto il progetto |
| `COPILOT.md` | il lavoro sul PC aziendale: cosa fare adesso, i blocchi PowerShell da lanciare |
| `MEMORIA.md` | la storia: cosa si è visto, i problemi già risolti, le decisioni prese |
| `MIGLIORIE.md` | cosa migliorare, in che ordine, metriche e registro delle prove |
| `AZIENDA.md` | guida tecnica: installare, configurare, avviare il servizio, formato della conoscenza |

Il repository è pubblico: qui ci sono **solo valori inventati**. Niente nomi di bucket,
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
21. [Come si aggiorna questo file](#21-come-si-aggiorna-questo-file)

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
| **Variante** | un file `eval/varianti/<nome>.yaml` che cambia una cosa sola delle impostazioni |
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
  PRECEDENTE ***`, banner `*** C O N T I N U A ***`);
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
`machine_tag`, `task_codes`, `process_sheet`), dati DR. I segnaposto come `-`, `N/A`, `nessuno`
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

Nessuna targa: N/A. Elenco delle attive non raggiungibile: WARNING `ERRORE_TECNICO` (mai
ERRATO). La targa è la riga sopra nella colonna TARGA; la riga sotto (centro responsabile) non
si controlla.

### 6.4 `process_sheet`: la scheda esiste (`checks/process_sheet.py`)

- Nessuna scheda: N/A `CAMPO_ASSENTE`.
- EJ200: N/A `NON_VERIFICATO_PER_PROFILO`.
- Prefissi esclusi (`SWJ`, `SSS`, `SPS`): N/A `ESCLUSO_DA_REGOLA`.
- I codici si confrontano senza spazi, trattini né maiuscole (`CPEC 100-BR` = `CPEC100BR`).
  `PG 300` è un codice a sé.
- Non trovata: WARNING `FONTE_ASSENTE`.
- Trovata ma non per la famiglia del motore (GENX, LEAP): WARNING `EVIDENZA_NON_TROVATA`.
- Trovata: CORRETTO. Se la scheda non elenca famiglie o la famiglia non si riconosce, il testo
  dice «applicabilità non verificata».

### 6.5 `operation_description`: la descrizione è d'accordo con il manuale (`checks/operation.py`)

È **l'unico controllo che usa il modello**. Per ogni operazione, in ordine:

1. descrizione vuota: N/A `CAMPO_ASSENTE`;
2. descrizione non confermata dal PDF: WARNING `ESTRAZIONE_NON_CONFERMATA` (niente modello);
3. **le due lingue** (`checks/languages.py`, senza modello): se nello stesso punto l'italiano e
   l'inglese hanno **numeri diversi**: ERRATO `INCOERENZA_LINGUE`. Si conta solo una
   sostituzione (un numero al posto di un altro). Non contano: un numero in una sola lingua,
   le conversioni mm ↔ pollici (2%) e °C ↔ °F (±1), i codici fatti di cifre (con `/`, o di 5
   cifre o più, come i part number);
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
| `coerente` o `contraddetto` | nessuna | WARNING `CITAZIONE_NON_VERIFICATA` |
| `contraddetto` | almeno una | ERRATO `CONTRADDIZIONE` (da confermare, sotto) |
| `coerente` | almeno una | CORRETTO `VERIFICATO` |
| sessione finita senza risposta (passi esauriti) | — | WARNING `BUDGET_ESAURITO` |
| errore, tempo scaduto, output storto | — | WARNING `ERRORE_TECNICO` |

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
| nessun serial number (né dato né nella stampa) | WARNING `DR_NON_VERIFICATA` | vanno avanti, senza la procedura DR |
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
| | `INCOERENZA_LINGUE` | italiano e inglese con numeri diversi |
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
| | `ESTRAZIONE_NON_CONFERMATA` | il valore letto non compare nel PDF |
| | `BUDGET_ESAURITO` | la sessione ha finito i passi |
| | `ERRORE_TECNICO` | guasto: modello, rete, sorgente, tempo |
| | `BLOCCATO_A_MONTE` | non eseguito: il controllo DR ha fermato il ciclo |
| **N/A** | `CAMPO_ASSENTE` | il campo non c'è |
| | `ESCLUSO_DA_REGOLA` | escluso da una regola (prefissi delle schede) |
| | `NON_VERIFICATO_PER_PROFILO` | il controllo non vale per questo tipo di ciclo |

---

## 8. Stato del ciclo, conteggi, report

**Stato** (`cycle_status`):

- `bloccato`: un controllo bloccante è fallito;
- `parziale`: c'è un guasto (`ERRORE_TECNICO`, `BUDGET_ESAURITO` o un errore della pipeline).
  Sul PC è quasi sempre così, perché le macchine attive non si raggiungono;
- `completo`: altrimenti.

**Conteggi:** totale, corretti, warning, errati, N/A, e quota di errori (errati / righe non
N/A). Le righe di integrità non si contano.

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
inferenza `eu.` scritto in `data/settings.yaml` sul PC). Si usa il **Claude Agent SDK**:
l'unico modulo che lo importa è `agent/sdk_session.py`. Il resto del codice parla con la porta
`AgentSession` (`agent/session.py`) e si prova senza rete.

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
  riprovare.

**Ragionamento:** `effort: low` nei controlli (circa -30% di costo), `high` nella lettura del
PDF.

**Transcript:** con `save_transcripts: true` (solo negli esperimenti) il testo di ogni
sessione va in `runs/.../transcripts/`. Contiene cicli e manuali: nel servizio è spento.

---

## 10. La conoscenza

### 10.1 Da dove arriva

La prepara e la pubblica **knowledge-index** su S3. Il formato completo, con esempi inventati,
è in `AZIENDA.md`, parte D.

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
  Tiene su disco le ultime 3 versioni. All'avvio, se un file non è valido, il servizio **non
  parte** e dice quale.
- **EJ200** (`kb/ej200.py`): catalogo delle pubblicazioni e testi su S3, con cache a tempo. Il
  `code` del catalogo contiene la issue (`EJ00020L-01`): il programma la toglie, così le issue
  della stessa pubblicazione restano una. Un ciclo può citare una issue precisa o solo il
  codice (vale la più recente). **La conoscenza EJ200 non si scarica mai sul PC.**
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

---

## 11. Le macchine attive

L'elenco delle macchine in uso oggi viene da **Redshift**, come nella v1: la tabella della v1,
prima colonna la targa, filtro `work_center_usage_cd = 'TO'`. Su Redshift non si crea niente.

| `MACHINES_SOURCE` | Come | Dove |
|---|---|---|
| `diretta` | `redshift_connector`, con host, porta, utente e password del secret della v1 (riletto a ogni aggiornamento), database da `REDSHIFT_DATABASE`, query da `MACHINES_QUERY`, 20 s per collegarsi | **in servizio** |
| `data_api` | Redshift Data API (HTTPS), con workgroup o cluster | alternativa |
| `file` | `MACHINES_FILE`: JSON con una lista di targhe o `{"active": [...]}` | prove |
| `nessuna` | ogni targa WARNING «non verificabile» | **sul PC**: dal PC Redshift non si raggiunge |

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
| `agent.confirm_contradiction` | 2 | sessioni di conferma per ogni ERRATO del modello |
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
secret. L'elenco completo delle variabili è in `AZIENDA.md`, sezione 4.2.

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
| WARNING | `Warning: <motivazione>` | Warning giallo |
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
| `manuali <percorsi>…` | quali manuali servono nella conoscenza per i cicli di prova; con `--conoscenza` quali mancano e perché; codici veri solo nel file `--out` | no |
| `golden <cartella>` | esegue il golden set (casi con esiti attesi riga per riga) e stampa la concordanza | sì |

### 14.2 Prove sui cicli veri (sezione 15.3)

| Comando | Cosa fa | Costa |
|---|---|---|
| `eval scegli <cartelle>` | sceglie i cicli: prima quelli noti, poi i veri civili con almeno l'80% di operazioni confrontabili (`--copertura`), fino a `--quanti` (0 = tutti) | no |
| `eval muta` | fa le copie cieche: `--lista`, `--knowledge`, `--quanti`, `--seme` | no |
| `eval prova [pdf]…` | valida, confronta con gli errori noti, scrive `prestazioni.md` e `riepilogo.md`. `--nome`, `--variante`, `--lista` (ripetibile), `--attesi` (ripetibile), `--cartella` | sì |
| `eval riepilogo` | riscrive `riepilogo.md` della cartella | no |

### 14.3 Esperimenti con i casi rivisti (sezione 15.2)

| Comando | Cosa fa |
|---|---|
| `eval fotografia` | copia i prefissi S3 della conoscenza in una cartella datata |
| `eval prepara <caso>` | valida un ciclo vero una volta e scrive la bozza `expected.json` da far rivedere |
| `eval esegui --variante` | esegue una variante su tutti i casi e scrive i risultati grezzi |
| `eval classifica` | mette in classifica le varianti |
| `eval mutazioni` | copie dei casi rivisti con difetti noti o modifiche innocue |
| `eval pipeline` | tutto insieme: verifiche del codice, baseline, varianti, classifica |

### 14.4 Azienda

| Comando | Cosa fa |
|---|---|
| `macchine` | scarica le macchine attive da Redshift in `data/macchine_attive.json` (stampa solo il numero) |
| `qa` | prepara la pubblicazione in QA (sezione 16); `--torna-alla-v1` la annulla |

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
simula guasti e **regge** se nessun guasto diventa ERRATO. Dettagli in `AZIENDA.md`, parte B.

### 15.3 Prove sui cicli veri (`evaluation/trials.py`, `evaluation/blind.py`)

È il sistema usato adesso (COPILOT 2.3). Non serve rivedere ogni riga: si conoscono solo gli
**errori** di alcuni cicli.

**Tipi di ciclo:**

- `errori`: stampa modificata a mano, con errori noti (`eval/errori-noti.yaml`, per impronta);
- `giusto`: la stampa originale di un ciclo «con errori»: non deve dare ERRATO;
- `vero`: ogni altro ciclo vero: un suo ERRATO è «da verificare».

**Errori visti e mai visti:**

- **visti**: i 12 errori noti. Chi scrive le migliorie li conosce: una miglioria può
  «impararli a memoria»;
- **mai visti**: misurano se la v2 **generalizza**:
  - **copie cieche** (`eval muta`): da ogni ciclo vero il programma fa copie con **una sola**
    operazione cambiata, al massimo 2 copie per ciclo, sempre le stesse per lo stesso seme. I
    tipi:

    | Tipo | Cosa cambia | Chi lo deve trovare |
    |---|---|---|
    | `numero_una_lingua` | un numero, solo in italiano o solo in inglese | **codice** (`INCOERENZA_LINGUE`) |
    | `numero_manuale` | un numero che c'è nelle due lingue e nel manuale, cambiato in tutte e due con un valore che il manuale non ha | **modello** |
    | `negazione_una_lingua` | un «non» / «not» tolto in una lingua sola | **modello** |
    | `task_inesistente` | l'ultimo gruppo di un task cambiato in uno che non c'è, mentre i fratelli ci sono | **codice** (`TASK_INESISTENTE`) |

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

**Metriche di una prova** (`prestazioni.md`):

| Metrica | Cosa misura |
|---|---|
| Trovati | errori noti con un ERRATO sulla loro operazione, a parte visti, mai visti per il modello e mai visti per il codice |
| Mancati | errori noti senza ERRATO, con quello che ha detto la v2 |
| Falsi errori | ERRATO nelle stampe giuste: deve essere 0 |
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
3. **classifica**: errori stabili (trovati in tutte le prove), trovati minimo, trovati medio,
   meno da verificare, meno warning, meno costo, meno tempo;
4. **si tiene** se non perde errori stabili, **non perde errori mai visti per il modello
   stabili** (altrimenti «non generalizza») e sta sopra la base.

**Come si scelgono le migliorie (dal 23-11):** non dagli errori noti che mancano. Si fa la
base, si guarda nel report la tabella «Errori mai visti, per tipo» e si sceglie una miglioria
per il tipo «modello» trovato peggio. Le varianti pronte sono in `eval/varianti/`; la lista è
in `MIGLIORIE.md`, «Da provare».

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

I passi da fare sono in `COPILOT.md`, sezione 4.

---

## 17. Regole sui dati e sicurezza

- **EJ200:** documenti e output restano su AWS EU. Nessuna copia locale della conoscenza
  EJ200; un ciclo EJ200 non si prova sul PC; nei documenti nessun contenuto EJ200.
- **Repository pubblico:** mai bucket, account, host, ARN, nomi o valori di secret, matricola o
  utente Windows, codici di manuali (si scrivono M1…M6), numeri DR, serial o part number,
  codici dei cicli, profilo AWS, database, tabella delle macchine, repository aziendale.
  Negli esempi valori inventati. Si possono scrivere: capitoli, sezioni e task (`72-56-32`),
  impronte dei PDF.
- **Dati veri solo in cartelle che git ignora:** `data/`, `runs/`, `eval/casi/aziendali/`,
  `eval/casi/mutazioni/`, `eval/risultati/`, `.env`, e tutta `docs/` tranne
  `DOCUMENTAZIONE.md` (esempi, foto, materiale di lavoro). Gli altri quattro file di `docs/`
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

Si lanciano tutte e quattro prima di ogni commit. La suite non usa rete né credenziali: ogni
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

Python: il progetto chiede 3.12 o più; sul PC si usa 3.14.

---

## 20. Limiti noti e regole da rivedere

**Cose che oggi mancano** (non sono difetti del codice):

- alcuni manuali e capitoli non sono nella conoscenza: le righe che ne hanno bisogno escono
  WARNING `FONTE_ASSENTE`, ed è giusto;
- sul PC le macchine attive non si leggono: le targhe escono WARNING e il ciclo `parziale`;
- EJ200 non è mai stato provato con i servizi veri: va fatto dentro AWS;
- il modello non risponde sempre uguale sullo stesso testo: per questo c'è la conferma degli
  ERRATO e le prove si ripetono almeno 2 volte.

**Regole scelte senza tutti i dati veri, da rivedere con chi conosce i cicli** (l'elenco
completo è in `AZIENDA.md`, parte C):

- una DR con una sola recommendation vale per qualunque condition;
- serial number non indicato = quello scritto nella stampa, se è uno solo;
- MOS: la fonte è l'OEM del piè di pagina più il task delle NOTE;
- stesso numero di operazione = stessa operazione, anche su pagine diverse;
- si leggono solo la prima SCHEDA e il primo SP.ORIG / SP.FIAT di ogni operazione;
- PDF misto testo e scansione: si legge solo il testo;
- oltre il 20% di parole della descrizione assenti dal PDF: niente modello, WARNING;
- chi vede i cicli militari vede anche i civili (come nella v1).

**Domande aperte alle persone:** in `COPILOT.md`, sezione 3.1.

---

## 21. Come si aggiorna questo file

- Claude lo aggiorna **nello stesso commit** in cui cambia una regola, un controllo, un
  comando, un'impostazione o una rotta.
- Qui va **come funziona**. La storia (cosa si è visto, quando, perché) va in `MEMORIA.md`;
  cosa fare sul PC in `COPILOT.md`; le idee in `MIGLIORIE.md`.
- Solo valori inventati. Prima del commit: le quattro verifiche della sezione 19 e il
  controllo del diff della sezione 17.
