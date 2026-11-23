# Migliorie

Qui c'è:

1. cosa è già stato migliorato;
2. cosa resta da fare, e in che ordine;
3. il registro delle prove fatte, con la decisione presa.

**Come si prova una miglioria.** Si scrive una *variante* in `eval/varianti/` che cambia una
cosa sola. Si fa girare sugli stessi cicli e sulla stessa conoscenza della `baseline` (la
versione di oggi), almeno tre volte. Si tiene solo se la classifica dice che non peggiora
niente; la decisione si scrive nel registro in fondo. Come si lancia: `docs/AZIENDA.md`,
parte B.

**Prova sui cicli veri (sul PC aziendale).** Ogni miglioria si prova con COPILOT 2.3
(`eval prova`, codice in `evaluation/trials.py`) contro i 12 errori noti di
`eval/errori-noti.yaml`, su due **insiemi** di cicli:

- **piccolo**, 10 cicli: i 7 «con errori» e le 3 stampe giuste. Ogni miglioria passa da qui;
- **grande**, 30 cicli: i 10 del piccolo e 20 cicli **veri** (stampe in uso, civili, con almeno
  l'80% delle operazioni confrontabili con la conoscenza), scelti da `eval scegli` e sempre gli
  stessi. Solo le migliorie che si tengono sul piccolo: un ERRATO su un ciclo vero è «da
  verificare» (quasi sempre falso), i suoi WARNING contano nel lavoro a mano.

Le prove si confrontano solo sullo stesso insieme (cartelle `runs/prove-piccolo` e
`runs/prove-grande`; il riepilogo avvisa se in una cartella gli insiemi sono diversi). Ogni
prova scrive il suo report (`<data>-<nome>/prestazioni.md`); `riepilogo.md` mette insieme le
prove, fa la classifica e dà la scelta migliore. Una miglioria con un file
`eval/varianti/<nome>.yaml` si lancia con `--variante` sopra le impostazioni del PC. Prima,
gratis: i test (`uv run pytest -q`) e, per una miglioria sulle descrizioni, `leggi --lingue`.

### Metriche (su una prova)

| Metrica | Definizione |
|---|---|
| Trovati (TP) | errori noti con un ERRATO sulla loro operazione |
| Mancati (FN) | errori noti senza ERRATO; il report dice cosa ha detto la v2 |
| Falsi errori (FP) | ERRATO su un'operazione di una stampa giusta |
| Da verificare (X) | ERRATO fuori dalla lista: nei cicli con errori (un errore vero non in lista o un falso errore) e nei cicli veri (quasi sempre falsi). Si guarda e, se è vero, il ciclo va nella lista |
| Precisione | TP / (TP + FP + X) |
| Warning per ciclo senza errori | WARNING medi sulle stampe giuste e sui cicli veri: lavoro a mano che resta |
| Costo e tempo per ciclo | medi; più il tempo del ciclo più lento |
| Non eseguiti | cicli andati in errore |

### Regola di scelta (su una variante = prove con lo stesso nome)

1. **Scartata** se: falsi errori > 0, un ciclo non eseguito, un ciclo oltre 10 minuti (il
   frontend aspetta 11), costo per ciclo oltre 2 volte la base.
2. **Da ripetere** se ha meno di 2 prove (il modello non risponde sempre uguale).
3. **Classifica**, in ordine: errori **stabili** (trovati in tutte le prove della variante),
   trovati minimo, trovati medio, meno da verificare, meno warning per ciclo senza errori, meno costo,
   meno tempo.
4. **Si tiene** se non ha meno errori stabili della base e sta sopra la base in classifica.
   La **scelta migliore** è la prima della classifica che si tiene (o la base).

Le soglie sono costanti in `evaluation/trials.py` (`MIN_REPETITIONS`, `MAX_CYCLE_MS`,
`MAX_COST_RATIO`). Il registro in fondo a questo file riporta la decisione di ogni variante.

### Da provare (lista del 23-11-2026)

Errori noti che mancano oggi (23-11 sera): 298bc28e op 035 (parole cambiate), c5ff3cd6 op 030
(scheda tolta), f355dc3c op 010 (tre numeri, cambiati in tutte e due le lingue), 040 (lettera
della classe), 050 (frase al contrario). Per ognuna: due prove sul piccolo con `$nome` = il
nome; se si tiene, due sul grande.

**Subito: basta il file della variante (nessun codice nuovo).**

| `$nome` | Cosa cambia | Cosa può migliorare | Rischio |
|---|---|---|---|
| `effort_medio` | ragionamento `medium` nei controlli invece di `low` | frasi al contrario e parole cambiate (f355dc3c 050, 298bc28e 035) | costo e tempo |
| `conferme_1` | un ERRATO del modello si conferma con 1 sessione invece di 2 (G1) | meno costo; errori che il modello vede solo a volte | falsi errori (devono restare 0) |
| `testo_lungo` | fino a 400 righe di manuale nel messaggio invece di 150 | più contesto in una volta: limiti scritti lontano dal passo (f355dc3c 010) | costo per sessione |
| `effort_pieno` | ragionamento predefinito ovunque (B2) | conferma che `low` non perde errori su Bedrock | costo |
| `prompt_task_mancante` | task citato che manca: il modello giudica lo stesso (A2) invece di WARNING subito (B6) | operazioni oggi `FONTE_ASSENTE` | falsi errori, costo |
| `concorrenza_12` | 12 operazioni insieme invece di 6 (B4) | solo il tempo | limiti di Bedrock: cicli non eseguiti |

`sonnet` (modello più grande) non ora: il costo per ciclo è circa 10 volte (la regola scarta
oltre 2 volte) e serve l'id di Sonnet abilitato su Bedrock.

**Con codice nuovo (lo scrive Claude, ognuna accesa dalla sua variante, la base non cambia).**

| `$nome` | Cosa fa | Cosa può migliorare | Costo |
|---|---|---|---|
| `negazioni_lingue` (I1) | come `INCOERENZA_LINGUE`, ma per le negazioni: «non» / «not», «mai» / «never», «evitare» / «avoid» in una lingua sola | frasi al contrario in una lingua sola (come 5ff17062 op 030); f355dc3c 050 se è così | piccolo, senza modello; misura gratis con `leggi --lingue` |
| `classi_lingue` (I2) | lettere e sigle dopo «classe», «tipo», «grado» diverse tra le due lingue | f355dc3c 040, se la lettera è cambiata in una lingua sola | piccolo, senza modello |
| `prompt_confronto` (I3) | il prompt chiede di confrontare numero per numero e frase per frase, e di dire cosa cambia | parole cambiate, frasi al contrario | piccolo; falsi errori da misurare |
| `numeri_manuale` (I4, è H12) | numeri e classi della descrizione contro quelli del passo del manuale: la sessione riceve le differenze da guardare | numeri cambiati in tutte e due le lingue (f355dc3c 010), se il passo giusto è nel contesto | medio |
| `contesto_sezione` (I5) | se i task citati non hanno i numeri della descrizione, si aggiungono altri task della stessa sezione (al massimo 4) | limiti scritti in un altro task (f355dc3c 010) | medio, più sessioni lunghe |
| `fatti_incerti` (F5) | il prompt dice quando un fatto è incerto | meno giudizi sbagliati su dati incerti | piccolo |

**Tempo e costo (dopo: non cambiano gli errori trovati).** B1 (chiamata diretta a Bedrock), poi
B4; H10 (prompt caching), H14 (più operazioni in una sessione). Si provano con le stesse prove:
devono tenere gli stessi errori stabili e costare o durare meno.

**Non sono migliorie: nessuna variante li trova finché mancano.** f355dc3c 040 e forse 010
chiedono documenti che non sono nella conoscenza (capitolo 70-23 dell'SPM, manuale d'ispezione
del motore, due REPAIR della sezione 72-56-31): ingestion, poi COPILOT 2.5 e una prova
`conoscenza-<data>`. c5ff3cd6 030 (scheda tolta) aspetta la regola della domanda P6.
f355dc3c 050 ha anche la domanda P7 («4 volte» c'è anche nella stampa giusta).

**Ordine consigliato.** 1. La base (piccolo e grande). 2. `negazioni_lingue` e `classi_lingue`:
non costano e si misurano prima gratis. 3. `effort_medio`. 4. `conferme_1`. 5. `testo_lungo`.
6. `prompt_confronto`. 7. `numeri_manuale` e `contesto_sezione`. 8. `effort_pieno`, per
confermare B2. 9. Tempo e costo.

---

## Dove sta il codice

Come funziona la v2, passo per passo, è in `docs/MEMORIA.md`, sezione 8. Qui solo dove sta ogni
parte nel codice (cartella `src/cycle_validation/`):

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
| B6 | task citato che il manuale non ha: WARNING `FONTE_ASSENTE` subito, senza modello (scelto il 20-11-2026 al posto di A2, che resta nella variante `prompt_task_mancante`) |
| A3 | targa che non c'è da nessuna parte (né dati TM né attive): WARNING `TARGA_SCONOSCIUTA`; ERRATO solo se è nei dati TM e non è attiva (20-11-2026) |
| B2 | ragionamento `low` nei controlli e `high` nella lettura del PDF, acceso di default (20-11-2026; da confermare su Bedrock) |
| F4 | documento LEAP intero come contesto quando la fonte non ha task. **Da verificare su un ciclo LEAP vero** |
| — | servizio montato dalle variabili d'ambiente, Redshift con la Data API, secret all'avvio |
| G1 | conferma delle contraddizioni: un ERRATO della descrizione si rifà con 2 sessioni uguali (`agent.confirm_contradiction`); se una non ritrova la contraddizione, WARNING `GIUDIZIO_INSTABILE`. Costa solo sugli ERRATO (21-11-2026, dopo l'op. 060 del ciclo DR vero) |
| G2 | DR `Accept as is`: provato come WARNING senza blocco il 21-11-2026, **tolto il 22-11-2026**: l'utente ha confermato la regola della v1 (vedi G3) |
| G3 | DR (22-11-2026): `Accept as is` torna ERRATO e ciclo bloccato come `Reject` (regola della v1). Serial number e condition facoltativi: il serial number, se manca, si prende dalla stampa (`APPLY ON S/N`); senza serial number, o senza la condition quando le recommendation sono diverse, WARNING `DR_NON_VERIFICATA` e gli altri controlli proseguono. Il frontend può togliere le due domande |
| G4 | risposta adattata al frontend di oggi (22-11-2026, dalle risposte di Copilot sul codice del frontend): `N/A` esatto per i campi vuoti e per i controlli fermati dal DR (bollino grigio, come la v1), `N/A - motivo` per quelli esclusi da una regola (bollino azzurro `Info`); esito DR nella riga della fonte DR con `DRCase` e `serialNumber` (il frontend non legge `drRecommendationFeedback`); `scheda.tabNumber`; passo DR della conversazione accettato anche con i due campi vuoti |
| G5 | (22-11-2026) serial number dalla stampa in più forme (`S/N:`, `S / N.`, con trattino); con più serial number vale quello che ha recommendation nei dati DR. `leggi --cerca` stampa le righe con un testo e i codici mascherati. `scheda.task` = codice dopo «SP.ORIG.» nei cicli civili, come la v1 |
| G6 | (22-11-2026) comando `confronta <giusto.pdf> <con errori.pdf>`: confronta due stampe dello stesso ciclo con il parser (zero token) e dice in quali fonti, operazioni e campi sono diverse, con i codici mascherati e solo i pezzi di descrizione che cambiano. Serve a sapere dove sono gli errori dei cicli «con errori» e a misurare se la v2 li trova |
| G7 | (22-11-2026) `leggi --struttura N`: come il parser vede ogni riga della pagina N (tipo di riga, numero di operazione, prima parola mascherata), senza il testo del ciclo. `confronta` dice quale delle due stampe il parser non legge |
| G8 | (22-11-2026) stampa modificata a mano: se nel PDF le righe sono fuori ordine rispetto alla pagina, la lettura le rimette in ordine di posizione e unisce i pezzi della stessa riga (`ingest/pdf.py`); `leggi` dice quali pagine. Le stampe normali restano come prima |
| G9 | (22-11-2026) comando `macchine`: elenco delle macchine attive da Redshift per le prove sul PC, con il secret e la tabella della v1 e la Data API; `leggi --breve` e `--senza-riordino`; nelle pagine rimesse in ordine una riga senza colonne resta nell'operazione in corso |
| G10 | (22-11-2026) titolo «OPERAZIONE EVENTUALE» in un blocco a sé attaccato all'operazione dopo; `confronta --primo-senza-riordino`; `macchine` prende `SECRET_NAME` dal secret «di ambiente» della v1 e il database dalla connessione della v1 (o `--database`); nelle descrizioni lette dopo il riordino si tolgono gli asterischi di cornice e le righe di soli segni. Il riordino recupera nelle stampe DR testo che prima si perdeva |
| G11 | (22-11-2026 sera) accesso come la v1: `API_AUTH=sdk` con `chatbot_ai_sdk` (token del cookie, permessi da `permissions.json`, utente da `current_user`), scelto da solo con il secret della v1; `CV_ENV_SECRET` per leggere all'avvio il secret «di ambiente» della v1; `macchine` segue il database fino alla funzione delle credenziali della v1 (analisi del codice) |

---

## Da fare

### Da confermare su Bedrock

- **B2, ragionamento ridotto (acceso dal 20-11-2026).** `effort: low` nei controlli,
  `extraction_effort: high` nella lettura del PDF: -31% di costo, stessa concordanza sui
  sintetici. La prima `eval pipeline` in azienda lancia anche `effort_pieno`: se la baseline
  concorda meno, si torna indietro lasciando vuoti i due campi in `config/settings.yaml`.

### Da costruire

| Id | Cosa | Perché | Costo |
|---|---|---|---|
| B1 | chiamata diretta a Bedrock (`converse`) per le sessioni in linea; l'agente resta solo per i testi lunghi | toglie l'avvio di 4 s per operazione: circa metà del tempo. Il guadagno più grande | medio: secondo adattatore dietro `AgentSession` |
| B4 | `agent.concurrency` sopra 6 | 40 operazioni: 21 s con 6, 12 s con 12. Limite: quote Bedrock | una riga, ma dopo B1 (sui sintetici `concorrenza_12` è stata scartata) |
| F5 | dire nel prompt che un fatto è incerto (valori alternativi, record parziale) | oggi il modello non lo sa | piccolo, `checks/operation.py`; variante spenta, da misurare con A2/B6 |
| B8 | `golden` e i casi degli esperimenti in parallelo | esperimenti più rapidi, il servizio non cambia | piccolo |
| T1 | tempo massimo per tutta la validazione, sotto i 600 s del backend v1 e i 660 s del frontend: allo scadere si chiude con quello che c'è (WARNING sui controlli non finiti) invece di essere tagliati dal server | oggi una validazione lunga verrebbe interrotta senza risposta | piccolo. Misurato il 22-11-2026: al massimo 131 s su un DR da 9 operazioni; serve quando si vedrà un ciclo MOS lungo vicino ai 600 s |
| D | togliere le rotte storiche (`/upload`, `/ej200/upload`, `/conversation`) | pulizia | **non ora**: il frontend di oggi usa proprio queste rotte (22-11-2026) |

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

### Idee tecniche nate dalle prove sul PC (22-11-2026)

Da decidere: nessuna è necessaria per la consegna. In ordine di valore.

| Id | Idea | Perché (cosa si è visto) | Costo |
|---|---|---|---|
| H1 | **Macchine attive come file su S3.** Un job pianificato (per esempio ogni notte: Redshift `UNLOAD`, o una Lambda) scrive l'elenco delle macchine attive accanto alla conoscenza; la v2 lo legge come le targhe (`MACHINES_SOURCE=file`, già pronto) | dal PC Redshift non si raggiunge (Data API senza permesso, nessuna rete verso il cluster): oggi le targhe sul PC escono sempre WARNING. Con il file: niente driver, niente password nel secret, prove complete anche sul PC. Una macchina dismessa non cambia di ora in ora | piccolo lato v2 (c'è già); il job lo fa chi gestisce il datalake |
| H2 | **Ingestion guidata dalla domanda.** Il servizio conta i manuali `FONTE_ASSENTE` e scrive ogni giorno la classifica dei più chiesti (S3 o CloudWatch); l'ingestion parte da lì | ingestionare tutto costa troppo (circa 2000 file), e i cicli «con errori» non sono misurabili senza i loro manuali. Il comando `manuali` lo fa a mano sul PC | piccolo |
| H3 | **`kb-check` dentro l'ingestion**, prima di spostare `current.json` | oggi la v2 rifiuta all'avvio una conoscenza rotta (B7): meglio che una versione rotta non venga mai pubblicata. Errori come la targa «90» si vedrebbero subito | piccolo, lato knowledge-index |
| H4 | **Prova «ombra» in QA:** la v2 riceve una copia delle richieste della v1, l'utente vede solo la v1, i due esiti si confrontano | misura la v2 su cicli veri senza rischio e senza chiedere niente agli utenti; oggi la misura dipende da pochi cicli preparati a mano | medio: un secondo servizio e un confronto |
| H5 | **Validazione come lavoro in coda:** il POST risponde subito con un numero, il frontend chiede lo stato (o riceve l'avanzamento, «operazione 12 di 40»); i lavori in una coda (SQS) con più worker | oggi una richiesta HTTP resta aperta fino a 10 minuti con un worker solo: T1 sparisce e si regge più traffico | medio-grande: serve anche il frontend |
| H6 | **Il ciclo dai dati strutturati invece che dal PDF**, se il sistema che stampa PVRM320 ha le stesse informazioni in una tabella (forse nel datalake) | metà dei problemi visti sono di lettura: stampe modificate a mano, righe fuori ordine, colonne tolte. Da chiedere (domanda per le persone) | dipende da dove sono i dati |
| H7 | **Gli esperimenti dentro AWS** (CodeBuild o un task ECS) invece che sul PC: stessi comandi `eval`, fuori escono solo le misure | EJ200 non si può provare fuori da AWS, Redshift nemmeno; sul PC ogni prova passa da foto | medio |
| H8 | **Il feedback del frontend diventa un caso di prova:** una risposta segnata sbagliata dall'utente finisce in una cartella per `eval prepara` | i casi aziendali rivisti sono la cosa che manca di più agli esperimenti (vedi «Ordine consigliato») | piccolo-medio |
| H9 | **OpenSearch solo come riserva**, non al posto della ricerca per codice: quando il task non c'è o la fonte non ha task (F4, LEAP), la ricerca propone i passi candidati, e la citazione si controlla sempre come oggi | la ricerca per codice dà citazioni verificabili, che è il punto della v2; una ricerca per somiglianza da sola riporterebbe il problema della v1 (passi «simili» ma non quelli giusti). Da misurare con le varianti | medio, più il costo del cluster |
| H10 | **Prompt caching di Bedrock** per le parti uguali tra le sessioni dello stesso ciclo (istruzioni, stesso capitolo per più operazioni), e **batch di Bedrock** per gli esperimenti | meno costo e meno tempo; da verificare quanto la cache funziona già con l'agente | piccolo, dopo B1 |
| H12 | (in parte fatto il 23-11: tra le due lingue, `INCOERENZA_LINGUE`; il resto è I4 in «Da provare») **Numeri e codici confrontati dal codice** prima del modello: numeri, classi e codici della descrizione contro quelli del passo del manuale; se sono tutti uguali e il testo coincide, CORRETTO senza modello; se un numero è diverso, la sessione riceve la differenza da guardare | 7 dei 10 errori dei cicli «con errori» sono numeri, lettere o codici cambiati: il codice li trova in pochi ms e sempre allo stesso modo, il modello costa e a volte oscilla (G1) | medio; da misurare con le mutazioni |
| H13 | **Risultato già calcolato:** stesso PDF (impronta), stessa versione della conoscenza, stesse impostazioni → la risposta salvata, subito | lo stesso ciclo si ricarica spesso (prove, riaperture) | piccolo |
| H14 | **Più operazioni dello stesso capitolo in una sessione** | meno sessioni e lo stesso testo del manuale mandato una volta sola; rischio: il modello confonde le operazioni. Solo con una variante misurata | medio |
| H11 | **Python 3.14 in `.python-version`** | tutti i PC e il Dockerfile della v1 usano 3.14: ogni blocco di COPILOT ripete `$env:UV_PYTHON` | piccolo: provare la suite su 3.14 prima |

### Punti aperti lato knowledge-index (lì, non qui)

- `aliases.json`: i nomi con cui i cicli veri citano manuali e documenti, LEAP compresi.
- Gli intervalli dei task (riga iniziale e finale) misurati sui manuali veri.
- Le 4 voci RDR marcate "detected OTHER": capire che documenti sono.

---

## Ordine consigliato

Prima di tutto la consegna: i punti di `MEMORIA.md`, sezione 1. Per le prove sui cicli veri vale
l'ordine di «Da provare» qui sopra. Per il resto:

1. Casi veri nella suite (`eval prepara` e revisione): senza, le misure valgono solo sui dati
   inventati. Poi la baseline aziendale.
2. B2 su Bedrock: baseline contro `effort_pieno`.
3. F5 (`fatti_incerti` in «Da provare»).
4. B1, poi B4.
5. F4: quando c'è un ciclo LEAP vero.
6. D, rotte storiche, quando il frontend è pronto.
7. E1, dopo i casi aziendali rivisti.
8. Le idee H: H1 e H3 sono le più semplici e tolgono problemi visti; H4 e H5 dopo il
   passaggio in produzione.

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
| 2026-11-21 | ciclo DR vero, Bedrock Haiku 5.5, sottoinsieme della conoscenza: ciclo letto dal modello contro ciclo letto dal parser, 2 condition Repair | parser | parser: due run identici (5 corretti, 0 errati); modello: run diversi tra loro e un ERRATO (op. 060) che col parser è CORRETTO | parser 0,006-0,010 USD contro 0,023-0,037 | — | tenere il parser per le stampe PVRM320; la descrizione 060 è letta uguale nei due run: l'ERRATO dipende dal documento di confronto (da capire) |
| 2026-11-21 | stessa operazione (060, ciclo DR vero), stesso documento e stessa pagina, 3 ripetizioni per ognuna delle due letture del ciclo | — | ERRATO 2 volte su 3 con la lettura del modello, 1 su 3 con quella del parser: il modello oscilla, l'ingresso conta poco | 0,007-0,010 USD per run | — | G1: un ERRATO deve essere confermato |
| 2026-11-21 | G1 sul PC: op. 060 del ciclo DR vero, condition 3, ciclo letto dal parser, 3 run | — | CORRETTO, CORRETTO, WARNING `GIUDIZIO_INSTABILE`; 0 ERRATO | 0,007-0,011 USD per run; la conferma aggiunge 2 sessioni solo dove serve | — | G1 confermata |
