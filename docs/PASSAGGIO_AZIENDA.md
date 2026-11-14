# Passaggio in azienda

Cosa serve per portare Cycle Validation v2 dall'ambiente offline a quello aziendale: che cosa è
cambiato con la revisione critica, che cosa va configurato, che cosa è stato assunto senza poterlo
verificare. Il quadro dei moduli e l'elenco completo delle porte sono in
`docs/superpowers/COMPLETION_REPORT.md`.

Tutto il lavoro è stato fatto senza accesso ad AWS né a dati di produzione: ogni servizio esterno
sta dietro una porta (Protocol) con un sostituto deterministico, e nessuna delle voci qui sotto è
stata provata contro il servizio vero.

## 1. Prima di condividere il repository

Le fixture del parser PVRM320 contenevano identificativi reali copiati dagli esempi ignorati
(targhe, centri di costo, codici di scheda e di attrezzatura, codici di ciclo, un manuale OEM, un
RDR). Sul ramo `review/correctness-and-optimization` sono stati sostituiti con valori inventati
(commit `14106d5`), ma **la history li contiene ancora** nei commit `3fdb450`, `f061e51` e
`5e95a33`. La history non è stata riscritta. Va deciso prima di un push verso un remoto condiviso:
riscriverla, oppure ripartire da un repository nuovo con il solo stato finale.

I test sugli esempi reali leggono gli esiti attesi da `atteso.json`, in
`docs/Esempio ciclo mos/trascrizione/` e `docs/Esempio EJ200/trascrizione/`: cartelle ignorate da
git, da ricreare su ogni macchina che deve eseguire quei test (senza i file i test si saltano).

## 2. Impostazioni nuove o cambiate

| Dove | Voce | Valore | Perché |
|---|---|---|---|
| ambiente del servizio | `API_MAX_UPLOAD_MB` | 50 | tetto del file caricato su ogni rotta: 413 prima di leggere il file in memoria. I profili civili non avevano alcun limite |
| profilo (`file_limits`) | `max_transcribed_pages` | 60 | tetto delle pagine di una scansione: ogni pagina è un rendering e una chiamata a pagamento |
| `redshift_machine_registry` | `ttl_s` | 900 | l'elenco delle macchine attive si rilegge ogni 15 minuti; prima restava quello del primo caricamento fino al riavvio |
| `BedrockPageTranscriber` | `retries`, `backoff_s` | 2, 1.0 | nuovi tentativi sui soli errori transitori di Bedrock |
| `config/settings.yaml` | `agent.model` | `haiku` | impostare l'id del modello o del profilo di inferenza Haiku abilitato in `eu-south-1` |
| `config/settings.yaml` | `agent.transcribe_model` | vuoto | vuoto = solo PDF con testo. Per foto e scansioni indicare un modello multimodale |

`API_MAX_WORKERS` viene letta e validata ma **nessun codice la usa**: oggi non limita le
validazioni contemporanee. O la si collega a un semaforo nel runner, o la si toglie.

`API_INCLUDE_TRACEBACK` resta attiva per impostazione predefinita. Con la revisione il campo
`traceback` contiene solo tipi di eccezione e posizioni nel codice (file, riga, funzione), mai il
messaggio né le righe di sorgente. In produzione conviene comunque spegnerla.

## 3. Comportamenti cambiati che chi integra deve conoscere

- **Errori imprevisti.** La busta `state: failed` e la risposta 500 riportano
  `Errore interno (<Tipo>).` invece del testo dell'eccezione. Gli errori previsti
  (`CycleValidationError`: file non valido, sorgente non raggiungibile, selettori errati)
  mantengono il loro messaggio, scritto per l'utente. Se il frontend mostrava il testo grezzo
  dell'errore, ora mostra questo.
- **Registro macchine vuoto.** Una query che restituisce zero macchine attive è trattata come
  sorgente non disponibile (WARNING), non come "tutte le macchine sono inattive" (ERRATO).
- **Descrizione non confermata.** Se un numero della descrizione estratta non compare nel PDF, o
  manca più del 20% delle parole, l'operazione non va al modello: esito WARNING
  `ESTRAZIONE_NON_CONFERMATA`. La soglia del 20% è una scelta, da tarare sui PDF reali.
- **Codici per intero.** In modalità documento (EJ200) un codice è trovato solo se compare per
  intero: `72-31-0` non è più trovato dentro `72-31-00`.
- **Blocchi orfani nel PVRM320.** Un blocco senza numero di operazione ferma l'estrazione con un
  errore che indica la pagina, invece di essere scartato in silenzio.
- **Nomi dei file di lavoro.** I documenti EJ200 materializzati stanno in
  `<workdir>/ej200/<impronta>/<chiave>.md`; i nomi con caratteri non ammessi portano un'impronta.
  L'agente cita i documenti per nome di file: i nomi già puliti sono rimasti quelli di prima.
- **Concorrenza.** Controlli a codice e sessioni dell'agente partono insieme; la pianificazione
  delle sessioni gira in un thread. Le implementazioni di `KnowledgeBase` e `MachineRegistry`
  devono essere sicure tra thread (quelle fornite lo sono).

