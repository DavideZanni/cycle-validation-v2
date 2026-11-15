# Migliorie possibili

Elenco delle migliorie, divise in quattro gruppi: affidabilità, velocità, costo, pulizia. Ognuna
dice cosa cambia, quanto rende (con la misura, quando c'è), quanto costa farla e se va provata
prima in azienda.

Ogni miglioria si prova come esperimento contro la baseline: un ramo, una modifica, le stesse
misure prima e dopo. Il metodo è in `docs/BASELINE.md`.

---

## Le misure di partenza (14 novembre 2026)

Fatte sul computer personale con un modello vero (Claude Haiku, login locale, non Bedrock) e solo
dati inventati.

| Misura | Valore |
|---|---|
| Tutto il codice, senza modello, ciclo da 40 operazioni | 30 ms |
| Ciclo di esempio da 4 operazioni, dall'inizio alla fine | 12,7 s |
| di cui controlli (4 sessioni in parallelo) | 8,9 s |
| Durata di una sessione dichiarata dal modello (mediana) | 3,0 s |
| Avvio del processo dell'agente, prima della risposta | circa 4 s per sessione |
| Costo di una sessione "in linea" | circa 0,0006-0,0012 USD |
| Token di "ragionamento" sul totale in uscita | circa la metà |

**Dove va il tempo.** Non nel codice. Per ogni operazione: avvio di un processo dell'agente
(circa 4 s) più risposta del modello (circa 3 s). Metà dell'attesa è l'avvio.

---

## A. Affidabilità

### A1. Strumento di risposta bloccato in modalità ricerca. **Fatto**

Quando il testo del manuale è lungo (oltre 150 righe) il modello lo cerca con `Grep` e `Read`.
L'hook di sicurezza rifiutava anche `StructuredOutput`, lo strumento con cui il modello consegna
la risposta. Effetto: ogni operazione con testo lungo finiva in WARNING "errore tecnico". Sono
tutti gli EJ200 (documenti interi) e i task MOS lunghi.

Prova con il modello vero, modalità ricerca forzata, casi MOS: prima 14 su 19, dopo 19 su 19.
Corretto in `src/cycle_validation/agent/hooks.py`, con un test.

**Lezione:** i test usano un modello finto e questo errore non lo potevano vedere. Da qui la
miglioria A5.

### A2. Dire al modello quando il task citato non esiste. **Pronta da misurare**

Se un'operazione cita un task che il manuale non ha, il programma manda al modello il testo dei
task delle fonti del ciclo, ma non glielo dice. Il modello vede "task citato: X" e un testo che
parla di Y, e a volte risponde "coerente", a volte "non verificabile". Nel caso di prova
`fonte_e_codice_assenti` la risposta cambia da un run all'altro.

Due strade:

1. aggiungere una riga al messaggio: "il task citato non è nel manuale; questo è il testo delle
   fonti del ciclo" (più stabile, stesso costo);
2. non chiamare il modello: WARNING diretto (più veloce, una sessione in meno, ma si perde il
   confronto con le fonti del ciclo).

Raccomandazione: strada 1, e decidere con chi conosce i cicli quale esito è giusto. Costo: poche
righe in `src/cycle_validation/agent/prompt.py`.

**Stato (14 novembre 2026):** strada 1 fatta, spenta di default (`agent.missing_task_note`). La
variante `eval/varianti/prompt_task_mancante.yaml` la accende; si tiene se in classifica è
ammessa e la riga di `fonte_e_codice_assenti` smette di cambiare tra le ripetizioni.

### A3. Distinguere "targa sconosciuta" da "macchina non attiva"

Oggi una targa assente dall'elenco delle macchine attive dà sempre ERRATO. Una targa scritta in
un altro modo (`AB/123` contro `AB123`) o un elenco incompleto danno ERRATO falsi. Proposta:
ERRATO solo se la targa è nei dati TM ma non è attiva; se non è da nessuna parte, WARNING "targa
sconosciuta". Va deciso con i dati veri di Redshift. Costo: piccolo, in
`src/cycle_validation/checks/machine_tag.py`.

### A4. Tempo massimo per sessione

Oggi non c'è. Se una sessione si blocca, tutta la validazione resta ferma e l'utente aspetta
fino al timeout del server (600 s). Proposta: 60-90 s per sessione, poi WARNING "errore
tecnico". Non accelera il caso normale, toglie le attese infinite. Costo: piccolo, in
`src/cycle_validation/agent/runner.py`.

### A5. Una prova con il modello vero, da lanciare a mano

Una piccola prova (`pytest -m live`) che fa una sessione vera in linea e una in ricerca sul ciclo
di esempio. Non parte con i test normali. In azienda si lancia dopo ogni aggiornamento della
libreria dell'agente o del modello. Avrebbe trovato subito l'errore A1. Costo: piccolo.

### A6. Leggere il DR senza modello, ma solo dopo una stampa DR vera

MOS ed EJ200 sono letti da un parser, il DR ancora dal modello. Oltre alla velocità (B5), il
parser è ripetibile: stessa stampa, stesso risultato. Va provato su una stampa DR vera, insieme
ai marcatori `module_check.dr_markers`.

---

## B. Velocità

### B1. Chiamata diretta al modello per i testi corti

Quasi tutte le sessioni sono "in linea": il testo del manuale è già nel messaggio, il modello non
deve cercare niente. Eppure ognuna avvia un processo dell'agente (circa 4 s). Con una chiamata
diretta a Bedrock (`converse`, la stessa già usata per trascrivere le foto) l'avvio sparisce.
L'agente con `Grep` e `Read` resta solo per i testi lunghi.

Guadagno stimato: circa metà del tempo di ogni operazione. È il guadagno più grande. Costo:
medio, un secondo adattatore dietro la stessa interfaccia `AgentSession`.

### B2. Meno "ragionamento" del modello (`agent.effort: low`)

Misurato oggi sui casi MOS, stesso modello:

| `effort` | Costo | Durata mediana di una sessione | Token di ragionamento |
|---|---|---|---|
| predefinito | 0,0038 USD | 3,0 s | 1740 |
| `low` | 0,0026 USD | 2,2 s | 806 |

Meno 30% di costo e meno 27% di durata. Concordanza uguale: l'unico caso che cambia è quello
ambiguo del punto A2, che cambia anche con l'impostazione predefinita. Costo: una riga in
`config/settings.yaml`. Da confermare su cicli veri, dove le contraddizioni sono più sottili.

**Aggiornamento (14 novembre 2026):** sul ciclo di prova letto dal PDF `effort: low` ha letto
peggio (estrazione 87,5% contro 100%) e ha dato un ERRATO falso: ha letto "Targa -" come una
targa che si chiama "-". Il trattino ora vuol dire "targa assente" per tutte le varianti. Due
varianti da misurare: `effort_low` di nuovo, e `effort_low_controlli`, che tiene il
ragionamento pieno nella lettura del PDF (`agent.extraction_effort: high`).

### B3. Trascrivere le pagine in parallelo

Le stampe di esempio sono foto. Ogni pagina è una chiamata al modello, e oggi le pagine si
trascrivono una dopo l'altra. Per esempio, se una pagina richiede 5 s, un ciclo di 6 pagine
richiede 30 s solo per essere letto; in parallelo, circa 5 s (tempo per pagina da misurare in
azienda). Se in produzione i cicli arrivano come foto o scansioni, è la
miglioria più utile dopo B1. Costo: piccolo, in `src/cycle_validation/ingest/document.py`.

### B4. Più operazioni insieme (`agent.concurrency`)

Oggi 6. Con risposte da 3 s, un ciclo da 40 operazioni dura circa 21 s con 6, 12 s con 12, 6 s
con 20. Si cambia in una riga. Il limite vero sono le quote Bedrock dell'account: alzare a
piccoli passi e guardare se compaiono errori di throttling. Conviene dopo B1, perché oggi ogni
operazione in più è un processo pesante in più.

### B5. Leggere il DR senza modello

Vedi A6. Una chiamata al modello in meno per ciclo DR. Si attiva con una riga in
`config/profiles/dr.yaml` (`layout_extractor: pvrm320`), dopo la prova su una stampa vera.

### B6. Non chiamare il modello quando non serve

Già oggi il modello non viene chiamato se la descrizione manca, se l'estrazione non è confermata
o se non c'è nessun testo di riferimento. Da aggiungere, se si sceglie la strada 2 del punto A2:
task citato inesistente.

### B7. Conoscenza pronta all'avvio

La cartella dei manuali su S3 viene scaricata tutta alla prima richiesta: la prima validazione
dopo un riavvio è lenta. Chiamare `preload()` all'avvio del servizio (Passo 7 della guida di
importazione) sposta l'attesa all'avvio. Con molti manuali grandi, meglio scaricare un documento
alla volta, quando serve.

