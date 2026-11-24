# Migliorie

Questo file spiega **come si migliora la v2**: come si prova una modifica, come si decide se
tenerla, cosa è già stato fatto, cosa resta da fare e in che ordine. In fondo c'è il **registro**
di tutte le prove già decise.

I comandi da lanciare sul PC sono in `COPILOT.md` (sezione 2.3). Come funziona il programma è
in `DOCUMENTAZIONE.md`.

---

## Indice

1. Le parole che servono
2. Come si prova una miglioria, passo per passo
3. Gli errori da trovare: visti e mai visti
4. I due insiemi di cicli
5. Le misure di una prova
6. La regola per decidere
7. Da provare adesso
8. Ordine consigliato
9. Già fatto
10. Da fare più avanti
11. Dove sta il codice
12. Misure di partenza (novembre 2026)
13. Registro degli esperimenti

---

## 1. Le parole che servono

| Parola | Cosa vuol dire |
|---|---|
| **Miglioria** | una modifica alla v2 che dovrebbe far trovare più errori, oppure costare meno, oppure andare più veloce |
| **Variante** | il modo di provare una miglioria: un file `eval/varianti/<nome>.yaml` che cambia **una cosa sola** delle impostazioni |
| **Proposta** | la parte della variante che spiega la miglioria: `descrizione` (cosa cambia), `ipotesi` (perché dovrebbe migliorare), `atteso` (cosa deve cambiare nei numeri) |
| **Base** | la v2 di oggi, senza modifiche. Ogni variante si confronta con la base. Il suo file è `eval/varianti/baseline.yaml`; sul PC la prova della base si chiama `base` |
| **Prova** | un giro della v2 su un gruppo di cicli, con una variante. Conta errori trovati, falsi errori, costo e tempo |
| **Ripetizione** | la stessa prova fatta un'altra volta. Serve perché il modello non risponde sempre uguale |
| **Errore stabile** | un errore trovato in **tutte** le ripetizioni di una variante |
| **Generalizzare** | trovare anche errori che nessuno ha usato per scrivere le migliorie. Se una miglioria trova solo gli errori che conosciamo, ha «imparato la lista» |
| **Modello** | l'intelligenza artificiale che confronta i testi: Claude Haiku su Amazon Bedrock (il servizio di AWS) |
| **Sessione** | una domanda al modello su una operazione del ciclo, con le sue risposte |
| **Ragionamento** (`effort`) | quanto il modello «pensa» prima di rispondere: `low` (poco), `medium`, `high` o predefinito. Più ragionamento costa di più |
| **Token** | i pezzetti di testo che il modello legge e scrive. Il costo dipende dai token |
| **Parser** | il pezzo di codice che legge la stampa PVRM320 senza modello: costa zero e legge sempre uguale |
| **Conoscenza** | i manuali preparati con l'ingestion, con cui la v2 confronta il ciclo |
| **Falso errore** | un ERRATO su una stampa giusta. Deve essere 0 |

---

## 2. Come si prova una miglioria, passo per passo

1. **Si sceglie la miglioria** dalla sezione 7 («Da provare adesso»).
2. **Si scrive la variante.** Se cambia solo le impostazioni, basta il file
   `eval/varianti/<nome>.yaml`. Se serve codice nuovo, lo scrive Claude, e la variante lo
   accende: la base non cambia.
3. **Si scrive la proposta** nel file della variante: cosa cambia, perché, cosa ci si aspetta.
   Esempio:

   ```yaml
   nome: effort_medio
   descrizione: ragionamento medium nei controlli invece di low
   ipotesi: "con low il modello a volte non vede le frasi al contrario"
   atteso: "più errori stabili; costo sotto il doppio della base"
   base: baseline
   agent:
     effort: medium
   ```

4. **Due prove sull'insieme piccolo** (COPILOT 2.3 A con `$nome` = il nome della variante).
   Stessi cicli e stessa conoscenza della base.
5. **Si guarda il riepilogo** (COPILOT 2.3 C). Il programma decide da solo con la regola della
   sezione 6: «si tiene», «non si tiene», «scartata» o «da ripetere».
6. **Se si tiene sul piccolo:** due prove sull'insieme grande, poi di nuovo il riepilogo.
7. **Claude scrive nel registro** (sezione 13) la decisione e le considerazioni: cosa si è
   capito, perché è andata così, cosa fare dopo.
8. **Se entra nella base:** si archiviano le prove, si fanno copie cieche nuove con un seme
   nuovo e si rifà la base (COPILOT, fase 3).

Prima delle prove, gratis: i test (`uv run pytest -q`) e, per una miglioria sulle descrizioni,
il comando `leggi --lingue`.

Sul computer personale, con i casi inventati, le varianti si provano anche con `eval pipeline`
(`AZIENDA.md`, parte B).

---

## 3. Gli errori da trovare: visti e mai visti

Ogni prova conta quanti errori messi apposta la v2 trova. Gli errori sono di due specie.