## 4. Punti di aggancio ancora aperti

Per ognuno esiste l'adattatore con client iniettato; manca solo il dato aziendale.

1. **Forma dei JSON su S3** (TM, SP, DR): prefissi in `StructuredLayout`, alias dei campi in
   `FieldMap`.
2. **Testo dei manuali civili: cartella su S3 nel formato locale** (`kb/snapshot.py`). OpenSearch
   non c'è più: l'ingestion pubblica `manifest.json`, `documents/*.md` (con `<!-- page N -->`) e
   `tasks.json` sotto un prefisso, e `SnapshotManualSource` li scarica una volta in una cartella
   di lavoro. Il formato è quello di `kb-check`; da verificare con lo snapshot reale di
   ingestion v2 (se le chiavi o i campi differiscono serve un piccolo convertitore, non altro).
3. **Dimensione dello snapshot.** Si scarica tutto il prefisso alla prima richiesta: con molti
   manuali grandi conviene un prefisso per programma o un download per documento.
4. **Catalogo EJ200** (`CatalogEntry`: `code`, `kind`, `issue`, `document_id`, `content_hash`,
   `published`, `partial`, `references`) e testo dei documenti: un markdown a righe per issue
   all'oggetto `<text_prefix><document_id>/<content_hash>.md` (`DEFAULT_TEXT_PREFIX`, da
   confermare con la pubblicazione reale).
