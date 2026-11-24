# Lavorare sul PC aziendale

Questo file dice **cosa fare sul PC aziendale**, un passo alla volta, e contiene **tutti i
comandi** da lanciare. È scritto per chi lo apre senza sapere niente del progetto.

**Chi fa cosa:**

| Chi | Cosa fa |
|---|---|
| **Tu** | lanci i comandi sul PC aziendale e mandi a Claude la foto dello schermo |
| **Claude** | scrive e corregge tutto il codice, legge le foto, dice il passo dopo |
| **Copilot** (in VS Code sul PC) | può leggere i file e lanciare i comandi di prova; **non cambia mai il codice** |

Gli altri documenti: `DOCUMENTAZIONE.md` (come è fatto tutto il programma), `MIGLIORIE.md`
(cosa migliorare e come si sceglie), `MEMORIA.md` (cosa è successo finora, risultati delle
prove, problemi già risolti, decisioni prese), `AZIENDA.md` (installare e configurare).

---

## Indice

- **0. Prima di iniziare**: le parole, come si lancia un comando, le regole, cosa fare se va
  storto
- **1. Cosa fare adesso**: dove siamo e la lista dei passi, in ordine
- **2. Aggiornare e salvare**
  - 2.1 Aggiornare il codice sul PC
  - 2.2 Salvare nel repository aziendale
- **3. Le prove**
  - 3.1 Come funzionano
  - 3.2 Scegliere i cicli veri
  - 3.3 Fare le copie cieche
  - 3.4 Il gruppo nascosto (facoltativo)
  - 3.5 La campagna: tutte le prove in automatico
  - 3.6 Leggere i risultati
  - 3.7 Una prova a mano
  - 3.8 Mettere ordine: togliere, azzerare, archiviare le prove
- **4. Prove dal frontend**
- **5. Dopo una nuova ingestion**
- **6. Le persone**: domande da fare, messaggio per il collega del frontend
- **7. QA**: la pubblicazione nell'ambiente di prova

---

## 0. Prima di iniziare

### 0.1 Le parole che servono