### B8. Casi di prova in parallelo

`cycle-validation golden` prova i casi uno dopo l'altro (MOS: 31 s per 5 casi). In parallelo
durerebbe quanto il caso più lento. Non tocca il servizio, ma rende più veloci gli esperimenti
della baseline. Costo: piccolo.

---

## C. Costo

| Miglioria | Effetto sul costo |
|---|---|
| B2, `effort: low` | meno 30% per sessione (misurato) |
| B1, chiamata diretta | niente istruzioni di sistema dell'agente per le sessioni corte: meno token in entrata |
| A2 strada 2 e B6 | una sessione in meno per ogni task citato inesistente |
| B5, DR senza modello | una chiamata in meno per ciclo DR |

Già attivo: il testo delle istruzioni è uguale per tutte le sessioni, quindi Bedrock lo riusa
dalla cache (visto oggi: circa 1500 token letti dalla cache per sessione).

---

## D. Pulizia

| Cosa | Perché | Costo |
|---|---|---|
| `API_MAX_WORKERS` viene letta ma non usata | o la si collega a un limite di validazioni contemporanee, o la si toglie | piccolo |
| `save_transcripts: true` come valore predefinito | nel servizio scrive su disco testo di cicli e manuali | una riga |
| `src/cycle_validation/legacy_prompts.py` | nessun codice lo usa, solo i suoi test | piccolo |
| `Dockerfile` installa `boto3` a parte | usare l'extra `aws` del progetto (`pip install .[aws]`) per avere una sola lista | una riga |
| rotte storiche (`/upload`, `/ej200/upload`, `/conversation`) | da togliere quando il frontend nuovo usa solo `validation/upload` | medio |
| autenticazione nel backend | hai deciso che è del frontend: si può togliere | medio |
| `data/simulazione/simula.py` (fuori da git) | usa una classe tolta con OpenSearch: non parte più | da rifare o cancellare |
| `mypy` | qui non si carica: va lanciato in azienda | — |

---

## Ordine consigliato

1. **A5** (prova con il modello vero): protegge tutte le altre modifiche.
2. **B2** (`effort: low`): una riga, guadagno misurato, da confermare su cicli veri.
3. **A2** e **A4**: piccole, tolgono un'ambiguità e le attese infinite.
4. **B1** (chiamata diretta): il guadagno più grande sul tempo.
5. **B3** se i cicli arrivano come foto, poi **B4**.
6. **A3**, **A6/B5**: quando ci sono i dati veri (Redshift, stampa DR).
