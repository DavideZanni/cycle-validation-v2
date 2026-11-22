# Lavorare sul PC aziendale

Questo è il file da usare sul PC. Dentro ci sono:

1. cosa fare adesso;
2. i comandi da lanciare (blocchi da copiare e incollare);
3. le domande per Copilot;
4. le domande per le persone e il messaggio per il collega del frontend.

Tutto quello che sappiamo già (PC, regole, problemi risolti) è in `docs/MEMORIA.md`.

**Come si lancia un blocco.** Apri il terminale di VS Code nella cartella
`app_cycle_validation_v2` (la riga finisce con `app_cycle_validation_v2>`). Copia il blocco
intero e incollalo. Poi guarda **Deve uscire** e manda a Claude la foto indicata in **Manda a
Claude**.

**Se qualcosa va storto:**

- c'è scritto `Token has expired`, `ExpiredToken` o `SSO session`: lancia `aws sso login`, poi
  rilancia lo stesso blocco;
- c'è scritto `SELF_SIGNED_CERT_IN_CHAIN` o `unable to get local issuer certificate`: lancia
  questa riga, poi rilancia il blocco (vale finché non chiudi il terminale):

```powershell
$env:NODE_EXTRA_CA_CERTS = (Resolve-Path ..\app_cycle_validation\zscaler.pem).Path; $env:AWS_CA_BUNDLE = $env:NODE_EXTRA_CA_CERTS
```

---

## 1. Cosa fare adesso (22-11-2026, notte)

Dove siamo e cosa manca per la consegna: `MEMORIA.md`, sezione 1. Qui solo i passi.

1. In Copilot passa ad **Ask** (in basso nella chat): nelle foto è ancora su **Agent** con
   **Allow all**.
2. Pulizia e 7.1 fatti e controllati (22-11): Dockerfile e buildspec giusti. Ora **Salvare**
   (sezione 6): salva anche Dockerfile, `vendor/`, `config/settings.azienda.yaml` e
   `../buildspec.yml`, sul ramo feature (QA non cambia).
