# Lavorare sul PC aziendale

Questo è il file da usare sul PC. Dentro ci sono:

1. cosa fare adesso;
2. i comandi da lanciare (blocchi da copiare e incollare);
3. le domande per Copilot;
4. le domande per le persone che conoscono i cicli.

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

## 1. Cosa fare adesso (22-11-2026)

1. Lancia **Aggiornare il codice sul PC** (sezione 2): ci sono le regole DR nuove.
2. Lancia la **prova del ciclo DR senza serial number e condition** (sezione 5.1).
3. Fai le **domande a Copilot** (sezione 3) e manda a Claude le foto delle risposte.
4. Lancia **Salvare nel repository aziendale** (sezione 6).
5. Quando hai tempo: lancia la **prova del ciclo MOS «con errori»** (sezione 5.2).
6. Quando capita: fai le **domande alle persone** (sezione 4).

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

Copilot può leggere il codice del repository aziendale (la v1, forse anche il frontend). Queste
domande servono a collegare la v2 al frontend senza sorprese.

**Prima di cominciare, due cose importanti:**

- in basso nella chat di Copilot scegli **Ask**, non **Agent**. In Agent Copilot può
  modificare file e lanciare comandi: non deve;
- se in basso nella chat c'è un file allegato che non c'entra (per esempio un file con accessi
  o password), toglilo con la **x** prima di scrivere. Copilot non deve leggerlo.

Poi incolla questo messaggio:

```text
Fai solo il consulente: non eseguire comandi, non creare, modificare o cancellare file, non
fare commit. Puoi solo leggere i file del workspace.

Apri app_cycle_validation_v2/docs/COPILOT.md, sezione "3. Domande per Copilot", e rispondi a
ogni domanda da C1 a C12, nell'ordine, cercando nel codice di tutto il repository (v1 in
app_cycle_validation/, frontend se c'è, file di deploy).

Per ogni risposta: numero della domanda, file e funzione (percorso esatto), il pezzo di codice
che conta (breve) e la risposta in due o tre righe, in modo semplice. Se non lo trovi o non sei
sicuro, scrivi "non trovato": non supporre. Non scrivere valori di segreti, account AWS, ARN,
URL o host interni, nomi di bucket: al loro posto <omesso>. I nomi delle variabili invece sì.
```

**Manda a Claude:** le foto di tutte le risposte. Se Copilot si ferma a metà, scrivigli
«continua dalla domanda C…».

**Le domande** (Copilot le legge da qui, tu non devi copiarle):

- **C1. Dov'è il frontend?** In quale cartella c'è il codice della pagina *Cycle Validation*
  (quella che chiede «Which cycle do you want to validate?»)? Se non è in questo repository,
  dillo.
- **C2. Come sceglie il bollino?** Quale funzione guarda il testo di un risultato e decide se
  mostrare `OK`, `Warning`, `Error`, `N/A` o `Info`? Incollala. Quando esce `Info` e quando
  `N/A` grigio? Un testo che comincia con `"N/A - "` che bollino dà?
- **C3. Passed o Errors?** Quando la pagina scrive «Validation Passed» e quando «Completed with
  Errors»? Da dove prende il numero «N errors» e il «1 err» vicino all'operazione? (un campo
  come `cycle_errors_count`, oppure conta i testi che cominciano con «Error found»?)
- **C4. Quali campi legge?** Elenca i campi della risposta che il frontend usa (quelli in alto,
  quelli di `sources` e quelli di `operations`) e dove li mostra. Da dove vengono la colonna
  *Type* («Manual») e le etichette «MOS Cycle» / «EJ200 Cycle»? Usa anche `cycle_status`,
  `drRecommendationFeedback` o `_pipeline_errors`?
- **C5. Serial number e condition: come li manda?** Per un ciclo DR, con quale indirizzo e con
  quali nomi il frontend manda `Serial Number (S/N)` e `DR Condition Numbers`? Come testo
  (`"1,2"`) o come lista? Se sono vuoti, il pulsante CONFIRM si può premere lo stesso?
- **C6. Serial number e condition nella v1.** Cosa ci fa la v1? Legge il serial number anche
  dal PDF? Cosa fa se lo stesso serial number ha più recommendation?
- **C7. Quali indirizzi chiama?** Quali rotte chiama il frontend in tutto il percorso (inizio,
  scelta del tipo, caricamento del PDF, elenco delle chat a sinistra, pollice su/giù,
  download), e con quali campi? Con quale variabile si sceglie l'indirizzo del backend? (il
  nome, non il valore)
- **C8. Cosa scarica?** Il pulsante di download in alto a destra cosa scarica (JSON, PDF,
  Excel…)? Lo prepara il frontend o lo chiede al backend?
- **C9. Quanto aspetta?** Il frontend ha un tempo massimo di attesa per la validazione? Quanti
  secondi? E il gateway o il backend della v1?
- **C10. Macchine attive nella v1.** Come legge la v1 l'elenco delle macchine attive (Redshift
  o altro)? Nomi delle variabili e colonne usate dalla query, senza valori.
- **C11. «non verificato per EJ200».** Dove nasce questo testo sulle schede EJ200? Il frontend
  lo tratta in modo speciale?
- **C12. Come gira la v1?** Come viene messa in funzione la v1 dietro il gateway (Dockerfile,
  buildspec, ECS, Lambda, SageMaker…)? Elenca i file e cosa fanno, in breve. Serve per mettere
  la v2 nello stesso posto e provarci i cicli EJ200.

---

## 4. Domande per le persone che conoscono i cicli

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

---

## 6. Salvare nel repository aziendale

Da lanciare quando Claude dice che ci sono cose nuove da salvare (**adesso sì**: regole DR e
documenti nuovi del 22-11-2026). Prima lancia **Aggiornare il codice sul PC**, poi questi due blocchi,
uno alla volta.

Salva solo codice, test, documenti e casi di prova della v2. I dati aziendali (`data/`,
`runs/`, `eval/casi/aziendali/`, i PDF) restano fuori: git li ignora.

**6.1 Commit**

```powershell
git add src tests docs eval/casi/sintetici
git status --short
git commit -m "v2: DR, serial number e condition facoltativi, accept as is blocca; documenti riorganizzati"
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
