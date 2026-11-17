# Migliorie

Cosa resta da fare, in che ordine, e il registro di ogni esperimento deciso. Come si lanciano
gli esperimenti è in `docs/AZIENDA.md`, parte B.

Ogni miglioria si prova contro la `baseline`: una variante in `eval/varianti/` che cambia una
cosa sola, gli stessi casi e la stessa fotografia, almeno tre ripetizioni. Si tiene solo se la
classifica la ammette, e la decisione va nel registro in fondo.

---

## Come è fatto, in breve

Un ciclo passa per: lettura del PDF (`ingest/`, `extract/`), verifica che i valori letti
compaiano nel PDF (`extract/`, integrità), controlli (`checks/`), esito per riga
(`verdict/`), report (`report/`). Il profilo (`config/profiles/mos|dr|ej200.yaml`) dice quali
controlli valgono; il controllo DR è bloccante.

**L'esito lo decide il codice.** Il modello giudica solo la descrizione dell'operazione contro il
testo del manuale, e ogni sua citazione viene ritrovata dal codice a quella riga; se non c'è,
WARNING `CITAZIONE_NON_VERIFICATA`. Un guasto (modello, Redshift, S3) dà WARNING, mai ERRATO.

| Dove | Cosa |
|---|---|
| `domain/check.py` | esiti e motivi (`Reason`), tabella motivo → esito |
| `checks/` | un file per controllo; `uncertainty.py` per le voci incerte dell'indice |
| `agent/` | sessioni del modello: prompt, hook di sicurezza, tempi massimi, Claude Agent SDK |
| `kb/` | conoscenza: `published.py` (puntatore `current.json`), `ej200.py`, `local.py` (cartella), `structured.py` |
| `services/` | macchine attive: file o Redshift Data API |
| `api/` | servizio FastAPI; `production.py` lo monta dalle variabili d'ambiente |
| `evaluation/` | esperimenti: suite, varianti, misure, classifica, mutazioni, guasti |
| `prompts/`, `config/` | i tre prompt, `settings.yaml`, i profili |

---

## Misure di partenza (14-15 novembre 2026)

Sul computer personale, Claude Haiku con login locale (non Bedrock), solo dati inventati.

| Misura | Valore |
|---|---|
| Tutto il codice, senza modello, ciclo da 40 operazioni | 30 ms |
| Ciclo di esempio da 4 operazioni | 12,7 s, di cui 8,9 s di controlli |
| Una sessione: avvio del processo + risposta | circa 4 s + 3 s |
| Costo di una sessione "in linea" | 0,0006-0,0012 USD |
| Casi MOS / DR / EJ200 | 19/19, 29/29, 22/22 |

Il tempo non è nel codice: metà è l'avvio di un processo dell'agente per ogni operazione. In
azienda, con Bedrock, latenze e prezzi cambiano: la prima `eval pipeline` lì è la baseline
aziendale.

---

## Già fatto

| Id | Cosa |
|---|---|
| A1 | l'hook non blocca più lo strumento di risposta in modalità ricerca (MOS ricerca: 14/19 → 19/19) |
| A4 | tempo massimo: 90 s per sessione, 300 s per leggere il PDF, poi errore tecnico (se Bedrock è più lento, alzarli) |
| A5 | `pytest -m live`: prova con il modello vero, dopo ogni aggiornamento della libreria o del modello |
| B3 | pagine delle foto trascritte in parallelo (`agent.transcribe_concurrency`, 4) |
| B7 | conoscenza scaricata all'avvio; il servizio non parte con un file non valido |
| D | `API_MAX_WORKERS` usato, transcript spenti nel servizio, codice morto tolto, mypy pulito, autenticazione al frontend |
| A6 / B5 | DR letto dal parser di layout PVRM320 come MOS ed EJ200 (verificato su una stampa DR vera il 16/11); il modello resta la riserva |
| F1 | voci incerte di `uncertainty.json`: `DATO_INCERTO` su targa, scheda o fonte (mai sul DR, che è bloccante); file incoerente = log nel servizio, errore in `kb-check` |
| F2 | trattamento della scheda solo per la famiglia del motore del ciclo |
| F3 | task di un DR senza manuale cercati nei manuali citati dall'operazione |
| F4 | documento LEAP intero come contesto quando la fonte non ha task. **Da verificare su un ciclo LEAP vero** |
| — | servizio montato dalle variabili d'ambiente, Redshift con la Data API, secret all'avvio |

---

## Da fare

### Pronte da misurare (variante già scritta, spenta di default)

- **A2, `prompt_task_mancante`.** Se il task citato non è nel manuale, il prompt lo dice al
  modello invece di mandargli il testo delle altre fonti senza spiegazione. Oggi il caso
  `fonte_e_codice_assenti` cambia esito tra un giro e l'altro. Si tiene se è ammessa e quella riga
  diventa stabile. Interruttore: `agent.missing_task_note`.