**Visti.** I 12 errori noti di `eval/errori-noti.yaml`, in 7 cicli «con errori». Chi scrive le
migliorie (Claude) li conosce, quindi può adattarsi a loro senza volerlo.

**Mai visti.** Misurano se la v2 **generalizza**. Sono di due tipi:

- **Copie cieche** (comando `eval muta`, codice in `evaluation/blind.py`). Il programma prende i
  cicli veri e fa delle copie con **una sola** operazione cambiata, in un modo che è sicuramente
  sbagliato. Ogni copia contiene solo l'operazione cambiata, quindi costa come una operazione.
  Da uno stesso ciclo al massimo 6 copie; dei due tipi del codice al massimo 5 copie ciascuno,
  così il resto va ai tipi del modello (dal 24-11: prima erano 2 per ciclo, e su 16 cicli
  uscivano solo 3 copie «numero del manuale»).
  Quali operazioni cambiare dipende da un numero chiamato **seme**: con lo stesso seme le copie
  sono sempre le stesse, con un seme nuovo sono nuove. Quando una miglioria entra nella base si
  cambia seme.
- **Gruppo nascosto.** Stampe con errori messi a mano da te o da un collega, in `data/nascosti`
  sul PC. Claude non le vede mai.

I tipi di copie cieche:

| Tipo | Cosa cambia | Chi lo deve trovare | Conta per la generalizzazione? |
|---|---|---|---|
| `numero_una_lingua` | un numero, solo nel testo italiano o solo in quello inglese | il **codice** (`INCOERENZA_LINGUE`) | no: il codice lo trova con la stessa regola che l'ha messo. Serve solo a vedere che non si è rotto niente |
| `numero_manuale` | un numero che c'è nelle due lingue e nel manuale, cambiato in tutte e due con un valore che il manuale non ha | il **modello** | sì |
| `negazione_una_lingua` | un «non» (o «not») tolto in una lingua sola | il **modello** | sì |
| `task_inesistente` | il codice di un task cambiato in uno che non esiste, mentre i task vicini esistono | il **codice** (`TASK_INESISTENTE`) | no, come sopra |

I due tipi del codice sono elencati in `CODE_KINDS` (`evaluation/blind.py`). **La
generalizzazione la misurano i tipi del modello e il gruppo nascosto.**

I report danno solo **quanti** errori mai visti ci sono per tipo, mai quali sono.

---

## 4. I due insiemi di cicli

| Insieme | Quali cicli | A cosa serve |
|---|---|---|
| **piccolo** | i 10 cicli noti (7 «con errori» e 3 giusti), le copie cieche e il gruppo nascosto | **ogni** miglioria passa da qui. È veloce |
| **grande** | i 10 noti e **tutti** i cicli veri civili con almeno l'80% delle operazioni confrontabili con la conoscenza (comando `eval scegli`) | solo le migliorie che si tengono sul piccolo: si controlla che sui cicli veri non aumentino ERRATO e WARNING |

Su un ciclo vero nessuno conosce gli errori: un suo ERRATO è «da verificare» (quasi sempre è un
falso errore), e i suoi WARNING sono lavoro a mano.

Regole:

- le prove si confrontano **solo sullo stesso insieme**. Le cartelle sono `runs/prove-piccolo`
  e `runs/prove-grande`;
- il riepilogo avvisa se in una cartella ci sono prove fatte su cicli diversi;
- quando cambiano il seme o la conoscenza, le prove vecchie si archiviano (COPILOT 2.3 F).

Ogni prova scrive il suo report (`<data>-<nome>/prestazioni.md`, con la proposta in cima).
`riepilogo.md` mette insieme le prove, fa la classifica e dà la scelta migliore. Una miglioria
con un file `eval/varianti/<nome>.yaml` si lancia con `--variante`, sopra le impostazioni del PC.

---

## 5. Le misure di una prova

| Misura | Cosa vuol dire |
|---|---|
| **Trovati** | errori noti con un ERRATO sulla loro operazione. Sono contati a parte: i **visti**, i **mai visti per il modello** (copie «numero del manuale» e «negazione», gruppo nascosto) e i mai visti per il codice |
| **Mancati** | errori noti senza ERRATO. Il report dice cosa ha risposto la v2 |
| **Falsi errori** | ERRATO su un'operazione di una stampa giusta. Deve essere 0. Non contano le operazioni «in attesa» di una risposta delle persone (`in_attesa` in `eval/errori-noti.yaml`): oggi l'op. 050 della stampa giusta `04ecaabe` (domanda P7) |
| **Da verificare** | ERRATO fuori dalla lista: nei cicli con errori (un errore vero che non è in lista, o un falso errore) e nei cicli veri (quasi sempre falsi). Si guarda; se è un errore vero, il ciclo va nella lista |
| **Precisione** | trovati diviso (trovati + falsi errori + da verificare) |
| **Warning per ciclo senza errori** | WARNING medi sulle stampe giuste e sui cicli veri: il lavoro a mano che resta |
| **Costo e tempo per ciclo** | la media, più il tempo del ciclo più lento |
| **Token riletti dalla cache** | dice se la cache dei prompt funziona (questi token costano circa un decimo) |
| **Non eseguiti** | cicli andati in errore |

