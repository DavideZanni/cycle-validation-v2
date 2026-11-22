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
  targhe escono WARNING `ERRORE_TECNICO` e il ciclo è `parziale`. La v1 le prende da una
  tabella con il filtro `work_center_usage_cd = 'TO'` e la targa in `work_center_cd`; il nome
  della tabella va in `MACHINES_QUERY` sul server (non nel repository).
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
| `Accept as is` / `Use as is` (va bene così) | WARNING `DR_SENZA_RIPARAZIONE` | vanno avanti, ma **senza** la procedura di riparazione come riferimento |
| `Reject` (scarta) | ERRATO | si fermano |
| `Repair` e `Accept as is` insieme | CORRETTO con una nota | solo la `Repair` come riferimento |

Il **serial number** serve a trovare la recommendation. La **condition** serve a scegliere
quando lo stesso serial number ha più recommendation. Oggi sono obbligatori tutti e due
(domanda P2 in `COPILOT.md`: si potrebbero rendere facoltativi). Il serial number è scritto
solo in alcune stampe («APPLY ON S/N …»); la condition mai.

## 8. Il frontend della v1

Visto dalle foto il 22-11-2026.

- **Percorso:** «Which cycle do you want to validate?» → *Civil cycle (DR/MOS)* oppure *EJ200
  cycle (military)*.
  - Civile → «Devi validare un ciclo DR?» → *Yes*: chiede `Serial Number (S/N)` e `DR Condition
    Numbers` (una o più, con le virgole), poi il PDF. *No (MOS)*: chiede subito il PDF.
  - EJ200: chiede subito il PDF.
  - Durante il lavoro: «Validating...».
- **Risultato:** in alto il nome del file e le etichette (codice ciclo, descrizione, tipo,
  `RC`, «MOS Cycle» o «EJ200 Cycle»). Poi la tabella *Sources* (Repair Code, Type, Reference,
  Task, Feedback) e la tabella *Operations* (Op #, Description, Targa C.Resp, Task Code,
  Scheda, Op. Feedback, TM Feedback, Task Code Feedback, Scheda Feedback). Pulsante di
  download, pollice su/giù, «New validation».
- **Intestazione:** «Validation Passed» (verde) se non ci sono errori, **anche se ci sono
  Warning**. «Completed with Errors» (arancione) con «N errors» se c'è almeno un errore, e
  «1 err» vicino all'operazione.
- **Bollini:** `OK` verde con «No errors found»; `Warning` giallo con la spiegazione; `Error`
  rosso con «Error found: …»; `N/A` grigio senza testo; `Info` azzurro con un testo (per
  esempio «N/A, non verificato per EJ200» sulle schede EJ200).
- La v2 manda gli stessi campi e gli stessi inizi di testo. **Ancora da capire:** la v2 manda
  `N/A - <motivo>` per ogni N/A; se il frontend mostra `Info` per ogni N/A con un testo, le
  celle che oggi sono grigie diventano azzurre (domanda C2 in `COPILOT.md`).
- **La v1 non è un riferimento.** Dà errori falsi (su un ciclo EJ200, due «Error» con valori
  che rispettano il limite) e giudizi diversi per casi uguali (stesso task, pezzi dello stesso
  tipo: OK in un ciclo, Warning nell'altro). Per sapere se la v2 ha ragione serve chi conosce
  i cicli.

## 9. Stato delle prove (22-11-2026)

Con Bedrock Haiku 5.5 e la conoscenza di prova:

- **MOS:** terzo ciclo con 7 corretti, 16 warning, 0 errati, 14 N/A, 0,0058 USD. I warning
  vengono dai manuali dei motori che mancano e dalle macchine attive non collegate.
- **DR:** le tre condition del ciclo vero danno l'esito atteso.
  - `Repair`: 5 corretti, 0 errati, 0,006-0,011 USD, 9-11 chiamate al modello per prova.
  - `Accept as is`: WARNING `DR_SENZA_RIPARAZIONE`, 0 errati, 0 USD.
  - Descrizioni: 4 CORRETTO, 5 WARNING `EVIDENZA_NON_TROVATA`; la scheda dell'op. 050 non è
    tra le 94 schede.
- **EJ200:** mai provato con i servizi veri (va fatto dentro AWS).
- **Ciclo MOS «con errori»:** blocco pronto in `COPILOT.md`; manca sapere quali sono gli
  errori (domanda P5).
- **Salvataggio:** tutto è nel repository aziendale fino al 21-11-2026; i documenti del
  22-11-2026 sono da salvare.

## 10. Problemi già visti e cosa fare

| Cosa si vede | Perché | Cosa fare |
|---|---|---|
| Tanti WARNING `FONTE_ASSENTE` | i manuali dei motori non sono ingestionati | niente: è giusto |
| Stato `parziale`, targhe WARNING `ERRORE_TECNICO` | macchine attive (Redshift) non collegate | niente, finché non si collegano |
| La stessa descrizione a volte ERRATO, a volte CORRETTO | il modello non risponde sempre uguale (op. 060 del DR: ERRATO 2 volte su 3) | c'è già la conferma con 2 domande in più. Prima di «correggere» un ERRATO, rifare la prova 3 volte |
| Esiti diversi tra lettura del modello e del parser | il modello legge il PDF in modo diverso | usare il parser |
| `Accept as is` bloccava tutto il DR | le procedure DR pubblicate parlano solo di riparazione | regola nuova (tabella DR sopra) |
| Una ricerca nel testo della conoscenza non trova niente | si cercava riga per riga e le frasi vanno a capo | cercare nel testo intero (`Get-Content -Raw`) |
| Previsto «completo», uscito `parziale` | dimenticate le macchine attive | ricordarsi che oggi è sempre `parziale` |
| Test degli esiti attesi falliti sul PC | mancava la copia di `eval\casi\sintetici` | il blocco di aggiornamento la copia |
| Il blocco del push si è rotto a metà | righe eseguite una alla volta, `else` su una riga a parte | `} else {` sulla stessa riga; commit e push in due blocchi |
| `PermissionError [WinError 5]` | antivirus | il codice riprova; un test può fallire una volta: si rilancia |
| Copilot rifiuta un comando o un file | blocco su `data/` | lancia l'utente, non aggirare |
| Copilot spiega invece di rispondere | gli è stato incollato un testo senza domande | usare il messaggio pronto in `COPILOT.md` |
| Copilot in modalità Agent | scelta in basso nella chat | passare ad Ask |
| Il bucket si vede in una foto | è aperto `data/bucket.txt` | non ripeterlo; chiedere di chiudere il file |
| Un esito della v1 sembra sbagliato | la v1 sbaglia | non usarla come riferimento |
| I documenti tolti restano sul PC | `robocopy` copia ma non cancella | il blocco di aggiornamento li cancella per nome |

## 11. Decisioni prese

Le risposte già date. Le domande ancora aperte sono in `COPILOT.md` (sezioni 3 e 4).

- **Task citato che il manuale non ha:** WARNING `FONTE_ASSENTE` subito, senza chiamare il
  modello (interruttore `agent.skip_missing_task`, acceso).
- **Task del capitolo 70:** se non sono nei manuali citati, si cercano nel manuale SPM. Da
  confermare (P3).
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
- **DR `Accept as is`:** WARNING, gli altri controlli vanno avanti (tabella in sezione 7). Da
  confermare (P1).
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
- **Frontend:** lo gestisce un collega.
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