3. Lancia **Aggiornare il codice sul PC** (sezione 2) quando Claude cambia qualcosa.
4. **5.3** prove in locale dal frontend (la lista è lì).
5. **Ingestion del manuale** (la fai tu, con l'ingestion aziendale), poi **5.2**. Il 22-11 la
   versione pubblicata era ancora quella del 19-11: l'ingestion non era arrivata.
6. **Pull request verso `develop`**: più avanti, quando lo decidi tu.
7. Se non l'hai già fatto: manda al collega del frontend il **messaggio** della sezione 4.1.

---

## 2. Aggiornare il codice sul PC

Da lanciare **ogni volta che Claude dice di aver cambiato qualcosa**. Prende dal repository
personale il codice, i test, i documenti, i casi di prova, le impostazioni predefinite, i
prompt e le dipendenze (`pyproject.toml`, `uv.lock`), li copia nella cartella della v2 e
lancia i test. Toglie anche i documenti vecchi che non servono più. Non tocca i dati
aziendali.

```powershell
$env:UV_PYTHON = "3.14"
$tmp = Join-Path $env:TEMP "cv2-aggiornamento"
Remove-Item -Recurse -Force $tmp -ErrorAction SilentlyContinue
git clone --quiet --depth 1 https://github.com/DavideZanni/cycle-validation-v2.git $tmp
robocopy "$tmp\src" src /E /XD __pycache__ /NFL /NDL /NJH /NJS /NP
robocopy "$tmp\tests" tests /E /XD __pycache__ /NFL /NDL /NJH /NJS /NP
robocopy "$tmp\docs" docs /E /NFL /NDL /NJH /NJS /NP
robocopy "$tmp\eval\casi\sintetici" eval\casi\sintetici /E /NFL /NDL /NJH /NJS /NP
robocopy "$tmp\config" config /E /NFL /NDL /NJH /NJS /NP
robocopy "$tmp\prompts" prompts /E /NFL /NDL /NJH /NJS /NP
Copy-Item "$tmp\pyproject.toml", "$tmp\uv.lock", "$tmp\README.md" . -Force
Remove-Item docs\AMBIENTE_AZIENDALE.md, docs\DOMANDE_APERTE.md, docs\FORMATO_CONOSCENZA.md, docs\IMPORTAZIONE.md, docs\README_RADICE.md -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force $tmp
uv run pytest -q
```

**Deve uscire:** tutti `passed` (qualche `skipped` va bene), nessun `failed`.

**Manda a Claude:** la foto solo se c'è un `failed`.


**Pulizia (una volta).** Nella foto del 22-11 `git status` mostra quattro cartelle non salvate
**fuori** dalla cartella della v2 (`../src`, `../tests`, `../docs`, `../eval`): sono copie della
v2 finite nella radice del repository (un blocco di aggiornamento lanciato dalla cartella
sbagliata). Il blocco le toglie solo se non sono nel repository e sembrano copie della v2;
altrimenti le lascia e lo scrive.

```powershell
foreach ($d in "src", "tests", "docs", "eval") { $p = "..\$d"; if (Test-Path $p) { $salvata = git ls-files -- $p; $copia = (Test-Path "$p\cycle_validation") -or (Test-Path "$p\COPILOT.md") -or (Test-Path "$p\test_api.py") -or (Test-Path "$p\casi"); if (-not $salvata -and $copia) { Remove-Item -Recurse -Force $p; "tolta la copia sbagliata: ..\$d" } else { "lasciata: ..\$d (è nel repository o non sembra una copia della v2)" } } }
git status --short ..
```

**Deve uscire:** `tolta la copia sbagliata: ...` per le cartelle che c'erano, e in `git status`
nessuna riga `?? ../src/`, `?? ../tests/`, `?? ../docs/`, `?? ../eval/`.
---

## 3. Domande per Copilot

Nessuna domanda aperta: C1-C21 hanno la risposta (`MEMORIA.md`). Quando ne servono altre,
Claude le scrive qui. Ricorda: modalità **Ask**, togli con la **x** gli allegati che non
c'entrano, e il testo comincia sempre con «Rispondi solo leggendo il codice, senza modificare né
eseguire niente».

---

## 4. Domande per le persone

Queste Copilot non le sa: la risposta non è nel codice. Chiedile quando capita e scrivi a
Claude la risposta a parole (senza codici veri).

- **P1. Task «70-».** I task che cominciano con `70-` stanno sempre nel manuale SPM (le pratiche
  standard)? C'è un altro gruppo di task con la stessa regola?
- **P2. Operazione 060 del ciclo DR.** In una prova la v2 ha segnato come sbagliata
  l'operazione 060 del ciclo DR (condition 3). Era davvero sbagliata? Il dettaglio è in
  `runs\dr-condition-3\report.md`: fallo guardare a chi conosce il ciclo, non mandarlo a
  Claude.
- **P4. Targa «90» nell'indice** (per chi cura knowledge-index). Nel file delle targhe la
  `90` ha come funzione una frase sbagliata e le lettere accentate rovinate. Va corretta
  nell'indice (i passi sono in `MEMORIA.md`, «Da correggere nell'indice»).
- **P6. Scheda mancante.** In un ciclo «con errori» l'errore è una scheda tolta da
  un'operazione. Quando un'operazione deve avere per forza una scheda? C'è una regola (tipo di
  lavorazione, targa, parola nella descrizione)? Oggi la v2 una scheda assente la segna N/A,
  come la v1: senza una regola non può sapere che manca.
- **P7. Redshift dal PC** (facoltativa, non blocca la consegna). Dal PC la Data API di
  Redshift risponde `AccessDeniedException` su `ExecuteStatement` e la connessione diretta non
  arriva al cluster. Chi gestisce AWS può dare al tuo ruolo SSO l'uso della Data API
  (`redshift-data:ExecuteStatement`, `DescribeStatement`, `GetStatementResult`)? Servirebbe
  solo per provare le targhe sul PC; in QA la v2 legge Redshift come la v1.

### 4.1 Messaggio per il collega del frontend

Oggi il pulsante **Confirm** resta spento se serial number o condition sono vuoti. La v2 non
ne ha più bisogno. Mandagli questo messaggio (Teams o mail):

```text
Ciao! Per la v2 di Cycle Validation il serial number e le DR condition diventano facoltativi
(il serial number, se manca, si prende dalla stampa del ciclo).

In CycleValidationPage.tsx il pulsante Confirm resta spento se uno dei due campi è vuoto: si
può lasciarlo attivo anche con i campi vuoti? Le due caselle possono restare, con la scritta
"facoltativo".

Il backend v2 accetta dr_serial_number e dr_condition vuoti (stringa vuota, null o lista
vuota) sia in POST /cycle_validation/conversation sia nel form di
POST /cycle_validation/upload. Tutto il resto resta uguale: stessi indirizzi, stessi campi,
stessa risposta.
```