| Parola | Cosa vuol dire |
|---|---|
| **v1** | il programma di oggi, quello che usano gli utenti. Non si tocca |
| **v2** | il programma nuovo, quello su cui lavoriamo. Sta nella cartella `app_cycle_validation_v2` |
| **Repository personale** | la copia del codice su GitHub dove scrive Claude. È pubblica: dentro non ci sono mai dati aziendali |
| **Repository aziendale** | il repository dell'azienda. La v2 sta sul ramo `feature/cycle-validation-v2` |
| **Ramo** (branch) | una linea di lavoro separata nel repository. `develop` = ambiente di prova (QA), `main` = produzione |
| **Terminale** | la finestra di VS Code dove si scrivono i comandi (in basso, scheda *Terminal*). Usa PowerShell 7 |
| **Blocco** | un gruppo di comandi di questo file, dentro un riquadro grigio. Si copia tutto insieme |
| **Ciclo** (o **stampa**) | il PDF di un ciclo di lavorazione (PVRM320). La v2 lo legge e controlla ogni operazione |
| **MOS, DR, EJ200** | i tre tipi di ciclo: civile normale, civile con Deviation Request, militare |
| **Impronta** | 8 lettere e cifre calcolate dal contenuto del PDF (per esempio `aaaa1111`). Si usa al posto del nome del file, così nelle foto non compaiono codici veri |
| **Conoscenza** | i manuali già letti e preparati (ingestion) con cui la v2 confronta il ciclo. Sta su AWS; sul PC c'è una copia chiamata **fotografia** |
| **Ingestion** | il lavoro che prende i manuali PDF e li trasforma in conoscenza |
| **Esiti** | per ogni controllo la v2 dice **CORRETTO**, **ERRATO** (c'è un errore) o **WARNING** (non può decidere da sola: serve un controllo a mano) |
| **Errore noto** | un errore messo apposta in una stampa per vedere se la v2 lo trova. Sono 12, in 7 cicli «con errori», scritti in `eval/errori-noti.yaml` |
| **Stampa giusta** | la stampa originale di un ciclo «con errori». Non deve avere nessun ERRATO |
| **Falso errore** | un ERRATO dove non c'è un errore. Deve essere sempre 0 |
| **Errori visti / mai visti** | *visti* = i 12 errori noti, che Claude conosce. *Mai visti* = errori che Claude non conosce (copie cieche e gruppo nascosto): dicono se la v2 funziona anche su errori nuovi |
| **Copie cieche** | copie di cicli veri in cui il programma cambia da solo una operazione. Nessuno sa quale |
| **Gruppo nascosto** | stampe in cui tu o un collega mettete errori a mano. Claude non le vede mai |
| **Prova** | un giro della v2 su un gruppo di cicli: conta gli errori trovati, i falsi errori, il costo e il tempo |
| **Insieme** | il gruppo di cicli di una prova: **piccolo** (veloce) o **grande** (tutti i cicli veri) |
| **Miglioria** | una modifica che dovrebbe far trovare più errori, o costare meno, o andare più veloce |
| **Variante** | una miglioria da provare. Il suo file è `eval/varianti/<nome>.yaml` e dice cosa cambia, perché e cosa ci si aspetta |
| **Base** | la v2 di oggi, senza modifiche. Ogni variante si confronta con la base |
| **Campagna** | un solo comando che lancia tutte le prove in fila (con Haiku e con Sonnet) e scrive un report unico |
| **Report della prova** | il file `prestazioni.md` che ogni prova scrive con i suoi risultati |
| **Riepilogo** | il file `riepilogo.md` di ogni cartella di prove: le mette insieme, fa la classifica e dice quale variante tenere |
| **Modello** | l'intelligenza artificiale che legge e confronta i testi: Claude Haiku (piccolo, economico) o Claude Sonnet (più grande, costa circa 10 volte), su Amazon Bedrock |
| **Copilot in modalità Ask** | Copilot risponde e lancia comandi, ma non modifica file. La modalità si sceglie in basso nella chat di Copilot: deve esserci scritto **Ask**, non *Agent* |

### 0.2 Come si lancia un blocco

1. Apri VS Code sul PC aziendale.
2. Apri il terminale: menu **Terminal → New Terminal**.
3. Controlla che la riga del terminale **finisca con** `app_cycle_validation_v2>`. Se no, scrivi
   `cd` seguito dal percorso della cartella `app_cycle_validation_v2` e premi Invio.
4. In questo file, passa con il mouse sul blocco e premi il pulsante di copia in alto a destra
   del riquadro (oppure seleziona **tutto** il blocco e premi Ctrl+C).
5. Clicca nel terminale e incolla con **Ctrl+V**. Se VS Code chiede conferma per incollare più
   righe, conferma.
6. Premi **Invio** e aspetta che torni la riga con `app_cycle_validation_v2>`.
7. Leggi la parte **Deve uscire** sotto il blocco e confronta con lo schermo.
8. Fai la foto dello schermo e mandala a Claude, come dice **Manda a Claude**.

Quasi tutti i blocchi iniziano con `$env:UV_PYTHON = "3.14"`: dice al programma di usare
Python 3.14, quello installato sul PC. Non toglierla.

### 0.3 Le regole

- **Copilot sempre in modalità Ask.** Può leggere e lanciare le prove; il codice lo cambia solo
  Claude.
- **Non mandare mai foto** di questi file:
  - `runs\mutazioni\errori.yaml`, `data\errori-nascosti.yaml` e le stampe in
    `data\nascosti\`: se li vedesse, Claude conoscerebbe gli errori «mai visti» e la misura non
    varrebbe più;
  - i `report.md` dei cicli, i `prestazioni.md` interi e i file in `transcripts`: contengono
    testo dei manuali.

  Si possono fotografare: le righe del terminale, `runs\campagna.md`, i `riepilogo.md` e le
  tabelle dei report che Claude chiede.
- **Nei messaggi a Claude non scrivere codici veri**: numeri di manuali, numeri DR, serial number,
  part number, codici dei cicli, nomi di bucket o di account. Usa le impronte o descrivi a
  parole. Se compaiono in una foto, Claude non li ripete.
- **Mai `--force`** nei comandi git. Se un push è rifiutato, manda la foto a Claude.
- **Non cambiare i blocchi.** Si cambiano solo i valori che il testo dice (per esempio `$nome` e
  `$insieme` nel blocco della sezione 3.7).

### 0.4 Se qualcosa va storto

| Cosa vedi | Cosa vuol dire | Cosa fare |
|---|---|---|
| `Token has expired`, `ExpiredToken` o `SSO session` | l'accesso ad AWS è scaduto | lancia `aws sso login`, accedi dal browser, poi rilancia il blocco |
| `SELF_SIGNED_CERT_IN_CHAIN` o `unable to get local issuer certificate` | il filtro di rete aziendale (Zscaler) blocca il certificato | lancia la riga qui sotto, poi rilancia il blocco. Vale finché non chiudi il terminale |
| `FERMO: ...` | il blocco si è fermato da solo prima di fare danni: non è cambiato niente | leggi il motivo scritto dopo `FERMO`, correggi (di solito la cartella del terminale) e rilancia; se non è chiaro, foto a Claude |
| `Campagna fermata: ...` | la campagna si è fermata da sola (tetto di spesa, accesso AWS scaduto) | leggi il motivo; per l'accesso: `aws sso login`, poi rilancia la campagna: riparte da dove era |
| `failed` nei test, o una scritta rossa `Errore` | qualcosa non va | **fermati**, non andare al passo dopo, foto a Claude |
| Il blocco non finisce dopo molti minuti | la campagna e le prove sul grande durano a lungo: è normale | lascialo girare. Se è un altro blocco, foto a Claude |

La riga per il certificato:

```powershell
$env:NODE_EXTRA_CA_CERTS = (Resolve-Path ..\app_cycle_validation\zscaler.pem).Path; $env:AWS_CA_BUNDLE = $env:NODE_EXTRA_CA_CERTS
```

---

## 1. Cosa fare adesso (24-11-2026)

### Dove siamo

- La v2 funziona sul PC, con il login e con il frontend.
- **Pronti per le prove** (preparazione fatta il 24-11):
  - **insieme grande: 23 cicli**, i 10 noti e 13 veri; per tipo **MOS 17, DR 6**;
  - **copie cieche: 31** (seme 1): `numero_una_lingua` 5, `numero_manuale` 3,
    `negazione_una_lingua` 18, `task_inesistente` 5;
  - **gruppo nascosto: rinviato** (vedi «In parallelo»). Il file `data\errori-nascosti.yaml`
    per ora è vuoto: non disturba.
- **Prima prova della base valida** (24-11, 15:08, Haiku, piccolo): errori visti **8 su 12**,
  mai visti per il modello **1 su 21**, per il codice **9 su 10**, **0 falsi errori**, 0,17 $.
  Il modello quasi non vede le negazioni tolte in una lingua sola.
- Gli errori visti che mancano hanno bisogno di cose che non ci sono ancora: tre documenti non
  nella conoscenza (vedi «In parallelo») e le risposte alle domande P6, P7 e P8 (sezione 6.1).
- I risultati di ogni prova e i problemi già risolti sono in `MEMORIA.md`.
- **Adesso:** fase 1, la campagna.

### Come si usa questa lista

- Si fa **un passo alla volta, in ordine**. Ogni passo dice quale sezione usare.
- Dopo ogni passo manda a Claude la foto di **Deve uscire**. Claude risponde se va bene e qual è
  il passo dopo. Quando un passo è fatto, Claude lo toglie da qui.
- «Gratis» vuol dire che il passo non usa il modello e non costa niente.

### Fase 1: la campagna (tutto in automatico)

Tutte le prove le lancia **un solo comando**, la **campagna** (sezione 3.5). Fa da sola, in
ordine:

1. con **Haiku**: la base e le 6 migliorie senza codice nuovo, due prove ciascuna, sul
   **piccolo**; poi sul **grande** la base e le migliorie che sul piccolo «si tengono»;
2. con **Sonnet**: le stesse cose, con una base sua (così si vede se il limite è il modello);
3. alla fine scrive **un report unico**, `runs\campagna.md`.

Le prove già fatte non si rifanno: se la campagna si ferma, la rilanci e riparte da dove era.
L'elenco degli esperimenti sta in `eval/campagna.yaml` e lo aggiorna Claude: tu non cambi
niente.

- [ ] **1. Aggiornare** (2.1).
- [ ] **2. Il piano** (3.5, primo blocco, gratis): dice cosa farà, senza lanciare niente. Foto.
- [ ] **3. La campagna** (3.5, secondo blocco). Dura **alcune ore** (stima: Haiku 1,5-2 ore,
  Sonnet di più) e costa al massimo 60 $ (stima: Haiku circa 5 $, Sonnet circa 10 volte).
  Lascia il PC acceso, con VS Code aperto e senza sospensione. Se si ferma, rilancia lo stesso
  blocco.
- [ ] **4. Il report finale** `runs\campagna.md` (si apre da solo; **Ctrl+Shift+V** per vederlo
  impaginato). Manda a Claude la foto di ogni sezione: le tabelle per modello e insieme, «I
  modelli a confronto» ed «Errori mai visti per tipo». Ci sono solo numeri: si può
  fotografare.

Per lanciare solo una parte (un modello, un insieme, una variante): sezione 3.5, «Solo una
parte».

### Fase 2: migliorie scelte sugli errori mai visti (il codice lo scrive Claude)

Le migliorie non si scelgono guardando gli errori noti che mancano: sarebbe come imparare a
memoria le risposte di un compito. Si scelgono sui **tipi** di errori mai visti che la v2 trova
peggio (tabella «Errori mai visti per tipo» del report della campagna).

- [ ] **5.** Claude propone una miglioria per il tipo «modello» trovato peggio (la prima pronta
  sarà `numeri_manuale`), la scrive e la aggiunge a `eval/campagna.yaml`.
- [ ] **6. Aggiornare** (2.1), poi **la campagna** (3.5): fa solo le prove nuove.
- [ ] **7.** Foto del report finale, come al passo 4. Si ripete dal passo 5 finché i tipi
  «modello» non migliorano più.

**Quando una miglioria entra nella base** (Claude te lo dice):

1. archivia le prove fatte (3.8);
2. rifai la scelta dei cicli veri (3.2) e le copie cieche (3.3) con un **seme nuovo**:
   `$seme = 2`, la volta dopo 3, e così via. Il seme nuovo crea errori nuovi, così restano
   davvero «mai visti»;
3. rilancia la campagna (3.5).

### Fase 3: tempo e costo

Qui si cerca di spendere meno o fare prima, **trovando gli stessi errori**. Il codice lo scrive
Claude e lo aggiunge alla campagna; tu fai i passi 6 e 7.

- [ ] **8. B1**: chiamata diretta a Bedrock (toglie circa 4 secondi di avvio per operazione).
- [ ] **9. Cache dei prompt** (H10): nel report di una prova (3.6) guarda la riga «Token di
  input riletti dalla cache» e mandala a Claude.
- [ ] **10. B4**: più operazioni controllate insieme.

### Fase 4: chiusura prima della QA

- [ ] **11. Prova finale**: la campagna con la base finale, poi il report: foto.
- [ ] **12. Prove dal frontend** (sezione 4): almeno un ciclo MOS e un DR.
- [ ] **13. Salvare** (2.2).

### Fase 5: QA (sezione 7)

- [ ] **14. Pull request** da `feature/cycle-validation-v2` verso `develop`.
- [ ] **15. Prova in QA** dal frontend con un ciclo MOS e un DR: foto dell'intestazione dei
  risultati.
- [ ] **16.** Se la v2 in QA non parte: blocco «torna alla v1» (sezione 7), poi Salvare e pull
  request.
- [ ] **17. Cicli militari**, solo dopo una prova QA riuscita.

**Attenzione:** quando il ramo arriva su `main`, anche la **produzione** passa alla v2. Prima
serve una prova QA riuscita.

### In parallelo, quando puoi

- Le **domande** alle persone (sezione 6.1): P6, P7, P8.
- Il **messaggio** al collega del frontend (sezione 6.2), se non l'hai già mandato.
- Il **gruppo nascosto** (sezione 3.4), rinviato il 24-11.
- I **file che mancano**: il capitolo 70-23 dell'SPM, il manuale d'ispezione del motore, due
  REPAIR della sezione 72-56-31. Cercali dove prendi i manuali; se li trovi, fai l'ingestion e
  poi la sezione 5.

---

## 2. Aggiornare e salvare

### 2.1 Aggiornare il codice sul PC

- **A cosa serve:** porta sul PC l'ultima versione del codice scritto da Claude e controlla che
  funzioni (lancia i test).
- **Quando:** ogni volta che Claude dice di aver cambiato qualcosa.
- **Costa:** niente.
- **Cosa fa, passo per passo:**
  1. scarica il repository personale in una cartella temporanea;
  2. controlla che il terminale sia nella cartella `app_cycle_validation_v2`; se no scrive
     `FERMO` e non tocca niente;
  3. toglie dal PC i file di codice che nel repository personale non ci sono più (scrive
     `tolto: ...` per ognuno);
  4. copia il codice (`src`, `tests`, `prompts`, `examples`, `config`, le cartelle di `eval/`, la
     lista degli errori noti, l'elenco della campagna, i documenti di `docs/`);
  5. cancella la cartella temporanea e lancia i test.
- **Non tocca:** i dati aziendali (`data/`, `runs/`, `eval/casi/aziendali/`), il `Dockerfile`,
  `vendor/` e `config/settings.azienda.yaml`.

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

**Deve uscire:** forse qualche riga `tolto: ...`; poi una lunga fila di puntini e, in fondo, una
riga con il numero di test `passed` (qualche `skipped` va bene) e **nessun** `failed`. Se esce
`FERMO`, non è cambiato niente: controlla la cartella del terminale (0.2, punto 3) e rilancia.

**Manda a Claude:** la foto dell'ultima riga dei test (e delle righe `tolto:`, se ci sono). Se
c'è un `failed`, la foto dell'elenco `FAILED` in fondo.

### 2.2 Salvare nel repository aziendale

- **A cosa serve:** salva il codice della v2 nel repository aziendale, sul ramo
  `feature/cycle-validation-v2`. I rami `develop` (QA) e `main` (produzione) **non cambiano**
  finché non apri tu la pull request.
- **Quando:** dopo ogni *Aggiornare* andato bene.
- **Costa:** niente.
- I dati aziendali restano fuori: git li ignora.

Si fa in **due blocchi**: prima il commit (salva sul PC), poi il push (manda al server).

**Primo blocco: commit**

```powershell
git add src tests docs examples eval/errori-noti.yaml eval/campagna.yaml eval/casi/sintetici eval/varianti eval/modelli config prompts pyproject.toml uv.lock README.md .gitignore Dockerfile ../buildspec.yml
if (Test-Path vendor) { git add vendor }
git status --short
git commit -m "v2: fonti per riparazione, subtask, task SPM, controllo delle due lingue, prove con metriche, cicli veri, errori ciechi e gruppo nascosto"
```

**Deve uscire:** l'elenco di `git status`, con righe solo sotto le cartelle del `git add`
(`M` = cambiato, `A` = nuovo, `D` = tolto) e **niente** sotto `data/` o `runs/`; poi il riepilogo
del commit. Se dice `nothing to commit`, non c'era niente di nuovo: va bene, lancia lo stesso il
secondo blocco.

**Secondo blocco: push.** Controlla da solo di essere sul ramo giusto e che nel commit ci siano
solo i file previsti; se no scrive `FERMO` e non manda niente.

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

**Deve uscire:** la riga del push, l'ultimo commit e
`## feature/cycle-validation-v2...origin/feature/cycle-validation-v2` **senza** `[ahead ...]`.

**Se esce `FERMO` o il push è rifiutato:** non insistere e non usare `--force`: manda la foto a
Claude.

**Manda a Claude:** la foto dell'ultima parte (push e riga `## feature/...`).

---

## 3. Le prove

### 3.1 Come funzionano

#### Cos'è una prova

Una **prova** fa girare la v2 su un gruppo di cicli (un **insieme**) e conta:

- quanti errori trova tra quelli messi apposta;
- quanti falsi errori dà sulle stampe giuste;
- quanto costa e quanto tempo ci mette.

Ogni prova ha un **nome**. Due o più prove con lo stesso nome formano una **variante**. Servono
almeno due prove per variante, perché il modello non risponde sempre uguale. Di solito le prove
le lancia la **campagna** (3.5); una prova a mano serve solo per casi particolari (3.7).

#### Gli errori da trovare

| Specie | Cosa sono | A cosa servono |
|---|---|---|
| **Visti** | i 12 errori noti di `eval/errori-noti.yaml`. Claude li conosce | dicono se la v2 trova gli errori che conosciamo. Rischio: una miglioria può «impararli a memoria» |
| **Mai visti: copie cieche** (3.3) | copie di cicli veri in cui il programma cambia una sola operazione. Nessuno guarda quale | dicono se la v2 trova anche errori nuovi (**generalizza**) |
| **Mai visti: gruppo nascosto** (3.4, facoltativo) | stampe con errori messi da te o da un collega. Claude non le vede mai | come le copie cieche, ma con errori pensati da una persona: è la misura migliore |

I tipi di copie cieche sono quattro:

| Tipo | Cosa cambia il programma | Chi lo deve trovare |
|---|---|---|
| `numero_una_lingua` | un numero, solo nel testo italiano o solo in quello inglese | il **codice**: serve solo a vedere che non si è rotto niente |
| `numero_manuale` | un numero che c'è nelle due lingue e nel manuale, cambiato in tutte e due con un valore che il manuale non ha | il **modello**: conta per la generalizzazione |
| `negazione_una_lingua` | un «non» (o «not») tolto in una lingua sola | il **modello**: conta per la generalizzazione |
| `task_inesistente` | il codice di un task cambiato in uno che non esiste | il **codice**: serve solo a vedere che non si è rotto niente |

I report degli errori mai visti danno **solo quanti sono per tipo**, mai quali. Per questo non
si mandano foto di `runs\mutazioni\errori.yaml` e `data\errori-nascosti.yaml`.

#### I due insiemi

| Insieme | Quali cicli | Quando si usa |
|---|---|---|
| **piccolo** | i 10 cicli noti (7 «con errori» e 3 giusti), le copie cieche (3.3) e il gruppo nascosto (3.4), se c'è | **ogni** miglioria. È veloce: qualche minuto a prova |
| **grande** | i 10 noti e **tutti** i cicli veri civili confrontabili con la conoscenza (3.2) | solo le migliorie che **si tengono** sul piccolo: si controlla che sui cicli veri non escano ERRATO o WARNING in più |

Un ciclo vero non ha errori noti: se la v2 dà un ERRATO, è «da verificare» (quasi sempre un
falso errore), e i suoi WARNING sono lavoro a mano in più. Le prove si confrontano **solo dentro
lo stesso insieme** e con le stesse copie cieche: il riepilogo avvisa se non è così.

#### Dove finiscono i risultati

| Cosa | Dove |
|---|---|
| Le prove con Haiku | `runs\prove-piccolo\` e `runs\prove-grande\` |
| Le prove con Sonnet | `runs\prove-piccolo-sonnet\` e `runs\prove-grande-sonnet\` |
| Il report di una prova | `<cartella>\<data>-<nome>\prestazioni.md`: in cima la proposta della variante (cosa cambia, perché, cosa ci si aspetta), poi i risultati |
| Il riepilogo di una cartella | `<cartella>\riepilogo.md`: scelta migliore, classifica, «Le proposte e la decisione», tutte le prove, errore per errore, falsi errori |
| Il report della campagna | `runs\campagna.md`: tutto insieme, per modello e insieme, più Haiku e Sonnet a confronto |

Le **considerazioni** (cosa si è capito) le scrive Claude in `MIGLIORIE.md`, dalle tue foto.

#### Come si sceglie

Lo fa da solo il riepilogo, nella sezione «Scelta migliore». Le regole:

| Misura | Cosa misura | Regola |
|---|---|---|
| Falsi errori | ERRATO nelle 3 stampe giuste | deve essere **0**, altrimenti la variante è scartata (non contano le operazioni «in attesa» di una risposta delle persone) |
| Cicli non eseguiti | cicli andati in errore | deve essere 0 |
| Tempo del ciclo più lento | il frontend aspetta al massimo 11 minuti | sotto **10 minuti** |
| Costo per ciclo | dollari per ciclo | non più del **doppio** della base dello stesso modello |
| **Stabili** | errori (visti e mai visti) trovati in **tutte** le prove della variante | 1° criterio: più alto è meglio; mai meno della base |
| **Mai visti stabili** | errori mai visti per il modello (copie «numero del manuale» e «negazione», gruppo nascosto) trovati in tutte le prove | mai meno della base: se scende, la miglioria **non generalizza** |
| Trovati (minimo, media) | errori trovati in ogni prova | 2° e 3° criterio |
| Da verificare | ERRATO fuori dalla lista (cicli con errori e cicli veri) | 4°: meno è meglio |
| Warning per ciclo senza errori | lavoro a mano lasciato su una stampa giusta o vera | 5°: meno è meglio |
| Costo, tempo | per ciclo | 6° e 7°: meno è meglio |
| Precisione | trovati diviso tutti gli ERRATO | solo da guardare |

Il report di ogni prova mette accanto **visti** e **mai visti per il modello**. Se i visti sono
trovati molto più spesso dei mai visti, la v2 ha «imparato la lista». La tabella «Errori mai
visti, per tipo» dice quali tipi la v2 trova peggio e cosa ha risposto sui mancati (solo esito e
motivo contati): le migliorie si scelgono su quelli.

### 3.2 Scegliere i cicli veri

- **A cosa serve:** sceglie i cicli dell'insieme grande: i 10 cicli noti e **tutti** i cicli
  veri civili che hanno almeno l'80% delle operazioni confrontabili con la conoscenza. Sono
  sempre gli stessi. Accanto a ogni ciclo scrive se è MOS o DR.
- **Quando:** una volta (fatto il 24-11), e di nuovo dopo una nuova ingestion (sezione 5) o
  quando una miglioria entra nella base.
- **Costa:** niente (legge le stampe con il parser, senza modello).
- I percorsi dei file restano nel file `runs\prove-grande\cicli.txt` sul PC; sullo schermo
  escono solo le impronte.

```powershell
$env:UV_PYTHON = "3.14"
[Console]::OutputEncoding = [Text.Encoding]::UTF8; $env:PYTHONIOENCODING = "utf-8"
$foto = (Get-ChildItem eval/casi/aziendali/conoscenza -Directory -Filter "foto-*" | Sort-Object Name | Select-Object -Last 1).FullName
$kb = "$foto/Manufacturing AI/ingestion-v2-test-qa-output/knowledge/civil/"; $v = $kb + (Get-Content ($kb + "current.json") | ConvertFrom-Json).path
uv run cycle-validation eval scegli (Resolve-Path "..\..").Path --knowledge $v --quanti 0 --out runs/prove-grande/cicli.txt
```

**Deve uscire:** `Stampe: ... Scelti N: noti 10, veri M. Per tipo: MOS ..., DR ....`, poi una
riga per ogni ciclo vero (`<impronta> vero (MOS): ...` oppure `vero (DR)`) e quanti sono
rimasti fuori e perché. Una prova sul grande dura circa N volte un ciclo: se N è più di 100,
manda la foto a Claude e si mette un limite (`--quanti 100`).

**Manda a Claude:** la foto dello schermo.

### 3.3 Fare le copie cieche

- **A cosa serve:** dai cicli veri scelti in 3.2 (e dalle 3 stampe giuste) fa le copie con un
  errore ciascuna: al massimo 6 da uno stesso ciclo, e al massimo 5 per ognuno dei due tipi del
  «codice».
- **Quando:** dopo 3.2 (fatto il 24-11), poi solo quando una miglioria entra nella base, con un
  **seme nuovo**: cambia `$seme = 1` in `2`, poi `3`, e così via.
- **Costa:** niente.

```powershell
$env:UV_PYTHON = "3.14"
[Console]::OutputEncoding = [Text.Encoding]::UTF8; $env:PYTHONIOENCODING = "utf-8"
$seme = 1
$foto = (Get-ChildItem eval/casi/aziendali/conoscenza -Directory -Filter "foto-*" | Sort-Object Name | Select-Object -Last 1).FullName
$kb = "$foto/Manufacturing AI/ingestion-v2-test-qa-output/knowledge/civil/"; $v = $kb + (Get-Content ($kb + "current.json") | ConvertFrom-Json).path
Remove-Item runs/mutazioni -Recurse -ErrorAction SilentlyContinue
uv run cycle-validation eval muta --lista runs/prove-grande/cicli.txt --knowledge $v --quanti 100 --seme $seme --out runs/mutazioni
```

**Deve uscire:** `Cicli veri letti: ... Copie con un errore cieco: N su 100 chieste, seme 1.` e
quante copie ci sono per tipo (`numero_una_lingua`, `numero_manuale`, `negazione_una_lingua`,
`task_inesistente`). N può essere meno di 100: dipende da quante operazioni adatte ci sono nei
cicli (il 24-11: 31).

**Non aprire** `runs\mutazioni\errori.yaml`. **Manda a Claude:** la foto dello schermo (solo i
conteggi).

### 3.4 Il gruppo nascosto (facoltativo)

È la misura migliore, perché gli errori li pensa una persona. Rinviato il 24-11: si fa quando
c'è tempo.

1. Apri la lista dei cicli scelti con `code runs/prove-grande/cicli.txt` (senza fotografarla):
   dopo le prime 10 righe (i cicli noti) ci sono i percorsi dei cicli veri.
2. Copia una decina di quelle stampe (PDF) in `data\nascosti\` (Copilot e Claude non leggono
   quella cartella).
3. In ogni copia cambia a mano uno o due punti della descrizione, come nei 7 cicli «con
   errori». I più utili:
   - **un numero cambiato in tutte e due le lingue** (italiano e inglese uguali tra loro,
     diversi dal manuale): le copie cieche di quel tipo sono solo 3;
   - parole o frasi cambiate in tutte e due le lingue.

   Se puoi, fallo fare a un collega: penserà errori diversi da quelli che conosci.
4. Lancia il blocco qui sotto: prepara il file `data\errori-nascosti.yaml` e lo apre.
5. Per ogni stampa scrivi le operazioni cambiate, una riga per operazione, per esempio
   `'030': quantità cambiata in tutte e due le lingue`. Poi salva.
6. Scrivi a Claude solo «gruppo nascosto pronto, N stampe». Da qui la campagna e la prova a
   mano lo aggiungono da sole al piccolo: si rifà la base.

```powershell
New-Item -ItemType Directory -Force data/nascosti | Out-Null
$righe = Get-ChildItem data/nascosti -Filter *.pdf | ForEach-Object { "  '" + (Get-FileHash $_.FullName).Hash.Substring(0, 8).ToLower() + "':  # " + $_.Name + "`n    visto: false`n    errori:`n      '010': cosa hai cambiato (il numero dell'operazione è un esempio)" }
"cicli:`n" + ($righe -join "`n") | Set-Content data/errori-nascosti.yaml -Encoding utf8; code data/errori-nascosti.yaml
```

**Non mandare a Claude foto di questo file né delle stampe.**

### 3.5 La campagna: tutte le prove in automatico

- **A cosa serve:** lancia da sola tutte le prove di `eval/campagna.yaml`: per ogni modello
  (Haiku, poi Sonnet) la base e le varianti sul piccolo, poi sul grande la base e le varianti
  che si tengono. Alla fine scrive `runs\campagna.md`, il report unico da leggere.
- **Da sola:** trova l'ultima fotografia della conoscenza, i cicli scelti (3.2), le copie cieche
  (3.3) e il gruppo nascosto (3.4), se ci sono; sceglie MOS o DR per ogni ciclo.
- **Riprende da dove era:** le prove già fatte (anche quelle lanciate a mano) si contano e non
  si rifanno.
- **Si ferma da sola:** al tetto di spesa (`massimo_dollari`, oggi 60 $), se una prova non
  riesce a eseguire nessun ciclo (accesso AWS scaduto: `aws sso login`, poi rilancia) o se
  premi Ctrl+C. In ogni caso scrive il report con quello che c'è.

**Primo blocco: il piano** (gratis, non lancia niente):

```powershell
$env:UV_PYTHON = "3.14"
[Console]::OutputEncoding = [Text.Encoding]::UTF8; $env:PYTHONIOENCODING = "utf-8"
uv run cycle-validation eval campagna --piano
```

**Deve uscire:** `Piano (gratis, niente viene lanciato). Piccolo: N cicli e copie; grande: 23
cicli.` e per ogni modello e insieme una riga per variante: `base: 1 da fare → runs/...` (una
base Haiku sul piccolo c'è già), `effort_medio: 2 da fare → ...`, e così via.

**Secondo blocco: la campagna** (costa: vedi sezione 1, fase 1, passo 3; dura ore):

```powershell
$env:UV_PYTHON = "3.14"
[Console]::OutputEncoding = [Text.Encoding]::UTF8; $env:PYTHONIOENCODING = "utf-8"
uv run cycle-validation eval campagna
code runs/campagna.md
```

**Deve uscire:** per ogni prova una riga `=== haiku · piccolo · effort_medio · prova 1 di 2 ·
spesa finora ... $`, le righe dei cicli e la riga finale della prova; alla fine
`Campagna finita. Prove fatte ora: N · spesa ... $.` (oppure `Campagna fermata: ...` con il
motivo) e `Report finale: runs\campagna.md`, che si apre da solo.

**Manda a Claude:** la foto della riga `Campagna finita` (o `fermata`) e del report (sezione 1,
fase 1, passo 4).

**Solo una parte.** Stesso secondo blocco, con in fondo alla riga `uv run cycle-validation eval
campagna` una o più di queste aggiunte:

| Aggiunta | Cosa fa |
|---|---|
| `--modelli haiku` | solo Haiku (oppure `--modelli sonnet`) |
| `--insiemi piccolo` | solo il piccolo (oppure `--insiemi grande`) |
| `--varianti effort_medio,conferme_1` | solo queste varianti (la base si fa sempre per prima) |
| `--ripetizioni 3` | tre prove per variante invece di due |
| `--grande sempre` | sul grande tutte le varianti, non solo quelle che si tengono (`mai` = niente grande) |
| `--massimo-dollari 10` | tetto di spesa diverso per questa volta |
| `--piano` | mostra solo cosa farebbe |

Esempio: `uv run cycle-validation eval campagna --modelli sonnet --insiemi piccolo`.

### 3.6 Leggere i risultati

Tutti gratis. I file si aprono in VS Code: per vederli impaginati premi **Ctrl+Shift+V** nella
finestra del file.

**Il report della campagna** (il più importante): `code runs/campagna.md`.

**Il riepilogo di una cartella** (classifica e scelta migliore per un modello e un insieme):

```powershell
code runs/prove-piccolo/riepilogo.md
```

Per le altre cartelle cambia il nome: `runs/prove-grande/riepilogo.md`,
`runs/prove-piccolo-sonnet/riepilogo.md`, `runs/prove-grande-sonnet/riepilogo.md`.

**Manda a Claude:** la foto di «Scelta migliore», «Classifica delle varianti» e «Le proposte e
la decisione».

**Il report dell'ultima prova** di una cartella (cambia `$insieme` se serve; per Sonnet scrivi
`"piccolo-sonnet"` o `"grande-sonnet"`):

```powershell
$insieme = "piccolo"; $ultima = Get-ChildItem "runs/prove-$insieme" -Directory | Where-Object Name -match "^\d{8}-" | Sort-Object Name | Select-Object -Last 1; code "$($ultima.FullName)/prestazioni.md"
```

Manda a Claude solo le tabelle che chiede (per esempio «Errori mai visti, per tipo»), non il
file intero: contiene testo dei manuali.

**L'elenco delle prove fatte:**

```powershell
Get-ChildItem runs/prove-piccolo, runs/prove-grande -Directory -ErrorAction SilentlyContinue | Select-Object Name
```

### 3.7 Una prova a mano

- **A cosa serve:** lancia **una** prova, con Haiku, su un insieme. Di solito non serve: lo fa
  la campagna. Serve per ripetere una prova sola o provare qualcosa che Claude chiede.
- **Cosa cambiare:** solo le due cose nella terza riga del blocco:
  - `$nome`: `"base"` oppure il nome di una variante (per esempio `"effort_medio"`);
  - `$insieme`: `"piccolo"` oppure `"grande"`.
- **Costa:** il piccolo come una quindicina di cicli (circa 0,17 $ con Haiku); il grande come
  tutti i cicli scelti.
- La prova finisce nella cartella di Haiku dell'insieme e conta anche per la campagna.

```powershell
$env:UV_PYTHON = "3.14"
[Console]::OutputEncoding = [Text.Encoding]::UTF8; $env:PYTHONIOENCODING = "utf-8"
$nome = "base"; $insieme = "piccolo"
$foto = (Get-ChildItem eval/casi/aziendali/conoscenza -Directory -Filter "foto-*" | Sort-Object Name | Select-Object -Last 1).FullName
$kb = "$foto/Manufacturing AI/ingestion-v2-test-qa-output/knowledge/civil/"; $v = $kb + (Get-Content ($kb + "current.json") | ConvertFrom-Json).path
$variante = if (Test-Path "eval/varianti/$nome.yaml") { @("--variante", "eval/varianti/$nome.yaml") } else { @() }
$dieci = Get-ChildItem (Resolve-Path "..\..").Path -Recurse -Filter "*.pdf" -ErrorAction SilentlyContinue | Where-Object { $_.Name -like "*errori*" -or (Get-FileHash $_.FullName).Hash.Substring(0, 8).ToLower() -in @("4e64d49a", "8bdb25d5", "04ecaabe") } | Group-Object { (Get-FileHash $_.FullName).Hash } | ForEach-Object { $_.Group[0] }
$cicli = @("--attesi", "eval/errori-noti.yaml")
if ($insieme -eq "grande") { $cicli += @("--lista", "runs/prove-grande/cicli.txt") } else { $cicli += @($dieci.FullName); if (Test-Path runs/mutazioni/lista.txt) { $cicli += @("--lista", "runs/mutazioni/lista.txt", "--attesi", "runs/mutazioni/errori.yaml") }; if (Test-Path data/errori-nascosti.yaml) { $cicli += @("data/nascosti", "--attesi", "data/errori-nascosti.yaml") } }
"prova «$nome» sull'insieme $insieme" + $(if ($variante) { " con la variante" } else { "" })
uv run cycle-validation eval prova @cicli --nome $nome --knowledge $v --config data/settings.yaml @variante --cartella "runs/prove-$insieme"
```

**Deve uscire:**

- prima `prova «<nome>» sull'insieme <insieme>` (con `con la variante`, se c'è il file);
- una riga per ciclo: `<impronta> errori|giusto|vero (MOS|DR): trovati ... · mancati ... ·
  ERRATO in più ...` (e `· in attesa ...` se un ERRATO aspetta una risposta delle persone);
  per le copie cieche solo `<impronta> mai visto: trovato` oppure `mancato`;
