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

## 1. Cosa fare adesso (22-11-2026, pomeriggio)

1. In Copilot passa ad **Ask** (in basso nella chat). Nelle ultime foto era su **Agent** con
   **Allow all** acceso: così può cambiare file e lanciare comandi senza chiedere.
2. Lancia **Aggiornare il codice sul PC** (sezione 2): la v2 ora manda le risposte come le
   legge il frontend.
3. Lancia la **prova del ciclo DR senza serial number e condition** (sezione 5.1).
4. Lancia **Quanto dura una validazione** (sezione 5.3): non costa niente.
5. Lancia **Salvare nel repository aziendale** (sezione 6).
6. Fai a Copilot le **domande C13 e C14** (sezione 3).
7. Manda al collega del frontend il **messaggio** della sezione 4.1.
8. Quando hai tempo: lancia la **prova del ciclo MOS «con errori»** (sezione 5.2).
9. Quando capita: fai le **domande alle persone** (sezione 4).

---

## 2. Aggiornare il codice sul PC

Da lanciare **ogni volta che Claude dice di aver cambiato qualcosa**. Prende dal repository
personale il codice, i test, i documenti e i casi di prova, li copia nella cartella della v2 e
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
Remove-Item docs\AMBIENTE_AZIENDALE.md, docs\DOMANDE_APERTE.md, docs\FORMATO_CONOSCENZA.md, docs\IMPORTAZIONE.md, docs\README_RADICE.md -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force $tmp
uv run pytest -q
```

**Deve uscire:** tutti `passed` (qualche `skipped` va bene), nessun `failed`.

**Manda a Claude:** la foto solo se c'è un `failed`.

---

## 3. Domande per Copilot

Copilot può leggere il codice del repository aziendale. Alle domande C1-C12 ha già risposto il
22-11-2026 (le risposte sono in `MEMORIA.md`, sezione 8). Ne restano due.

**Prima di cominciare, due cose importanti:**

- in basso nella chat di Copilot scegli **Ask**, non **Agent**. In Agent Copilot può
  modificare file e lanciare comandi: non deve;
- se in basso nella chat c'è un file allegato che non c'entra (per esempio un file con accessi
  o password), toglilo con la **x** prima di scrivere. Copilot non deve leggerlo.

Poi incolla questo messaggio:

```text
Fai solo il consulente: non eseguire comandi, non creare, modificare o cancellare file, non
fare commit. Puoi solo leggere i file del workspace.

Apri app_cycle_validation_v2/docs/COPILOT.md, sezione "3. Domande per Copilot", e rispondi
alle domande C13 e C14, cercando nel codice della v1 (app_cycle_validation/) e, se lo vedi,
del frontend.