5. **Query Redshift** delle macchine attive e intervallo di rilettura.
6. **Modello Haiku** in `eu-south-1`: id o profilo di inferenza; smoke test di una sessione vera
   (l'adattatore SDK è provato solo su messaggi simulati, versione 0.2.181).
7. **Trascrizione**: modello, limiti per immagine di Bedrock (assunti 3,75 MB e 8000 px per
   lato), configurazione dei tentativi del client boto3 (per non sommarli a quelli
   dell'adattatore).
8. **Autenticazione**: `AuthBackend` sopra `chatbot_ai_sdk.auth` (introspezione, permessi `cv` e
   `cv_ej200`).
9. **Cablaggio**: la `factory(config) -> ApiServices` da passare a
   `create_app_from_env(environ, factory)`. Quella predefinita solleva un errore esplicito.
10. **Golden set reale** e **confronto in ombra** con il sistema attuale (Fase 7).
11. **`mypy`**: su questa macchina non si carica (`DLL load failed`); va eseguito in azienda.

## 5. Assunzioni non verificate

Nessuna è stata modificata: sono scelte del codice che solo i dati reali possono confermare.
Per ognuna, il rischio se è sbagliata.

### Estrazione dal PVRM320

| Assunzione | Rischio |
|---|---|
| La colonna TARGA è la targa macchina da verificare | Se è altro, ogni operazione riceve esiti sulla macchina sbagliata |
| C.RESP non viene estratto | Se serve a un controllo, quel controllo non esiste |
| Fonte civile = OEM del piè di pagina + task letto dalle NOTE | Note con forma diversa (RIPARAZIONE vuota, NOTE in linea, testo in coda) danno fonti mancanti o errate |
| Fonti EJ200 = solo i codici RDR nel testo | RN ed EF non vengono estratti: le operazioni si confrontano con meno documenti |
| Un OEM che contiene `/` è un segnaposto e si ignora | Un manuale reale con `/` nel nome verrebbe perso |
| Numeri di operazione di tre cifre, colonna sinistra entro 22 caratteri | Stampe con altra impaginazione: operazioni non riconosciute (errore esplicito) o testo attribuito alla colonna sbagliata |
| Stesso numero di operazione = stessa operazione, unita su tutto il documento | Due operazioni distinte con lo stesso numero diventano una |
| La prima SCHEDA e il primo SP.ORIG di un'operazione valgono | Le successive non vengono verificate |
| Il layout di riferimento in `extract/pvrm320.py` (`OP 0010`, `MACHINE:`) | È inventato: sulle stampe reali lavora `pvrm320_report.py`; l'altro è probabilmente codice morto |
| Il profilo DR non usa il parser di layout (`layout_extractor: none`, fissato da un test) | Una chiamata al modello in più per ciclo. Abilitarlo è una riga di YAML, ma senza un PDF DR reale non è stato provato |

### Regole dei controlli

| Assunzione | Rischio |
|---|---|
| Una targa assente dall'elenco delle attive è "macchina non attiva" (ERRATO) | Una targa scritta in modo diverso o un elenco incompleto danno un ERRATO falso: targa sconosciuta e targa inattiva non si distinguono |
| DR: una sola recommendation per il serial vale qualunque sia la condition | Recommendation applicata a una condition per cui non era prevista |
| DR: `accept as is` e `reject` riconosciuti come stringhe esatte | Varianti di scrittura trattate come riparazione normale |
| DR: nessuna corrispondenza = ERRATO, per scelta di progetto | Dati DR incompleti danno ERRATO invece di WARNING |
| Scheda presente ma famiglia del motore non riconosciuta = CORRETTO (sola presenza) | Una scheda di un'altra famiglia passa come corretta; la motivazione ora dice che l'applicabilità non è stata verificata |
| La famiglia del motore si riconosce come sottostringa del modello | Una famiglia il cui nome è contenuto in un altro modello viene riconosciuta a torto |
| Citazione valida da 8 caratteri in su (`MIN_QUOTE_CHARS`) | Citazioni cortissime ma decisive vengono scartate (WARNING), mai accettate a torto |
| Integrità del numero di operazione: basta che compaia ovunque nel PDF | Controllo quasi sempre vero: non prova che l'operazione sia stata letta bene |

### Servizio

| Assunzione | Rischio |
|---|---|
| Chi ha solo il permesso `cv_ej200` può usare anche le rotte civili (un test lo fissa) | Se non è voluto, è un accesso più largo del dovuto |
| Solo `SourceUnavailableError` diventa un WARNING sul singolo controllo | Ogni altra eccezione in un controllo fa fallire l'intero run (mai un ERRATO, ma nessun risultato parziale) |
| I documenti letti dall'indice restano in memoria fino al riavvio, anche un risultato vuoto | Un manuale aggiornato o un indice momentaneamente vuoto non vengono riletti. Catalogo EJ200 (5 minuti) e macchine (15 minuti) invece scadono |
| PDFium non è sicuro tra thread: un solo lock per tutte le chiamate | Se è falso, si perde solo parallelismo nella lettura dei PDF |
| Un PDF con alcune pagine di testo e altre scansionate si legge solo con PDFium | Le pagine scansionate risultano vuote e le loro operazioni mancano, senza avviso |
| Per scansioni e foto la trascrizione è l'unica fonte | La verifica di integrità confronta l'estrazione con la trascrizione, non con la pagina: un errore di trascrizione non viene visto |
| `save_transcripts: true` | Le trascrizioni delle sessioni (testo del ciclo e dei manuali) finiscono su disco nella cartella del run: decidere dove va quella cartella nel servizio e per quanto si conserva |
| Tetto di caricamento di 50 MB | Scelto senza conoscere i file reali: va tarato |

### Scelta iniziale e modulo sbagliato (aggiunta del 14 novembre 2026)

Due rotte nuove, additive (le rotte storiche non cambiano):

- `GET /cycle_validation/validation/options`: albero delle scelte per i pulsanti del frontend
  (civile o militare; per il civile MOS o DR).
- `POST /cycle_validation/validation/upload`: file più `domain` (`civil` | `military`),
  `civil_type` (`mos` | `dr`, solo civile), `dr_serial_number` e `dr_condition` (solo DR).
  Scelta mancante o incoerente: 422 prima di leggere il file. Militare senza permesso
  `cv_ej200`: 403. Militare con `EJ200_VALIDATION_ENABLED` spento: 501.

Su **tutte** le rotte di caricamento e sulla CLI il file deve essere del tipo scelto: il tipo si
legge dalla testata della stampa (`module_kind.py`, senza modello) e un tipo diverso ferma il run
con 422 `Modulo sbagliato: hai scelto ..., ma il file caricato è ...`, prima dell'estrazione.
Testata non riconosciuta = nessun blocco. Impostazioni in `config/settings.yaml`, `module_check`.

| Assunzione | Rischio |
|---|---|
| "Ciclo militare" = profilo EJ200 | Se il militare comprende altri programmi, `selection.py` va esteso |
| Civile o militare si legge dal campo `PROGETTO` della testata (`EJ200` contro `GENX`, `LEAP`) | Verificato sulle due stampe di esempio (una MOS, una EJ200). Un progetto civile diverso da GENX e LEAP non viene riconosciuto: nessun blocco |
| Un ciclo DR ha in testata la parola `DR` o `DEPARTURE RECOMMENDATION` (`module_check.dr_markers`) | **Non verificato: nessuna stampa DR vista.** Se è falso, ogni ciclo DR caricato come DR viene rifiutato come "ciclo civile MOS". Correggere i marcatori, oppure lasciare la lista vuota per non distinguere MOS da DR |

Offline, `cycle-validation run` e `golden` provano comunque a chiamare il modello: senza
credenziali ogni operazione esce WARNING `ERRORE_TECNICO` dopo i tentativi (circa un minuto per
quattro operazioni). Il golden set con modello simulato gira in `tests/test_golden.py`.

## 6. Ordine consigliato

1. Decidere sulla history (sezione 1).
2. Scrivere la `factory` con i client aziendali e far partire `preload()`: gli errori di forma dei
   JSON e dello snapshot dei manuali escono subito, con il nome del campo o del file.
3. `cycle-validation kb-check` sulla cartella dello snapshot scaricata (stesso formato di S3),
   per lavorare senza rete.
4. Smoke test di una sessione vera e di una trascrizione vera.
5. Golden set su PDF reali con esiti attesi scritti da chi conosce i cicli: è l'unico modo per
   chiudere le voci della sezione 5.
6. Confronto in ombra con il sistema attuale (Fase 7).