---

## 6. La regola per decidere

Una **variante** è l'insieme delle prove con lo stesso nome. Il riepilogo decide così, in
ordine:

1. **Scartata** se succede anche una sola di queste cose:
   - un falso errore;
   - un ciclo non eseguito;
   - un ciclo che dura più di 10 minuti (il frontend aspetta al massimo 11);
   - un costo per ciclo più del doppio della base.
2. **Da ripetere** se ha meno di 2 prove.
3. **Classifica**, in quest'ordine (al primo che è diverso si decide):
   1. più errori **stabili** (trovati in tutte le prove);
   2. più errori trovati nella prova peggiore;
   3. più errori trovati in media;
   4. meno ERRATO da verificare;
   5. meno warning per ciclo senza errori;
   6. meno costo;
   7. meno tempo.
4. **Si tiene** solo se:
   - non ha meno errori stabili della base;
   - non ha meno errori **mai visti per il modello** stabili della base (se no: «non
     generalizza»);
   - sta sopra la base in classifica.

La **scelta migliore** è la prima della classifica che si tiene (oppure la base, se nessuna la
batte).

I numeri della regola sono nel codice, in `evaluation/trials.py`: `MIN_REPETITIONS` (2),
`MAX_CYCLE_MS` (10 minuti), `MAX_COST_RATIO` (2).

---

## 7. Da provare adesso (lista del 23-11-2026)

### 7.1 Come si scelgono le migliorie (dal 23-11)

**Non** dagli errori noti che mancano. Una miglioria fatta per un errore preciso trova
quell'errore, ma non dice niente sugli altri: è «imparare la lista».

Si fa così:

1. si fa la base;
2. si guarda nel report la tabella «Errori mai visti, per tipo»;
3. si sceglie una miglioria per il tipo «modello» trovato **peggio**;
4. si prova, e si guarda di nuovo la tabella.

Per questo motivo il 23-11 sono state tolte sei migliorie pensate sugli errori noti:
`negazioni_lingue`, `classi_lingue`, `prompt_confronto`, `contesto_sezione`, `fatti_incerti` e
`modello_grande_sui_dubbi`.

Per ognuna: due prove sul piccolo con `$nome` = il nome; se si tiene, due sul grande.

### 7.2 Subito: basta il file della variante (nessun codice nuovo)

| `$nome` | Cosa cambia | Cosa può migliorare | Rischio |
|---|---|---|---|
| `effort_medio` | ragionamento `medium` nei controlli invece di `low` | frasi al contrario, parole cambiate | costa e dura di più |
| `conferme_1` | un ERRATO del modello si conferma con 1 sessione in più invece di 2 (G1) | meno costo; errori che il modello vede solo a volte | falsi errori (devono restare 0) |
| `testo_lungo` | fino a 400 righe di manuale nella domanda invece di 150 | più contesto in una volta: limiti scritti lontano dal passo | costo per sessione |
| `effort_pieno` | ragionamento predefinito ovunque (controlla B2) | conferma che `low` non perde errori su Bedrock | costo |
| `prompt_task_mancante` | se il task citato manca nel manuale, il modello giudica lo stesso (A2) invece di dare subito WARNING (B6) | operazioni che oggi escono `FONTE_ASSENTE` | falsi errori, costo |
| `concorrenza_12` | 12 operazioni controllate insieme invece di 6 (B4) | solo il tempo | limiti di Bedrock: cicli non eseguiti |

`sonnet` (un modello più grande) **non ora**: costa circa 10 volte per ciclo (la regola scarta
sopra 2 volte) e serve il codice di Sonnet abilitato su Bedrock.

### 7.3 Con codice nuovo (lo scrive Claude; la variante lo accende, la base non cambia)

| `$nome` | Cosa fa | Cosa può migliorare | Costo del lavoro |
|---|---|---|---|
| `numeri_manuale` (I4, è H12) | confronta i numeri e le classi della descrizione con quelli del passo del manuale. Alla sessione passa le differenze da guardare; se tutto coincide, CORRETTO senza modello | numeri cambiati in tutte e due le lingue (tipo cieco «numero del manuale»). È generale: 7 errori noti su 10 sono numeri, classi o codici. E servono meno sessioni | medio |

Le migliorie successive si decidono dopo la base, dai tipi «modello» trovati peggio.

### 7.4 Tempo e costo (dopo: non cambiano gli errori trovati)

In ordine: B1 (chiamata diretta a Bedrock), poi B4; H10 (cache dei prompt), H14 (più operazioni
in una sessione). Si provano con le stesse prove: devono tenere gli stessi errori stabili e
costare o durare meno.

Cosa c'è già e cosa resta, per costo e tempo (aggiornato al 23-11; nelle novità sull'IA di
settembre-novembre non c'è altro che si possa usare con Bedrock):