**Scrivi a Claude** la risposta del collega, a parole.

---

## 5. Prove da lanciare

### 5.1 La v2 in locale, al posto della v1: fatto (22-11-2026)

Login, frontend e v2 insieme, voce composta «CV v2»: il ciclo MOS di esempio è stato validato
dal frontend (`Validation Passed`, circa 20 secondi), con l'accesso e i permessi della v1. La
configurazione finale e le correzioni fatte sono in `AZIENDA.md`, sezione 7.

### 5.2 Dopo l'ingestion: i tre cicli «con errori»

Da lanciare **dopo** l'ingestion del manuale, quando la nuova versione è pubblicata. Questo
blocco **non fa l'ingestion**: la fai tu con l'ingestion aziendale, prima. Il blocco fa una
fotografia nuova della conoscenza civile di prova (ogni volta, con data e ora), stampa la
versione pubblicata accanto a quella del 21-11 (se sono uguali, l'ingestion non è ancora
pubblicata), poi rilancia i tre cicli «con errori» e stampa, per ognuno, il riepilogo e le
righe ERRATO (operazione e controllo, niente testi). Qualche centesimo per ciclo.

Prima prova (22-11, sera): 0 errati e quasi tutto WARNING nei tre cicli, come senza il manuale.

```powershell
$env:UV_PYTHON = "3.14"
[Console]::OutputEncoding = [Text.Encoding]::UTF8; $env:PYTHONIOENCODING = "utf-8"
$foto = "eval/casi/aziendali/conoscenza/foto-" + (Get-Date -Format "yyyyMMdd-HHmm")
uv run cycle-validation eval fotografia --bucket (Get-Content data/bucket.txt) --prefisso "Manufacturing AI/ingestion-v2-test-qa-output/knowledge/civil/" --out $foto --regione eu-south-1
$kb = "$foto/Manufacturing AI/ingestion-v2-test-qa-output/knowledge/civil/"
$prima = "eval/casi/aziendali/conoscenza/foto-20261121/Manufacturing AI/ingestion-v2-test-qa-output/knowledge/civil/current.json"
"versione pubblicata: " + (Get-Content ($kb + "current.json") | ConvertFrom-Json).path + " · il 21-11: " + $(if (Test-Path $prima) { (Get-Content $prima | ConvertFrom-Json).path } else { "?" })
$v = $kb + (Get-Content ($kb + "current.json") | ConvertFrom-Json).path
$radice = (Resolve-Path "..\..").Path
$errati = Get-ChildItem $radice -Recurse -Filter "*con errori*.pdf" -ErrorAction SilentlyContinue | Group-Object { (Get-FileHash $_.FullName).Hash } | ForEach-Object { $_.Group[0] }
foreach ($f in $errati) { $h = (Get-FileHash $f.FullName).Hash.Substring(0, 8).ToLower(); "$h " + (@(uv run cycle-validation run $f.FullName --profile mos --knowledge $v --config data/settings.yaml --out "runs/errori-$h") -match '^Ciclo' | Select-Object -First 1); if (Test-Path "runs/errori-$h/report.json") { (Get-Content "runs/errori-$h/report.json" -Raw | ConvertFrom-Json).results | Where-Object { $_.verdict -eq 'ERRATO' } | ForEach-Object { "    ERRATO op $(if ($_.target.kind -eq 'operation') { $_.target.label } else { $_.target.kind }) · $($_.check) · $($_.reason)" } } }
```

**Deve uscire:** la riga `Fotografia in ...`, la riga `versione pubblicata: ... · il 21-11:
...` (devono essere **diverse**), poi per ognuno dei tre cicli una riga `<impronta> Ciclo ...: N corretti, ...` e sotto le righe `ERRATO op ...`.
Claude le confronta con i 10 errori trovati da `confronta` (`MEMORIA.md`, sezione 10).

**Manda a Claude:** la foto, e scrivi a parole quanti manuali hai ingestionato.

### 5.3 Prove in locale dal frontend

