# Il computer aziendale e le regole delle prove

Quello che si sa del PC aziendale, di chi fa cosa e di cosa è permesso. Aggiornato il
21-11-2026. Niente valori veri qui (il repository è pubblico): bucket, account, matricola,
codici di manuali, numeri DR, serial number e part number restano solo sul PC.

## Chi fa cosa

| Chi | Cosa fa | Cosa non fa |
|---|---|---|
| Claude | modifica codice, test e documenti nel repository personale (`main`, nessun branch); scrive in `docs/COPILOT.md` i blocchi da lanciare; legge le foto del terminale | non ha accesso al PC aziendale, ad AWS né al repository aziendale: vede solo le foto |
| L'utente | lancia i blocchi di `docs/COPILOT.md` nel terminale di VS Code e manda le foto; fa i commit nel repository aziendale | non modifica il codice a mano |
| Copilot (sul PC) | può lanciare prove | **non modifica il codice** (regola dell'utente); la *content exclusion* dell'organizzazione GitHub gli vieta `data/` e gli URI S3 che ne vengono: rifiuta. Non si aggira (niente rinomine o spostamenti): solo gli amministratori possono cambiarla |

Le correzioni arrivano sul PC con il blocco **Aggiornare il codice sul PC** di `COPILOT.md`
(clone temporaneo del repository personale, `robocopy` di `src/`, `tests/`, `docs/`, test).
Nel repository aziendale la v2 sta in `app_cycle_validation_v2/`, branch
`feature/cycle-validation-v2`; l'utente salva le correzioni con un commit a fine prova. La v1
(`app_cycle_validation/`) è in produzione e non si tocca.

## Il PC

- Windows 11, VS Code, terminale **PowerShell 7** (`pwsh`): i comandi sono PowerShell, non bash.
  Il terminale sta in `app_cycle_validation_v2` (il prompt finisce con `app_cycle_validation_v2>`).
- Python di sistema 3.14 (il progetto dice 3.13): **ogni blocco comincia con
  `$env:UV_PYTHON = "3.14"`**. Si usa `uv`.
- `git clone` da github.com funziona (account GitHub personale). I commit aziendali usano
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
  `machine_tag` escono WARNING `ERRORE_TECNICO`.

## La conoscenza di prova

L'utente ha ingestionato solo un sottoinsieme (i file sono circa 2000, tutti costerebbero
troppo): 8 capitoli del manuale SPM (capitolo 70), 2 procedure DR, 104 targhe, 94 schede,
23 recommendation DR. I manuali dei motori **non** ci sono: le righe che ne dipendono escono
WARNING `FONTE_ASSENTE`, ed è giusto. **Decisione del 21-11-2026: per ora non si ingestiona
altro**, si prova solo con questo sottoinsieme. Il comando per trovare i sorgenti da
aggiungere è in fondo a `COPILOT.md`, per quando servirà.

## Regole sui dati

- Guida aziendale (`Guida_test_QA_SageMaker.md`): *«Non caricare o spostare documenti per fare
  il test. I documenti e gli output EJ200 restano su AWS EU; non copiarli nella repository o
  fuori dall'ambiente autorizzato.»* Quindi: **nessuna copia locale della conoscenza EJ200**
  (quella scaricata per errore è stata cancellata il 21-11-2026) e la fotografia si fa solo di
  `civil/`. Le copie locali della parte civile e dei PDF dei cicli: l'utente verifica con la
  guida.
- I dati veri stanno solo in cartelle che git ignora: `data/`, `runs/`, `eval/casi/aziendali/`,
  `docs/Esempio*/`.
- Nel repository personale non vanno mai: nome del bucket, account AWS, host, ARN, nomi dei
  segreti, matricola o utente Windows, codici dei manuali, numeri delle procedure DR, serial
  number, part number. Negli esempi e nei test: valori inventati. I comandi di `COPILOT.md`
  prendono i codici veri dai file sul PC (conoscenza, PDF, output di `leggi`).
- Le foto possono mostrare il nome del bucket (scheda `data/bucket.txt` aperta): non ripeterlo
  mai e chiedere di chiudere la scheda.
- `report.md` non si manda a Claude (contiene le citazioni dei manuali): bastano le righe di
  riepilogo stampate dai blocchi.

## Come si scrive `docs/COPILOT.md`

- Blocchi PowerShell da copiare così come sono, senza niente da sostituire; ogni blocco comincia
  con `$env:UV_PYTHON = "3.14"`.
- Dopo ogni blocco: **Deve uscire** (cosa aspettarsi) e **Manda a Claude** (cosa fotografare).
- Se un blocco costa (Bedrock), dirlo. Per esplorare a costo zero c'è `cycle-validation leggi`
  (parser, nessun modello; `--pagina N` stampa il testo di una pagina).
- Le parti fatte si riducono a un riassunto di poche righe; restano: *Se qualcosa va storto*,
  *Dove siamo*, *Aggiornare il codice sul PC*, i messaggi aperti, *Più avanti*.
- Accorgimenti PowerShell: nei pattern di `Select-String` usare `\S+` al posto di caratteri come
  `·`; `Get-Content -Raw` prima di `ConvertFrom-Json`; in `aws s3 ls` il nome del file comincia
  alla colonna 31.

## Le stampe PVRM320 viste finora

- MOS e DR hanno lo stesso modulo: testata ripetuta a ogni pagina, tabella a colonne con
  asterischi, manuale OEM nel piè. Il parser di layout le legge a zero token; se non ci riesce,
  `run` passa all'estrazione con il modello.
- I task stanno nel testo come `TASK 70-xx-xx-xxx-xxx` e si leggono per intero. I task del
  capitolo 70 si cercano anche nel manuale SPM (scelta da confermare, domanda 16 in
  `DOMANDE_APERTE.md`).
- DR: la riga NOTE (op. 005) si ferma a metà frase e il seguito sta dopo il banner di fine
  pagina `*** C O N T I N U A ***`. Una delle stampe scrive nel testo il caso DR e il serial
  number del pezzo («D.R. CASE #…», «APPLY ON S/N …»); `leggi` li stampa. I cicli DR non citano
  task: i task vengono dalla recommendation (serial number e condition).
- Aperto: a pagina 5 delle due stampe DR c'è un altro blocco senza numero di operazione.