- alla fine `Prova «...»: errori noti trovati N su M (visti ..., mai visti per il modello ...,
  per il codice ...) · falsi errori ... · costo ...` e i percorsi dei due report.

**Manda a Claude:** la foto della riga finale.

### 3.8 Mettere ordine: togliere, azzerare, archiviare le prove

**Togliere una prova** (per esempio una lanciata per sbaglio): cancella la sua cartella dentro
`runs\prove-...`, poi rifai il riepilogo di quella cartella (gratis; cambia il nome della
cartella se serve):

```powershell
$env:UV_PYTHON = "3.14"; uv run cycle-validation eval riepilogo --cartella runs/prove-piccolo
```

**Azzerare tutte le prove** (gratis): cancella **per sempre** le cartelle delle prove
(`runs\prove-piccolo`, `runs\prove-grande`, `runs\prove-piccolo-sonnet`,
`runs\prove-grande-sonnet`, con tutto quello che c'è dentro) e il report della campagna, per
ripartire da zero. Tiene da parte la lista dei cicli scelti (`runs\prove-grande\cicli.txt`) e
la rimette al suo posto, così non serve rifare 3.2. **Non** tocca le copie cieche
(`runs\mutazioni`), il gruppo nascosto (`data\`), gli archivi e le altre cartelle di `runs`.
Se vuoi tenere le prove da rileggere, usa invece «Archiviare» qui sotto.

```powershell
$ok = (Split-Path -Leaf (Get-Location).ProviderPath) -eq "app_cycle_validation_v2"; if (-not $ok) { "FERMO: terminale non nella cartella app_cycle_validation_v2. Niente cancellato." }
if ($ok) { $lista = "runs/prove-grande/cicli.txt"; $copia = Join-Path $env:TEMP "cv2-cicli.txt"; $tieni = Test-Path $lista; if ($tieni) { Copy-Item $lista $copia -Force }; $via = @(Get-ChildItem runs -Directory -Filter "prove-*" -ErrorAction SilentlyContinue); $via | ForEach-Object { "tolta: runs\" + $_.Name }; $via | Remove-Item -Recurse -Force; Remove-Item runs/campagna.md -ErrorAction SilentlyContinue; if ($tieni) { New-Item -ItemType Directory -Force runs/prove-grande | Out-Null; Move-Item $copia $lista -Force; "resta: runs\prove-grande\cicli.txt (la lista dei cicli scelti)" } else { "lista dei cicli scelti assente: rifai 3.2" } }
```

**Deve uscire:** una riga `tolta: runs\prove-...` per ogni cartella (fino a quattro), poi
`resta: runs\prove-grande\cicli.txt (la lista dei cicli scelti)`. Dopo, la campagna (3.5) rifà
tutto da capo: lancia prima il piano, che deve dire `base: 2 da fare` dappertutto.

**Archiviare tutte le prove** (gratis): quando cambiano le copie cieche o la conoscenza, le
prove di prima non si possono più confrontare con le nuove. Questo blocco le sposta in
`runs\archivio-<data>-...` (restano da leggere). Dopo: rifai 3.2, 3.3 e la campagna.

```powershell
$d = Get-Date -Format "yyyyMMdd-HHmm"; "piccolo", "grande" | ForEach-Object { if (Test-Path "runs/prove-$_") { Move-Item "runs/prove-$_" "runs/archivio-$d-$_" } }
```

Il blocco sposta `runs\prove-piccolo` e `runs\prove-grande`. Per le cartelle di Sonnet, sposta a
mano `runs\prove-piccolo-sonnet` e `runs\prove-grande-sonnet` nella stessa cartella di archivio.

---

## 4. Prove dal frontend

- **A cosa serve:** provare la v2 come la userà un utente, dalla pagina web.
- **Come si avvia:** in VS Code, **Run and Debug** → scegli **«CV v2»** → avvia. Poi apri nel
  browser `http://localhost:3000`.
- **Costa:** qualche centesimo per ciclo.
- Le targhe escono sempre WARNING: dal PC Redshift (il database delle macchine) non si
  raggiunge. È normale.

Le prove, in ordine:

1. **I tre cicli «con errori»** (MOS): gli ERRATO devono essere quelli del report della prova
   (3.6).
2. **Il ciclo MOS più lungo:** misura il tempo fino al risultato. Deve stare sotto i 10 minuti
   (il frontend aspetta al massimo 11).
3. **Un DR con serial number e condition**, poi lo stesso **senza** (se il pulsante Confirm non
   si accende, salta).
4. **File sbagliato:** carica un DR scegliendo MOS. Deve uscire «Modulo sbagliato».
5. **Storico:** riapri una chat di prima, rinominala, cancellala.
6. **Download** del CSV dei risultati.

**Manda a Claude:** la foto dell'intestazione dei risultati di ogni prova e il tempo della prova
2 scritto a parole. Se qualcosa non va: la foto del frontend e quella del log di CV v2.

---

## 5. Dopo una nuova ingestion

- **Quando:** dopo aver caricato manuali nuovi nella conoscenza (per esempio i file che
  mancano).
- **In ordine:**
  1. blocco A qui sotto: **fotografia** della conoscenza (va su AWS);
  2. blocco B qui sotto: **lista dei manuali** (gratis);
  3. archivia le prove fatte (3.8);
  4. rifai la scelta dei cicli veri (3.2) e le copie cieche (3.3);
  5. rilancia la campagna (3.5): le prove di prima erano con un'altra conoscenza.

**A. Fotografia della conoscenza.** Scarica dal bucket la conoscenza civile di prova pubblicata e
la controlla (`kb-check`). Le prove e la lista dei manuali usano da sole l'ultima fotografia.

```powershell
$env:UV_PYTHON = "3.14"
$foto = "eval/casi/aziendali/conoscenza/foto-" + (Get-Date -Format "yyyyMMdd-HHmm")
uv run cycle-validation eval fotografia --bucket (Get-Content data/bucket.txt) --prefisso "Manufacturing AI/ingestion-v2-test-qa-output/knowledge/civil/" --out $foto --regione eu-south-1
$kb = "$foto/Manufacturing AI/ingestion-v2-test-qa-output/knowledge/civil/"; "versione pubblicata: " + (Get-Content ($kb + "current.json") | ConvertFrom-Json).path; uv run cycle-validation kb-check ($kb + (Get-Content ($kb + "current.json") | ConvertFrom-Json).path)
```

**Deve uscire:** `Fotografia in ...`, una `versione pubblicata` **diversa** da
`v/20261123T142517Z/` e i conteggi di `kb-check` senza righe `Errore:`.

**B. La lista dei manuali.** Gratis: non usa il modello e non va su AWS. Legge tutte le stampe
dei cicli e cerca ogni task citato come lo cerca la v2. Per ogni manuale dice `c'è`, `manca`
oppure `c'è, ma mancano N task`, e per i task che mancano dice perché. Sullo schermo i manuali
si chiamano M1, M2, ...; i codici veri restano nel file `runs\manuali-da-ingestionare.txt`.

```powershell
$env:UV_PYTHON = "3.14"
[Console]::OutputEncoding = [Text.Encoding]::UTF8; $env:PYTHONIOENCODING = "utf-8"
$foto = (Get-ChildItem eval/casi/aziendali/conoscenza -Directory -Filter "foto-*" | Sort-Object Name | Select-Object -Last 1).FullName
$kb = "$foto/Manufacturing AI/ingestion-v2-test-qa-output/knowledge/civil/"; $v = $kb + (Get-Content ($kb + "current.json") | ConvertFrom-Json).path; "conoscenza: " + (Split-Path -Leaf $foto) + " · " + (Get-Content ($kb + "current.json") | ConvertFrom-Json).path
uv run cycle-validation manuali (Resolve-Path "..\..").Path --conoscenza $v --errori 298bc28e=005,035 --errori c5ff3cd6=040 --errori f355dc3c=010,030,040,050
```

**Deve uscire:** una riga per manuale (`M1: ...`). Il 23-11 alle 17:20 M1 aveva 3 task mancanti
e M2 (SPM) 1. Con i file nuovi devono scendere.

**Manda a Claude:** la foto dello schermo (non quella del file).

---

## 6. Le persone

### 6.1 Domande

Sono domande per chi conosce i cicli e i manuali. Copilot non può rispondere. Chiedile quando
capita e scrivi a Claude la risposta **a parole**, senza codici veri.

| Id | Domanda | Perché serve |
|---|---|---|
| **P1** | Task che iniziano con «70-»: stanno sempre nel manuale SPM? C'è un altro gruppo di task con la stessa regola? | la v2 cerca questi task nell'SPM |
| **P2** | Operazione 060 del ciclo DR (condition 3): la v2 l'ha segnata sbagliata. Lo era davvero? Il dettaglio è in `runs\dr-condition-3\report.md`, da far guardare a chi conosce il ciclo (non mandarlo a Claude) | capire se l'ERRATO è giusto |
| **P4** | Targa «90» (per chi cura l'indice): funzione sbagliata e lettere accentate rovinate. I passi sono in `MEMORIA.md`, sezione «Da correggere nell'indice» | l'indice ha un dato rotto |
| **P6** | Scheda mancante: quando un'operazione deve avere per forza una scheda? | senza una regola la v2 (come la v1) non può sapere che manca |
| **P7** | Ispezione FPI, indicazione lineare (ciclo f355dc3c e la sua stampa giusta, op. 050): il ciclo dice «lunga almeno **4** volte la larghezza», l'SPM «**3** volte o più». Il ciclo segue un'altra regola (manuale del motore) o è da correggere? | oggi la v2 lo segna ERRATO anche sulla stampa giusta: finché non c'è risposta, quell'operazione è «in attesa» e non conta nelle prove |
| **P8** | Riparazione senza task in testata (c5ff3cd6, nota «applicazione lubrificante secco»; 298bc28e): quale task del manuale vale per le operazioni che non ne citano uno? | la v2 non sa con cosa confrontarle |

### 6.2 Messaggio per il collega del frontend

Da mandare se non l'hai già fatto. Copialo così com'è:

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

## 7. QA (più avanti)

**Cos'è:** QA è l'ambiente di prova dell'azienda, uguale alla produzione ma usato solo per
provare. Corrisponde al ramo `develop`.

- Il Dockerfile e il buildspec (i file che costruiscono il servizio) per la v2 sono già sul ramo
  feature.
- Finché il ramo non arriva su `develop`, QA resta sulla v1.
- **Attenzione:** quando il ramo arriverà su `main`, anche la **produzione** passerà alla v2:
  prima serve una prova QA riuscita.

**Passi:**

1. **Pull request** da `feature/cycle-validation-v2` verso `develop` (su GitHub). Quando è unita,
   dal frontend QA prova un ciclo MOS e un DR (in QA le targhe si controllano davvero). Manda a
   Claude la foto dell'intestazione dei risultati.
2. **Se la v2 in QA non parte:** torna alla v1 con il blocco qui sotto, poi Salvare (2.2) e pull
   request.

```powershell
$env:UV_PYTHON = "3.14"
uv run cycle-validation qa --torna-alla-v1
```

3. **Cicli militari** (solo dopo una prova QA riuscita): lancia il blocco qui sotto, poi Salvare
   (2.2) e pull request.

```powershell
$env:UV_PYTHON = "3.14"
uv run cycle-validation qa --conoscenza-civile "Manufacturing AI/ingestion-v2-test-qa-output/knowledge/civil/current.json" --ej200 --conoscenza-ej200 "Manufacturing AI/ingestion-v2-test-qa-output/knowledge/ej200/current.json"
```

Se Claude dice che il comando `qa` è cambiato, rilancia lo stesso comando (senza `--ej200`
finché i cicli militari sono spenti), poi Salvare.