| Tecnica | Stato | Effetto |
|---|---|---|
| GRASP: dopo una ricerca nel manuale si legge solo un pezzo di righe, mai il file intero (`agent/hooks.py`) | in uso | meno token per sessione |
| Testo del task nella domanda, fino a 150 righe (`inline_max_lines`): il modello non deve cercare | in uso | sessioni di 1-3 scambi |
| Parser PVRM320 al posto del modello per leggere la stampa | in uso | lettura a zero token, sempre uguale |
| Controlli senza modello: lingue, task inesistente, task mancante (B6) | in uso | zero token quando l'esito è sicuro |
| `effort: low` nei controlli (B2) | in uso, da confermare (`effort_pieno`) | circa -30% di costo |
| Conferma solo sugli ERRATO (G1) | in uso | costa solo dove serve |
| **B1** chiamata diretta a Bedrock (`converse`) per le sessioni con il testo nella domanda | da fare | toglie circa 4 secondi di avvio per operazione: il guadagno di tempo più grande |
| **H10** cache dei prompt di Bedrock (istruzioni e testo del manuale uguali tra le sessioni) | da misurare: il report della prova dà i token riletti dalla cache; se sono pochi, si attiva con B1 | i token in cache costano circa un decimo |
| **H12** CORRETTO senza modello quando numeri e testo coincidono con il manuale | da fare (con I4) | meno sessioni |
| **H13** risultato già calcolato (stesso PDF, stessa conoscenza, stesse impostazioni) | da fare | risposta subito quando si riapre un ciclo |
| **H14** più operazioni dello stesso task in una sessione | da misurare (rischio: il modello confonde le operazioni) | meno sessioni, testo mandato una volta |
| **B4** più operazioni insieme (dopo B1) | da misurare | meno tempo, stesso costo |
| Batch di Bedrock per le prove (non per il servizio) | da fare dopo B1 | circa -50% sul costo delle prove |
| Inferenza «latency-optimized» di Bedrock | da verificare con AWS: forse non c'è per i modelli e la regione abilitati | meno attesa |

### 7.5 Errori che nessuna miglioria può trovare (per ora)

Questi errori noti mancano per motivi che non dipendono dalla v2:

- **f355dc3c op. 040, e forse 010:** servono documenti che non sono nella conoscenza (capitolo
  70-23 dell'SPM, manuale d'ispezione del motore, due REPAIR della sezione 72-56-31). Si fa
  l'ingestion, poi COPILOT 2.5 e una prova `conoscenza-<data>`.
- **c5ff3cd6 op. 030** (scheda tolta): aspetta la regola della domanda P6.
- **f355dc3c op. 050:** aspetta la risposta alla domanda P7 («4 volte» c'è anche nella stampa
  giusta).

---

## 8. Ordine consigliato

**Prove sui cicli veri** (lo stesso ordine di COPILOT, sezione 1):

1. la base, sul piccolo e sul grande;
2. le varianti senza codice: `effort_medio`, `conferme_1`, `testo_lungo`, `effort_pieno`,
   `prompt_task_mancante`, `concorrenza_12`;
3. `numeri_manuale`;
4. le migliorie scelte sui tipi «modello» trovati peggio;
5. tempo e costo.

**Il resto**, dopo i punti per la consegna (`MEMORIA.md`, sezione 1):

1. casi veri rivisti nella suite (`eval prepara` e revisione): senza, le misure di `eval
   pipeline` valgono solo sui dati inventati. Poi la baseline aziendale;
2. B2 su Bedrock: baseline contro `effort_pieno`;
3. B1, poi B4;
4. F4: quando c'è un ciclo LEAP vero;
5. D, togliere le rotte storiche, quando il frontend è pronto;
6. E1, dopo i casi aziendali rivisti;
7. le idee H: H1 e H3 sono le più semplici e tolgono problemi già visti; H4 e H5 dopo il
   passaggio in produzione.

---

## 9. Già fatto

Ogni miglioria ha un codice (Id) che si usa nei documenti e nel codice.

