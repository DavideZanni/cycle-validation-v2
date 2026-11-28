# Lavorare sul PC aziendale

Cosa fare sul PC aziendale, un passo alla volta, con tutti i comandi pronti da copiare.

👉 **Cosa fare adesso: [sezione 1](#1-cosa-fare-adesso).** Le altre sezioni si aprono solo
quando un passo lo dice.

| Chi | Cosa fa |
|---|---|
| **Tu** | lanci i blocchi sul PC e mandi a Claude la foto dello schermo |
| **Claude** | scrive tutto il codice, legge le foto, dice il passo dopo |
| **Copilot** | sempre in modalità **Ask**: legge i file e lancia i comandi di prova, **non cambia mai il codice** |

Gli altri documenti: `DOCUMENTAZIONE.md` (come funziona il programma), `MIGLIORIE.md` (cosa si
prova e cosa si è deciso), `MEMORIA.md` (cosa è successo finora).

---

## Indice

| Sezione | Cosa c'è |
|---|---|
| **0. Prima di iniziare** | parole, come si lancia un blocco, regole, cosa fare se va storto |
| **1. Cosa fare adesso** | le tappe e i passi di oggi |
| **2. Aggiornare e salvare** | 2.1 Aggiornare il codice · 2.2 Salvare nel repository aziendale |
| **3. Le prove** | 3.1 Come funzionano · 3.2 Cicli veri · 3.3 Copie cieche · 3.4 Gruppo nascosto · 3.5 Campagna · 3.6 Leggere i risultati · 3.7 Prova a mano · 3.8 Mettere ordine · 3.9 La v1 sugli stessi cicli |
| **4. Prove dal frontend** | la v2 dalla pagina web |
| **5. Dopo una nuova ingestion** | fotografia della conoscenza, lista dei manuali, cosa rifare |
| **6. Le persone** | domande aperte, messaggio per il collega del frontend, prompt per la documentazione completa |
| **7. QA** | la pubblicazione nell'ambiente di prova |

---

## 0. Prima di iniziare

### 0.1 Le parole che servono

| Parola | Cosa vuol dire |
|---|---|
| **v1 / v2** | v1 = il programma di oggi, usato dagli utenti: non si tocca. v2 = quello nuovo, nella cartella `app_cycle_validation_v2` |
| **Repository personale / aziendale** | personale = dove scrive Claude (pubblico, mai dati aziendali). Aziendale = quello dell'azienda; la v2 sta sul ramo `feature/cycle-validation-v2` (`develop` = QA, `main` = produzione) |
| **Blocco** | i comandi dentro un riquadro grigio di questo file. Si copia tutto insieme |
| **Ciclo** (o **stampa**) | il PDF PVRM320 di un ciclo di lavorazione. Tipi: **MOS** (civile), **DR** (civile con Deviation Request), **EJ200** (militare) |
| **Impronta** | 8 caratteri calcolati dal PDF (es. `aaaa1111`): si usa al posto del nome, così nelle foto non ci sono codici veri |
| **Conoscenza / fotografia** | i manuali preparati (ingestion) con cui la v2 confronta il ciclo. Sta su AWS; sul PC ce n'è una copia, la fotografia |
| **Esiti** | **CORRETTO**, **ERRATO** (c'è un errore), **WARNING** (serve un controllo a mano) |
| **Modello** | l'IA che confronta i testi: Claude **Haiku** su Amazon Bedrock (dal 25-11 solo Haiku) |
| **Errori visti** | gli errori noti messi apposta in 9 stampe (`eval/errori-noti.yaml`: dal 26-11 sera 20 che contano). Claude li conosce |
| **Errori mai visti** | errori che Claude non conosce: **copie cieche** (il programma cambia da solo un'operazione di un ciclo vero) e **gruppo nascosto** (stampe con errori messi a mano da te). Dicono se la v2 funziona anche su errori nuovi |
| **Stampa giusta / falso errore** | stampa originale senza errori / un ERRATO dove non c'è errore. I falsi errori devono essere **0** |
| **Prova** | un giro della v2 su un insieme di cicli: conta errori trovati, falsi errori, costo e tempo |
| **Insieme** | **piccolo** (cicli noti + copie cieche, veloce) o **grande** (cicli noti + tutti i cicli veri) |
| **Base / variante** | base = la v2 di oggi. Variante = una miglioria da provare (`eval/varianti/<nome>.yaml`), sempre confrontata con la base |
| **Campagna** | un solo comando che lancia tutte le prove in fila e scrive il report `runs\campagna.md` |
| **Riepilogo** | `riepilogo.md` di ogni cartella di prove: classifica e decisione |
| **Modalità Ask** | in basso nella chat di Copilot deve esserci scritto **Ask**, non *Agent* né *Autopilot* |

### 0.2 Come si lancia un blocco

1. VS Code → menu **Terminal → New Terminal**.
2. La riga del terminale deve **finire con** `app_cycle_validation_v2>`. Se no: `cd` + il
   percorso della cartella `app_cycle_validation_v2`, Invio.
3. Copia il blocco (pulsante di copia in alto a destra del riquadro).
4. Incolla nel terminale con **Ctrl+V** (conferma se chiede di incollare più righe) e premi
   **Invio**.
5. Aspetta che torni `app_cycle_validation_v2>`, confronta con **Deve uscire**, manda la foto
   come dice **Mandami**.

La riga `$env:UV_PYTHON = "3.14"` all'inizio dei blocchi serve: non toglierla.

### 0.3 Le regole

- **Copilot sempre in modalità Ask**, mai Agent o Autopilot: controlla in basso nella chat
  prima di ogni domanda. Il codice lo cambia solo Claude.
- **Mai foto di:** `runs\mutazioni\errori.yaml`, `data\errori-nascosti.yaml`, le stampe in
  `data\nascosti\` (Claude non deve conoscere gli errori mai visti); i `report.md`, i
  `prestazioni.md` interi e i file in `transcripts` (contengono testo dei manuali).
- **Si possono fotografare:** il terminale, `runs\campagna.md`, i `riepilogo.md`, le tabelle che
  Claude chiede.
- **Niente codici veri nei messaggi** (manuali, DR, serial e part number, cicli, bucket,
  account): usa le impronte o le parole.
- **Mai `--force`** in git. **Non cambiare i blocchi**, tranne i valori che il testo indica.

### 0.4 Se qualcosa va storto

| Cosa vedi | Cosa vuol dire | Cosa fare |
|---|---|---|
| `costo 0.00 $` in una prova, oppure `Campagna fermata: il modello non ha risposto` | l'accesso AWS è scaduto: i cicli girano ma il modello non risponde | Ctrl+C se gira ancora → `aws sso login` → rilancia lo stesso blocco: toglie da solo le prove senza risposte e le rifà |
| `Token has expired`, `ExpiredToken`, `SSO session` | accesso AWS scaduto | `aws sso login`, accedi dal browser, rilancia il blocco |
| `Campagna fermata: ...` (altro motivo) | si è fermata da sola (es. tetto di spesa) | leggi il motivo; foto a Claude |
| `SELF_SIGNED_CERT_IN_CHAIN`, `unable to get local issuer certificate`, `certificato (filtro di rete?)` | il filtro di rete (Zscaler) blocca il certificato | lancia la riga qui sotto e rilancia il blocco (vale fino alla chiusura del terminale) |
| `FERMO: ...` | il blocco si è fermato prima di fare danni: niente è cambiato | leggi il motivo (di solito la cartella del terminale), correggi, rilancia |
| `failed` nei test o una scritta rossa `Errore` | qualcosa non va | **fermati** e manda la foto a Claude |
| la campagna non finisce dopo ore | è normale: dura ore | lasciala girare |
| devi staccarti (rete, PC spento o in sospensione) con la campagna che gira | si può: riparte da dove era | aspetta la riga `Prova «...»`, **Ctrl+C**, poi stacca. Al ritorno: `aws sso login` e lo stesso blocco. Non staccare la rete a prova in corso: una variante buona può risultare scartata |

```powershell
$env:NODE_EXTRA_CA_CERTS = (Resolve-Path ..\app_cycle_validation\zscaler.pem).Path; $env:AWS_CA_BUNDLE = $env:NODE_EXTRA_CA_CERTS
```

---

## 1. Cosa fare adesso

| | Tappa | Stato |
|---|---|---|
| ✅ | 1-3 · Preparare, campagne, migliorie | 28-11: base `quasi_finale`, 0 falsi errori, 42/45 e 31/31 stabili |
| 👉 | 4 · Prove dal frontend (sezione 4) | A3 e A1 fatte |
| ⬜ | 5 · Grande ingestion, prova di controllo, QA | più avanti, quando hai tempo |
| ⬜ | 6 · Produzione (`develop` → `main`) | quando i cancelli di `V1_CONTRO_V2.md` sono ✅ |

| | Passo | Quando · costo |
|---|---|---|
| ✅ | 1-4e · campagne, v1 sugli stessi cicli, base nuova, schede e regole | 27-11 |
| ✅ | 4g · Domande P13 e P14 | 27-11 notte |
| ✅ | 4h · Versione quasi finale: senza modello, banco, campagna | 28-11 notte: si tiene |
| ✅ | 4i · Chiamata diretta, rigioca, tabelle, una prova di `diretta` | 28-11 mattina: `diretta` -37% di costo |
| 👉 | **4j · Due regole a 0 $ (MG83, MG87), poi la campagna delle migliorie che usano il modello** | adesso · circa 4-5 $, 2-3 ore |
| ⬜ | **4f · EJ200 sul PC** | dopo l'ingestion EJ200 · centesimi |
| ⬜ | **5 · Grande ingestion e QA** | dopo |

---

**👉 Passo 4j · Due regole a 0 $, poi la campagna delle migliorie che usano il modello**
(circa 4-5 $, 2-3 ore)

Passo 4i fatto il 28-11 mattina: chiamata diretta `ok`, `eval rigioca` ok, MG48 sul grande
senza differenze, tabelle ✅, una prova di `diretta` sul piccolo: 0,22 $ contro 0,35 $ con gli
stessi errori. Dalle tabelle Claude ha scritto due regole finali (si provano sulle prove già
fatte, 0 $): `meno_avvisi` (MG83, la fonte assente detta una volta sola) e `limiti_citati`
(MG87, il falso OK del limite invertito).

1. **Aggiornare** (2.1).
   - **Deve uscire:** in fondo `... passed` e nessun `failed`.
   - **Mandami:** la foto dell'ultima riga.
2. **Le due regole sulle prove già fatte, e MG48 sul piccolo** (0 $, qualche minuto):

   ```powershell
   $env:UV_PYTHON = "3.14"
   [Console]::OutputEncoding = [Text.Encoding]::UTF8; $env:PYTHONIOENCODING = "utf-8"
   uv run cycle-validation eval rigioca --variante meno_avvisi
   uv run cycle-validation eval rigioca --variante limiti_citati
   uv run cycle-validation eval senza-modello --insiemi piccolo --variante eval/varianti/altro_stadio.yaml
   ```

   - **Deve uscire:** quattro righe `Rigiocate 3 prove di quasi_finale con ...` (piccolo e
     grande per ogni regola), poi `Senza modello con altro_stadio, piccolo: ...` e `Differenza
     sul piccolo: ...`. Atteso per `meno_avvisi`: grande `WARNING per ciclo 8.9 → 5` circa,
     errori, falsi OK e falsi errori uguali. Per `limiti_citati`: piccolo `falsi OK a prova 1.0
     → 0.0` se la riga citata dal modello contiene il limite (altrimenti nessuna differenza),
     falsi errori sempre 0.
   - **Mandami:** la foto delle quattro righe `Rigiocate ...` e delle righe `Senza modello con
     altro_stadio, piccolo` e `Differenza sul piccolo`.
3. **La campagna** (circa 4-5 $, 2-3 ore): le 2 prove che mancano di `diretta` sul piccolo e
   le 3 sul grande, poi `testo_comune` e `lingue_insieme` (3 sul piccolo e 3 sul grande). Le
   prove già fatte si saltano; se si ferma (tetto di spesa o PC spento), rilanciata riparte da
   dove era. Prima `aws sso login` se serve:

   ```powershell
   $env:UV_PYTHON = "3.14"
   [Console]::OutputEncoding = [Text.Encoding]::UTF8; $env:PYTHONIOENCODING = "utf-8"
   uv run cycle-validation eval campagna
   ```

   - **Deve uscire:** per ogni prova le righe dei cicli e `Prova «...»: ...`, alla fine
     `Campagna finita. Prove fatte ora: 14 · spesa ... $` e `Report finale: runs\campagna.md`.
     Non deve uscire `ATTENZIONE: prova non valida`.
   - **Mandami:** da `runs\campagna.md` le due tabelle delle varianti (piccolo e grande, con
     la colonna «Decisione») e la foto della riga `Campagna finita`.

Con queste foto Claude decide che cosa entra nella base e aggiorna `V1_CONTRO_V2.md`.

---

**⬜ Passo 4f · EJ200 sul PC**

`prova-ej200` non lascia niente: legge la conoscenza EJ200 da S3, tiene i testi in una cartella
temporanea che cancella alla fine, non scrive in `runs\`. A schermo solo impronte e conteggi.
A Claude solo la foto dello schermo; a Copilot niente di EJ200.

1. **Documenti su S3 e ingestion EJ200** (knowledge-index). La v2 conosce RDR, EF e RN: un'altra
   sigla (per esempio «RI») dimmela prima. Le copie sul PC: fuori da `ProgettoDocumenti` e dalle
   cartelle git, cancellate dopo il caricamento.
   - **Mandami:** a parole, la chiave del `current.json` EJ200 (senza bucket) e i conteggi.
2. **Le stampe EJ200** in una cartella fuori da ogni cartella git. Sostituisci
   `<cartella EJ200>` e, se è diversa, la chiave:

```powershell
$env:UV_PYTHON = "3.14"
[Console]::OutputEncoding = [Text.Encoding]::UTF8; $env:PYTHONIOENCODING = "utf-8"
aws sso login
uv run cycle-validation prova-ej200 "<cartella EJ200>" --bucket (Get-Content data/bucket.txt) --conoscenza-ej200 "Manufacturing AI/ingestion-v2-test-qa-output/knowledge/ej200/current.json" --regione eu-south-1
```

   - **Deve uscire:** `Conoscenza EJ200 ...`, una riga per stampa con i conteggi, `Totale: ...`,
     `Cartella temporanea cancellata; niente in runs.` (oppure `prova non partita (...)`).
   - **Mandami:** la foto dello schermo.

---

**⬜ Passo 5 · Grande ingestion e QA**

1. Ingestion di tutti i documenti civili, con le 2 schede LEAP di M5.
2. Sezione [5](#5-dopo-una-nuova-ingestion) blocco A, cicli veri (3.2) e una prova della base sul
   grande (3.7, 0,25 $).
   - **Mandami:** riga finale e riepilogo.
3. Dimmi il puntatore della conoscenza scelta; poi Salvare (2.2) e QA (sezione 7).

**Quando hai tempo:** dimmi se la guida agli unit test la vuoi in Markdown o in Word; manda il
messaggio al collega del frontend (6.2).

---

## 2. Aggiornare e salvare

### 2.1 Aggiornare il codice sul PC

**Quando:** ogni volta che Claude dice di aver cambiato qualcosa. **Costa:** niente.

**Cosa fa:** scarica il repository personale; controlla di essere nella cartella
`app_cycle_validation_v2` (se no scrive `FERMO` e non tocca niente); toglie i file che non ci sono
più (`tolto: ...`); copia codice, test, prompt, impostazioni, varianti, campagna, errori noti e
documenti; lancia i test. **Non tocca** `data/`, `runs/`, `eval/casi/aziendali/`, `Dockerfile`,
`vendor/`, `config/settings.azienda.yaml`.

```powershell
$env:UV_PYTHON = "3.14"
$tmp = Join-Path $env:TEMP "cv2-aggiornamento"; Remove-Item -Recurse -Force $tmp -ErrorAction SilentlyContinue
git clone --quiet --depth 1 https://github.com/DavideZanni/cycle-validation-v2.git $tmp
$qui = (Get-Location).ProviderPath; $mirror = "src", "tests", "prompts", "eval\casi\sintetici", "eval\varianti", "examples"
$ok = (Test-Path "$tmp\src\cycle_validation\cli.py") -and ((Split-Path -Leaf $qui) -eq "app_cycle_validation_v2"); if (-not $ok) { "FERMO: download non riuscito o terminale non nella cartella app_cycle_validation_v2. Niente cambiato." }
if ($ok) { $tolti = @(foreach ($d in $mirror) { if (Test-Path $d) { Get-ChildItem $d -Recurse -File | Where-Object { $_.FullName -notmatch '\\__pycache__\\' -and -not (Test-Path -LiteralPath (Join-Path $tmp $_.FullName.Substring($qui.Length + 1))) } } }) + @(Get-ChildItem docs -File -Filter *.md | Where-Object { -not (Test-Path -LiteralPath "$tmp\docs\$($_.Name)") }); $tolti | ForEach-Object { "tolto: " + $_.FullName.Substring($qui.Length + 1); Remove-Item -LiteralPath $_.FullName -Force } }
if ($ok) { foreach ($d in $mirror) { robocopy "$tmp\$d" $d /MIR /XD __pycache__ /NFL /NDL /NJH /NJS /NP | Out-Null }; foreach ($d in "docs", "config", "eval\modelli") { robocopy "$tmp\$d" $d /E /NFL /NDL /NJH /NJS /NP | Out-Null } }
if ($ok) { Copy-Item "$tmp\pyproject.toml", "$tmp\uv.lock", "$tmp\README.md", "$tmp\.gitignore" . -Force; Copy-Item "$tmp\eval\errori-noti.yaml", "$tmp\eval\campagna.yaml" eval -Force }
if ($ok) { Get-ChildItem src, tests -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force; Remove-Item -Recurse -Force .pytest_cache, .mypy_cache, .ruff_cache -ErrorAction SilentlyContinue }
Remove-Item -Recurse -Force $tmp -ErrorAction SilentlyContinue
uv run pytest -q
```

- **Deve uscire:** forse qualche `tolto: ...`; poi puntini e, in fondo, `... passed` (qualche
  `skipped` va bene) e **nessun** `failed`. Con `FERMO` niente è cambiato: controlla la cartella
  del terminale (0.2) e rilancia.
- **Mandami:** la foto dell'ultima riga (e delle righe `tolto:`). Se c'è `failed`: la foto
  dell'elenco `FAILED`.

### 2.2 Salvare nel repository aziendale

**Quando:** dopo un Aggiornare andato bene, quando Claude lo dice. **Costa:** niente. Salva la v2
sul ramo `feature/cycle-validation-v2`; `develop` e `main` non cambiano. I dati aziendali restano
fuori (git li ignora). Due blocchi: commit, poi push.

**Blocco 1: commit**

```powershell
git add src tests docs examples eval/errori-noti.yaml eval/campagna.yaml eval/casi/sintetici eval/varianti eval/modelli config prompts pyproject.toml uv.lock README.md .gitignore Dockerfile ../buildspec.yml
if (Test-Path vendor) { git add vendor }
git status --short
git commit -m "v2: aggiornamento dal repository personale"
```

- **Deve uscire:** righe `M`/`A`/`D` solo sotto le cartelle del `git add`, **niente** sotto
  `data/` o `runs/`; poi il riepilogo del commit. `nothing to commit` va bene: lancia lo stesso
  il blocco 2.

**Blocco 2: push** (controlla da solo ramo e file; se qualcosa non torna scrive `FERMO` e non
manda niente)

```powershell
$branch = git branch --show-current
$fuori = git show --name-only --format= HEAD | Where-Object { $_ -and $_ -notmatch '^app_cycle_validation_v2/(src|tests|docs|examples|eval/casi/sintetici|eval/varianti|eval/modelli|config|prompts|vendor)/|^app_cycle_validation_v2/(pyproject\.toml|uv\.lock|README\.md|\.gitignore|Dockerfile|eval/errori-noti\.yaml|eval/campagna\.yaml)$|^buildspec\.yml$' }
if ($branch -ne "feature/cycle-validation-v2") {
  "FERMO: sei sul branch '$branch', non su feature/cycle-validation-v2. Niente push."
} elseif ($fuori) {
  "FERMO: nell'ultimo commit ci sono file fuori dalle cartelle previste. Niente push:"; $fuori
} else {
  git push origin feature/cycle-validation-v2; git log --oneline -1; git status -sb | Select-Object -First 1
}
```

- **Deve uscire:** la riga del push, l'ultimo commit e
  `## feature/cycle-validation-v2...origin/feature/cycle-validation-v2` **senza** `[ahead ...]`.
- **Se esce `FERMO` o il push è rifiutato:** non insistere, niente `--force`: foto a Claude.
- **Mandami:** la foto della parte finale.

---

## 3. Le prove

### 3.1 Come funzionano

**Una prova** fa girare la v2 su un insieme di cicli e conta errori trovati, falsi errori, costo
e tempo. Più prove con lo stesso nome formano una **variante**; servono almeno 2 prove (oggi 3),
perché il modello non risponde sempre uguale. Di solito le lancia la **campagna** (3.5).

**Gli errori da trovare**

| Specie | Cosa sono | Cosa dicono |
|---|---|---|
| **Visti** | gli errori noti di `eval/errori-noti.yaml` (20 dal 26-11 sera) | se la v2 trova gli errori che conosciamo |
| **Mai visti: copie cieche** (3.3) | copie di cicli veri con **una** operazione cambiata dal programma | se la v2 trova anche errori nuovi (**generalizza**) |
| **Mai visti: gruppo nascosto** (3.4) | stampe con errori messi a mano | come sopra, con errori pensati da una persona: la misura migliore |

I sei tipi di copie cieche:

| Tipo | Cosa cambia | Chi lo trova |
|---|---|---|
| `numero_una_lingua` | un numero, in una lingua sola | il **codice** (serve solo a vedere che non si è rotto niente) |
| `task_inesistente` | il codice di un task in uno che non esiste | il **codice** (come sopra) |
| `numero_manuale` | un numero cambiato nelle due lingue con un valore che il manuale non ha | il **modello** |
| `negazione_una_lingua` | un «non»/«not» tolto in una lingua | il **modello** |
| `negazione_due_lingue` | un «non»/«not» tolto in tutte e due le lingue | il **modello**, confrontando con il manuale |
| `limite_invertito` | minimo ↔ massimo, almeno ↔ al massimo, nelle due lingue | il **modello**, confrontando con il manuale |

I report dicono solo **quanti** errori mai visti ci sono per tipo, mai quali.

**I due insiemi**

| Insieme | Cicli | Quando |
|---|---|---|
| **piccolo** | i cicli noti (dal 26-11 sera 14: 9 con errori, 5 giusti), le copie cieche, il gruppo nascosto | ogni variante |
| **grande** | i cicli noti e tutti i cicli veri civili confrontabili (3.2) | le varianti che si tengono sul piccolo (tutte con `grande: sempre`, come oggi): controlla che sui cicli veri non escano più ERRATO o WARNING |

Le prove si confrontano solo dentro lo stesso insieme e con le stesse copie cieche.

**Dove finiscono i risultati**

| Cosa | Dove |
|---|---|
| Prove con Haiku | `runs\prove-piccolo\`, `runs\prove-grande\` (Sonnet, 24-11: `...-sonnet\`) |
| Report di una prova | `<cartella>\<data>-<nome>\prestazioni.md` (non fotografarlo intero) |
| Riepilogo di una cartella | `<cartella>\riepilogo.md`: scelta migliore, classifica, tutte le prove, errore per errore |
| Report della campagna | `runs\campagna.md` |

**Come si decide** (da solo, nel riepilogo; dettagli in `DOCUMENTAZIONE.md` 15.3): una variante
è **scartata** con un solo falso errore, un ciclo non eseguito, un ciclo oltre 10 minuti o un
costo oltre il doppio della base. **Si tiene** se trova più errori **stabili** (trovati in tutte
le prove) della base senza perdere errori mai visti, oppure gli stessi errori con un risparmio
vero (costo -10%, tempo -20% o 1 WARNING in meno per ciclo).

### 3.2 Scegliere i cicli veri

**Cosa fa:** sceglie i cicli del grande (i cicli noti e tutti i cicli veri civili con almeno l'80%
delle operazioni confrontabili). **Quando:** fatto il 24-11; di nuovo dopo una nuova ingestion.
**Costa:** niente. I percorsi restano in `runs\prove-grande\cicli.txt`; a schermo solo impronte.

```powershell
$env:UV_PYTHON = "3.14"
[Console]::OutputEncoding = [Text.Encoding]::UTF8; $env:PYTHONIOENCODING = "utf-8"
$foto = (Get-ChildItem eval/casi/aziendali/conoscenza -Directory -Filter "foto-*" | Sort-Object Name | Select-Object -Last 1).FullName
$kb = "$foto/Manufacturing AI/ingestion-v2-test-qa-output/knowledge/civil/"; $v = $kb + (Get-Content ($kb + "current.json") | ConvertFrom-Json).path
uv run cycle-validation eval scegli (Resolve-Path "..\..").Path --knowledge $v --quanti 0 --out runs/prove-grande/cicli.txt
```

- **Deve uscire:** `Stampe: ... Scelti N: noti 14, veri M. Per tipo: MOS ..., DR ....` e una riga
  per ciclo. Se N è più di 100: foto a Claude (si mette `--quanti 100`).
- **Mandami:** la foto.

### 3.3 Fare le copie cieche

**Cosa fa:** dai cicli scelti fa copie con un errore ciascuna (al massimo 6 per ciclo, 5 per
ognuno dei due tipi del codice; le copie uguali si saltano). **Quando:** solo quando un passo lo
dice (nuova ingestion o miglioria nella base), ogni volta con un **seme nuovo**. Usati: 1 il 24-11,
2 il 26-11; il prossimo è `3`. **Costa:** niente.

```powershell
$env:UV_PYTHON = "3.14"
[Console]::OutputEncoding = [Text.Encoding]::UTF8; $env:PYTHONIOENCODING = "utf-8"
$seme = 3
$foto = (Get-ChildItem eval/casi/aziendali/conoscenza -Directory -Filter "foto-*" | Sort-Object Name | Select-Object -Last 1).FullName
$kb = "$foto/Manufacturing AI/ingestion-v2-test-qa-output/knowledge/civil/"; $v = $kb + (Get-Content ($kb + "current.json") | ConvertFrom-Json).path
Remove-Item runs/mutazioni -Recurse -ErrorAction SilentlyContinue
uv run cycle-validation eval muta --lista runs/prove-grande/cicli.txt --knowledge $v --quanti 100 --seme $seme --out runs/mutazioni
```

- **Deve uscire:** `Copie con un errore cieco: N su 100 chieste, seme ...` e quante copie per
  tipo.
- **Non aprire** `runs\mutazioni\errori.yaml`. **Mandami:** la foto (solo i conteggi).

### 3.4 Il gruppo nascosto (facoltativo)

La misura migliore: gli errori li pensa una persona.

1. `code runs/prove-grande/cicli.txt` (non fotografarlo): le prime righe sono i cicli noti
   (10, o 14 se la lista è stata rifatta dopo il 26-11), dopo ci sono i cicli veri. Non usare
   895167b9, 22f586bb, 737dec71 e 2d724fba: ora sono cicli noti.
2. Copia una decina di quelle stampe in `data\nascosti\`.
3. In ogni copia cambia a mano uno o due punti della descrizione. I più utili: **un numero
   cambiato in tutte e due le lingue**; parole o frasi cambiate in tutte e due le lingue. Meglio
   se lo fa un collega.
4. Lancia il blocco: prepara e apre `data\errori-nascosti.yaml`.
5. Per ogni stampa scrivi le operazioni cambiate (es. `'030': quantità cambiata in tutte e due
   le lingue`) e salva.
6. Scrivi a Claude solo «gruppo nascosto pronto, N stampe». Da lì il piccolo lo comprende.

```powershell
New-Item -ItemType Directory -Force data/nascosti | Out-Null
$righe = Get-ChildItem data/nascosti -Filter *.pdf | ForEach-Object { "  '" + (Get-FileHash $_.FullName).Hash.Substring(0, 8).ToLower() + "':  # " + $_.Name + "`n    visto: false`n    errori:`n      '010': cosa hai cambiato (il numero dell'operazione è un esempio)" }
"cicli:`n" + ($righe -join "`n") | Set-Content data/errori-nascosti.yaml -Encoding utf8; code data/errori-nascosti.yaml
```

**Mai foto di questo file né delle stampe.**

### 3.5 La campagna: tutte le prove in automatico

**Cosa fa:** lancia da sola le prove di `eval/campagna.yaml` (lo scrive Claude): la base e le
varianti sul piccolo, poi sul grande la base e le varianti che si tengono. Alla fine scrive
`runs\campagna.md`.

- **Da sola** trova la conoscenza, i cicli scelti, le copie cieche e il gruppo nascosto, e
  sceglie MOS o DR per ogni ciclo.
- **Riprende da dove era:** le prove già fatte non si rifanno. Una prova interrotta con Ctrl+C
  non conta.
- **Si ferma da sola:** al tetto di spesa (oggi 10 $) o se il modello non risponde (accesso
  scaduto: `aws sso login` e rilancia). Le prove senza risposte si tolgono e si rifanno.

**Il piano** (gratis, non lancia niente):

```powershell
$env:UV_PYTHON = "3.14"
[Console]::OutputEncoding = [Text.Encoding]::UTF8; $env:PYTHONIOENCODING = "utf-8"
uv run cycle-validation eval campagna --piano
```

- **Deve uscire:** `Piccolo: N cicli e copie; grande: M cicli.` e per ogni insieme una riga per
  variante: `N da fare` oppure `già fatte`.

**La campagna** (dura ore; costa al massimo il tetto):

```powershell
$env:UV_PYTHON = "3.14"
[Console]::OutputEncoding = [Text.Encoding]::UTF8; $env:PYTHONIOENCODING = "utf-8"
uv run cycle-validation eval campagna
code runs/campagna.md
```

- **Deve uscire:** per ogni prova `=== haiku · <insieme> · <variante> · prova N di 3 · spesa
  finora ... $`, una riga per ciclo e `Prova «...»: visti ... · mai visti ... · costo ... $`;
  alla fine `Campagna finita. Prove fatte ora: N · spesa ... $.`
- **Mandami:** la riga finale e le foto del report che Claude chiede.

**Solo una parte:** aggiungi in fondo alla riga `uv run cycle-validation eval campagna`:

| Aggiunta | Cosa fa |
|---|---|
| `--insiemi piccolo` / `--insiemi grande` | solo un insieme (il report diventa `runs\campagna-<insieme>.md`) |
| `--varianti a,b` | solo queste varianti (la base sempre per prima) |
| `--ripetizioni 3` | prove per variante |
| `--grande sempre` / `--grande mai` | sul grande tutte le varianti / nessuna |
| `--massimo-dollari 10` | tetto di spesa diverso per questa volta |
| `--modelli haiku` | solo un modello (se nel file ce ne sono due) |
| `--piano` | mostra cosa farebbe |
| `--solo-report` | riscrive `runs\campagna.md` con le prove che ci sono, senza lanciare niente |

### 3.6 Leggere i risultati

Gratis. Nei file premi **Ctrl+Shift+V** per la vista impaginata.

| Cosa | Comando |
|---|---|
| Report della campagna | `code runs/campagna.md` |
| Riepilogo del piccolo / del grande | `code runs/prove-piccolo/riepilogo.md` · `code runs/prove-grande/riepilogo.md` |
| Elenco delle prove fatte | blocco qui sotto |

```powershell
Get-ChildItem runs/prove-piccolo, runs/prove-grande -Directory -ErrorAction SilentlyContinue | Select-Object Name
```

Il report di una prova (`prestazioni.md`) contiene testo dei manuali: si fotografano solo le
tabelle che Claude chiede.

```powershell
$insieme = "piccolo"; $ultima = Get-ChildItem "runs/prove-$insieme" -Directory | Where-Object Name -match "^\d{8}-" | Sort-Object Name | Select-Object -Last 1; code "$($ultima.FullName)/prestazioni.md"
```

### 3.7 Una prova a mano

**Quando:** solo se Claude lo chiede (di solito basta la campagna). **Cosa cambiare:** nella terza
riga `$nome` (`"base"` o il nome di una variante) e `$insieme` (`"piccolo"` o `"grande"`).
**Costa:** circa 0,17 $ il piccolo con Haiku. La prova conta anche per la campagna.

```powershell
$env:UV_PYTHON = "3.14"
[Console]::OutputEncoding = [Text.Encoding]::UTF8; $env:PYTHONIOENCODING = "utf-8"
$nome = "base"; $insieme = "piccolo"
$foto = (Get-ChildItem eval/casi/aziendali/conoscenza -Directory -Filter "foto-*" | Sort-Object Name | Select-Object -Last 1).FullName
$kb = "$foto/Manufacturing AI/ingestion-v2-test-qa-output/knowledge/civil/"; $v = $kb + (Get-Content ($kb + "current.json") | ConvertFrom-Json).path
$variante = if (Test-Path "eval/varianti/$nome.yaml") { @("--variante", "eval/varianti/$nome.yaml") } else { @() }
$dieci = Get-ChildItem (Resolve-Path "..\..").Path -Recurse -Filter "*.pdf" -ErrorAction SilentlyContinue | Where-Object { $_.Name -like "*errori*" -or (Get-FileHash $_.FullName).Hash.Substring(0, 8).ToLower() -in @("4e64d49a", "8bdb25d5", "04ecaabe", "5ff17062", "895167b9", "22f586bb", "737dec71", "2d724fba") } | Group-Object { (Get-FileHash $_.FullName).Hash } | ForEach-Object { $_.Group[0] }
$cicli = @("--attesi", "eval/errori-noti.yaml")
if ($insieme -eq "grande") { $cicli += @("--lista", "runs/prove-grande/cicli.txt") } else { $cicli += @($dieci.FullName); if (Test-Path runs/mutazioni/lista.txt) { $cicli += @("--lista", "runs/mutazioni/lista.txt", "--attesi", "runs/mutazioni/errori.yaml") }; if (Test-Path data/errori-nascosti.yaml) { $cicli += @("data/nascosti", "--attesi", "data/errori-nascosti.yaml") } }
"prova «$nome» sull'insieme $insieme" + $(if ($variante) { " con la variante" } else { "" })
uv run cycle-validation eval prova @cicli --nome $nome --knowledge $v --config data/settings.yaml @variante --cartella "runs/prove-$insieme"
```

- **Deve uscire:** una riga per ciclo (`<impronta> errori|giusto|vero (MOS|DR): trovati ... ·
  mancati ... · ERRATO in più ...`; per le copie cieche solo `mai visto: trovato|mancato`), poi
  `Prova «...»: visti ... · costo ... $`. Se esce `ATTENZIONE: prova non valida`: sezione 0.4.
- **Mandami:** la foto della riga finale.

### 3.8 Mettere ordine: togliere, azzerare, archiviare le prove

**Togliere una prova:** cancella la sua cartella in `runs\prove-...`, poi rifai il riepilogo
(gratis):

```powershell
$env:UV_PYTHON = "3.14"; uv run cycle-validation eval riepilogo --cartella runs/prove-piccolo
```

**Archiviare** (quando cambiano copie cieche o conoscenza: le prove vecchie non si confrontano
più con le nuove). Sposta `runs\prove-piccolo` e `runs\prove-grande` in `runs\archivio-<data>-...`
(restano da leggere). Dopo: la campagna (le copie cieche 3.3 si rifanno solo se il passo lo dice).

```powershell
$d = Get-Date -Format "yyyyMMdd-HHmm"; "piccolo", "grande" | ForEach-Object { if (Test-Path "runs/prove-$_") { Move-Item "runs/prove-$_" "runs/archivio-$d-$_" } }
New-Item -ItemType Directory -Force runs/prove-grande | Out-Null; Copy-Item "runs/archivio-$d-grande/cicli.txt" runs/prove-grande/cicli.txt; Get-ChildItem runs -Directory | Select-Object Name
```

La seconda riga rimette al suo posto la lista dei cicli scelti (serve alle copie cieche e al
grande). Le cartelle `runs\prove-piccolo-sonnet` e `runs\prove-grande-sonnet` si spostano a mano nella
stessa cartella di archivio.

**Azzerare** (cancella **per sempre** tutte le cartelle `runs\prove-*` e i report della
campagna; tiene la lista dei cicli scelti; non tocca copie cieche, gruppo nascosto, archivi).
Di solito meglio archiviare.

```powershell
$ok = (Split-Path -Leaf (Get-Location).ProviderPath) -eq "app_cycle_validation_v2"; if (-not $ok) { "FERMO: terminale non nella cartella app_cycle_validation_v2. Niente cancellato." }
if ($ok) { $lista = "runs/prove-grande/cicli.txt"; $copia = Join-Path $env:TEMP "cv2-cicli.txt"; $tieni = Test-Path $lista; if ($tieni) { Copy-Item $lista $copia -Force }; $via = @(Get-ChildItem runs -Directory -Filter "prove-*" -ErrorAction SilentlyContinue); $via | ForEach-Object { "tolta: runs\" + $_.Name }; $via | Remove-Item -Recurse -Force; Remove-Item runs/campagna*.md -ErrorAction SilentlyContinue; if ($tieni) { New-Item -ItemType Directory -Force runs/prove-grande | Out-Null; Move-Item $copia $lista -Force; "resta: runs\prove-grande\cicli.txt (la lista dei cicli scelti)" } else { "lista dei cicli scelti assente: rifai 3.2" } }
```

- **Deve uscire:** `tolta: runs\prove-...` per ogni cartella e `resta: runs\prove-grande\cicli.txt`.

---

### 3.9 La v1 sugli stessi cicli

**Fatto il 27-11** con la v1 (la versione di prima, in QA come in produzione): risultati e testo
originale delle stampe in `docs/CONFRONTO_V1_14_CICLI.md`. La v1 ha preso le stampe MOS; le tre
A6 si sono fermate (chiede serial e condition del DR) e 298bc28e non si è caricata. Il blocco
resta per ricaricare 298bc28e.

**A cosa serve:** la v2 si misura nelle campagne sulle stampe con errori conosciuti
(`eval/errori-noti.yaml`); la v1 no. Per dire quale delle due è più giusta servono le stesse
stampe nella v1 (in QA, uguale alla produzione). **Costa:** niente per noi, circa 1 ora.

**1. Le copie con il nome = impronta** (così nelle foto non ci sono codici veri):

```powershell
$env:UV_PYTHON = "3.14"
$noti = @("298bc28e", "c5ff3cd6", "f355dc3c", "38960731", "5ff17062", "22f586bb", "895167b9", "8d3c673c", "e9b74c84", "4e64d49a", "8bdb25d5", "04ecaabe", "737dec71", "2d724fba")
New-Item -ItemType Directory -Force runs/v1-confronto | Out-Null
Get-ChildItem (Resolve-Path "..\..").Path -Recurse -Filter "*.pdf" -ErrorAction SilentlyContinue | ForEach-Object { $h = (Get-FileHash $_.FullName).Hash.Substring(0, 8).ToLower(); if ($h -in $noti -and -not (Test-Path "runs/v1-confronto/$h.pdf")) { Copy-Item $_.FullName "runs/v1-confronto/$h.pdf" } }
$trovate = (Get-ChildItem runs/v1-confronto -Filter "*.pdf").BaseName; "copie: " + $trovate.Count + " su " + $noti.Count; "mancano: " + (($noti | Where-Object { $_ -notin $trovate }) -join ", ")
```

- **Deve uscire:** `copie: 14 su 14` e `mancano:` vuoto (se ne manca qualcuna, va bene lo
  stesso: mandami la riga).

**2. Nel frontend della QA**, per ogni file di `runs\v1-confronto` (Nuova validazione, MOS,
carica il file): se chiede serial number e condition o dice che è un DR, **saltalo** e scrivimi
l'impronta. **Mandami** per ogni stampa una foto dell'intestazione (si vede il nome del file =
impronta e il numero di errori) e una foto di **ogni riga con un bollino rosso «Error»**. Non
servono le righe OK.

**3. Facoltativo, dopo la campagna finale:** lo stesso con la v2 in locale (localhost), con le
impostazioni scelte per la produzione, così le due tabelle sono fatte nello stesso modo.

## 4. Prove dal frontend

**Come si avvia:** VS Code → **Run and Debug** → **«CV v2»** → avvia; poi nel browser
`http://localhost:3000`. **Costa:** qualche centesimo per ciclo. Le targhe escono sempre
N/A (dal PC il database delle macchine non si raggiunge; prima del 27-11 uscivano WARNING): è
normale.

Le prove, in ordine:

1. **I tre cicli «con errori»** (MOS): gli ERRATO devono essere quelli delle prove.
2. **Il ciclo MOS più lungo:** tempo fino al risultato sotto i **10 minuti**.
3. **Un DR con serial number e condition**, poi lo stesso **senza** (se Confirm non si accende,
   salta).
4. **File sbagliato:** un DR scegliendo MOS → deve uscire «Modulo sbagliato».
5. **Storico:** riapri una chat, rinominala, cancellala.
6. **Download** del CSV dei risultati.

**Mandami:** la foto dell'intestazione dei risultati di ogni prova e il tempo della prova 2 a
parole. Se qualcosa non va: foto del frontend e del log di CV v2.

---

## 5. Dopo una nuova ingestion

**Quando:** dopo aver caricato manuali nuovi nella conoscenza. **In ordine:** blocco A
(fotografia), blocco B (lista dei manuali), archiviare le prove (3.8), cicli veri (3.2), copie
cieche (3.3), campagna (3.5).

**A. Fotografia della conoscenza** (scarica e controlla la conoscenza civile di prova)

```powershell
$env:UV_PYTHON = "3.14"
$foto = "eval/casi/aziendali/conoscenza/foto-" + (Get-Date -Format "yyyyMMdd-HHmm")
uv run cycle-validation eval fotografia --bucket (Get-Content data/bucket.txt) --prefisso "Manufacturing AI/ingestion-v2-test-qa-output/knowledge/civil/" --out $foto --regione eu-south-1
$kb = "$foto/Manufacturing AI/ingestion-v2-test-qa-output/knowledge/civil/"; "versione pubblicata: " + (Get-Content ($kb + "current.json") | ConvertFrom-Json).path; uv run cycle-validation kb-check ($kb + (Get-Content ($kb + "current.json") | ConvertFrom-Json).path)
```

- **Deve uscire:** `Fotografia in ...`, una `versione pubblicata` **diversa** da
  `v/20261123T142517Z/` e i conteggi di `kb-check` senza righe `Errore:`.

**B. La lista dei manuali** (gratis; a schermo i manuali si chiamano M1, M2...; i codici veri
restano in `runs\manuali-da-ingestionare.txt`)

```powershell
$env:UV_PYTHON = "3.14"
[Console]::OutputEncoding = [Text.Encoding]::UTF8; $env:PYTHONIOENCODING = "utf-8"
$foto = (Get-ChildItem eval/casi/aziendali/conoscenza -Directory -Filter "foto-*" | Sort-Object Name | Select-Object -Last 1).FullName
$kb = "$foto/Manufacturing AI/ingestion-v2-test-qa-output/knowledge/civil/"; $v = $kb + (Get-Content ($kb + "current.json") | ConvertFrom-Json).path; "conoscenza: " + (Split-Path -Leaf $foto) + " · " + (Get-Content ($kb + "current.json") | ConvertFrom-Json).path
uv run cycle-validation manuali (Resolve-Path "..\..").Path --conoscenza $v --errori 298bc28e=005,035 --errori c5ff3cd6=030,040 --errori f355dc3c=010,030,040,050 --errori 5ff17062=010,030,040,050 --errori 895167b9=010,030,050,060 --errori 22f586bb=010,030,050,060 --errori 38960731=050 --errori 8d3c673c=140 --errori e9b74c84=025
```

- **Deve uscire:** `Manuali citati: N; da ingestionare (mancano): M; già dentro ma con task che
  mancano: K.` e una riga per manuale (`M1: ...`). Il 26-11: M1 con 3 task mancanti, l'SPM con
  1, M4 e M5 mancano: con i file nuovi devono scendere.
- **Mandami:** la foto dello **schermo**. Il file `runs\manuali-da-ingestionare.txt` ha i codici
  veri e i percorsi: serve a te per l'ingestion, **non fotografarlo**.

---

## 6. Le persone

### 6.1 Domande

P1-P9 chiuse il 26-11, P10 e P11 il 27-11 (decise da Copilot sui dati, con la **regola prudente**:
dove i dati non bastano, WARNING e mai ERRATO). Le risposte e cosa cambiano sono in
`MEMORIA.md` (note del 26-11 e del 27-11), `MIGLIORIE.md` ed `eval/errori-noti.yaml`. Se una persona che conosce cicli e manuali dice altro, scrivilo
a Claude a parole, senza codici veri.

### 6.2 Messaggio per il collega del frontend

Da mandare se non l'hai già fatto, così com'è:

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

### 6.3 Prompt per Copilot: la documentazione completa

**A cosa serve:** Copilot vede sul PC quello che Claude non vede: il codice dell'ingestion,
la v1, il frontend, il buildspec, le cartelle su S3 (solo i nomi). Con questo prompt confronta
`docs/DOCUMENTAZIONE.md` con tutto quello che c'è e scrive cosa manca, cosa è sbagliato e
com'è fatta l'ingestion. Claude poi lo mette in `DOCUMENTAZIONE.md` e nella guida allo studio,
così una persona nuova (o un'altra IA) impara tutto da zero leggendo solo quello.

**Quando:** quando hai tempo, non mentre gira una campagna (non costa niente, ma è lungo).
Copilot **in modalità Ask**: non deve modificare niente.

```text
Sei un revisore tecnico. Lavori in sola lettura: NON modificare, creare o cancellare file, NON
lanciare comandi che scrivono qualcosa. Non leggere la cartella data/ (è esclusa) e non
aggirare l'esclusione.

OBIETTIVO
Il file app_cycle_validation_v2/docs/DOCUMENTAZIONE.md deve permettere a una persona nuova, o
a un'altra intelligenza artificiale, di capire DA ZERO tutto il sistema Cycle Validation v2:
l'ingestion (come nasce la conoscenza dai documenti) e la validazione dei cicli (come la v2
controlla una stampa). Deve essere completo, corretto e senza parti nascoste: anche le regole
implicite nel codice, i valori predefiniti, i casi limite, cosa succede quando qualcosa non va.

COSA LEGGERE
1. docs/DOCUMENTAZIONE.md, tutto, poi docs/MEMORIA.md per la storia.
2. Il codice della v2: app_cycle_validation_v2/src, config, prompts, tests, Dockerfile.
3. Il codice dell'ingestion che pubblica la conoscenza su S3 (knowledge-index o la cartella
   che nel workspace la contiene): tutti i passi, i file di regole (per esempio regole.json),
   i comandi, i formati di uscita.
4. La v1 (app_cycle_validation) e il frontend (la pagina Cycle Validation): solo quello che
   serve a capire come la v2 li sostituisce o li usa.
5. buildspec.yml e i file di pubblicazione: come si passa da develop (QA) a main
   (produzione).

COSA SCRIVERE (in italiano molto semplice, frasi corte, termini tecnici spiegati la prima volta)
Parte A - Errori: ogni punto di DOCUMENTAZIONE.md che il codice smentisce. Per ognuno: sezione,
  cosa dice il documento, cosa fa davvero il codice (file e funzione), il testo corretto.
Parte B - Cosa manca: ogni cosa che il codice fa e il documento non dice (regole, soglie,
  valori predefiniti, rami d'errore, tentativi, tempi massimi, cache, permessi, variabili
  d'ambiente, formati). Per ognuna: in quale sezione va e il testo da aggiungere.
Parte C - L'ingestion, dall'inizio alla fine: da dove arrivano i documenti (cartelle S3 solo
  come forma, per esempio <bucket>/.../landing_area/), quali tipi di documento, come si
  leggono i PDF, come si trovano task, targhe, schede, recommendation DR, come si scrive
  ogni file pubblicato (manifest.json, tasks.json, machine_tags.json, process_sheets.json,
  dr_recommendations.json, uncertainty.json, catalog.json di EJ200, current.json), come si
  lancia, quanto costa, quanto dura, cosa fa se un file non si legge, come si aggiunge un
  manuale, come si ripubblica, i limiti noti. Con un diagramma a blocchi in testo (frecce ->).
Parte D - Il giro completo: dall'utente che carica un PDF nel frontend fino al risultato a
  schermo, passando per il servizio, la conoscenza, Redshift, Bedrock. Con un diagramma in
  testo. Dove sta ogni pezzo in AWS (solo il tipo di risorsa e la regione, mai nomi veri).
Parte E - Cose implicite o nascoste: comportamenti che una persona non si aspetta (valori
  scritti nel codice, condizioni che saltano un controllo, differenze tra QA e produzione,
  differenze tra v1 e v2, cose che dipendono dall'ordine dei file).
Parte F - Domande aperte: quello che non riesci a capire dal codice e va chiesto a una persona.

REGOLE SUI DATI (obbligatorie: il testo finisce in un repository pubblico)
Mai scrivere: nomi di bucket, account AWS, ARN, host, nomi o valori di secret, nomi utente,
matricole, nomi di persone, nome dell'azienda o del repository aziendale, codici veri di
manuali (chiamali M1, M2...), numeri DR, serial number, part number, codici di ciclo, contenuti
o codici EJ200. Al loro posto usa segnaposto: <bucket>, <secret di ambiente>, M1, SN-0001.
Gli esempi di file con valori inventati, la forma deve essere quella vera.

FORMATO DELLA RISPOSTA
Markdown, dentro un unico blocco di codice, così si copia tutto insieme. Se è troppo lungo,
dividi in parti («Parte 1 di N») e aspetta che io scriva «continua».
```

**Mandami:** il testo della risposta (copiato e incollato, non in foto: è lungo). **Prima di
mandarlo, controlla** che non ci siano nomi veri (bucket, persone, codici): se ce ne sono,
cancellali. Claude aggiorna `DOCUMENTAZIONE.md` e la guida allo studio.

---

## 7. QA (più avanti)

QA è l'ambiente di prova dell'azienda (ramo `develop`). Dockerfile e buildspec della v2 sono già
sul ramo feature. Finché il ramo non arriva su `develop`, QA resta sulla v1. **Quando arriva su
`main`, anche la produzione passa alla v2:** prima serve una prova QA riuscita.

1. **Pull request** da `feature/cycle-validation-v2` verso `develop`. Quando è unita: dal
   frontend QA un ciclo MOS e un DR (in QA le targhe si controllano davvero). Mandami la foto
   dell'intestazione dei risultati.
2. **Se la v2 in QA non parte:** torna alla v1, poi Salvare (2.2) e pull request.

```powershell
$env:UV_PYTHON = "3.14"
uv run cycle-validation qa --torna-alla-v1
```

3. **Cicli militari** (solo dopo una prova QA riuscita), poi Salvare (2.2) e pull request:

```powershell
$env:UV_PYTHON = "3.14"
uv run cycle-validation qa --conoscenza-civile "Manufacturing AI/ingestion-v2-test-qa-output/knowledge/civil/current.json" --ej200 --conoscenza-ej200 "Manufacturing AI/ingestion-v2-test-qa-output/knowledge/ej200/current.json"
```

La conoscenza: nei blocchi c'è quella di prova; quando scegli la tua (passo 5 della sezione 1)
Claude cambia il puntatore qui. Se Claude dice che il comando `qa` è cambiato: rilancia lo
stesso comando (senza `--ej200` finché i cicli militari sono spenti), poi Salvare.