- **B6, `salta_task_mancante`.** Stesso caso, WARNING `FONTE_ASSENTE` subito, senza sessione.
  Sui sintetici è scartata (lì l'atteso è CORRETTO). Si tiene solo se chi conosce i cicli dice
  che l'esito giusto è WARNING, e allora va cambiato anche `expected.json`. Interruttore:
  `agent.skip_missing_task`. **Si sceglie una tra A2 e B6.**
- **B2, `effort_low` / `effort_low_controlli`.** Meno ragionamento: -22/-33% di costo, stessa
  concordanza sui sintetici. `effort_low_controlli` tiene pieno il ragionamento nella lettura del
  PDF, che con `low` leggeva peggio. Da confrontare su Bedrock con casi veri.

### Da costruire

| Id | Cosa | Perché | Costo |
|---|---|---|---|
| B1 | chiamata diretta a Bedrock (`converse`) per le sessioni in linea; l'agente resta solo per i testi lunghi | toglie l'avvio di 4 s per operazione: circa metà del tempo. Il guadagno più grande | medio: secondo adattatore dietro `AgentSession` |
| B4 | `agent.concurrency` sopra 6 | 40 operazioni: 21 s con 6, 12 s con 12. Limite: quote Bedrock | una riga, ma dopo B1 (sui sintetici `concorrenza_12` è stata scartata) |
| A3 | targa assente da tutto = WARNING "sconosciuta"; ERRATO solo se è nei dati TM e non è attiva | targhe scritte diverse o elenco incompleto danno ERRATO falsi | piccolo, `checks/machine_tag.py`; decidere con i dati Redshift |
| F5 | dire nel prompt che un fatto è incerto (valori alternativi, record parziale) | oggi il modello non lo sa | piccolo, `checks/operation.py`; variante spenta, da misurare con A2/B6 |
| B8 | `golden` e i casi degli esperimenti in parallelo | esperimenti più rapidi, il servizio non cambia | piccolo |
| D | togliere le rotte storiche (`/upload`, `/ej200/upload`, `/conversation`) | pulizia | medio; quando il frontend usa solo `validation/upload` |

### E1. Varianti proposte dal modello (`eval proponi`), più avanti

Idea dal paper Harness² (Google Research, arXiv 2610.14224): il modello propone modifiche ai
propri prompt, il programma le prova. Da noi la scelta resta alla classifica con i paletti, che
ha gli esiti attesi; il modello fa solo **la proposta**.

- Il comando legge l'ultimo risultato della baseline (righe sbagliate, instabili, citazioni non
  ritrovate), i tre prompt e l'elenco delle varianti già provate; scrive due varianti in
  `eval/varianti/proposte/`, una generale e una di profilo.
- Rifiuta una proposta che tocca altro oltre ai tre prompt, cambia più di 20 righe, non cita
  almeno due righe sbagliate o ripete una variante già scartata.
- Per evitare di adattarsi ai casi: l'editor vede i sintetici e le mutazioni, la proposta deve
  passare anche sui casi aziendali, che non ha visto. Per l'editor, un modello diverso da quello
  dei controlli.
- Niente nel servizio: tutto in `eval/`, e la promozione in `prompts/` resta una scelta umana.
- Prima servono i casi aziendali rivisti: sui sintetici la concordanza è già 99,5-100%. Dopo tre
  giri senza proposte ammesse, si toglie.

### Punti aperti lato knowledge-index (lì, non qui)

- `aliases.json`: i nomi con cui i cicli veri citano manuali e documenti, LEAP compresi.
- Gli intervalli dei task (riga iniziale e finale) misurati sui manuali veri.
- Le 4 voci RDR marcate "detected OTHER": capire che documenti sono.

---

## Ordine consigliato

1. Casi veri nella suite (`eval prepara` e revisione): senza, le misure valgono solo sui dati
   inventati. Poi la baseline aziendale.
2. B2: una riga, guadagno già misurato.
3. A2 contro B6, insieme a F5, con 3 ripetizioni, e la scelta con chi conosce i cicli.
4. B1, poi B4.
5. A3 e F4: quando ci sono i dati veri (Redshift, ciclo LEAP).
6. D, rotte storiche, quando il frontend è pronto.
7. E1, dopo i casi aziendali rivisti.

---

## Registro degli esperimenti

Una riga per ogni prova decisa, contro la baseline dello stesso giro.

| Data | Esperimento | Variante | Concordanza | Costo | Tempo | Decisione |
|---|---|---|---|---|---|---|
| 2026-11-14 | `effort: low` (prova veloce, una volta sola) | — | MOS 18-19 su 19 | -30% | -27% per sessione | da ripetere con il metodo sopra |
| 2026-11-14 | `effort: low`, casi sintetici, 3 ripetizioni, login locale | `effort_low` | 99,5% (come baseline) | -22% | -9% | ammessa e più veloce; da confermare su Bedrock con casi veri |
| 2026-11-14 | concorrenza 12 | `concorrenza_12` | 99,0% | -17% | uguale | scartata: concordanza più bassa |
| 2026-11-14 | modello Sonnet | `sonnet` | 98,6% | ×10 | -17% | scartata: concordanza più bassa, costo |
| 2026-11-14 | `effort: low`, un ciclo MOS di prova letto dal PDF, 2 ripetizioni | `effort_low` | 97,6% (baseline 100%) | -22% | -11% | scartata: un ERRATO falso ("Targa -" letta come targa) ed estrazione 87,5%; causa corretta nel codice, da rimisurare |
| 2026-11-15 | giro 3, stesso ciclo di prova, 2 ripetizioni, login locale | `effort_low` | 100% | -33% | +25% | ammessa: il "-" letto come targa c'è ancora, ma ora vale "targa assente"; tempi su un caso solo troppo rumorosi per decidere |
| 2026-11-15 | come sopra | `effort_low_controlli` | 100% | -31% | +26% | ammessa; non legge più il "-"; da misurare in azienda contro `effort_low` |
| 2026-11-15 | come sopra | `prompt_task_mancante` | 100% | -30% | +66% | ammessa; il tempo è rumore (cambia una sola sessione); serve `fonte_e_codice_assenti` con più ripetizioni |
| 2026-11-15 | come sopra | `guasti` | — | — | — | regge: 0 ERRATO falsi, 4,5 esiti tecnici per ripetizione |