La v2 gira in locale al posto della v1 (5.1): voce composta **«CV v2»**, oppure **login**,
**app_frontend** e **CV v2 (porta 8003)** a mano, poi `http://localhost:3000`. Qualche centesimo
per ciclo. Le targhe escono sempre WARNING (dal PC Redshift non si raggiunge): non contano.

Prove, nell'ordine (salta quelle che non puoi fare):

1. **I tre cicli «con errori»**, MOS, dal frontend. Gli esiti devono essere quelli del
   blocco 5.2 (stessa v2, stessa conoscenza): conta corretti, warning, errati.
2. **Un ciclo MOS lungo** (quello con più operazioni che hai): il tempo dall'invio al
   risultato. Deve stare sotto i 10 minuti (il frontend aspetta al massimo 11).
3. **Un DR con serial number e condition**, poi **lo stesso DR senza** (oggi il pulsante
   Confirm vuole i due campi: se non si può, salta il secondo).
4. **File sbagliato:** un DR caricato scegliendo MOS. Deve uscire «Modulo sbagliato».
5. **Pulsante militare** (se lo vedi): deve dire che i cicli EJ200 sono spenti (in locale
   è giusto).
6. **Storico:** riapri una chat di prima dall'elenco a sinistra, rinominala, cancellala.
7. **Download** del CSV dei risultati.

**Manda a Claude:** per ogni prova la foto dell'intestazione dei risultati (o del messaggio)
e scrivi a parole il tempo della prova 2. Se qualcosa non va: la foto del frontend e quella
del log di CV v2 nel terminale.

---

## 6. Salvare nel repository aziendale

Da lanciare quando Claude dice che ci sono cose nuove da salvare (**adesso sì**: comandi `qa`,
blocchi nuovi, documenti). Salva sul ramo `feature/cycle-validation-v2`: `develop` (QA) e
`main` non cambiano finché non apri tu la pull request. Prima lancia **Aggiornare il codice sul
PC**, poi questi due blocchi, uno alla volta.

Salva codice, test, documenti, casi di prova, impostazioni, prompt e dipendenze. Dopo il
blocco 7.1 anche il Dockerfile scritto da `qa`, la libreria in `vendor/` e il `buildspec.yml`
della radice (prima del 7.1 restano come sono). I dati aziendali
(`data/`, `runs/`, `eval/casi/aziendali/`, i PDF) restano fuori: git li ignora.

**6.1 Commit**

```powershell
git add src tests docs eval/casi/sintetici config prompts pyproject.toml uv.lock README.md Dockerfile ../buildspec.yml
if (Test-Path vendor) { git add vendor }
git status --short
git commit -m "v2: prova in locale con login e frontend, comando qa per la pubblicazione, blocchi e documenti aggiornati"
```

**Deve uscire:** in `git status` righe sotto `src/`, `tests/`, `docs/`, `eval/casi/sintetici/`,
`config/`, `prompts/`, forse `pyproject.toml`, `uv.lock`, `README.md`; dopo il 7.1 anche
`vendor/`, `Dockerfile` e `../buildspec.yml` (`M` cambiato, `A` nuovo, `D` tolto); poi il riepilogo del commit. Niente
sotto `data/` o `runs/`.

**6.2 Push**

Manda il commit su GitHub, ma solo se sei sul branch giusto e se nel commit non c'è niente fuori
dalle cartelle previste. Altrimenti scrive `FERMO` e non fa niente.

```powershell
$branch = git branch --show-current
$fuori = git show --name-only --format= HEAD | Where-Object { $_ -and $_ -notmatch '^app_cycle_validation_v2/(src|tests|docs|eval/casi/sintetici|config|prompts|vendor)/|^app_cycle_validation_v2/(pyproject\.toml|uv\.lock|README\.md|Dockerfile)$|^buildspec\.yml$' }
if ($branch -ne "feature/cycle-validation-v2") {
  "FERMO: sei sul branch '$branch', non su feature/cycle-validation-v2. Niente push."
} elseif ($fuori) {
  "FERMO: nell'ultimo commit ci sono file fuori dalle cartelle previste. Niente push:"; $fuori
} else {
  git push origin feature/cycle-validation-v2; git log --oneline -1; git status -sb | Select-Object -First 1
}
```

**Deve uscire:** la riga del push (`feature/cycle-validation-v2 -> feature/cycle-validation-v2`),
l'ultimo commit e `## feature/cycle-validation-v2...origin/feature/cycle-validation-v2` senza
`[ahead ...]`.