Per ogni risposta: numero della domanda, file e funzione (percorso esatto), il pezzo di codice
o di prompt che conta (breve) e la risposta in due o tre righe, in modo semplice. Se non lo
trovi o non sei sicuro, scrivi "non trovato": non supporre. Non scrivere valori di segreti,
account AWS, ARN, URL o host interni, nomi di bucket, codici veri di manuali, cicli o DR: al
loro posto <omesso>. I nomi delle variabili invece sì.
```

**Manda a Claude:** le foto delle risposte.

**Le domande** (Copilot le legge da qui, tu non devi copiarle):

- **C13. La scheda nella v1.** Il frontend mostra `scheda.tabNumber`, `scheda.task` e
  `scheda.class`. Cosa ci mette la v1 in questi tre campi, per un ciclo civile (MOS/DR) e per
  uno EJ200? Da quale colonna o scritta della stampa vengono? Incolla il pezzo del prompt di
  estrazione o del codice che li riempie.
- **C14. DR fermo nella v1.** Quando la validazione DR si ferma (`Reject`, `Accept as is`,
  nessuna recommendation per quelle condition), in quale campo della risposta la v1 scrive il
  motivo che l'utente vede? E i campi `DRCase` e `serialNumber` delle `sources`: chi li
  riempie e con cosa (dal PDF, dai dati DR, da quello che scrive l'utente)?

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
- **P3. Ciclo MOS «con errori».** Questo ciclo è stato dato già segnato come sbagliato. Quali
  sono gli errori, e in quali operazioni? Serve per capire se la v2 li trova.
- **P4. Targa «90» nell'indice** (per chi cura knowledge-index). Nel file delle targhe la
  `90` ha come funzione una frase sbagliata e le lettere accentate rovinate. Va corretta
  nell'indice (i passi sono in `MEMORIA.md`, «Da correggere nell'indice»).
- **P5. Dove gira la v1** (per chi gestisce AWS o il gateway). Il backend della v1 è
  un'immagine Docker in ECR, ma dove gira (ECS o altro)? Chi configura il gateway che manda
  `/cycle_validation` al backend? Serve per mettere la v2 accanto e provare i cicli EJ200
  dentro AWS.

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

### 5.1 Ciclo DR senza serial number e condition

Dal 22-11-2026 il ciclo DR si può validare senza dire serial number e condition, e
«accept as is» ferma il ciclo come «reject». Il blocco fa due prove sulla stampa DR che scrive
il serial number:

- **senza dati**: il serial number deve essere preso dalla stampa. Quel serial number ha
  recommendation diverse (riparazione e «accept as is»), quindi senza condition deve uscire
  WARNING `DR_NON_VERIFICATA` e gli altri controlli devono andare avanti;
- **condition 2** («accept as is»): deve uscire ERRATO e il ciclo fermo.

Costa qualche centesimo (solo la prima prova chiama il modello).

```powershell
$env:UV_PYTHON = "3.14"
$kb = "eval/casi/aziendali/conoscenza/foto-20261121/Manufacturing AI/ingestion-v2-test-qa-output/knowledge/civil/"
$v = $kb + (Get-Content ($kb + "current.json") | ConvertFrom-Json).path
$ciclo = (Get-ChildItem "docs/Esempio ciclo dr/*sn.pdf" | Select-Object -First 1).FullName
uv run cycle-validation run $ciclo --profile dr --knowledge $v --config data/settings.yaml --out runs/dr-senza-dati
uv run cycle-validation run $ciclo --profile dr --condition 2 --knowledge $v --config data/settings.yaml --out runs/dr-condition-2
foreach ($r in "dr-senza-dati", "dr-condition-2") { $j = Get-Content "runs/$r/report.json" -Raw | ConvertFrom-Json; $d = $j.results | Where-Object { $_.check -eq 'dr_recommendation' }; "$r : stato $($j.status), DR $($d.verdict) $($d.reason), serial number trovato: $(if ($j.meta.selectors.serial_number) { 'sì' } else { 'no' })" }
```

**Deve uscire:** due righe `Ciclo ...` con i conteggi, poi:

- `dr-senza-dati : stato parziale, DR WARNING DR_NON_VERIFICATA, serial number trovato: sì`
- `dr-condition-2 : stato bloccato, DR ERRATO DR_NON_APPLICABILE, serial number trovato: sì`

**Manda a Claude:** la foto delle due righe `Ciclo ...` e delle due righe finali.

### 5.2 Il ciclo MOS «con errori»

Passa alla v2 il PDF del ciclo MOS «con errori» e mostra cosa dice su fonti e task. Il PDF lo
cerca in `docs\` e in `Downloads`. Costa qualche centesimo.

```powershell
$env:UV_PYTHON = "3.14"
$kb = "eval/casi/aziendali/conoscenza/foto-20261121/Manufacturing AI/ingestion-v2-test-qa-output/knowledge/civil/"
$v = $kb + (Get-Content ($kb + "current.json") | ConvertFrom-Json).path
$ciclo = (Get-ChildItem docs, "$HOME\Downloads" -Recurse -Filter "*con errori*.pdf" -ErrorAction SilentlyContinue | Select-Object -First 1).FullName
if ($ciclo) { "Trovato: " + (Split-Path $ciclo -Leaf) } else { "FERMO: PDF con errori non trovato, mettilo in docs\Esempio ciclo mos\" }
uv run cycle-validation run $ciclo --profile mos --knowledge $v --config data/settings.yaml --out runs/mos-con-errori
(Get-Content runs/mos-con-errori/report.json -Raw | ConvertFrom-Json).results | Where-Object { $_.check -in 'source', 'task_code' } | Format-Table @{n='controllo'; e={$_.check}}, @{n='riga'; e={$_.target.label}}, verdict, reason, @{n='motivo'; e={$_.rationale}} -Wrap
```

**Deve uscire:** `Trovato: ...`, poi una riga `Ciclo ...` con i conteggi e il costo, poi una
tabella con le fonti e i task: esito, motivo e spiegazione.

**Manda a Claude:** la foto della riga dei conteggi e della tabella (anche in due foto).

### 5.3 Quanto dura una validazione

Il frontend aspetta al massimo 660 secondi l'upload e il backend della v1 ferma tutto dopo 600
secondi. Questo blocco legge i report delle prove già fatte e mostra quanto è durata ognuna.
Non chiama il modello e non costa niente.

```powershell
$env:UV_PYTHON = "3.14"
Get-ChildItem runs -Directory | ForEach-Object { $f = Join-Path $_.FullName "report.json"; if (Test-Path $f) { $j = Get-Content $f -Raw | ConvertFrom-Json; [pscustomobject]@{ prova = $_.Name; operazioni = @($j.cycle.operations).Count; secondi = [math]::Round($j.timings_ms.total / 1000) } } } | Sort-Object secondi -Descending | Format-Table -AutoSize
```

**Deve uscire:** una tabella con il nome della prova, il numero di operazioni e i secondi.
Tutto sotto 600 va bene.

**Manda a Claude:** la foto della tabella.

---

## 6. Salvare nel repository aziendale

Da lanciare quando Claude dice che ci sono cose nuove da salvare (**adesso sì**: regole DR,
risposte adattate al frontend e documenti nuovi del 22-11-2026). Prima lancia **Aggiornare il
codice sul PC**, poi questi due blocchi, uno alla volta.

Salva solo codice, test, documenti e casi di prova della v2. I dati aziendali (`data/`,
`runs/`, `eval/casi/aziendali/`, i PDF) restano fuori: git li ignora.

**6.1 Commit**

```powershell
git add src tests docs eval/casi/sintetici
git status --short
git commit -m "v2: DR con serial number e condition facoltativi, accept as is blocca; risposta adattata al frontend; documenti riorganizzati"
```

**Deve uscire:** in `git status` solo righe sotto `src/`, `tests/`, `docs/`,
`eval/casi/sintetici/` (`M` cambiato, `A` nuovo, `D` tolto); poi il riepilogo del commit.

**6.2 Push**

Manda il commit su GitHub, ma solo se sei sul branch giusto e se nel commit non c'è niente fuori
dalle cartelle previste. Altrimenti scrive `FERMO` e non fa niente.

```powershell
$branch = git branch --show-current
$fuori = git show --name-only --format= HEAD | Where-Object { $_ -and $_ -notmatch '^app_cycle_validation_v2/(src|tests|docs|eval/casi/sintetici)/' }
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

## 7. Più avanti: trovare i documenti da ingestionare

**Non adesso**: per ora si prova solo con la conoscenza già ingestionata. Quando si deciderà di
aggiungere documenti, questo blocco cerca su S3 i file dei manuali citati dai cicli e delle
procedure DR che mancano. Legge soltanto, non costa niente.

```powershell
$env:UV_PYTHON = "3.14"
$kb = "eval/casi/aziendali/conoscenza/foto-20261121/Manufacturing AI/ingestion-v2-test-qa-output/knowledge/civil/"
$v = $kb + (Get-Content ($kb + "current.json") | ConvertFrom-Json).path
$manuali = uv run cycle-validation leggi (Get-ChildItem "docs/Esempio ciclo mos/*.pdf", "docs/Esempio ciclo dr/*.pdf").FullName | Select-String 'fonti: ([^\s,]+)' | ForEach-Object { $_.Matches[0].Groups[1].Value }
$procedure = (Get-Content ($v + "dr_recommendations.json") -Raw | ConvertFrom-Json).reference
$codici = (@($manuali) + @($procedure) | Where-Object { $_ -and $_ -ne '-' } | Sort-Object -Unique | ForEach-Object { [regex]::Escape($_) }) -join '|'
$codici
aws s3 ls "s3://$(Get-Content data/bucket.txt)/Manufacturing AI/" --recursive --region eu-south-1 | Where-Object { $_ -match "$codici|72-56-3[12]|70-32-0[02]" -and $_ -notmatch 'ingestion-v2' } | Select-Object -First 40 | ForEach-Object { $_.Substring(31) }
```

**Deve uscire:** una riga con i codici cercati, separati da `|`, poi fino a 40 percorsi di file.

**Manda a Claude:** la foto. Claude dice quali file passare all'ingestion (poche sezioni, non
tutti i 2000 file). Se non esce nessun percorso, scrivi a Claude da quale cartella parte la tua
ingestion.