| Id | Cosa è stato fatto |
|---|---|
| A1 | il controllo di sicurezza delle sessioni non blocca più lo strumento con cui il modello risponde quando cerca nel manuale (casi MOS in ricerca: da 14 su 19 a 19 su 19) |
| A3 | targa che non c'è da nessuna parte (né nei dati TM né tra le macchine attive): WARNING `TARGA_SCONOSCIUTA`. ERRATO solo se è nei dati TM e non è attiva (20-11-2026) |
| A4 | tempi massimi: 90 secondi per sessione, 300 secondi per leggere il PDF, poi errore tecnico (se Bedrock è più lento, si alzano) |
| A5 | `pytest -m live`: prova con il modello vero, da fare dopo ogni aggiornamento della libreria o del modello |
| A6 / B5 | anche il DR si legge con il parser PVRM320, come MOS ed EJ200 (verificato su una stampa DR vera il 16-11). Il modello resta come riserva |
| B2 | ragionamento `low` nei controlli e `high` nella lettura del PDF, acceso di default (20-11-2026; da confermare su Bedrock) |
| B3 | le pagine fotografate si trascrivono in parallelo (`agent.transcribe_concurrency`, 4 alla volta) |
| B6 | task citato che il manuale non ha: WARNING `FONTE_ASSENTE` subito, senza modello (scelto il 20-11-2026 al posto di A2, che resta nella variante `prompt_task_mancante`) |
| B7 | la conoscenza si scarica all'avvio del servizio; con un file non valido il servizio non parte |
| D | `API_MAX_WORKERS` usato, testo delle sessioni non salvato nel servizio, codice inutile tolto, controllo dei tipi (mypy) pulito, accesso dal frontend |
| F1 | voci incerte dell'indice (`uncertainty.json`): `DATO_INCERTO` su targa, scheda o fonte (mai sul DR, che blocca il ciclo). Un file incoerente: un messaggio nel log del servizio, un errore in `kb-check` |
| F2 | il trattamento della scheda si controlla solo per la famiglia del motore del ciclo |
| F3 | i task di un DR senza manuale si cercano nei manuali citati dall'operazione |
| F4 | documento LEAP intero come contesto quando la fonte non ha task. **Da verificare su un ciclo LEAP vero** |
| — | servizio avviato dalle variabili d'ambiente, Redshift letto con la Data API, secret letto all'avvio |
| G1 | conferma delle contraddizioni: un ERRATO sulla descrizione si rifà con 2 sessioni uguali (`agent.confirm_contradiction`). Se una delle due non ritrova la contraddizione: WARNING `GIUDIZIO_INSTABILE`. Costa solo sugli ERRATO (21-11-2026, dopo l'op. 060 del ciclo DR vero) |
| G2 | DR `Accept as is` come WARNING senza bloccare il ciclo: provato il 21-11-2026, **tolto il 22-11-2026** perché l'utente ha confermato la regola della v1 (vedi G3) |
| G3 | DR (22-11-2026): `Accept as is` torna ERRATO e blocca il ciclo, come `Reject` (regola della v1). Serial number e condition diventano facoltativi: il serial number, se manca, si prende dalla stampa (`APPLY ON S/N`). Senza serial number, o senza condition quando le recommendation sono diverse: WARNING `DR_NON_VERIFICATA` e gli altri controlli continuano. Il frontend può togliere l'obbligo dei due campi |
| G4 | risposta adattata al frontend di oggi (22-11-2026, dalle risposte di Copilot sul codice del frontend): `N/A` esatto per i campi vuoti e per i controlli fermati dal DR (bollino grigio, come la v1); `N/A - motivo` per quelli esclusi da una regola (bollino azzurro `Info`); esito DR nella riga della fonte DR con `DRCase` e `serialNumber` (il frontend non legge `drRecommendationFeedback`); `scheda.tabNumber`; il passo DR della conversazione è accettato anche con i due campi vuoti |
| G5 | (22-11-2026) serial number letto dalla stampa in più forme (`S/N:`, `S / N.`, con trattino); con più serial number vale quello che ha recommendation nei dati DR. `leggi --cerca` stampa le righe con un testo, con i codici nascosti. `scheda.task` = il codice dopo «SP.ORIG.» nei cicli civili, come la v1 |
| G6 | (22-11-2026) comando `confronta <giusto.pdf> <con errori.pdf>`: confronta due stampe dello stesso ciclo con il parser (zero token) e dice in quali fonti, operazioni e campi sono diverse, con i codici nascosti e solo i pezzi di descrizione che cambiano. Serve a sapere dove sono gli errori dei cicli «con errori» |
| G7 | (22-11-2026) `leggi --struttura N`: mostra come il parser vede ogni riga della pagina N (tipo di riga, numero di operazione, prima parola nascosta), senza il testo del ciclo. `confronta` dice quale delle due stampe il parser non riesce a leggere |
| G8 | (22-11-2026) stampa modificata a mano: se nel PDF le righe sono in un ordine diverso da quello della pagina, la lettura le rimette in ordine di posizione e unisce i pezzi della stessa riga (`ingest/pdf.py`); `leggi` dice quali pagine. Le stampe normali restano come prima |
| G9 | (22-11-2026) comando `macchine`: elenco delle macchine attive da Redshift per le prove sul PC, con il secret e la tabella della v1 e la Data API. `leggi --breve` e `--senza-riordino`. Nelle pagine rimesse in ordine una riga senza colonne resta nell'operazione in corso |
| G10 | (22-11-2026) il titolo «OPERAZIONE EVENTUALE» diventa un blocco a sé, attaccato all'operazione dopo. `confronta --primo-senza-riordino`. `macchine` prende `SECRET_NAME` dal secret «di ambiente» della v1 e il database dalla connessione della v1 (o da `--database`). Nelle descrizioni rimesse in ordine si tolgono gli asterischi di cornice e le righe fatte solo di segni. Il riordino recupera nelle stampe DR testo che prima si perdeva |
| G11 | (22-11-2026 sera) accesso come la v1: `API_AUTH=sdk` con `chatbot_ai_sdk` (token dal cookie, permessi da `permissions.json`, utente da `current_user`), scelto da solo quando c'è il secret della v1. `CV_ENV_SECRET` per leggere all'avvio il secret «di ambiente» della v1. `macchine` segue il database fino alla funzione delle credenziali della v1 |

---

## 10. Da fare più avanti

### 10.1 Da confermare su Bedrock

- **B2, ragionamento ridotto** (acceso dal 20-11-2026): `effort: low` nei controlli,
  `extraction_effort: high` nella lettura del PDF. Sui casi inventati: -31% di costo, stessa
  concordanza. Si conferma con la variante `effort_pieno` (sezione 7.2). Se la base trova meno
  errori di `effort_pieno`, si torna indietro lasciando vuoti i due campi in
  `config/settings.yaml`.

### 10.2 Da costruire

| Id | Cosa | Perché | Costo del lavoro |
|---|---|---|---|
| B1 | chiamata diretta a Bedrock (`converse`) per le sessioni con il testo nella domanda; l'agente resta solo per i testi lunghi | toglie l'avvio di 4 secondi per operazione: circa metà del tempo. È il guadagno più grande | medio: un secondo adattatore dietro `AgentSession` |
| B4 | `agent.concurrency` sopra 6 (più operazioni insieme) | 40 operazioni: 21 secondi con 6, 12 secondi con 12. Il limite sono le quote di Bedrock | una riga, ma dopo B1 (sui casi inventati `concorrenza_12` è stata scartata) |
| B8 | `golden` e i casi degli esperimenti in parallelo | esperimenti più veloci; il servizio non cambia | piccolo |
| T1 | tempo massimo per tutta la validazione, sotto i 600 secondi del backend v1 e i 660 del frontend: allo scadere si chiude con quello che c'è (WARNING sui controlli non finiti) invece di essere tagliati dal server | oggi una validazione lunga verrebbe interrotta senza risposta | piccolo. Misurato il 22-11-2026: al massimo 131 secondi su un DR da 9 operazioni. Serve quando si vedrà un ciclo MOS lungo vicino ai 600 secondi |
| D | togliere le rotte storiche (`/upload`, `/ej200/upload`, `/conversation`) | pulizia | **non ora**: il frontend di oggi usa proprio queste rotte (22-11-2026) |

### 10.3 E1. Varianti proposte dal modello (`eval proponi`), più avanti

L'idea viene dal paper Harness² (Google Research, arXiv 2610.14224): il modello propone
modifiche ai propri prompt e il programma le prova. Da noi la scelta resta alla classifica con
la regola della sezione 6; il modello fa solo **la proposta**.

- Il comando leggerebbe l'ultimo risultato della base (righe sbagliate, instabili, citazioni non
  ritrovate), i tre prompt e l'elenco delle varianti già provate, e scriverebbe due varianti in
  `eval/varianti/proposte/`: una generale e una per un solo tipo di ciclo.