**Se esce `FERMO`, o il push è rifiutato** (`rejected`, `fetch first`): non insistere e non
usare `--force`, manda la foto a Claude. Se il commit dice `nothing to commit`, era già tutto
salvato: lancia lo stesso il push.

---

## 7. Pubblicare in QA

**Decisione dell'utente (22-11):** il blocco 7.1 e il salvataggio si fanno; la pull request
verso `develop` più avanti, dopo le prove in locale (5.3). Finché il ramo non arriva su
`develop`, QA resta sulla v1. Se prima di allora serve portare su `develop` altro lavoro dello
stesso ramo, lancia prima `qa --torna-alla-v1` (fine sezione 7.2) e salva.

La v2 prende il posto della v1 in QA. Oggi `buildspec.yml` (nella radice del repository)
costruisce l'immagine dalla cartella della v1. Il comando `cycle-validation qa` prepara tutto
sul PC, senza mettere valori aziendali nel repository personale:

- scrive il `Dockerfile` della v2 partendo da quello della v1: stessa base Python, stesse
  istruzioni sui certificati;
- copia in `vendor/` la libreria di accesso dei requirements della v1 (0.4.0rc2 con `[auth]`);
- mette nelle righe `ENV` del Dockerfile i valori che la v1 ha nel codice: il nome del secret
  di ambiente, il database e la query delle macchine (Redshift come la v1);
- copia `data/settings.yaml` (le impostazioni provate in locale, con l'id del modello) in
  `config/settings.azienda.yaml`;
- nel `buildspec.yml` cambia `cd app_cycle_validation` in `cd app_cycle_validation_v2`.

La prima volta i cicli militari restano **spenti**: se la conoscenza EJ200 pubblicata avesse un
problema, il servizio non partirebbe. Si accendono dopo la prima prova (7.3).

**7.1 Preparare.** Gratis. Stampa solo nomi e il Dockerfile con i valori aziendali coperti.

```powershell
$env:UV_PYTHON = "3.14"
uv run cycle-validation qa --conoscenza-civile "Manufacturing AI/ingestion-v2-test-qa-output/knowledge/civil/current.json"
```

**Deve uscire:** `Dalla v1: base e N istruzioni sui certificati; libreria ... copiata in vendor;
secret di ambiente, database e tabella trovati.`, `Impostazioni: ... (modello ...)`,
`buildspec: percorsi spostati sulla v2: N.` con le righe del buildspec che parlano della cartella
e del certificato (tutte con `app_cycle_validation_v2`), poi il Dockerfile.

**Manda a Claude:** la foto (tutta l'uscita, anche in due foto). Claude controlla il Dockerfile
prima del salvataggio.

**Poi:** **Salvare** (sezione 6) e, come fate di solito, la pull request da
`feature/cycle-validation-v2` verso `develop`. Quando è unita, CodeBuild costruisce la v2 e QA
la usa al posto della v1.

**Attenzione:** quando `feature/cycle-validation-v2` (o `develop`) arriverà su `main`, anche la
produzione passerà alla v2. Prima di farlo serve una prova QA riuscita.

**7.2 La prova in QA.** Dal frontend QA (pagina *Cycle Validation*), con il tuo utente: un
ciclo MOS e un ciclo DR, come in locale. Qui le targhe si controllano davvero (Redshift come la
v1).

**Manda a Claude:** la foto dell'intestazione dei risultati di tutti e due (esito, numero di
errori) e, se ci sono, le righe delle targhe.

**Se la v2 in QA non parte o non risponde:** si torna alla v1 così, poi Salvare e pull request
verso `develop`:

```powershell
$env:UV_PYTHON = "3.14"
uv run cycle-validation qa --torna-alla-v1
```

**Deve uscire:** `buildspec: percorsi rimessi sulla v1: N.`

**7.3 Accendere i cicli militari** (dopo 7.2 riuscita). Stesso comando con la conoscenza EJ200,
poi Salvare e pull request:

```powershell
$env:UV_PYTHON = "3.14"
uv run cycle-validation qa --conoscenza-civile "Manufacturing AI/ingestion-v2-test-qa-output/knowledge/civil/current.json" --ej200 --conoscenza-ej200 "Manufacturing AI/ingestion-v2-test-qa-output/knowledge/ej200/current.json"
```