- Rifiuterebbe una proposta che tocca altro oltre ai tre prompt, cambia più di 20 righe, non cita
  almeno due righe sbagliate o ripete una variante già scartata.
- Per non adattarsi ai casi: il modello che propone vede i casi inventati e le mutazioni; la
  proposta deve passare anche sui casi aziendali, che non ha visto. Chi propone deve essere un
  modello diverso da quello dei controlli.
- Niente nel servizio: tutto in `eval/`. Mettere una proposta in `prompts/` resta una scelta
  umana.
- Prima servono i casi aziendali rivisti: sui casi inventati la concordanza è già 99,5-100%. Se
  dopo tre giri nessuna proposta viene ammessa, l'idea si toglie.

### 10.4 Idee tecniche nate dalle prove sul PC (22-11-2026)

Da decidere: nessuna serve per la consegna. In ordine di valore.

| Id | Idea | Perché (cosa si è visto) | Costo del lavoro |
|---|---|---|---|
| H1 | **Macchine attive come file su S3.** Un lavoro automatico (per esempio ogni notte) scrive l'elenco delle macchine attive accanto alla conoscenza; la v2 lo legge come le targhe (`MACHINES_SOURCE=file`, già pronto) | dal PC Redshift non si raggiunge: oggi le targhe sul PC escono sempre WARNING. Con il file: niente driver, niente password, prove complete anche sul PC. Una macchina dismessa non cambia di ora in ora | piccolo lato v2 (c'è già); il lavoro automatico lo fa chi gestisce il datalake |
| H2 | **Ingestion guidata dalla domanda.** Il servizio conta i manuali `FONTE_ASSENTE` e scrive ogni giorno la classifica dei più chiesti; l'ingestion parte da lì | fare l'ingestion di tutto costa troppo (circa 2000 file), e i cicli «con errori» non si misurano senza i loro manuali. Il comando `manuali` lo fa a mano sul PC | piccolo |
| H3 | **`kb-check` dentro l'ingestion**, prima di pubblicare la nuova versione (`current.json`) | oggi la v2 rifiuta all'avvio una conoscenza rotta (B7): meglio che una versione rotta non venga mai pubblicata. Errori come la targa «90» si vedrebbero subito | piccolo, lato knowledge-index |
| H4 | **Prova «ombra» in QA:** la v2 riceve una copia delle richieste fatte alla v1; l'utente vede solo la v1; i due esiti si confrontano | misura la v2 su cicli veri senza rischi e senza chiedere niente agli utenti | medio: un secondo servizio e un confronto |
| H5 | **Validazione come lavoro in coda:** la richiesta risponde subito con un numero, il frontend chiede lo stato («operazione 12 di 40»); i lavori stanno in una coda con più esecutori | oggi una richiesta resta aperta fino a 10 minuti con un esecutore solo: T1 non servirebbe più e si regge più traffico | medio-grande: serve anche il frontend |
| H6 | **Il ciclo dai dati strutturati invece che dal PDF**, se il sistema che stampa PVRM320 ha le stesse informazioni in una tabella (forse nel datalake) | metà dei problemi visti sono di lettura: stampe modificate a mano, righe fuori ordine, colonne tolte. Da chiedere alle persone | dipende da dove sono i dati |
| H7 | **Gli esperimenti dentro AWS** invece che sul PC: stessi comandi `eval`, escono solo le misure | EJ200 e Redshift non si possono provare fuori da AWS; sul PC ogni prova passa dalle foto | medio |
| H8 | **Il feedback del frontend diventa un caso di prova:** una risposta segnata sbagliata dall'utente finisce in una cartella per `eval prepara` | i casi aziendali rivisti sono quello che manca di più agli esperimenti | piccolo-medio |
| H9 | **OpenSearch solo come riserva:** quando il task non c'è o la fonte non ha task (F4, LEAP), la ricerca propone i passi candidati, e la citazione si controlla sempre come oggi | la ricerca per codice dà citazioni verificabili, che è il punto della v2; una ricerca «per somiglianza» da sola riporterebbe il problema della v1 (passi simili, ma non quelli giusti). Da misurare con le varianti | medio, più il costo del servizio |
| H10 | **Cache dei prompt di Bedrock** per le parti uguali tra le sessioni dello stesso ciclo, e **batch di Bedrock** per gli esperimenti | meno costo e meno tempo; da vedere quanto la cache funziona già | piccolo, dopo B1 |
| H11 | **Python 3.14 in `.python-version`** (oggi c'è 3.13) | tutti i PC e il Dockerfile della v1 usano 3.14: ogni blocco di COPILOT ripete `$env:UV_PYTHON` | piccolo: prima provare tutti i test su 3.14 |
| H12 | **Numeri e codici confrontati dal codice** prima del modello (in parte fatto il 23-11 tra le due lingue, `INCOERENZA_LINGUE`; il resto è `numeri_manuale`, I4, sezione 7.3) | 7 dei 10 errori dei cicli «con errori» sono numeri, lettere o codici cambiati: il codice li trova in pochi millesimi di secondo e sempre allo stesso modo; il modello costa e a volte cambia risposta (G1) | medio; da misurare con le copie cieche |
| H13 | **Risultato già calcolato:** stesso PDF, stessa conoscenza, stesse impostazioni → la risposta salvata, subito | lo stesso ciclo si ricarica spesso (prove, riaperture) | piccolo |
| H14 | **Più operazioni dello stesso capitolo in una sessione** | meno sessioni e lo stesso testo del manuale mandato una volta sola. Rischio: il modello confonde le operazioni. Solo con una variante misurata | medio |

### 10.5 Punti aperti nel progetto dell'indice (knowledge-index, si fanno lì)

- `aliases.json`: i nomi con cui i cicli veri citano manuali e documenti, LEAP compresi.
- Gli intervalli dei task (riga iniziale e finale) misurati sui manuali veri.
- Le 4 voci RDR marcate «detected OTHER»: capire che documenti sono.

---

## 11. Dove sta il codice

Come funziona la v2, passo per passo, è in `DOCUMENTAZIONE.md`. Qui solo dove sta ogni parte
(cartella `src/cycle_validation/`):

| Dove | Cosa c'è |
|---|---|
| `domain/check.py` | gli esiti e i motivi (`Reason`), e quale esito dà ogni motivo |
| `checks/` | un file per ogni controllo; `uncertainty.py` per le voci incerte dell'indice |
| `agent/` | le sessioni del modello: prompt, controlli di sicurezza, tempi massimi, Claude Agent SDK |
| `kb/` | la conoscenza: `published.py` (il puntatore `current.json`), `ej200.py`, `local.py` (da una cartella), `structured.py` |
| `services/` | le macchine attive: da file o da Redshift |
| `api/` | il servizio web (FastAPI); `production.py` lo avvia dalle variabili d'ambiente |
| `evaluation/` | gli esperimenti: casi, varianti, misure, classifica, copie cieche, guasti, prove (`trials.py`) |
| `prompts/`, `config/` (fuori da `src/`) | i tre prompt, `settings.yaml`, i profili |

---

## 12. Misure di partenza (14-15 novembre 2026)

Misurate sul computer personale, con Claude Haiku con login locale (non Bedrock) e solo dati
inventati.

| Misura | Valore |
|---|---|
| Tutto il codice, senza modello, ciclo da 40 operazioni | 30 millisecondi |
| Ciclo di esempio da 4 operazioni | 12,7 secondi, di cui 8,9 di controlli |
| Una sessione: avvio del processo + risposta | circa 4 + 3 secondi |
| Costo di una sessione con il testo nella domanda | 0,0006-0,0012 dollari |
| Casi inventati con l'esito atteso: MOS / DR / EJ200 uguali all'atteso | 19 su 19, 29 su 29, 22 su 22 |

Il tempo non è nel codice: metà è l'avvio di un processo dell'agente per ogni operazione (è
quello che toglie B1). Con Bedrock latenze e prezzi cambiano.

---

## 13. Registro degli esperimenti

Una riga per ogni prova decisa, confrontata con la base dello stesso giro.

- **Decisione:** si tiene, scartata o da ripetere (dal riepilogo).
- **Considerazioni:** cosa si è capito, perché è andata così, cosa fare dopo.
- La proposta (cosa cambia, ipotesi, atteso) sta nel file della variante e compare in cima a
  `prestazioni.md` e nel riepilogo.
- Le considerazioni le scrive Claude qui, dalle foto, quando la variante è decisa.

| Data | Esperimento | Variante | Concordanza | Costo | Tempo | Decisione | Considerazioni |
|---|---|---|---|---|---|---|---|
| 2026-11-14 | `effort: low` (prova veloce, una volta sola) | — | MOS 18-19 su 19 | -30% | -27% per sessione | da ripetere | una prova sola non basta: rifatta con il metodo sopra |
| 2026-11-14 | `effort: low`, casi sintetici, 3 ripetizioni, login locale | `effort_low` | 99,5% (come baseline) | -22% | -9% | ammessa | più veloce; da confermare su Bedrock con casi veri |
| 2026-11-14 | concorrenza 12 | `concorrenza_12` | 99,0% | -17% | uguale | scartata | concordanza più bassa; da rifare dopo B1 |
| 2026-11-14 | modello Sonnet | `sonnet` | 98,6% | ×10 | -17% | scartata | concordanza più bassa e costo troppo alto |
| 2026-11-14 | `effort: low`, un ciclo MOS di prova letto dal PDF, 2 ripetizioni | `effort_low` | 97,6% (baseline 100%) | -22% | -11% | scartata | un ERRATO falso ("Targa -" letta come targa) ed estrazione 87,5%; causa corretta nel codice, da rimisurare |
| 2026-11-15 | giro 3, stesso ciclo di prova, 2 ripetizioni, login locale | `effort_low` | 100% | -33% | +25% | ammessa | il "-" letto come targa c'è ancora, ma ora vale "targa assente"; tempi su un caso solo troppo rumorosi per decidere |
| 2026-11-15 | come sopra | `effort_low_controlli` | 100% | -31% | +26% | ammessa | non legge più il "-"; da misurare in azienda contro `effort_low` |
| 2026-11-15 | come sopra | `prompt_task_mancante` | 100% | -30% | +66% | ammessa | il tempo è rumore (cambia una sola sessione); serve `fonte_e_codice_assenti` con più ripetizioni |
| 2026-11-15 | come sopra | `guasti` | — | — | — | regge | 0 ERRATO falsi, 4,5 esiti tecnici per ripetizione |
| 2026-11-21 | ciclo DR vero, Bedrock Haiku 5.5, sottoinsieme della conoscenza: ciclo letto dal modello contro ciclo letto dal parser, 2 condition Repair | parser | parser: due run identici (5 corretti, 0 errati); modello: run diversi tra loro e un ERRATO (op. 060) che col parser è CORRETTO | parser 0,006-0,010 USD contro 0,023-0,037 | — | parser per le stampe PVRM320 | la descrizione 060 è letta uguale nei due run: l'ERRATO dipende dal documento di confronto (da capire) |
| 2026-11-21 | stessa operazione (060, ciclo DR vero), stesso documento e stessa pagina, 3 ripetizioni per ognuna delle due letture del ciclo | — | ERRATO 2 volte su 3 con la lettura del modello, 1 su 3 con quella del parser | 0,007-0,010 USD per run | — | G1: un ERRATO deve essere confermato | il modello oscilla, l'ingresso conta poco |
| 2026-11-21 | G1 sul PC: op. 060 del ciclo DR vero, condition 3, ciclo letto dal parser, 3 run | — | CORRETTO, CORRETTO, WARNING `GIUDIZIO_INSTABILE`; 0 ERRATO | 0,007-0,011 USD per run | — | G1 confermata | la conferma aggiunge 2 sessioni solo dove serve |
