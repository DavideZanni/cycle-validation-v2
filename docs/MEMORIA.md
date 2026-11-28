# Memoria del progetto

Qui c'è tutto quello che sappiamo già: com'è il PC aziendale, cosa si può fare, come funziona la
v2, il frontend, i problemi già visti e le decisioni prese. Serve a non rifare le stesse analisi.

**Claude la legge prima di ogni lavoro sulle prove e la aggiorna quando impara qualcosa di
nuovo.** Ultimo aggiornamento: 27-11-2026.

Il repository è pubblico: qui non ci sono mai valori veri (bucket, account, host, matricola,
codici di manuali, numeri DR, serial number, part number, codici dei cicli, contenuti EJ200).
Unica eccezione: `docs/CONFRONTO_V1_14_CICLI.md` (sezione 7).

Gli altri documenti:

| File | A cosa serve |
|---|---|
| `docs/DOCUMENTAZIONE.md` | com'è fatto e come funziona tutto il progetto, nei dettagli |
| `docs/COPILOT.md` | il file per lavorare sul PC: cosa fare adesso, blocchi da lanciare, domande per Copilot e per le persone |
| `docs/MEMORIA.md` | questo file |
| `docs/MIGLIORIE.md` | cosa migliorare, in che ordine, e il registro delle prove fatte |
| `docs/CONFRONTO_V1_14_CICLI.md` | la v1 sui 14 cicli con errori noti (in QA) e il testo originale delle stampe: **con i codici veri**, permesso dal responsabile (27-11) |

---

## 0. Adesso: verso la presentazione (dal 27-11-2026)

**L'utente presenta la v2 fra circa 2 settimane (dal 27-11).** Il 27-11, dopo le prime prove dal
frontend, ha chiesto: «perché la v2 dà così tanti warning? quale è più giusta, la v1 o la
v2?». La risposta, con i fatti, è nella nota del 27-11 in sezione 12. Il messaggio per la
presentazione: nella v1 «OK» vuol dire «non ho trovato contraddizioni»; nella v2 vuol dire «ho
controllato, e la frase citata l'ha ritrovata il programma nel manuale». Dove il manuale non
dice niente, la v2 lo dice invece di scrivere OK.

**Le cose da fare, in ordine** (i blocchi sono in `COPILOT.md`; lo stato aggiornato è nella
sezione 1 di `COPILOT.md`):

| # | Cosa | Dove | Stato |
|---|---|---|---|
| 1 | Aggiornare il codice sul PC | COPILOT 2.1 | ✅ 27-11 12:35, test passati |
| 2 | `aws sso login` | terminale | ✅ |
| 3 | Archiviare le prove vecchie | COPILOT 3.8 | ✅ 27-11 12:35 (le cartelle `-sonnet` da spostare a mano) |
| 4 | Copie cieche con il seme 3 | COPILOT 3.3 | ✅ 27-11: 14 copie (seme 2: 15) |
| 5 | Piano della campagna: per ogni insieme `base`, `fonte_ispezione`, `finale`, ognuna `3 da fare` | COPILOT 3.5 | ✅ |
| 6 | Campagna finale (circa 6 $, 3 ore); foto della riga finale, di `campagna.md` e dei due `riepilogo.md` | COPILOT 3.5 | ✅ 27-11 (piccolo 14:05-15:13, grande 16:03-17:02, circa 5,3 $): vince `finale` (MIGLIORIE 13) |
| 7 | La v1 sugli stessi 14 cicli noti, in QA, con le copie rinominate con l'impronta (si può fare mentre gira la campagna) | COPILOT 3.9 | ✅ 27-11: `docs/CONFRONTO_V1_14_CICLI.md` (298bc28e da ricaricare una volta) |
| 7b | Aggiornare, riepiloghi ricalcolati con gli errori aggiunti dal testo delle stampe (gratis), domanda P12 a Copilot | COPILOT passo 4c | ✅ 27-11 sera |
| 7c | Claude: `finale` nella base e tre controlli del codice (H17, H19, la 010 in più parti) | Claude | ✅ 27-11 sera |
| 7d | Aggiornare, archiviare, campagna della sola base nuova | COPILOT passo 4d | ✅ 27-11 sera: 30 su 43 stabili sul piccolo, 18 su 29 sul grande; falso errore 04ecaabe 050 in 2 prove su 3 |
| 7e2 | Campagna della variante `schede_e_limiti` (H18, regola «almeno N») | COPILOT passo 4e | ✅ 27-11 notte: vince, nella base |
| 7e5 | Aggiornare, ricalcolare, domande P13 e P14 | COPILOT passo 4g | ✅ 27-11 notte: P13 8d3c673c 070 errore vero, le due 060 falsi errori del codice; P14 il numero del DR è in `reference` |
| 7e6 | Claude: versione quasi finale (MG44, MG45, MG47, MG50, MG53, MG75-MG80), comando `eval senza-modello`, test sulle 14 stampe vere | Claude | ✅ 27-11 notte |
| 7e7 | Aggiornare, ricalcolare, prova senza modello (0 $) | COPILOT passo 4h | ✅ 27-11 notte: piccolo 39 su 45, grande 29 su 31, 0 falsi errori, 4 ERRATO da verificare nei cicli veri del grande |
| 7e8 | Claude: MG81 (massimo contro minimo), MG82 (motivo degli ERRATO in più), domanda P15 | Claude | ✅ 27-11 notte |
| 7e9 | Aggiornare, di nuovo senza modello, P15 | COPILOT passo 4h | ✅ 27-11 notte: piccolo 41 su 45, grande 31 su 31, 0 falsi errori; i 4 da verificare falsi errori di MG47 |
| 7e10 | Claude: MG47 corretta (condizioni, «ripristinare») | Claude | ✅ 27-11 notte |
| 7e11 | Aggiornare, senza modello (0 e 0 attesi), poi subito la campagna `quasi_finale` | COPILOT passo 4h | senza modello ✅ 27-11 notte: piccolo 41 su 45, grande 31 su 31, 0 falsi errori, 0 da verificare; campagna da fare |
| 7e12 | Claude: banco di prova (`eval banco`), metriche di controllo nel riepilogo, date e limiti ripetuti | Claude | ✅ 27-11 notte |
| 7e13 | Aggiornare, senza modello, `eval banco`; campagna (o, se già partita, ricalcolo dei riepiloghi per le metriche di controllo) | COPILOT passo 4h | senza modello e banco ✅ 27-11 notte: 41 su 45 e 31 su 31, 0 e 0; banco sul PC uguale a quello di Claude (308 su 310, 0 falsi allarmi, lettura 105 su 105); campagna ✅ 28-11 notte: `quasi_finale` si tiene (42 su 45, 31 su 31, 0 falsi errori, 0 da verificare) |
| 7e14 | Claude: tabelle per tipo e per motivo sulla scelta migliore; MG58 risultato già calcolato (solo servizio) | Claude | ✅ 28-11 |
| 7e15 | Claude: MG48, MG54, MG56, MG59, MG55 (spente, una variante ciascuna), dati per MG83, riferimento della campagna | Claude | ✅ 28-11 |
| 7e16 | Aggiornare, `eval chiamata-diretta`, MG48 senza modello, report rifatto con i WARNING per operazione, prova di `eval rigioca`, una prova sola di `diretta` sul piccolo (circa 0,40 $) | COPILOT passo 4i | da fare |
| 7e17 | Claude: MG83 (regola finale e variante `meno_avvisi`, provata con `eval rigioca`) dai dati del 7e16 | Claude | da fare |
| 7e18 | Campagna delle varianti che usano il modello (`diretta`, `testo_comune`, `lingue_insieme`), contro `quasi_finale` (circa 6-7 $; era 12-14 $ con tutte) | COPILOT passo 4j | da fare |
| 7e3 | Claude: comando `prova-ej200` (EJ200 sul PC senza tracce), misura con 2900 documenti (`eval scala`), cache dei codici, file `docs/V1_CONTRO_V2.md` | Claude | ✅ 27-11 notte |
| 7e4 | Ingestion EJ200 e prova EJ200 sul PC | COPILOT passo 4f | da fare |
| 7e | Claude: tabella finale v1 contro v2, cosa deve fare la v2 (sezione 0, sotto), pagina per la presentazione | Claude | dopo 7d |
| 8 | Le altre prove dal frontend della v2, dopo la campagna (due cicli «con errori», il più lungo con il tempo, DR con e senza serial, file sbagliato, storico, CSV) | COPILOT 4 | A3 e A1 fatte il 27-11 |
| 9 | Prompt della documentazione completa (quando c'è tempo) | COPILOT 6.3 | da fare |

**Cosa fa Claude con i risultati:**

- dopo la campagna (6): sceglie la configurazione per la produzione e la accende nella base,
  poi l'utente rifà Aggiornare;
- dopo la v1 (7): la tabella «v1 contro v2 sugli stessi cicli» (errori trovati, falsi errori,
  WARNING per ciclo, costo, tempo) e, se l'utente vuole, una pagina o qualche slide per la
  presentazione;
- poi, se c'è tempo prima della presentazione: grande ingestion, prova di controllo, QA
  (COPILOT passo 5). Per la presentazione basta la demo in locale con la configurazione
  scelta.

**v1 contro v2, in breve** (27-11 sera, dalla campagna finale e da `docs/CONFRONTO_V1_14_CICLI.md`;
numeri della v2 da confermare con i riepiloghi ricalcolati):

| Dove | Meglio | Perché |
|---|---|---|
| Codici cambiati (task accanto all'operazione, scheda, macchina) | v1 | li confronta con l'indice delle schede, il registro delle macchine e il task giusto; la v2 controlla solo che esistano |
| Documenti | v1 | ha la classe dell'etchant (capitolo 70 dell'SPM) che la v2 non ha nella conoscenza |
| Falsi errori | **v2** | v1: 6 sulle 4 stampe giuste, più 2; v2: 0 contati (resta il P7 della 050) |
| Testo in italiano | **v2** | la v1 legge l'inglese: perde 3 cambi fatti solo in italiano |
| Stampe che legge | **v2** | la v1 si ferma sulle 3 A6 (vuole serial e condition) e non carica 298bc28e |
| Prove di quello che dice | **v2** | ogni ERRATO ha la frase del manuale ritrovata dal programma; dove non può controllare lo dice invece di OK |
| Errori tra le due lingue (negazioni, limiti al contrario) | **v2** | trova anche 2 errori veri in stampe che si credevano giuste (737dec71 060, 04ecaabe 030) |

**Per rendere la v2 migliore della v1** (proposte del 27-11 sera, in ordine): (1) H17, il task
accanto all'operazione contro quello della testata; (2) capire perché i limiti cambiati in una
lingua nella 010 (5ff17062, f355dc3c, 38960731) non li trova il controllo delle lingue: forse
la pagina a due colonne; (3) H18, la scheda coerente con l'operazione; (4) H19, la stessa
operazione con due macchine, e in QA il registro delle macchine attive acceso; (5) togliere
il falso errore P7 (dopo la P12); (6) nella grande ingestion i documenti che ha la v1 e la v2
no (capitolo 70 dell'SPM con le classi dell'etchant, indice delle schede con materiale e
motore); (7) `finale` nella base; (8) H15, due tipi di WARNING, per la presentazione.

**Cosa deve fare la v2 e cosa deve fare meglio della v1** (ragionamento del 27-11 sera, chiesto
dall'utente: non sugli esperimenti ma sul prodotto). Il lavoro: chi prepara un ciclo vuole
sapere, prima di rilasciarlo, se c'è un errore e dove, in pochi minuti, fidandosi della
risposta. Quindi, in ordine di importanza:

| # | La v2 deve | v1 | v2 oggi |
|---|---|---|---|
| 1 | non dare errori falsi (chi usa lo strumento smette di leggerlo) | 6 su 4 stampe giuste | 0 contati ✅ |
| 2 | trovare almeno gli errori che trova la v1 | 15 su 19 | circa 13 su 19 dopo i controlli del 27-11 sera (da misurare, passo 4d): mancano schede (H18), una parola cambiata in inglese, un documento |
| 3 | leggere tutte le stampe (MOS, DR con e senza serial, stampe modificate) e le due lingue | 10 su 14, solo inglese | 14 su 14, due lingue ✅ |
| 4 | dire dove e perché, con la frase del manuale ritrovata | testo libero, a volte si contraddice | citazione ritrovata dal programma ✅ |
| 5 | dire cosa non ha potuto controllare, senza confondere con i dubbi veri | OK anche senza controllo | ✅ dal 27-11 sera: `[da guardare]` e `[non controllabile]` (H15) |
| 6 | dare la stessa risposta ogni volta, in tempo, a poco costo | mai misurata | misurata: stabile, 15-30 s e 0,01-0,02 $ a ciclo ✅ |

Da migliorare, in ordine: H18 (schede); il registro delle macchine in QA; nella grande
ingestion i documenti che ha la v1 (classi dell'etchant, indice delle schede con materiale);
H15 (due tipi di WARNING); le differenze di significato in una lingua sola che non sono né
negazioni né limiti (una parola cambiata); due regole da decidere con le persone (scheda
mancante in un processo speciale: errore o avviso? «almeno 4 volte» contro «più di 4»:
errore?).

**Decisioni dell'utente (27-11 sera, dopo questo ragionamento):**

- **scheda mancante** in un processo speciale: **avviso**, con il commento «Scheda mancante»
  (la regola P6 di oggi; cambiato solo il testo). c5ff3cd6 030 resta in attesa;
- **«almeno 4 volte» contro «più di 4 volte»: non è un errore.** 04ecaabe 050 non è più in
  attesa: un ERRATO lì conta come falso errore. Regola nel prompt (`boundary_limits_note`);
- **nel confronto con la v1 tenere conto della conoscenza:** la v1 aveva documenti che la v2
  non ha ancora (l'indice delle schede con materiale e motore, le classi dell'acido dell'SPM,
  forse altri). Una parte dei mancati della v2 viene da lì e si chiude con la grande
  ingestion, non con il codice. Nella tabella finale va scritto quali mancati sono «manca il
  documento» e quali «manca il controllo»;
- **lavorare subito su tutto**, mentre l'utente lancia il passo 4d: fatti H15 (nella base,
  cambia solo come si mostra) e H18 più la regola «almeno N» (variante `schede_e_limiti`,
  spenta nella base per non cambiare la campagna in corso; passo 4e).

**Previsione data all'utente (27-11 sera):** la v2 migliore della v1 sui 10 cicli che la v1
valida in 2-3 giorni di lavoro (due campagne: 4d e 4e); «perfetta» (tutti gli errori noti
trovati, 0 falsi errori) in circa 2 settimane, soprattutto per la grande ingestion: 2-3 errori
si trovano solo con documenti che oggi la v2 non ha. Perfetta del tutto mai: ogni stampa
nuova può avere un tipo di errore non visto.

**Come l'utente vuole le risposte** (detto il 27-11): le cose da fare scritte in modo preciso e
puntuale, in ordine, ognuna con il paragrafo di `COPILOT.md`, *Deve uscire* e *Mandami*.

---

## 1. Dove siamo e cosa manca per la consegna (22-11-2026)

**In breve:** la v2 funziona sui cicli veri (MOS e DR) e legge tutte le stampe viste. Per
consegnarla mancano soprattutto **i collegamenti con l'azienda**: accesso degli utenti, macchine
attive, configurazione e pubblicazione. Sono lavori conosciuti, non problemi aperti. La misura
sugli errori veri aspetta i manuali nella conoscenza.

**Chiuso (non si riapre senza un fatto nuovo):**

- **Lettura delle stampe.** Il parser legge tutte le stampe PVRM320 viste (esempi MOS e DR e
  le cartelle `cicli MOS`), anche quelle modificate a mano e quelle con «OPERAZIONE
  EVENTUALE». Una stampa senza layout PVRM320 la legge il modello (sezione 10).
- **Regole DR** (`Accept as is` e `Reject` bloccano; serial number e condition facoltativi) e
  risposta nel formato del frontend di oggi (sezioni 8 e 9).
- **Tempi:** al massimo 131 s su un DR da 9 operazioni, sotto i 600 s del backend.
- **Come funziona la v1 in azienda** (risposte di Copilot C1-C20): frontend, permessi, avvio in
  locale, costruzione dell'immagine (sezione 9).
- **Una sola pipeline** per MOS, DR ed EJ200; il pulsante militare lo decide già il frontend
  con `permissions.json` (sezione 9).
- **Macchine attive dal PC: non si leggono** (prova del 22-11 notte). La Data API risponde
  `AccessDeniedException` su `ExecuteStatement` (il ruolo SSO non ha il permesso) e la
  connessione diretta dà `OperationalError` (il PC non arriva al cluster; i tunnel di
  centralizer non c'entrano). In locale la v2 parte con `MACHINES_SOURCE=nessuna` (targhe
  WARNING); in servizio legge Redshift come la v1 (`MACHINES_SOURCE=diretta`, sezione 5).

**Da chiudere, in ordine.** Chi: C = Claude, U = utente.

| # | Cosa | Perché serve | Come si chiude | Chi |
|---|---|---|---|---|
| 1 | Misura sugli errori veri | 23-11 sera: 3 degli 8 errori noti trovati in modo stabile, più uno per ciascuno degli altri 4 cicli; 0 falsi errori nei 3 cicli giusti | ingestion del manuale principale fatta il 23-11 (10 manuali); due correzioni nel 23-11 (titoli `CIR`, fonti con la sola sezione). Mancano i file di due REPAIR e il capitolo 70-23 dell'SPM: **decisione del 26-11 sera, non si chiedono più** (si va in produzione senza). Si chiude con la campagna finale del 27-11 (seme 3) e la prova di controllo dopo la grande ingestion | U, poi C |
| 2 | Accesso degli utenti come la v1 | il frontend manda solo il cookie con il token | **fatto nel codice** (22-11 sera): `API_AUTH=sdk`, scelto da solo quando c'è `AUTH_INTROSPECT_URL`, con gli stessi middleware della v1 (sezione 9). Provato in locale il 22-11 (punto 4); da provare in QA | U |
| 3 | Stessa configurazione della v1 | in servizio la v2 deve partire con lo stesso secret «di ambiente» della v1, senza chiavi nuove | **fatto nel codice**: `CV_ENV_SECRET` = nome del secret di ambiente, letto come `load_secrets` (22-11 sera); macchine attive come la v1 con `MACHINES_SOURCE=diretta`: `redshift_connector` con il secret `SECRET_NAME` (22-11 notte). Da provare in QA | C, poi U |
| 4 | Prova in locale | è il passo prima di develop | **fatto** (22-11 notte): login, frontend e v2 da Run and Debug; ciclo MOS di esempio `Validation Passed` in circa 20 s, con accesso e permessi della v1. Configurazione in `DOCUMENTAZIONE.md`, sezione 13.7 | — |
| 5 | Pubblicazione in QA | oggi `buildspec.yml` costruisce solo la cartella della v1: un push della v2 su develop non cambia il servizio | **pronto nel codice** (22-11 notte): `cycle-validation qa` sul PC scrive il Dockerfile della v2 da quello della v1 (base, certificati), copia la libreria in `vendor/`, mette i valori aziendali nelle righe `ENV`, copia le impostazioni in `config/settings.azienda.yaml` e sposta il buildspec sulla v2. Primo passaggio con EJ200 spento. Dockerfile e buildspec scritti sul PC e controllati (22-11). Manca la pull request verso develop: COPILOT 4 | U |
| 6 | Pulsante Confirm | per usare DR senza serial number e condition | messaggio COPILOT 6.2 | U |
| 7 | Prova in QA: EJ200 e targhe | i dati EJ200 non escono da AWS; Redshift si raggiunge solo da AWS | dopo il punto 5, dal frontend QA | U |
| 8 | Domande agli esperti | P1-P9 chiuse il 26-11 (Copilot sui dati, regola prudente) | fatto | U |

**Decisioni da prendere:**

- **D1. Dove scrivere il nome del secret «di ambiente» per la v2.** **Confermato dall'utente
  (22-11 notte).** Nella v1 è scritto nel
  codice; nel repository personale (pubblico) non si può. Fatto così (22-11 sera, da
  confermare dall'utente): la v2 lo legge dalla variabile `CV_ENV_SECRET`; in locale la mette
  `launch.json`, nel container una riga `ENV` nel Dockerfile della copia aziendale (il blocco
  di aggiornamento non copia il Dockerfile). Nello stesso Dockerfile vanno anche
  `MACHINES_SOURCE=diretta`, `REDSHIFT_DATABASE` (il database scritto nel file delle credenziali
  della v1) e `MACHINES_QUERY` (la query di `verify_active_TM`), a meno che non stiano già nel
  secret di ambiente.
- **D2. Quando passare a QA.** **Deciso dall'utente (22-11 notte):** prima altre prove in
  locale dal frontend (COPILOT sezione 4), poi QA quando lo dice lui. Il comando `qa` e il salvataggio
  sul ramo `feature/cycle-validation-v2` si fanno subito; solo la pull request verso `develop`
  aspetta (è quella che fa passare QA alla v2). La misura sugli errori (punto 1) può andare avanti in parallelo.

**Non serve per la consegna** (`MIGLIORIE.md`, «Da fare»): chiamata diretta a Bedrock (B1), più
concorrenza (B4), varianti proposte dal modello (E1), togliere le rotte storiche (D).

---

## 2. Chi fa cosa

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

## 3. Il PC aziendale

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

## 4. Copilot

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
  («Rispondi solo leggendo il codice, senza modificare né eseguire niente», poi la domanda).

## 5. I servizi

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
- **Macchine attive**: in azienda vengono da Redshift (il database aziendale con l'elenco
  delle macchine). Su Redshift non si crea niente: si legge la tabella che legge la v1. La v1
  la legge in `verify_active_TM` con `redshift_connector` (porta 5439): colonne
  `work_center_cd` (la targa) e `work_center_usage_cd`, filtro `= 'TO'`. Le credenziali sono
  in un secret di Secrets Manager (`SECRET_NAME` in `config.py`). Se la query fallisce la v1
  salta il controllo; la v2 dà WARNING `ERRORE_TECNICO` e il ciclo è `parziale`.
  - **In servizio** la v2 fa come la v1 (dal 22-11 notte): `MACHINES_SOURCE=diretta`,
    `redshift_connector` con host, porta, utente e password del secret `SECRET_NAME` (riletto
    a ogni aggiornamento dell'elenco, ogni 15 minuti), database da `REDSHIFT_DATABASE`, query
    da `MACHINES_QUERY`, 20 secondi al massimo per collegarsi. Resta possibile la Data API
    (`MACHINES_SOURCE=data_api`, `DOCUMENTAZIONE.md`, sezione 13.6).
  - **Sul PC** (dal 22-11): `cycle-validation macchine --v1 ..\app_cycle_validation`
    scrive `data\macchine_attive.json`; poi `run --machines data\macchine_attive.json`.
    Nella v1 il nome del secret di Redshift non è nel codice: `config.py` ha
    `SECRET_NAME = os.getenv("SECRET_NAME")`, e all'avvio `app_backend.py` chiama
    `load_secrets("<secret di ambiente>")` che mette le chiavi del secret di ambiente nelle
    variabili d'ambiente (`secret_loader.py`). Il comando fa lo stesso: legge il secret di
    ambiente, prende `SECRET_NAME`, legge il secret di Redshift, fa la query con la Data API.
    Stampa solo il numero di macchine.
  - **Il secret di Redshift** (prova del 22-11) ha i campi `dbClusterIdentifier`, `engine`,
    `host`, `password`, `port`, `username`: è un cluster, e **il database non c'è**.
  - **Da dove la v1 prende il database (C21):** in `verify_active_TM`
    `REDSHIFT_HOST, REDSHIFT_USER, REDSHIFT_PWD, REDSHIFT_DBNAME = get_db_credentials()`, poi
    `RedshiftConnector(host=..., port=5439, database=REDSHIFT_DBNAME, ...)`, che passa i
    valori a `redshift_connector.connect`. `get_db_credentials` sta in
    `src/config/credentials.py`, che Copilot non può leggere (esclusione dell'organizzazione).
    Il comando `macchine` segue il valore fino a quella funzione (analisi del codice Python, solo
    la struttura) e trova la chiave che legge; poi cerca la chiave nei due secret e
    nell'ambiente. Stampa solo il nome della chiave. Se non basta: `--database`.
  - **Il file delle credenziali (visto dall'utente, 22-11 sera):** `get_db_credentials` legge
    il secret `SECRET_NAME` (regione `REGION_NAME`), costruisce un dizionario con `host`,
    `username`, `password` presi dal secret e **`database` scritto nel codice**, e restituisce
    i quattro valori. Il comando segue anche il dizionario. Se il database non si trova, prova
    quello creato con il cluster (`describe_clusters`, `DBName`).
  - **Dal PC non si legge (prova del 22-11 notte).** Il comando trova tutto (secret, tabella,
    database scritto nel codice), ma la Data API risponde `AccessDeniedException` su
    `ExecuteStatement` (manca il permesso al ruolo SSO: P7, facoltativa) e la connessione
    diretta (`macchine --diretto`) dà `OperationalError`: il PC non arriva alla porta del
    cluster. Copilot ha controllato: lo script dei tunnel di centralizer non c'è nel workspace e
    comunque apre solo i tunnel di OpenSearch. La v1 legge Redshift solo quando gira su AWS.
  - **Perché Redshift e non il documento delle targhe su S3:** il documento dice se una targa
    esiste e che macchina è; Redshift dice se la macchina è in uso oggi. Una macchina dismessa
    che è ancora nel documento è un errore. Alternativa possibile: l'ingestion copia ogni
    giorno l'elenco delle attive su S3 e la v2 lo legge con `MACHINES_FILE`.
- **Frontend**: il gateway QA aziendale (pagina *Cycle Validation*) oggi parla con la v1. La v2
  non è ancora collegata.

## 6. La conoscenza di prova

È stato ingestionato solo un pezzo (i file sono circa 2000, tutti costerebbero troppo):

- 8 capitoli del manuale SPM (capitolo 70);
- 2 procedure DR;
- 104 targhe, 94 schede;
- 23 recommendation DR (17 serial number, 5 con più recommendation).

I **manuali dei motori non ci sono**: le righe che ne hanno bisogno escono WARNING
`FONTE_ASSENTE`, ed è giusto. Decisione del 21-11-2026: per ora non si ingestiona altro.
**Cambiata il 22-11 notte:** l'utente ingestiona i manuali (solo i capitoli citati) di tutti i
cicli di prova sul PC. La lista la fa il comando `manuali` (COPILOT sezione 5): legge con il parser
tutte le stampe di `ProgettoDocumenti`, confronta con l'ultima fotografia della conoscenza e mette
in cima i manuali che servono per i 10 errori noti. Codici veri solo nel file sul PC
(`runs/manuali-da-ingestionare.txt`).
**Lista del 23-11** (29 cicli letti su circa 2500 PDF; codici solo nel file sul PC): 6 manuali.
M1 (manuale del motore, manca) capitolo 72-56: serve a 20 cicli e a tutti e 7 gli errori dei
tre cicli «con errori» legati a un manuale; sul PC 7 file nella cartella del corpus
dell'ingestion (più copie vecchie in `Extra\storico\old`, da non usare). SPM: c'è, manca solo il
task del capitolo 70-23 (nessun file sul PC). M3 (altro manuale motore, manca) capitolo 72-56:
3 file, 3 cicli (due con «errori» nel nome). M4 e M5 (senza task, 3 cicli): nessun file sul PC.
M6 è EJ200 (una guida d'esempio non riconosciuta come EJ200): non va nell'ingestion civile. I
cicli con «errori» nel nome sono 7, non 3: il blocco dei cicli con errori (COPILOT 2.1) li prende tutti.
**Ingestion del 23-11** (fatta dall'utente): 10 manuali nuovi, 21 file già presenti saltati,
versione pubblicata. Il controllo di Copilot sull'indice diceva che mancano alcuni task (tipo
`REPAIR 00N` di M1, uno del capitolo 72-56 e quello del 70-23), ma guardava solo l'indice: la v2,
se l'indice non ha un task, lo cerca nel testo del manuale (`kb/task_text.py`). Per sapere
quali mancano davvero alla v2 c'è il blocco COPILOT sezione 5 B: `manuali` con la fotografia nuova, che
per ogni task mancante dice perché (nel testo ma non come titolo, solo la sezione, non nel
testo, forma non da task) e nel file sul PC scrive le righe del manuale dove compare. Dal codice di
`knowledge-index` (repository personale, collegato il 23-11): l'indice registra come titolo di
un task solo il codice completo (`codice_task` in `regole.json`), quindi i titoli `REPAIR 00N`
non li ha mai; i «conflitti» del report dell'indice sono targhe e schede con lo stesso codice
e valori diversi (si uniscono con «; »), non riguardano i manuali. I 44 c'erano già prima.
**Prova del 23-11 pomeriggio** (versione `v/20261123T142517Z/`, 20 documenti, 28 task):
i 7 cicli con «errori» danno tutti 0 errati. M1 c'è, ma mancano 7 task. La risposta di Copilot
(in sola lettura) spiega perché:
- due REPAIR hanno il titolo `CIR <sezione>, REPAIR 00N`, con `CIR` davanti e una virgola. La
  ricerca nel testo della v2 non lo riconosceva: corretto il 23-11 (`kb/task_text.py`);
- due citazioni sono la sola sezione: non sono task;
- due REPAIR sono nominati solo in una frase («Refer to TASK <codice completo> (<sezione>,
  REPAIR 00N)»): sono task di altri file del manuale, non ingestionati. I file del manuale
  hanno nel nome la sezione e `-09-` con il numero del REPAIR;
- il task SPM del capitolo 70-23 è citato con la sola sezione: adesso la v2 lo accetta nei
  documenti SPM, ma il capitolo 70-23 dell'SPM non è nella conoscenza.
Dopo la correzione (lista delle 16:00) M1 ha 5 task mancanti: le 2 sezioni e i 2 REPAIR della
sezione 72-56-31 citati solo in una frase (più il codice completo di uno dei due). I loro PDF
(`-09-001`, `-09-003`) **non sono sul PC**: vanno presi dalla fonte dei manuali.
I 7 cicli con la correzione (16:15): ancora 0 errati in tutti (2-6 corretti, 15-24 warning).
Il controllo della descrizione, se un task citato dall'operazione manca, non confronta niente
(`skip_missing_task`, FONTE_ASSENTE): per capire quale controllo ferma gli errori noti c'è il
blocco COPILOT 2.1b.
**2.1b del 23-11 (16:40)** sui tre cicli «con errori»:
- 298bc28e op 035, c5ff3cd6 op 030 e 040, f355dc3c op 030: nessun task citato e nessun testo
  delle fonti collegate (FONTE_ASSENTE). Causa probabile: le fonti citano solo la sezione
  (`CIR <sezione>`). Corretto il 23-11 (`section_locations` in `resolve/civil.py`): una fonte con
  la sola sezione porta i task di quella sezione in tutti i documenti del manuale; anche il
  controllo `source` e il comando `manuali` la danno trovata;
- 298bc28e op 005 e f355dc3c op 010: il modello ha avuto il task d'ispezione della sezione
  72-56-32 e ha risposto EVIDENZA_NON_TROVATA (op 005: errore in un codice; op 010: tre numeri
  cambiati). Da capire con la spiegazione intera (2.1b allungato);
- f355dc3c op 040 e 050: fuori dalla foto.

**2.3, 2.1 e 2.1b del 23-11 (16:50)**, dopo la correzione delle sezioni: M1 ha 3 task mancanti
(nel testo, ma non come titolo), M2 uno. I 7 cicli: ancora 0 errati. In 2.1b la fonte risulta
**senza task** (rc A1) e le operazioni 035 (rc A3), c5ff3cd6 030/040 (rc A2) e f355dc3c
030/040/050 (rc A1) restano FONTE_ASSENTE. Causa trovata nel parser della stampa: la fonte era
una sola, con la riparazione e la nota della **prima** pagina, e il task veniva preso dalla nota
solo se cominciava con le cifre (una nota `CIR <sezione>` dava task vuoto). Corretto il 23-11
(17:10, `extract/pvrm320_report.py`): una fonte per ogni riparazione, con la nota della testata
delle sue pagine e il manuale del piè di pagina; la nota può cominciare con `CIR` o `TASK` e
avere la virgola dopo la sezione. `leggi --fonti` stampa le fonti senza codici di manuali
(COPILOT 2.0). Non ancora visto sui PDF veri: la forma della nota è un'ipotesi da confermare con
2.0. Le spiegazioni di op 005 e op 010 (task d'ispezione 72-56-32): il testo dell'ispezione non
parla di rimozione del metallo né dei limiti di numero delle raccordature; quelle cose stanno nei
REPAIR, quindi senza i REPAIR giusti il modello non può trovare l'errore.

**2.0 del 23-11 (17:00)**, con le fonti per riparazione: c5ff3cd6 ha una sola riparazione (A2)
con nota `APPL. LUBRIFIC. SECCO` (una descrizione, nessun task); f355dc3c una sola (A1) con nota
`BLENDING <task completo>` (parola prima del codice: corretto alle 17:20, il task si cerca in
tutta la nota). 298bc28e in 2.1b non ha **nessuna** fonte (OEM del piè di pagina assente o con
`/`?): da vedere con 2.0. op 005 di 298bc28e cita dei subtask SPM della sezione 70-42-00 in una
forma che la v2 non legge come task (non c'è la parola TASK davanti): `leggi --fonti` ora stampa
questi codici, per capire la forma prima di leggerli. Rilanciati i 7 cicli (17:02): ancora 0
errati.

**2.0 del 23-11 (17:10)**, con il parser nuovo: tutti e tre i cicli hanno una fonte (M1, OEM
nel piè di pagina). 298bc28e (rc A3) e c5ff3cd6 (rc A2): nota senza task. f355dc3c (rc A1):
task della nota = un task SPM della sezione 70-42-00 (raccordatura), quindi le sue operazioni
030/040/050 ora hanno un testo. Codici non letti come task: `SUBTASK <codice completo>` (op 005
di 298bc28e, sezione 70-42-00; op 005 di c5ff3cd6, sezione 72-56-31). Corretto (17:30): SUBTASK
è letto come task code; nel manuale, se il codice non apre un task, si cerca la riga che comincia
con `SUBTASK <codice>` (anche dopo «(1)») fino al prossimo SUBTASK o task. L'indice non registra
i SUBTASK e non serve cambiarlo. Per c5ff3cd6 030/040 resta il problema: nessun task né nella
nota né nell'operazione (domanda alle persone: quale task vale per quella riparazione?).

**2.3, 2.1 e 2.1b del 23-11 (17:20)**, con i SUBTASK: M2 (SPM) ha 1 task «non nel testo», che
serve per 298bc28e op 005. I 7 cicli: ancora 0 errati. Analisi dei 8 errori dei tre cicli:
- 298bc28e op 005 (codice cambiato): ora i subtask SPM 70-42-00 sono letti. Uno dei due non è
  da nessuna parte nel testo SPM, dove ci sono i suoi fratelli: è il codice sbagliato. Il
  modello giudica solo la descrizione e ha detto CORRETTO. Corretto (17:50): `task_code` dà
  ERRATO `TASK_INESISTENTE` se un codice completo non compare in nessun punto dei documenti
  dove dovrebbe stare e lì ci sono task della stessa famiglia (stesse prime quattro parti).
  Se la famiglia non c'è (documento mancante), resta FONTE_ASSENTE;
- f355dc3c op 030/040/050: la fonte (task SPM 70-42-00 della nota) veniva presa dal manuale del
  motore, che la cita su una riga a sé: la ricerca nel testo la scambiava per il titolo. Il
  modello ha detto «il testo del task non è presente». Corretto (17:50): i task del capitolo 70
  si cercano prima nell'SPM. op 040 (la classe, un attacco chimico a tampone) sta
  probabilmente nel capitolo 70-23 dell'SPM, che manca; op 050 (frase al contrario): con il
  testo SPM giusto forse si trova;
- 298bc28e op 035 e c5ff3cd6 op 040: nessun task né nell'operazione né nella testata. Corretto
  (17:50): si usano i task citati dalle altre operazioni della stessa riparazione (al massimo
  4). Più chiamate al modello per ciclo;
- f355dc3c op 010 (tre numeri): i limiti di numero delle raccordature non sono nel task
  d'ispezione citato; stanno in un altro task (forse un REPAIR della sezione 72-56-32). Aperto;
- c5ff3cd6 op 030 (scheda tolta): regola P6. Aperto.
Per i falsi errori c'è COPILOT 2.1c (le tre stampe giuste: non devono dare ERRATO).

**2.1, 2.1b e 2.1c del 23-11 (17:30)**, con le correzioni delle 17:50:
- 7 cicli con errori: 298bc28e 0 errati; 5ff17062 **2 errati** (op 030 e 050,
  CONTRADDIZIONE: da vedere se veri); f355dc3c **1 errato** (op 050). Cicli giusti: 4e64d49a 0,
  8bdb25d5 0, 04ecaabe **1** (op 050, stessa spiegazione di f355dc3c: il ciclo dice indicazione
  lineare «almeno 4 volte la larghezza», l'SPM «3 volte o più»). Quindi f355dc3c op 050 non è
  l'errore messo apposta: è una differenza che c'è anche nella stampa vera (domanda P7);
- 298bc28e op 005: i due subtask SPM ci sono tutti e due (il 035 parla di raccordatura del
  titanio su parti rotanti); `TASK_INESISTENTE` non scatta. Il codice cambiato va visto
  confrontando i task dell'op. 005 nella stampa giusta (COPILOT 2.0);
- 298bc28e op 035 e c5ff3cd6 op 030/040: ora confrontate con i task della stessa riparazione,
  ma sono task d'altro (lubrificante, raccordatura): EVIDENZA_NON_TROVATA. In c5ff3cd6 op 040 il
  modello ha notato che **l'italiano dice 13-38 micron e l'inglese 13-58**: è il numero cambiato;
- f355dc3c op 030: CONTRADDIZIONE alla prima risposta (il ciclo dice raccordatura lunga almeno
  30 volte la profondità, l'SPM 10 volte), non ritrovata nelle due verifiche: GIUDIZIO_INSTABILE;
- f355dc3c op 010 e 040: EVIDENZA_NON_TROVATA (limiti in un altro task; classe d'attacco nel
  capitolo 70-23 o nel manuale d'ispezione del motore).
Corretto il 23-11 (18:10): controllo senza modello delle **due lingue** (`checks/languages.py`):
se nello stesso punto la descrizione italiana e quella inglese hanno numeri diversi (non una
conversione mm/pollici o °C/°F), ERRATO `INCOERENZA_LINGUE`. Misura gratis con `leggi --lingue`
(COPILOT 2.0) sui 10 cicli, prima di rilanciare.

**2.0 del 23-11 (17:40)**, `leggi --lingue` sui 10 cicli (prima versione):
- con errori: f355dc3c op 030 `30 → 10, 0,5 → 1,5` (**è l'errore messo apposta**: in italiano
  30 volte, in inglese 10; la verifica che diceva «corretto» aveva letto l'inglese); 5ff17062
  op 030 `30 → 2, 0,5 → 1,5`; 38960731 op 050 `4 → 2`; 8d3c673c op 140 `32 → 31`; e9b74c84 op
  025 `500 → 60` (questi quattro cicli non hanno la stampa giusta conosciuta: probabili errori
  messi apposta, da confermare); c5ff3cd6: niente (il modello aveva visto 13-38 / 13-58);
- giusti: 4e64d49a niente; **8bdb25d5 op 040: falso errore** (un part number scritto in punti
  diversi nelle due lingue spostava l'allineamento dei numeri). Corretto (17:55): i codici fatti
  di cifre (con `/`, o di 5 cifre o più) restano fuori dal confronto. Con questo anche c5ff3cd6
  op 040 dovrebbe uscire. 298bc28e e 04ecaabe fuori dalla foto;
- 298bc28e op 005: nella stampa giusta i task sono il subtask SPM 029 e l'ispezione; in quella
  con errori c'è **in più il subtask 035** (raccordatura del titanio su parti rotanti): il codice
  cambiato è un subtask che esiste, ma è un altro lavoro. Né `TASK_INESISTENTE` né il modello lo
  vedono: serve chi conosce il pezzo (domanda P9);
- 5ff17062 op 030 ERRATO dal modello: l'inglese dice di usare abrasivi a matrice vetrificata,
  l'italiano di non usarli e il manuale li vieta: **vero errore**. op 050: stesso «4 volte
  contro 3 volte» della domanda P7;
- f355dc3c op 030: verifica 1 CONTRADDIZIONE, verifiche 2 e 3 VERIFICATO (hanno letto il «10
  volte» inglese): ora la prende il controllo delle due lingue.

**2.0 del 23-11 (17:49)**, `leggi --lingue` con i part number fuori dal confronto: i tre cicli
giusti (04ecaabe, 4e64d49a, 8bdb25d5) **puliti**. Trovati: 298bc28e op 005 `035 → 029` (il
codice cambiato è il subtask, cambiato **solo in italiano**: la domanda P9 non serve più),
c5ff3cd6 op 040 `38 → 58`, f355dc3c op 030 `30 → 10, 0,5 → 1,5`; e negli altri cicli 5ff17062
op 030, 38960731 op 050, 8d3c673c op 140, e9b74c84 op 025. Dei 8 errori noti dei tre cicli: 3
trovati senza modello (005, c5ff3cd6 040, f355dc3c 030). Restano: 298bc28e op 035 (parole),
c5ff3cd6 op 030 (scheda, P6), f355dc3c op 010 (numeri cambiati in tutte e due le lingue), 040
(classe), 050 (frase).

**2.1, 2.1b e 2.1c del 23-11 (17:58)**, con tutte le correzioni:
- i 7 cicli con errori: un ERRATO `INCOERENZA_LINGUE` in ognuno (298bc28e op 005, 38960731 op
  050, 5ff17062 op 030, 8d3c673c op 140, c5ff3cd6 op 040, e9b74c84 op 025, f355dc3c op 030);
  in più CONTRADDIZIONE del modello in 5ff17062 op 050 e f355dc3c op 050 («4 volte» contro i
  «3 volte» dell'SPM, domanda P7);
- i 3 cicli giusti: **0 errati** (04ecaabe questa volta non ha dato l'op. 050: il giudizio del
  modello su quel punto cambia da una prova all'altra);
- dei 8 errori noti dei tre cicli: **3 trovati in modo stabile** (298bc28e 005, c5ff3cd6 040,
  f355dc3c 030); f355dc3c 050 segnato, ma per il «4 volte» che c'è anche nella stampa giusta.
  Restano 298bc28e 035 (parole: confrontata con i task della riparazione, nessun collaudo
  visivo), c5ff3cd6 030 (scheda tolta, P6; la descrizione esce CORRETTO), f355dc3c 010 (limiti
  delle raccordature in un altro task), 040 (classe d'attacco: l'SPM rimanda al manuale
  d'ispezione del motore, che non è nella conoscenza), 050 (frase al contrario).

**COPILOT riordinato (23-11 sera).** Tolti i blocchi di analisi già fatti (2.0 lingue, 2.1 cicli
con errori, 2.1b, 2.1c cicli giusti): li sostituisce la prova con metriche (`eval prova`, ora
COPILOT 2.3). Nuova numerazione: 2.1 Aggiornare, 2.2 Salvare, 2.3 Prove delle migliorie, 2.4
Frontend, 2.5 Dopo una nuova ingestion (fotografia e lista dei manuali). Nelle note sopra i
numeri dei blocchi sono quelli vecchi. Metriche e regola di scelta: `MIGLIORIE.md`.

**Due insiemi di prova (23-11 sera).** L'utente vuole provare le migliorie anche su più cicli.
Insieme **piccolo** = i 10 cicli noti (`runs/prove-piccolo`); insieme **grande** = i 10 più 20
cicli veri civili con almeno l'80% delle operazioni confrontabili con la conoscenza, scelti da
`eval scegli` (zero token, lista dei percorsi in `runs/prove-grande/cicli.txt`, solo sul PC).
Un ciclo vero non ha errori noti: tipo `vero`, i suoi ERRATO sono «da verificare», i suoi
WARNING contano nel lavoro a mano. Si confrontano solo prove sullo stesso insieme (colonna
«Cicli» con l'impronta dell'insieme nel riepilogo). Una miglioria con file
`eval/varianti/<nome>.yaml` si lancia con `eval prova --variante`; il blocco della prova a mano (COPILOT 3.7) lo fa da
solo. La lista delle migliorie da provare è in `MIGLIORIE.md`, «Da provare».

**Errori mai visti (23-11 sera).** L'utente vuole sapere se la v2 generalizza o ha imparato la
lista dei 12 errori (che Claude conosce). Fatto: `eval muta` (copie cieche dai cicli veri, un
errore per copia, quattro tipi, seme; `runs/mutazioni` sul PC), gruppo nascosto facoltativo in
`data/nascosti` + `data/errori-nascosti.yaml` (Claude non lo vede mai), `visto: false` negli
attesi. I report danno visti e mai visti a parte, i mai visti solo per tipo; la regola non tiene
una variante che perde errori mai visti stabili. Il piccolo ora = 10 noti + copie cieche +
nascosti; il grande = 10 noti + tutti i cicli veri confrontabili (`--quanti 0`). Quando cambia
il seme o la conoscenza, le prove si archiviano (COPILOT 3.8). Non chiedere mai foto degli
errori ciechi o nascosti.

**Migliorie scelte sui mai visti (23-11 notte).** Decisione dell'utente: le migliorie non si
scelgono più dagli errori noti mancati (erano fatte su misura, cioè «imparare la lista»). Tolte
`negazioni_lingue` (I1), `classi_lingue` (I2), `prompt_confronto` (I3), `contesto_sezione` (I5),
`fatti_incerti` (F5), `modello_grande_sui_dubbi` (I6); resta solo `numeri_manuale` (I4). Dopo la
base si guarda la tabella «Errori mai visti, per tipo» e si sceglie sul tipo «modello» trovato
peggio. Corretto anche un errore di misura: i tipi ciechi `numero_una_lingua` e
`task_inesistente` li trova il codice con la stessa regola che li mette (`CODE_KINDS`), quindi
non contano nella generalizzazione né nella regola; si vedono a parte come controllo.

Sul PC la copia della parte civile è in `eval/casi/aziendali/conoscenza/foto-20261121/`; i PDF
dei cicli in `docs\Esempio ciclo mos\` e `docs\Esempio ciclo dr\` (git li ignora).

## 7. Regole sui dati

- La guida aziendale dice: *«I documenti e gli output EJ200 restano su AWS EU; non copiarli
  nella repository o fuori dall'ambiente autorizzato.»* Quindi:
  - nessuna copia della conoscenza EJ200 sul PC (quella scaricata per errore è stata cancellata
    il 21-11-2026);
  - **un ciclo EJ200 non si prova sul PC**, perché il risultato finirebbe in `runs\`. Va
    provato dentro AWS, per esempio con la v2 dietro il gateway QA;
  - **eccezione dal 27-11 sera:** l'utente ha l'autorizzazione scritta di chi decide sulla
    sicurezza per provare EJ200 sul suo PC. Si prova **solo** con `prova-ej200`: catalogo e
    testi letti da S3, testi usati in una cartella temporanea cancellata alla fine, niente in
    `runs\`, niente transcript, a schermo e a Claude solo esiti e conteggi; Copilot non legge
    niente di EJ200;
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
- **Regole dell'utente (ripetute in ogni giro, scritte qui il 27-11 perché valgono sempre):**
  - mai scrivere nel repository, nei documenti o in chat: nome del bucket, account, profilo
    AWS, host, nome utente Windows o matricola (compaiono nei percorsi delle foto), nomi di
    colleghi, codici veri di manuali, numeri DR, serial o part number, codici di ciclo,
    contenuti EJ200, nome dell'azienda o del repository aziendale. I manuali si chiamano
    M1…M6; le impronte di 8 caratteri vanno bene;
  - mai chiedere né guardare: `runs/mutazioni/errori.yaml`, `data/errori-nascosti.yaml`, le
    stampe nascoste, i `report.md`, i `prestazioni.md` interi, i `transcripts`,
    `runs/manuali-da-ingestionare.txt` (di quello si fotografa solo lo schermo);
  - prima di ogni commit: `uv run pytest -q`, `ruff check`, `ruff format --check`,
    `mypy src`; nel diff niente numeri di 6 o più cifre (anche le date scritte tutte attaccate),
    né le sigle dei codici veri (le lettere G-E-K e T-E-C-P-R scritte attaccate); le impronte
    vanno bene;
  - italiano molto semplice; `DOCUMENTAZIONE.md` si aggiorna nello stesso commit quando cambia
    il comportamento; in `COPILOT.md` le parti fatte si tolgono;
  - **Copilot sempre in Ask**: nelle foto è spesso su **Agent con «Allow all»** (anche il 27-11,
    tre volte): ricordarlo all'utente ogni volta che si vede.
- **Eccezione del 27-11 sera: `docs/CONFRONTO_V1_14_CICLI.md`.** L'utente l'ha messo nel
  repository (i risultati della v1 in QA sui 14 cicli noti, dai CSV della v1, e il testo
  originale delle 14 stampe, con codici di ciclo, manuali, task, schede, macchine). Claude ha
  avvisato che il repository è pubblico; l'utente ha risposto che **il suo responsabile ha
  detto che può stare nel repository pubblico** e di usarlo. Quindi: il file resta, è un dato
  (non si modifica, non si toglie), Claude lo legge per le analisi. **Le altre regole non
  cambiano:** in tutto quello che scrive Claude (codice, altri documenti, chat, errori noti)
  restano impronte, numeri di operazione e descrizioni generiche; il controllo del diff vale
  per tutti i commit che non aggiungono quel file.

---

## 8. Come funziona la v2, in breve

Più dettagli in `MIGLIORIE.md` e `DOCUMENTAZIONE.md`.

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
| `Accept as is` / `Use as is` (va bene così) | ERRATO: un ciclo di riparazione non dovrebbe esistere | si fermano |
| `Reject` (scarta) | ERRATO | si fermano |
| `Repair` e `Accept as is` insieme (condition diverse) | CORRETTO, la parte `Accept as is` si salta | solo la `Repair` come riferimento |

È la regola della v1, confermata dall'utente il 22-11-2026 (prima, dal 21-11, `Accept as is`
dava solo un WARNING).

**Serial number e condition sono facoltativi** (decisione del 22-11-2026, per rendere il
frontend meno macchinoso):

| Cosa c'è | Cosa succede |
|---|---|
| serial number dato da chi carica | si usa quello |
| serial number non dato, ma scritto nella stampa («APPLY ON S/N …») | si prende dalla stampa |
| nessun serial number | WARNING `DR_NON_VERIFICATA`; gli altri controlli vanno avanti, senza la procedura DR |
| condition non data, una sola recommendation | si usa quella |
| condition non data, più recommendation tutte `Repair` | valgono tutte |
| condition non data, recommendation diverse (`Repair` e `Accept as is`/`Reject`) | WARNING `DR_NON_VERIFICATA`; si va avanti con le sole `Repair` |
| condition non data, nessuna `Repair` | ERRATO, ciclo bloccato |

Il frontend può quindi togliere l'obbligo delle due domande (oggi il pulsante Confirm resta
spento se sono vuote: sezione 9); finché le fa, i valori dati si usano come prima. Il serial
number è scritto solo in alcune stampe; la condition mai.

## 9. Il frontend della v1

Visto dalle foto e dal codice (risposte di Copilot, 22-11-2026).

**Dove sta.** Non nel repository della v1: è nel repository del frontend del collega. La
pagina con le domande è `CycleValidationPage.tsx`, i risultati li mostra
`CycleValidationResultDisplay.tsx`. L'indirizzo del backend viene dalla variabile
`VITE_BACKEND_URL`.

**Percorso.** «Which cycle do you want to validate?» → *Civil cycle (DR/MOS)* oppure *EJ200
cycle (military)*.

- Civile: `GET /cycle_validation/flow/start?session_id=…`, poi «Devi validare un ciclo DR?»
  → `POST /cycle_validation/conversation` con `{answer: "yes"|"no"}`. Se è DR, chiede
  `Serial Number (S/N)` e `DR Condition Numbers` e li manda con un secondo
  `POST /cycle_validation/conversation` `{dr_serial_number, dr_condition: [1, 2]}`.
- Poi il PDF: `POST /cycle_validation/upload?session_id=…`, form con `file`, `is_dr`,
  `dr_serial_number`, `dr_condition` (qui come testo `"1,2"`).
- **Il pulsante Confirm resta spento se serial number o condition sono vuoti.** Per togliere
  le due domande il collega deve cambiare questo (messaggio pronto in `COPILOT.md`). La v2 è
  già pronta: accetta i due campi vuoti in tutti e due i passi.
- EJ200: rotte sotto `/cycle_validation/ej200/…`; l'upload ha solo `file`.
- Altre rotte: elenco, apertura, salvataggio e cancellazione delle chat
  (`/cycle_validation/sessions…`), pollice su/giù (`POST /cycle_validation/feedback`).
  L'header `sso` porta l'utente.

**Risposta letta.** `{state, result: {file_name, payload, error}, error, error_info,
finished_at, job_id}`. Dal `payload`:

- in alto: `cycleCode`, `cycleDescription`, `operationType`, `repairCode`,
  `cycle_errors_count`, `_pipeline_errors`;
- `sources`: `repairCode`, `DRCase`, `manual`, `serialNumber`, `task`, `sourceFeedback`. La
  colonna *Type* dice «DR Case» se la riga ha `DRCase`, altrimenti «Manual»;
- `operations`: `operationNumber`, `operationDescription`, `repairCode`, `targaCResp`,
  `taskCodeCited`, `scheda.tabNumber`, `scheda.task`, `scheda.class` e i quattro feedback;
- **non legge** `cycle_status` né `drRecommendationFeedback`. `_pipeline_errors` va nel
  riquadro «Pipeline issues»;
- l'etichetta «MOS Cycle», «DR Cycle», «EJ200 Cycle» la sceglie il frontend dal percorso.

**Bollini** (funzione `feedbackSeverity`, guarda solo l'inizio del testo, maiuscole non
contano):

| Testo | Bollino |
|---|---|
| vuoto, oppure esattamente `N/A` | `N/A` grigio |
| comincia con `error` | `Error` rosso |
| comincia con `warning` | `Warning` giallo |
| comincia con `no error` | `OK` verde |
| qualsiasi altro testo (anche `N/A - motivo`) | `Info` azzurro |

**Intestazione.** «Validation Failed» se `state` è `failed`. «Completed with Errors» se
`cycle_errors_count > 0` oppure `_pipeline_errors` non è vuoto. Altrimenti «Validation
Passed», **anche con dei Warning**. Il «N errors» in alto è `cycle_errors_count`; il «1 err»
vicino all'operazione lo conta il frontend (feedback dell'operazione che cominciano con
`error`). Nella v1, quando il DR ferma il ciclo, `cycle_errors_count = 1`.

**Download.** Un CSV fatto dal browser (`cycle_validation_<nome>_<data>.csv`): metadati, fonti,
operazioni. Il backend non è chiamato.

**Tempi massimi.** Frontend: 300 s per le chiamate normali, **660 s per l'upload**. Backend v1:
gunicorn con `--timeout 600`. Un commento parla di 650 s nel gateway nginx, ma nei file non
c'è. **La v2 deve finire una validazione in meno di 10 minuti.** Misurato il 22-11-2026 sui
cicli DR da 9 operazioni: al massimo 131 s (con la lettura del PDF fatta dal modello), di solito
12-30 s; 0 s quando nessun controllo chiama il modello (ciclo bloccato, o DR senza riferimento).
Un ciclo MOS lungo è ancora da misurare.

**«N/A, non verificato per EJ200».** Nasce nel backend v1 (`ej200/validation.py`) e va in
`schedaFeedback` quando un'operazione EJ200 ha una scheda. Il frontend lo mostra `Info`
azzurro perché non è esattamente `N/A`.

**Come la v2 si adatta** (dal 22-11-2026, `report/legacy_payload.py`):

- `N/A` esatto (grigio) quando il campo manca o il controllo non è partito perché il DR ha
  fermato il ciclo; `N/A - motivo` (azzurro) quando il controllo è escluso per una regola o
  per il tipo di ciclo, come fa la v1 con le schede EJ200;
- l'esito DR va nella riga della fonte che cita il DR (con `DRCase` e `serialNumber`); se
  nessuna fonte lo cita, si aggiunge una riga DR in cima alle fonti. Se la fonte ha anche un
  suo avviso, si mostra prima il più grave e poi l'altro, separati da ` | `;
- la scheda ha i campi che il frontend mostra, riempiti come nella v1: `tabNumber` = il codice;
  `task` = il codice dopo «SP.ORIG.» nei cicli civili, vuoto negli EJ200; `class` vuoto (la v2
  non la legge).

**La scheda nella v1** (risposta C13). Civile: il modello legge solo la riga dopo `SCHEDA`
(prompt `cycle_extraction.yaml`): `tabNumber` il codice, `task` il codice sulla stessa riga
(senza «SP.ORIG.»/«SP.FIAT»), `class` la lettera dopo «Class». I task dopo `SCHEDA` non vanno
in `taskCodeCited`; se manca il codice ma c'è un task, `check_task_codes` sposta il task in
`taskCodeCited` e la scheda diventa vuota. EJ200 (`ej200_cycle_extraction.yaml`, `_scheda`):
solo `tabNumber`; `task` e `class` sempre vuoti; le righe SCHEDA si tolgono dalla descrizione.

**DR fermo nella v1** (risposta C14, `DR_source_validation`, `process_single_cycle_bytes`):

- il motivo va in `sources[0].sourceFeedback`, in inglese, uno per caso (`Accept as is`,
  `Reject`, nessuna recommendation: «Error found: no matching DR data found…», serial number e
  condition mancanti). Il frontend lo mostra nella riga «DR Case»;
- ogni operazione riceve `fallbackFeedback: "Error during validation."` (il frontend non lo
  mostra); `_pipeline_errors` riceve un messaggio generico «Attenzione: validazione
  bloccata…»;
- `DRCase` lo legge il modello dalla prima operazione (la NOTE, di solito 005/010);
  `serialNumber` è quello scritto dall'utente, in maiuscolo (sovrascrive quello letto dal PDF).
  Per un DR serial number e condition sono obbligatori (`_enforce_dr_policy`);
- **se il modello non trova il `DRCase`, la v1 salta del tutto la validazione DR.** La v2 no:
  senza riferimento dà WARNING `DR_NON_VERIFICATA`.

**La v1 non è un riferimento.** Dà errori falsi (su un ciclo EJ200, due «Error» con valori che
rispettano il limite) e giudizi diversi per casi uguali. Per sapere se la v2 ha ragione serve
chi conosce i cicli.

### Come si prova e si pubblica la v1 (risposte C18-C20, 22-11-2026)

**L'utente:** in locale si avviano da Run and Debug centralizer, login e il backend da provare;
quando funziona, push su `develop` (QA) e poi su `main` (produzione).

**In locale.** Un solo `launch.json`, nella radice del workspace. La configurazione composta
«CV» avvia insieme login, backend della v1 e frontend; prima lancia il task «Centralizer
prerequisites» (`tasks.json`, lo script che apre i tunnel verso OpenSearch). Copilot (22-11
notte): lo script `scripts\ensure-opensearch-tunnels.ps1` non c'è nel workspace, è solo
descritto in una guida; comunque apre solo OpenSearch, non Redshift.

| | Backend v1 | Login | Frontend (centralizer) |
|---|---|---|---|
| Comando | debugpy, modulo `uvicorn app_backend:app --reload --port 8003` | debugpy, `uvicorn app_backend:app --reload --port 8000` | `npm run dev` (vite) |
| Cartella | `app_cycle_validation` | la cartella del login | la cartella del frontend React |
| Python | `.venv` della cartella | `.venv` della cartella | — |
| Porta | 8003 | 8000 | 3000 |
| Variabili nel launch | `AWS_PROFILE` | `AWS_PROFILE`, `REDIRECT_URI`, `FRONTEND_URL` | nessuna (`.env.development`) |
| Configurazione | all'avvio `load_secrets("<secret di ambiente>")` copia le chiavi di un secret AWS in `os.environ` | allo stesso modo, con il suo secret | `.env.development` |

`VITE_BACKEND_URL` è vuota: il frontend chiama indirizzi relativi e il proxy di vite manda
`/login` alla porta 8000 e `/cycle_validation/` alla 8003. Per provare la v2 basta avviarla
sulla porta 8003 al posto della v1.

Variabili della v1 (solo i nomi, da `config.py`, `app_backend.py`, `logger.py`): API e log
(`API_MAX_WORKERS`, `API_INCLUDE_TRACEBACK`, `FRONTEND_URL`, `ENVIRONMENT`, `LOG_LEVEL`);
OpenSearch e RAG (`OPENSEARCH_HOST`, `OPENSEARCH_KNOWLEDGE_BASE_INDEX`, `RAG_TOP_K`,
`CHUNK_*`); modello (`EMBEDDING_*`, `LOCAL_MODEL_*`, `MODEL_ID`, `BEDROCK_MODEL_ID`, costi dei
token); S3 e AWS (`BUCKETNAME`, `REGION_NAME`, `SECRET_NAME`, `RAW_PATH`, `TM_STRUCTURED_PATH`,
`SP_STRUCTURED_PATH`, `DR_STRUCTURED_PATH`, `CA_BUNDLE_PATH`); EJ200 (`EJ200_OPENSEARCH_INDEX`,
`EJ200_CATALOG_KEY`, `EJ200_VALIDATION_ENABLED`); accesso (`AUTH_INTROSPECT_URL`,
`AUTH_CLIENT_ID`, `AUTH_CLIENT_SECRET`, `AUTH_EXPECTED_CLIENT_ID`, `AUTH_SSO_CLAIM`,
`AUTH_PERMISSIONS_BUCKET`, `AUTH_PERMISSIONS_KEY`, `AUTH_CACHE_TTL_S`).

**Costruzione e pubblicazione.** `buildspec.yml` sta nella radice del repository aziendale e fa
`cd app_cycle_validation`, poi `docker build`: **costruisce solo la v1**. La v2 ha un suo
Dockerfile, ma oggi nessuno lo costruisce: un push della v2 su develop o main non cambia il
servizio. Il Dockerfile della v1: Python `3.14.10-slim`, copia `ca-certificates.crt` (lo prende
la macchina di CodeBuild), installa AWS CLI, torch solo CPU, `requirements.txt` con la libreria
in `vendor/`, gunicorn con 1 worker sulla porta 8000. Immagine in ECR con due tag: i primi 7
caratteri del commit e `latest`. Nel buildspec non c'è nessuna regola sui branch: quale branch
fa partire la build si decide in CodeBuild/CodePipeline, fuori dal repository (la documentazione
dice develop = QA, main = produzione). Le variabili di CodeBuild: `AWS_REGION`,
`AWS_ACCOUNT_ID`, `ECR_REPO_NAME`, `CODEBUILD_RESOLVED_SOURCE_VERSION`. La configurazione non è
nell'immagine: arriva dal secret letto da `load_secrets`, con lo stesso nome nei due ambienti
(cambia l'account AWS).

### Come si pubblica la v2 in QA (deciso il 22-11-2026, notte)

- **Il comando `cycle-validation qa`** (`src/cycle_validation/deploy.py`) gira sul PC nella
  cartella della v2 e legge la v1: dal suo Dockerfile la riga `FROM` e le istruzioni sui
  certificati; dai requirements il `.whl` di `chatbot_ai_sdk` con le aggiunte; dal codice il
  nome del secret di ambiente, il database e la tabella (come il comando `macchine`). Scrive il
  Dockerfile della copia aziendale con le righe `ENV` (`CV_ENV_SECRET`,
  `MACHINES_SOURCE=diretta`, `REDSHIFT_DATABASE`, `MACHINES_QUERY`, `CYCLE_VALIDATION_CONFIG`,
  i due puntatori della conoscenza, `EJ200_VALIDATION_ENABLED`, `API_INCLUDE_TRACEBACK=false`),
  copia `data/settings.yaml` in `config/settings.azienda.yaml` e cambia nel buildspec
  `cd app_cycle_validation` in `cd app_cycle_validation_v2`. Stampa il Dockerfile con i tre
  valori aziendali coperti. `--torna-alla-v1` rimette il buildspec com'era.
- **Prima prova del comando (22-11 notte):** dalla v1 base
  `public.ecr.aws/docker/library/python:3.14.10-slim` e 2 istruzioni sui certificati (`COPY
  ca-certificates.crt /etc/ssl/certs/ca-certificates.crt` e un `ENV` con `SSL_CERT_FILE` e
  `REQUESTS_CA_BUNDLE`); libreria 0.4.0rc2 `[auth]`; secret, database e tabella trovati; modello
  `eu.anthropic.claude-haiku-5-5`. Il buildspec copia il certificato della macchina di build con
  `cp ... app_cycle_validation/ca-certificates.crt` **prima** del `cd`: la prima versione del
  comando cambiava solo il `cd`, e il certificato sarebbe finito nella cartella della v1
  (build della v2 fallita su `COPY ca-certificates.crt`). Corretto: ora cambia ogni percorso
  con la cartella. Le impostazioni del PC avevano `save_transcripts: true`: nella copia per il
  servizio il comando lo spegne.
- **Seconda prova (22-11 notte): giusta.** `buildspec: percorsi spostati sulla v2: 1` (la copia
  del certificato), tutte le righe del buildspec con `app_cycle_validation_v2`; impostazioni
  copiate con i testi su disco spenti; Dockerfile come previsto. Da salvare sul ramo feature.
- **Pulizia del progetto (22-11 notte).** Tolti dal codice due pezzi mai usati
  (`RemoteKnowledge.structured`, il contatore `text_reads` di EJ200). `COPILOT.md` riscritto corto:
  solo il punto in cui siamo, cosa manca e i blocchi; sezioni nuove: 2 Aggiornare, 3 Salvare, 4
  prove in locale, 5 domande e messaggio, 6 QA (il 23-11 riordinato: 1 cosa fare, 2 blocchi, 3 persone, 4 QA). Il blocco
  Aggiornare ora toglie sul PC i file che nel repository personale non ci sono più (prima
  `robocopy /E` copiava e basta, quindi i file vecchi restavano e finivano nel commit) e copia
  anche `eval/varianti`, `eval/modelli` e `.gitignore`.
- **Perché così:** il repository personale è pubblico; la configurazione resta quella della v1
  (stesso secret di ambiente, stesso nome in QA e in produzione); nessun valore nuovo da
  chiedere a nessuno.
- **Il Dockerfile del repository personale** resta generico (Python 3.14, senza certificati e
  senza libreria di accesso): in azienda vale quello scritto da `qa`. Il blocco di
  aggiornamento ora copia anche `config/`, `prompts/`, `pyproject.toml`, `uv.lock`, `README.md`.
- **EJ200 spento al primo passaggio:** all'avvio la v2 scarica la conoscenza pubblicata e, se un
  file non è valido, non parte. La conoscenza EJ200 non si può controllare dal PC (resta su
  AWS), quindi prima si prova il civile, poi si accende EJ200 (COPILOT 4, punto 3).
- **Produzione:** passa alla v2 quando il ramo arriva su `main`. Prima serve una prova QA
  riuscita.
- **Da verificare in QA:** che il ruolo del servizio possa usare Bedrock con il modello delle
  impostazioni e leggere i prefissi della conoscenza v2 su S3; che `uvicorn.workers` ci sia
  nella versione di uvicorn installata.

### Accesso ai cicli militari (22-11-2026, risposte C15-C17)

Cosa vuole l'utente: chi entra ed è autorizzato ai cicli militari vede i pulsanti civile (MOS,
DR) e militare (EJ200); gli altri vedono solo MOS e DR. Una sola pipeline per i tre.

- **Pipeline:** è già la stessa (`run_validation`). Cambiano solo le impostazioni del profilo:
  EJ200 cita pubblicazioni intere, le schede EJ200 non si verificano, la conoscenza EJ200 resta
  su AWS EU, il DR aggiunge la recommendation che blocca.
- **Come fa oggi il frontend (C15):** il pulsante militare (`ScopeChooser`) compare solo se
  l'utente è nella lista `cv_ej200` o `all` di `permissions.json` su S3. Il frontend la riceve
  da `GET {BACKEND_URL}/login/permissions` (servizio di login, `get_s3_permissions`, cache 10
  minuti, solo le voci dell'utente verificato dal token). Non viene dai gruppi SSO. Chi è in
  `cv_ej200` vede anche il civile. Quello che l'utente vuole **c'è già** nel frontend.
- **Cosa manda il frontend (C16):** solo l'header `sso` (nome utente), `Content-Type` e il
  cookie di sessione HttpOnly con il token. **Nessun header con i permessi.** Chiavi dei
  servizi: `all`, `cv`, `cv_ej200` e altre di altri progetti.
- **Come controlla la v1 (C17):** middleware della libreria interna `chatbot_ai_sdk` (file
  `.whl` in `vendor/`): `AuthMiddleware` con `IntrospectionValidator` (token del cookie,
  pubblica solo `/cycle_validation/health`) e `ServiceAccessMiddleware` (servizi `cv`,
  `cv_ej200`; sotto `/cycle_validation/ej200` solo `cv_ej200`; permessi da
  `S3PermissionsSource.from_env()`). In più `Depends(current_user)` sul router EJ200. L'utente
  viene dal token (`current_user(request).sso`), non dall'header `sso`. Risposte: 401 token
  mancante o non valido; 403 senza permesso; 503 se il provider d'identità o
  `permissions.json` non rispondono.
- **Come controlla il token (C19).** In `app_backend.py`:
  `AuthMiddleware(validator=IntrospectionValidator(AuthSettings.from_env()),
  public_paths={"/cycle_validation/health"}, allowed_origins=[FRONTEND_URL])` e
  `ServiceAccessMiddleware(..., permissions=S3PermissionsSource.from_env())`. Il token arriva
  dal cookie HttpOnly del login (vale anche `Authorization: Bearer`); l'`Origin` deve essere
  `FRONTEND_URL`. `IntrospectionValidator` chiede all'identity provider SSO se il token è
  valido (`AUTH_INTROSPECT_URL` e gli altri `AUTH_*`). **In locale è uguale**: niente token
  finti. `permissions.json` si legge sempre da S3 (`AUTH_PERMISSIONS_BUCKET`,
  `AUTH_PERMISSIONS_KEY`); se non si legge, 503.
- **La libreria (prova sul PC, 22-11):** `chatbot_ai_sdk.auth.middleware.AuthMiddleware(app,
  validator, public_paths, allowed_origins)` (tutto protetto per default, tranne i preflight
  CORS; l'utente va in `request.state.user`); `chatbot_ai_sdk.auth.middleware.current_user(request)
  -> VerifiedUser`; `chatbot_ai_sdk.auth.validator.IntrospectionValidator(settings, *,
  transport, clock)`. Variabili lette direttamente: `AUTH_CACHE_TTL_S`, `ENVIRONMENT`,
  `LOG_LEVEL`.
- **Le versioni della libreria (22-11 notte).** In `vendor` della v1 ci sono
  `chatbot_ai_sdk-0.3.0` e `chatbot_ai_sdk-0.4.0rc2`. I requirements della v1 (quindi il
  servizio) usano `./vendor/chatbot_ai_sdk-0.4.0rc2-py3-none-any.whl[auth]`. Solo la 0.4.0rc2
  ha `ServiceAccessMiddleware` e `S3PermissionsSource`; la 0.3.0 no. Sul PC il `.venv` della
  v1 ha ancora la 0.3.0 (non aggiornato dai requirements): il backend v1 in locale con quel
  `.venv` non ha i pezzi che importa. La v2 installa la riga dei requirements della v1
  (`DOCUMENTAZIONE.md`, sezione 13.7) e nel Dockerfile farà lo stesso.
- **Come la v1 usa la libreria (C21).** Import: `from chatbot_ai_sdk.auth import
  AuthMiddleware, AuthSettings, IntrospectionValidator, current_user, ServiceAccessMiddleware,
  S3PermissionsSource` (in `routes.py` anche `VerifiedUser`). Chiamata:
  `app.add_middleware(ServiceAccessMiddleware, service_keys={"cv", "cv_ej200"},
  path_service_keys={"/cycle_validation/ej200": {"cv_ej200"}},
  permissions=S3PermissionsSource.from_env())`. Le rotte civili leggono solo
  `username = current_user(request).sso`; il router EJ200 ha
  `dependencies=[Depends(current_user)]` e usa `user.sso`. `VerifiedUser` ha `sso` e
  `client_id`. **Nessuna rotta legge i servizi dell'utente** e non c'è `request.state` nel
  codice: il permesso lo controlla solo il middleware.
- **Prima prova completa in locale (22-11 notte).** Dopo aver messo `FRONTEND_URL` =
  `http://localhost:3000` nella configurazione della v2, dal frontend: sessioni, conversazione
  e caricamento rispondono 200, il ciclo MOS di esempio esce `Validation Passed` in circa 20
  secondi. Il frontend chiede spesso `POST /cycle_validation/sessions`: è il suo aggiornamento
  dell'elenco, non un errore.
- **Prima partenza della v2 in locale (22-11 notte).** Con la libreria 0.4.0rc2 `[auth]`, il
  secret di ambiente della v1 in `CV_ENV_SECRET` e `MACHINES_SOURCE=nessuna` la v2 parte sulla
  porta 8003. Aperta direttamente nel browser risponde 401 `Login richiesto.` e nel log
  `chatbot_ai_sdk.auth.middleware ... Request rejected on /: no access token`: l'accesso
  funziona come nella v1. La prova vera passa dal frontend (porta 3000) dopo il login.
- **Cosa fa la v2 (dal 22-11 sera, `api/auth.py`).** `API_AUTH=sdk` (scelto da solo se c'è
  `AUTH_INTROSPECT_URL`, cioè con il secret della v1): gli stessi tre pezzi della v1 (token,
  permessi, utente) con gli stessi parametri; l'utente delle sessioni e dei feedback è
  `current_user(request).sso`. I servizi non arrivano alle rotte, quindi la v2 li deduce dal
  percorso, già controllato dalla libreria. Conseguenza: le rotte nuove
  `validation/options` e `validation/upload` non offrono il militare; i cicli militari passano
  da `/cycle_validation/ej200/...`, come nel frontend di oggi. Senza la libreria installata la
  v2 non parte (meglio che partire senza controllo). `API_AUTH=header` resta per le prove.
- La libreria nella v2: `uv pip install` del `.whl` della v1 (`DOCUMENTAZIONE.md`, sezione 13.7). `uv run` la
  lascia; `uv sync` la toglierebbe (va reinstallata).
- `GET /validation/options` della v2 mostra il pulsante militare solo a chi ha `cv_ej200` o
  `all` (per un frontend futuro; quello di oggi usa `/login/permissions`).

## 10. Stato delle prove (22-11-2026)

- **24-11, cicli dell'insieme grande (`eval scegli`, COPILOT 3.2):** sotto
  `ProgettoDocumenti` ci sono 2600 PDF; 29 sono cicli PVRM320 diversi, gli altri 2531 sono
  manuali o altri documenti. Scelti 23: i 10 noti e 13 veri (dalle 9 alle 21 operazioni, quasi
  tutte confrontabili). Lasciati fuori 1 EJ200 e 5 con poche operazioni confrontabili. Il
  grande è piccolo: 23 cicli, nessun limite da mettere.
- **24-11, copie cieche (`eval muta`, seme 1, primo giro):** 16 cicli letti (13 veri e 3
  giusti), 32 copie: `numero_una_lingua` 11, `numero_manuale` 3, `negazione_una_lingua` 11,
  `task_inesistente` 7. Il tetto di 2 copie per ciclo si era riempito (16 × 2) e i tipi del
  codice, che servono solo come controllo, prendevano metà del posto. Cambiato: 6 copie per
  ciclo (`--per-ciclo`) e al massimo 5 per tipo del codice. Da rifare con lo stesso seme.
- **24-11, MOS e DR nelle prove:** `eval scegli` lasciava fuori solo gli EJ200, quindi nella
  lista potevano esserci stampe DR; `eval prova` le avrebbe lanciate tutte come MOS, fermandole
  con «Modulo sbagliato» (ciclo non eseguito = variante scartata). Ora `eval prova` sceglie il
  profilo ciclo per ciclo dalla testata (`--profile auto`, predefinito) e `eval scegli` scrive
  MOS o DR accanto a ogni ciclo. A0 da rifare per vedere quanti DR ci sono.
- **24-11, secondo giro (dopo le correzioni):** A0 di nuovo 23 cicli, **MOS 17, DR 6** (i 6 DR
  sono tra i 13 veri). A1, seme 1: 16 cicli, **31 copie**: `numero_una_lingua` 5,
  `numero_manuale` 3, `negazione_una_lingua` 18, `task_inesistente` 5. Mai visti per il
  modello: 21. `numero_manuale` resta a 3 anche con 6 copie per ciclo: il limite ora sono le
  operazioni adatte (un numero nelle due lingue e nel testo del task del manuale), non il
  tetto. Un seme nuovo non ne aggiunge (stesse operazioni adatte). Per misurare bene
  `numeri_manuale` servono errori di quel tipo nel gruppo nascosto.
- **24-11, prime due prove `base` sul piccolo (14:41 e 14:47):** visti trovati 8 e 7 su 12,
  costo 0,16 e 0,14 $. Due problemi, corretti lo stesso giorno: (1) le 31 copie cieche uscivano
  come cicli «vero» (`mai visti 0 su 0`): `eval muta` le scriveva con `write_text`, che su
  Windows mette `\r\n`, quindi l'impronta del file non era quella di `errori.yaml`. Ora le
  scrive byte per byte ed `eval prova` toglie i `\r` prima dell'impronta (le copie già fatte
  vanno bene). Nelle due prove 4-5 copie avevano un ERRATO (contato come «da verificare»).
  (2) 1 falso errore su `04ecaabe` op. 050, la stampa giusta di f355dc3c: è P7 («4 volte»
  contro «3 volte» dell'SPM). Nuovo campo `in_attesa` in `errori-noti.yaml`: un ERRATO lì non
  conta finché P7 non ha risposta. Le due prove si cancellano e la base si rifà.
- **24-11 ore 14:57, terza prova `base`:** copie riconosciute, ma mai visti per il modello
  **0 su 21** e per il codice **4 su 10**; visti 8 su 12, 0 falsi errori, 0,16 $. Causa: il
  controllo di integrità confrontava la copia con il PDF originale, dove il valore cambiato non
  c'è, e declassava ogni ERRATO a WARNING `ESTRAZIONE_NON_CONFERMATA`. Le negazioni tolte non
  aggiungono valori, quindi passavano il controllo: per loro lo 0 su 18 sembra un limite vero
  del modello (da rivedere dopo la base corretta). Ora per le copie il controllo si salta
  (`RunRequest.check_integrity`). Anche questa prova si cancella.
- **24-11 ore 15:08, prima prova `base` valida (piccolo):** visti **8 su 12**; mai visti per il
  modello **1 su 21**; per il codice **9 su 10**; **0 falsi errori** (op. 050 di 04ecaabe «in
  attesa»); 1 ERRATO da verificare (5ff17062 op. 050); 0,17 $. Grande distanza tra visti (67%)
  e mai visti per il modello (5%): sulle negazioni tolte in una lingua sola il modello quasi
  non vede l'errore. Per capire il perché senza vedere gli errori, il report dà ora sui
  mancati mai visti esito e motivo contati per tipo.
- **24-11 ore 16:09, campagna partita** (dopo aver azzerato le prove): le due prove `base`
  Haiku sul piccolo sono uguali: visti **8 su 12**, mai visti per il modello **2 su 21**, per il
  codice **9 su 10**, **0 falsi errori**, 1 ERRATO da verificare, 0,16 $ ciascuna (circa 5
  minuti a prova). È il riferimento stabile della base Haiku.
- **24-11 ore 17:17, campagna Haiku sul piccolo quasi finita** (13 prove, manca la seconda di
  `concorrenza_12`): nessuna variante si tiene; decisioni e considerazioni nel registro di
  `MIGLIORIE.md`. I 12 visti sono identici in tutte le prove (8 sempre, 4 mai). Il costo per
  ciclo usciva `0.00 $` (circa 0,004 $ arrotondato): ora i report lo danno con 4 decimali.
- **24-11 sera, campagna fermata dall'utente** per sistemare prima le migliorie. Perché il
  modello manca le negazioni: il prompt chiede solo «la descrizione è coerente con il
  manuale?» e una lingua giusta copre l'altra. Nuova variante `lingue_separate`
  (`agent.separate_languages`), aggiunta alla campagna; la base non cambia, quindi le 13 prove
  restano valide. `numeri_manuale` rimandata: troverebbe le copie «numero del manuale» per
  costruzione (vedi MIGLIORIE 7.3).
- **24-11 sera, rianalisi da capo (richiesta dell'utente: «metriche molto basse»).** Cosa non
  andava e cosa è cambiato:
  1. il numero in evidenza («19 su 43, 44%») sommava cose diverse (visti, mai visti per il
     modello, controlli del codice): ora il report e la riga finale danno separati visti, mai
     visti per il modello, falsi errori; il totale solo per ultimo;
  2. 2 errori visti oggi non si possono trovare (c5ff3cd6 030 = P6; f355dc3c 040 = documento
     mancante): ora sono `in_attesa` e fuori dal conto. Visti contati: 10 (la base ne trova 8;
     mancati sempre 298bc28e 035 e f355dc3c 010);
  3. i mai visti per il modello erano 21, 18 dello stesso tipo: due tipi nuovi di copie
     cieche, `negazione_due_lingue` e `limite_invertito` (si vedono solo con il manuale);
  4. i 14 WARNING per ciclo non si sapeva da dove venissero: ora il report li conta per motivo;
  5. per i visti mancati il riepilogo dà l'ultimo esito (solo esito e motivo);
  6. due migliorie sul metodo: `lingue_separate` e `elementi_uno_per_uno`;
  7. domanda nuova P9: 5ff17062 op. 050, ERRATO in tutte le prove ma non nella lista.
  Le copie cieche cambiano: si azzera e si rifà tutto (COPILOT, tappa 2).

Con Bedrock Haiku 5.5 e la conoscenza di prova:

- **MOS:** terzo ciclo con 7 corretti, 16 warning, 0 errati, 14 N/A, 0,0058 USD. I warning
  vengono dai manuali dei motori che mancano e dalle macchine attive non collegate.
- **DR:** le tre condition del ciclo vero danno l'esito atteso.
  - `Repair`: 5 corretti, 0 errati, 0,006-0,011 USD, 9-11 chiamate al modello per prova.
  - `Accept as is`: provata il 21-11 con la regola di allora (WARNING); dal 22-11 dà ERRATO
    e ciclo bloccato. Da riprovare sul PC insieme al DR senza serial number e condition.
  - Descrizioni: 4 CORRETTO, 5 WARNING `EVIDENZA_NON_TROVATA`; la scheda dell'op. 050 non è
    tra le 94 schede.
- **EJ200:** mai provato con i servizi veri (va fatto dentro AWS).
- **Cicli MOS «con errori» (22-11):** sono 3 cicli diversi, ognuno in due cartelle di
  `ProgettoDocumenti`; si chiamano con le prime 8 lettere dell'impronta SHA-256. Sono stampe
  modificate a mano: l'editor mette in fondo al PDF le righe toccate e a volte toglie loro le
  colonne TARGA e NUM. OPER. Dal 22-11 la lettura rimette le righe in ordine di posizione e
  attacca all'operazione in corso le righe senza colonne (solo nelle pagine rimesse in
  ordine).
  - **Errori trovati con `confronta`** (stampa giusta contro «con errori»):
    - `298bc28e` (giusta `4e64d49a`): op. 005 un codice cambiato nella descrizione; op. 035
      parole cambiate nella descrizione.
    - `c5ff3cd6` (giusta `8bdb25d5`): op. 030 scheda tolta; op. 040 un numero cambiato.
    - `f355dc3c` (giusta `04ecaabe`): op. 010 tre numeri cambiati; op. 030 numeri e parole
      cambiati; op. 040 una lettera cambiata (la classe); op. 050 una frase sostituita (dice
      il contrario della giusta).
  - **La v2 non ne trova nessuno** (prova del 22-11 sera, righe in ordine): 0 errati in tutti
    e tre. Motivo: i manuali citati non sono nella conoscenza di prova (fonti `FONTE_ASSENTE`,
    descrizioni non confrontate). La scheda tolta esce N/A come nella v1 (P6). Per misurare la
    v2 su questi errori servono quei manuali nella conoscenza.
  - Gli `ERRORE_TECNICO` (7-9 per ciclo) sono tutti sulla targa: sul PC il registro delle
    macchine non è collegato. Dal 22-11 c'è il comando `macchine`
  - **Lettura di tutte le stampe** (esempi MOS e DR e cartelle `cicli MOS`, `leggi --breve`,
    22-11): **il parser le legge tutte**, tranne `8e6c9c8d` che non ha il layout PVRM320 (la
    legge il modello). Il riordino fa leggere `298bc28e`, `38960731`, `5ff17062`, `f355dc3c`
    (e la stampa con «AREE RIPARATE…»); il titolo «OPERAZIONE EVENTUALE» passato
    all'operazione dopo fa leggere `b1261d11` e `d206cc9c`. Dove il riordino non serviva per
    leggere (`c5ff3cd6`, `e9b74c84`, `298bc28e`) le letture con e senza riordino sono uguali.
  - **Stampe DR** (`22f586bb`, `895167b9`): tutte le pagine rimesse in ordine, stesse 9
    operazioni, 4 differenze. Il riordino **aggiunge testo che prima si perdeva**: nella 005
    il testo della procedura (riferimento alla SA e al caso DR), nella 030 «BLOW THE PART WITH
    CLEAN AND DRY AIR». Erano righe in fondo al PDF. Dal 22-11 pomeriggio nelle descrizioni si
    tolgono gli asterischi di cornice e le righe di soli segni (trattini, «/ .»).
  - **Caratteri strani nei blocchi** («À» al posto di «·»): l'output di Python passato in una
    pipe di PowerShell usa un'altra codifica. Nei blocchi che leggono l'output:
    `[Console]::OutputEncoding = [Text.Encoding]::UTF8; $env:PYTHONIOENCODING = "utf-8"`.
- **Frontend:** Copilot ha letto il codice del frontend e della v1 il 22-11-2026 (domande
  C1-C20, sezione 9). La v2 è stata adattata. Mancano: la modifica del pulsante Confirm
  (collega). La prova in locale insieme a centralizer e login è riuscita il 22-11 notte
  (sezione 1, punto 4).
- **DR senza serial number e condition (22-11): riuscita.**
  - Stampa «SENZA sn» (campo `S/N:` vuoto): nessun serial number trovato, e nessuno preso per
    sbaglio dalle frasi «REGISTRARE P/N E S/N...». WARNING `DR_NON_VERIFICATA`, ciclo non
    bloccato, anche con condition 2.
  - Stampa «CON sn»: `leggi --cerca "S/N"` trova un solo serial number (riga «APPLY ON S/N»).
    - senza condition: ciclo parziale, 4 corretti, 16 warning, 0 errati, 18 N/A, DR WARNING
      `DR_NON_VERIFICATA` (il serial number ha recommendation diverse, non si sa quale vale);
    - condition 2: ciclo bloccato, 0 corretti, 37 warning, 1 errato, DR ERRATO
      `DR_NON_APPLICABILE`. I 37 warning sono i controlli fermati (`BLOCCATO_A_MONTE`): il
      frontend li mostra come `N/A` grigio e il motivo sta nella riga «DR Case» delle fonti.
- **Tempi:** vedi sezione 9, «Tempi massimi».
- **Salvataggio:** il lavoro fino al 22-11-2026 mattina (regole DR, risposta adattata al
  frontend) è nel ramo `feature/cycle-validation-v2` del repository aziendale. Da salvare:
  riordino delle stampe, `confronta`, `macchine`, documenti riordinati.

- **Tre cicli «con errori», 22-11 sera (oggi COPILOT 2.1, senza ingestion nuova).** Fotografia del
  22-11 (16 oggetti), poi i tre cicli: 0 errati in tutti e tre (0-3 corretti, 16-19 warning,
  15-18 non applicabili), come prima. Il blocco non fa l'ingestion: ora stampa la versione
  pubblicata accanto a quella del 21-11 per vedere se l'ingestion è arrivata.

## 11. Problemi già visti e cosa fare

| Cosa si vede | Perché | Cosa fare |
|---|---|---|
| Dopo Aggiornare 3 test `failed` con `No such file or directory: 'eval\\errori-noti.yaml'` (24-11) | il blocco 2.1 copiava solo alcune cartelle: `eval/errori-noti.yaml` (nato il 23-11) e `examples/` non arrivavano | corretto il 24-11: 2.1 copia anche quei due, 2.2 li mette in git; un test (`test_copilot_blocks.py`) controlla che i blocchi portino tutto quello che serve ai test. Rilanciare 2.1 |
| Dopo Aggiornare i test di `test_campaign.py` danno `ERROR at setup` con `WinError 1314` (24-11) | i test creavano collegamenti simbolici, che su Windows chiedono permessi da amministratore | corretto il 24-11: i test copiano le cartelle. Regola: nei test niente `symlink_to`, solo copie |
| Tanti WARNING `FONTE_ASSENTE` | i manuali dei motori non sono ingestionati | niente: è giusto |
| Stato `parziale`, targhe WARNING `ERRORE_TECNICO` | macchine attive (Redshift) non collegate: dal PC Redshift non si raggiunge | niente: in locale è giusto. In QA la v2 legge Redshift come la v1 |
| `macchine`: `AccessDeniedException, ExecuteStatement` e poi `OperationalError` con `--diretto` | dal PC: manca il permesso della Data API e la rete non arriva al cluster | niente da fare sul PC (P7 facoltativa). I tunnel di centralizer non c'entrano |
| La stessa descrizione a volte ERRATO, a volte CORRETTO | il modello non risponde sempre uguale (op. 060 del DR: ERRATO 2 volte su 3) | c'è già la conferma con 2 domande in più. Prima di «correggere» un ERRATO, rifare la prova 3 volte |
| Esiti diversi tra lettura del modello e del parser | il modello legge il PDF in modo diverso | usare il parser |
| Dubbio: `Accept as is` deve bloccare il DR? | le procedure DR pubblicate parlano solo di riparazione | sì: la guida della v1 dice che con `Accept as is` o `Reject` un ciclo di riparazione è sbagliato. Confermato dall'utente il 22-11-2026 |
| Una ricerca nel testo della conoscenza non trova niente | si cercava riga per riga e le frasi vanno a capo | cercare nel testo intero (`Get-Content -Raw`) |
| Previsto «completo», uscito `parziale` | dimenticate le macchine attive | ricordarsi che oggi è sempre `parziale` |
| Test degli esiti attesi falliti sul PC | mancava la copia di `eval\casi\sintetici` | il blocco di aggiornamento la copia |
| Il blocco del push si è rotto a metà | righe eseguite una alla volta, `else` su una riga a parte | `} else {` sulla stessa riga; commit e push in due blocchi |
| `PermissionError [WinError 5]` | antivirus | il codice riprova; un test può fallire una volta: si rilancia |
| Copilot rifiuta un comando o un file | blocco su `data/` | lancia l'utente, non aggirare |
| Copilot spiega invece di rispondere | gli è stato incollato un testo senza domande | usare il messaggio pronto in `COPILOT.md` |
| Copilot in modalità Agent (anche con «Allow all» acceso) | scelta in basso nella chat | passare ad Ask. Il 22-11 ha risposto alle domande in Agent senza cambiare niente, ma in Agent potrebbe |
| Il bucket si vede in una foto | è aperto `data/bucket.txt` | non ripeterlo; chiedere di chiudere il file |
| Un esito della v1 sembra sbagliato | la v1 sbaglia | non usarla come riferimento |
| DR senza dati: `serial number trovato: no` | il blocco ha preso la stampa «SENZA sn» (`*sn.pdf` ne trova due), oppure il serial number è scritto in un modo non previsto | usare `*CON sn.pdf`; `leggi <pdf> --profile dr --cerca "S/N"` mostra le righe con i codici mascherati |
| Un blocco va avanti anche se il file non c'è (`Missing argument 'pdf'`) | le righe incollate partono una alla volta | mettere il comando dentro `if ($ciclo) { ... }` sulla stessa riga |
| I documenti tolti restano sul PC | `robocopy` copia ma non cancella | il blocco di aggiornamento li cancella per nome |
| `macchine`: «Nel secret mancano host o database» | il secret di Redshift della v1 non ha il database: la v1 lo scrive nella connessione | il comando lo cerca nel codice della v1; se no `--database` |
| Un blocco Python si ferma su un modulo della libreria standard | un file con lo stesso nome (`inspect.py`) nella cartella TEMP | lo script gira in una cartella sua con `python -I` |
| Dal frontend locale ogni POST della v2 dà 403 `Origine non ammessa.` (log: `cookie sent from a foreign origin`) | la libreria accetta solo l'`Origin` uguale a `FRONTEND_URL`; dal secret arriva l'indirizzo del servizio, in locale il frontend è `http://localhost:3000` | `FRONTEND_URL` nella configurazione CV v2 di `launch.json` (`DOCUMENTAZIONE.md`, sezione 13.7) |
| Nel terminale del frontend: `[vite] http proxy error: /prc/sessions/...`, `/mrb/...`, `/me/...`, `/psr/...` `ECONNREFUSED` | il frontend chiede le sessioni anche ai backend di altri progetti, che in locale non sono accesi | niente: non riguarda Cycle Validation |
| `git status` mostra `?? ../src/`, `../tests/`, `../docs/`, `../eval/` | un blocco di aggiornamento lanciato dalla radice del repository invece che dalla cartella della v2 | tolte il 22-11 (blocco Pulizia); ora il blocco Aggiornare si ferma con `FERMO` se il terminale non è nella cartella della v2; controllare sempre che il terminale finisca con `app_cycle_validation_v2>` |
| Avviando una voce composta: `ensure-opensearch-tunnels.ps1 ... non esiste`, exit code 1 | il task «Centralizer prerequisites» chiama uno script che sul PC non c'è | la voce «CV v2» senza il task (`DOCUMENTAZIONE.md`, sezione 13.7); oppure avviare le voci una per una |
| Avviando «CV» partono v1 e v2 insieme | la v2 aggiunta alla voce composta della v1: tutte e due sulla porta 8003 | voce composta a parte «CV v2» (login, frontend, v2): `DOCUMENTAZIONE.md`, sezione 13.7 |
| Avvio della v2 in locale: `Secret '...' non leggibile o non valido (ResourceNotFoundException)` | in `CV_ENV_SECRET` un nome diverso da quello della v1 (per esempio con `_v2` in fondo) | lo stesso nome di `load_secrets` della v1: `DOCUMENTAZIONE.md`, sezione 13.7 |
| Nel pannello di Claude in VS Code tante chat con i nomi delle operazioni dei cicli | il Claude Agent SDK (le sessioni della v2, con Bedrock) salva ogni sessione in `~/.claude/projects` come una chat di Claude Code; il pannello le mostra. Non sono Copilot e non sono chat dell'utente | dal 23-11 la v2 passa `--no-session-persistence` (provato: nessun file scritto); le vecchie (167 chat) spostate il 23-11 in `.claude\chat-validazioni-v2`; il blocco è tolto da COPILOT |
| In una prova della campagna `costo 0.00 $`, nel riepilogo `WARNING ERRORE_TECNICO` come ultimo esito e «mai visti 0 su 29» (25-11 mattina) | l'accesso AWS (SSO) della sera prima era scaduto: i cicli girano, ma ogni chiamata al modello fallisce; la prova contava come fatta | dal 25-11 una prova così non conta (`Trial.unusable`): la campagna si ferma con «il modello non ha risposto» e al lancio dopo la toglie e la rifà. Prima di una campagna: `aws sso login` |
| Blocco della libreria: mancano delle classi (`libreria pronta: False`) | in `vendor` ci sono la 0.3.0 e la 0.4.0rc2; era stata presa la 0.3.0 | installare la riga dei requirements della v1, 0.4.0rc2 con `[auth]` (`DOCUMENTAZIONE.md`, sezione 13.7) |

## 12. Decisioni prese

Le risposte già date. Le domande ancora aperte sono in `COPILOT.md` (sezione 6.1).

- **Task citato che il manuale non ha:** WARNING `FONTE_ASSENTE` subito, senza chiamare il
  modello (interruttore `agent.skip_missing_task`, acceso).
- **Task del capitolo 70:** se non sono nei manuali citati, si cercano nel manuale SPM. Da
  confermare (P1).
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
- **DR `Accept as is`:** ERRATO e ciclo bloccato, come `Reject` (regola della v1, confermata il
  22-11-2026).
- **DR, serial number e condition:** facoltativi; il serial number si prende dalla stampa se
  manca (sezione 8). Chi carica un DR li conosce, ma le domande rendono il frontend
  macchinoso.
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
- **Frontend:** lo gestisce un collega. La v2 manda i testi come li vuole il frontend di
  oggi (sezione 9): `N/A` grigio per i campi vuoti, esito DR nella riga della fonte DR.
- **DR nella v1** (per confronto): serial number letto anche dal PDF, ma sostituito da quello
  scritto dall'utente; con più recommendation tiene quelle con almeno una condition in comune,
  se non ne resta nessuna si ferma con errore; con una sola recommendation la usa senza
  guardare la condition. La v2 fa lo stesso, e in più funziona senza serial number e
  condition.
- **Repository:** si lavora su `main`; un codice vero rimasto in un vecchio messaggio di commit
  si lascia così (nessuna riscrittura della storia).
- **Proposte delle migliorie (24-11-2026):** niente cartelle con un report per variante in
  `eval/` (il repository è pubblico e i risultati veri restano in `runs/`). Ogni variante ha
  `descrizione`, `ipotesi` e `atteso`; `eval prova` li mette in cima a `prestazioni.md` e nella
  tabella «Le proposte e la decisione» del riepilogo. Le considerazioni le scrive Claude nel
  registro di `MIGLIORIE.md`, colonna «Considerazioni».
- **Campagna di prove (24-11-2026, richiesta dell'utente):** «lanciare tutti gli esperimenti
  in automatico, prima con Haiku e poi con Sonnet, sul piccolo e sul grande; io leggo solo i
  risultati finali», e poterne lanciare anche solo una parte. Fatto con `eval campagna` ed
  `eval/campagna.yaml` (lo aggiorna Claude). Sonnet ha cartelle e base sue. Le prove fatte si
  saltano; tetto di spesa 60 $. Report unico `runs/campagna.md`.
- 24-11 sera, l'utente: Haiku e Sonnet in parallelo, un terminale ciascuno. Si può: cartelle
  diverse, nessun file in comune tranne il report, che ora con `--modelli` è
  `runs/campagna-<modello>.md`; alla fine `--solo-report` fa `runs/campagna.md` (gratis). Il
  tetto vale per terminale: COPILOT dà 10 $ a Haiku e 50 $ a Sonnet. Se escono «cicli non
  eseguiti» (troppe richieste ad AWS insieme), Sonnet si rifà da solo dopo Haiku.
- 24-11 sera, l'utente: quattro terminali (modello × insieme)? Sconsigliato: il grande dipende
  dal piccolo (farebbe solo la base) e due terminali dello stesso modello si dividono la quota
  AWS (WARNING per errore tecnico, numeri falsati). Sistemato comunque: report con anche
  l'insieme nel nome, `prova.json` scritto e poi rinominato, prove illeggibili saltate.
- 24-11 sera, passi 1–4 fatti. Copie cieche nuove (seme 1): 41 su 100 chieste, sei tipi:
  numero_una_lingua 5, numero_manuale 3, negazione_una_lingua 9, task_inesistente 5,
  negazione_due_lingue 9, limite_invertito 10 (mai visti per il modello 31, del codice 10;
  prima 21 e 10). Piano: piccolo 51 cicli e copie, grande 23, tutto `2 da fare`, grande solo
  base (dipende dal piccolo). Sonnet sul piccolo potrebbe stare vicino al tetto di 50 $.
- **24-11 sera, campagna sul piccolo finita** (Sonnet 19:20-21:12, Haiku 19:20-21:22, in
  parallelo senza problemi). Cicli 49 (non 51): due copie cieche erano doppie (due stampe dello
  stesso ciclo, stessa copia, stessa impronta); corretto in `blind_mutations`, vale dalle
  prossime copie. Haiku: base 19 stabili (visti 8 su 10, mai visti 2 su 29, codice 9 su 10),
  `elementi_uno_per_uno` 21 (mai visti 4), `lingue_separate` 20 (4). Sonnet: base 18 (mai
  visti 1), `lingue_separate` 19, costo ×12. Visti mancati sempre 298bc28e 035 e f355dc3c 010,
  con `EVIDENZA_NON_TROVATA`: il testo del manuale giusto non arriva al modello. Regola «si
  tiene» resa più severa (serve più errori o un risparmio vero): quattro varianti per
  differenze di rumore finivano anche sul grande. Registro e considerazioni in MIGLIORIE 13.
- **24-11 notte, preparato il 25-11** (richiesta: «risolvi tutti i problemi», domani si
  rilancia). Nuova miglioria `seconda_ricerca` (`agent.search_when_unverifiable`): dopo un
  «non verificabile» una seconda sessione cerca con i tool in tutti i documenti del ciclo
  (ipotesi: il testo del task arriva spesso nel messaggio, senza tool, e il passo giusto è
  altrove). Varianti `elementi_e_lingue` e `tutto_insieme`. Campagna: solo Haiku (Sonnet tolto),
  solo le migliorie, 3 prove, tetto 15 $. Copie cieche **non** rifatte (restano le 39 diverse):
  le prove del 24-11 valgono ancora. COPILOT sezione 1: tappa 3, passi Aggiornare, piano,
  campagna, report (con «Errori mai visti per tipo» e «WARNING per motivo», che mancano ancora).
- **25-11 mattina, tappa 3.** Aggiornare e piano a posto (piccolo come previsto; grande 3 da
  fare per base, elementi e lingue: la sera del 24-11 Haiku non era arrivato al grande). La
  campagna partita con l'accesso AWS scaduto: prova «base» con `costo 0.00 $`, visti 7 su 10
  (solo i controlli del codice), mai visti 0 su 29. Il riepilogo **non sovrascrive**: ogni
  prova è una colonna in più (da 18 a 19), «Ultimo esito» è quello dell'ultima prova. Corretto:
  le prove senza risposte del modello non contano, la campagna si ferma e le rifà.
- **25-11 mezzogiorno.** Piccolo finito (12 prove, circa 4 $); l'utente ferma con Ctrl+C alla
  prima riga del grande, stacca il PC per il pranzo e rilancia lo stesso blocco: il piccolo si
  salta da solo (prove già fatte), una prova interrotta non conta. Prima prova di
  `tutto_insieme`: mai visti 5 su 29 ma 0,37 $ a prova (×2,2 la base: rischio «scartata» per
  costo). `COPILOT.md` riscritto corto (stesse sezioni 0-7, stessi blocchi); `MIGLIORIE.md` con
  «In breve», regola della prova non valida e registro del 25-11.
- **25-11, risposte di Copilot alle domande** (chat in modalità *Agent* con «Allow all»:
  ricordato all'utente di tornare in **Ask**; Copilot si offriva di cambiare
  `eval/errori-noti.yaml`, lo fa Claude). P1 chiusa (capitolo 70 civile = SPM). P4 confermata
  (lettere rovinate in `�`). P6, P7, P8 proposte da confermare (COPILOT 6.1). P7: il «4 volte»
  viene dalla sezione d'ispezione del manuale del motore citato in testata → l'ERRATO della v2
  sulla stampa giusta sarebbe un **falso errore**: la v2 confronta solo con il task SPM. P9:
  5ff17062 sarebbe una copia di 04ecaabe con 010, 030, 040, 050 cambiate (come f355dc3c):
  da verificare con `confronta`. La lista degli errori noti **non** si cambia durante la
  campagna: si cambia quando la base cambia (prove archiviate, seme nuovo).
- **26-11, report della campagna del 25-11** (piccolo e grande, 33 prove, 4,13 $). Scelta:
  `elementi_e_lingue` nella base (valori predefiniti nel codice: `data/settings.yaml` sul PC
  non li nomina, quindi la base nuova vale anche lì; il passo 2 di COPILOT lo controlla).
  `tutto_insieme` 22 stabili e 5 mai visti ma ×2,2 il costo: si riprova come `seconda_ricerca`
  sopra la base nuova. Scoperto: 22 dei 26 mai visti mancati erano su operazioni senza task
  nella conoscenza (FONTE_ASSENTE) → copie cieche del modello solo su operazioni confrontabili;
  ERRORE_TECNICO 7,7 per ciclo sul PC = targhe. **Errore di Claude:** la regola «prova non
  valida» per le prove vecchie contava tutti i WARNING tecnici e al rilancio del 25-11 ha
  cancellato le prove buone di Haiku del 24-11 (Sonnet intatto; i numeri restano nel registro
  di MIGLIORIE). Corretta: per le prove vecchie solo zero token. Nuovo nel riepilogo: «ERRATO da
  verificare» per ciclo e operazione. Prossimo giro: archiviare, seme 2, campagna base nuova
  contro `seconda_ricerca`. Il blocco Archiviare ora rimette la lista dei cicli scelti.
- **26-11, secondo giro.** Due riavvii del PC (problema del computer): la campagna riparte da
  sola dalle prove mancanti (una prova scrive il suo file solo alla fine; quella interrotta non
  conta e si rifà). Piano dopo il secondo riavvio: piccolo finito, `seconda_ricerca` **si
  tiene** sul piccolo, sul grande mancano le sue 3 prove.
- **26-11, domande P1-P9 chiuse** (decise da Copilot sui dati, senza referente; dove i dati non
  bastano: regola prudente, WARNING e mai ERRATO). P2: l'ERRATO del ciclo DR era un giudizio
  instabile, G1 lo evita già. P6: scheda obbligatoria solo nei processi speciali → WARNING
  «scheda forse mancante» (I9 da scrivere). P7: vale il manuale del motore, l'ERRATO su
  04ecaabe 050 è un falso errore (I8 `fonte_ispezione` da scrivere; fino ad allora resta in
  attesa). P8: operazioni senza task → task della prima riga di note, per le ispezioni anche la
  sezione d'ispezione del manuale del motore. P9 verificata con `confronta`: 5ff17062 ha 010,
  030, 040, 050 cambiate; `eval/errori-noti.yaml` aggiornato, vale dal giro dopo questa
  campagna (non aggiornare il PC mentre la campagna gira).
- **26-11, report della campagna** (seme 2): `seconda_ricerca` stessi errori della base (14 su
  25 sul piccolo, 7 su 10 sul grande), costo ×2,1 sul grande → non entra; la base resta.
  Scoperte: i 7 visti stabili li trova tutti il controllo delle lingue (il modello ne aggiunge
  pochi); le copie «numero in una lingua» trovate 1 su 5 → corretto il controllo delle lingue
  (I10: conversione in una lingua sola). Da verificare sul grande: 895167b9 010/030/060,
  2d724fba 050 (domanda a Copilot in COPILOT sezione 1). Prossimo: ingestion del manuale del
  motore, `fonte_ispezione`, regola della scheda.
- **26-11, richiesta nuova:** in azienda chiedono una guida agli unit test (Python, backend del
  chatbot, forse il frontend) per gli sviluppatori dei vari use case, che sono data scientist.
- **`.gitignore` di `docs/` (24-11-2026):** in git entra solo `DOCUMENTAZIONE.md`; gli altri
  quattro file erano già seguiti e restano (servono al blocco Aggiornare e alla memoria).
- **26-11 sera, ERRATO da verificare del grande (Copilot, che era di nuovo in Agent: ricordare
  Ask).** 895167b9 è una copia modificata, non un ciclo vero (come 5ff17062): 4 errori, ora in
  `eval/errori-noti.yaml`. 2d724fba 050 è un falso errore su un ciclo vero, causa P7 («4 volte»
  contro la definizione generica di «3 volte» dell'SPM): 2d724fba è ora una stampa giusta con
  la 050 in attesa. Tre errori veri la v2 li trova per il motivo sbagliato. Scritta la variante
  `definizioni_generali` (I11); campagna base contro questa, `grande: sempre`. Da chiedere a
  Copilot: l'impronta della stampa originale di 895167b9 e se nella lista del grande ci sono
  altre copie modificate.
- **26-11 sera, le copie modificate della lista (Copilot, di nuovo in Agent).** 895167b9 è
  22f586bb con il serial nella 005; 22f586bb è la stampa giusta 737dec71 con 4 operazioni
  cambiate. 22f586bb (4 errori) e 737dec71 (stampa giusta) ora in `eval/errori-noti.yaml`:
  14 cicli noti, 20 errori che contano. Le altre copie erano già in lista. Copilot leggeva un
  elenco vecchio (diceva che 5ff17062 ha solo la 030): il PC non era aggiornato. L'utente fa
  l'ingestion dopo la campagna.
- **26-11 sera, campagna base contro `definizioni_generali`** (14:31-15:39, 2,77 $; foto del
  report e dei due riepiloghi leggibili): la variante non si tiene (14 contro 15 sul piccolo, 8
  contro 10 sul grande). Copie «numero in una lingua» ancora 1 su 5: il controllo non
  confrontava i codici e perdeva i numeri vicino a una conversione scritta prima: corretto
  (I13, nella base). 22f586bb è un DR senza serial: FONTE_ASSENTE su tutte le operazioni.
  Scritta `lingue_tra_loro` (I12). Prossimo: domanda a Copilot su 895167b9 005 (unico ERRATO da
  verificare), Aggiornare, archiviare, campagna base contro `lingue_tra_loro`.
- **26-11 sera (16:20), Copilot su 895167b9 005** (di nuovo in Agent con «Allow all»): falso
  errore. CONTRADDIZIONE perché il manuale manda a sostituire il pezzo, ma la deroga citata
  nella stessa 005 autorizza la raccordatura; la v2 non aveva la procedura della D.R. (arriva
  solo quando nessun task si trova). Il serial è solo nella parte inglese. Scritta
  `procedura_dr` (I14), nella stessa campagna di `lingue_tra_loro`. Il riepilogo ora conta gli
  ERRATO in attesa per variante.
- **26-11 sera, lista dell'ingestion (16:46) e Copilot.** Niente di nuovo da ingestionare sul PC
  né su S3: M1, M2 e SPM già dentro (giro del 23-11). I task che mancano (2 REPAIR di M1 e un
  task citati solo in «Refer to TASK ...», il capitolo 70-23 dell'SPM) non si recuperano
  ingestionando di nuovo gli stessi file: vanno procurati dalla fonte dei manuali, come M4 e M5
  (non ci sono da nessuna parte). M6 è EJ200. Il conteggio «da ingestionare» contava anche i
  manuali già dentro con task mancanti (e M6): ora li tiene separati. Copilot, in Agent con
  «Allow all», aveva copiato 7 doppioni nella cartella `landing_area` di RM su S3: li toglie
  l'utente con il comando scritto da Copilot, prima con `--dryrun`: tolti tutti e 7 alle 17:00
  (stesso contenuto dei file in `RM/manuali/`, nessun giro di ingestion li aveva presi). La campagna si fa con la conoscenza di oggi e le copie del seme 2.
  L'utente ha fotografato il file della lista: ha codici veri e percorsi, non si ripetono.
- **26-11 sera, dove sono i file che mancano (Copilot, 17:10, tutto S3 e tutto il PC).** La
  sezione d'ispezione di M1 (il «4 volte», «length of more than 4 times its width») c'è ed è
  già nella conoscenza dal 23-11 (le sezioni `08-001`): il falso errore della P7 viene dalla
  definizione generica dell'SPM, e `fonte_ispezione` (I8) non aspetta l'ingestion. Il capitolo
  70-23 dell'SPM, i due REPAIR (`09-001`, `09-003`) e M4 non ci sono da nessuna parte: vanno
  chiesti. M5: il manuale no, ma le 2 schede SPM LEAP citate dal suo ciclo sono su S3 in una
  sottocartella `landing_area_test/LEAP/`, che l'ingestion non legge (prende solo i file
  diretti di `SPM/landing_area/`). Decisione: si copiano (non si spostano) insieme ai file
  chiesti, alla prossima ingestion; comando scritto da Copilot in Ask, lanciato dall'utente.
- **26-11 sera, decisione dell'utente: niente altri manuali.** Le campagne si finiscono tra il
  26 e il 27-11 (quella in corso, poi `fonte_ispezione` e regola della scheda, campagna finale
  con il seme 3). Il capitolo 70-23 dell'SPM, i due REPAIR e M4 **non si chiedono**: si va in
  produzione senza, l'azienda li aggiunge poi a mano. La conoscenza del servizio la sceglie
  l'utente: una grande ingestion di tutti i documenti civili (dentro anche le schede LEAP di
  M5). Su S3 entra solo l'utente, come oggi: nessun collegamento ai documenti per gli utenti
  (deciso il 26-11 sera); la v2 legge la conoscenza e non scrive niente su S3.
  Dopo l'ingestion: fotografia, `kb-check` e una prova della base sul grande (i manuali nuovi
  portano confronti nuovi, quindi possibili falsi errori nuovi). Prove dal frontend il 27-11,
  mai mentre gira una campagna (quota di Bedrock divisa). Tempo e costo dopo la produzione.
- **26-11 sera, EJ200 (l'utente).** Anche i documenti militari andranno su S3 (AWS EU, l'ambiente
  autorizzato): l'utente li carica, fa l'ingestion EJ200 e prova la pipeline EJ200; poi Claude
  dice cosa sistemare, come per il civile. Regole che restano: ingestion e prove EJ200 **dentro
  AWS** (QA), mai sul PC (niente download, niente `runs\`, niente fotografia); a Claude solo
  esiti e conteggi (CORRETTO, ERRATO, WARNING per motivo), mai testi EJ200. Una conoscenza EJ200
  rotta ferma tutto il servizio all'avvio (B7): EJ200 si accende in QA solo dopo che il civile
  funziona; se il servizio non parte, si rilancia `qa` senza `--ej200`.
  I documenti EJ200 sono arrivati all'utente per email (quindi sono già sul PC): li carica lui su
  S3. Consiglio: fuori da `ProgettoDocumenti` e dalle cartelle git, copie locali cancellate dopo
  il caricamento. Prove EJ200 sul PC solo con la conferma scritta di chi decide sulla sicurezza.
- **26-11 sera, idee H (MIGLIORIE 10.4):** all'utente piacciono tutte (H1-H14). Si fanno dopo la
  produzione; prima le migliorie I8 e I9 e la campagna finale.
- **27-11 mattina, campagna e accesso scaduto.** Rilanciata la campagna senza `aws sso login`:
  la prima prova (`lingue_tra_loro` sul grande, prova 2 di 3) ha dato 142 controlli in errore
  tecnico e costo 0.00 $. La campagna l'ha buttata da sola e si è fermata; le prove già fatte
  restano. Rimedio: `aws sso login` e lo stesso blocco. Regola per staccarsi (rete o PC): aspettare
  la riga `Prova «...»`, Ctrl+C, poi `aws sso login` e rilanciare: riparte da dove era (il
  risultato di una prova si salva solo alla fine; quella a metà si rifà). Staccare la rete con la
  prova in corso può dare pochi «cicli non eseguiti» e scartare una variante buona.
- **27-11, pulizia dei documenti e del codice (richiesta dell'utente).** `AZIENDA.md` tolto: le
  parti ancora utili (variabili d'ambiente, avvio in locale con login, formato della conoscenza,
  installazione e prima prova, regole da rivedere, «se qualcosa non va») sono in
  `DOCUMENTAZIONE.md` (sezioni 10.4, 13.6, 13.7, 19, 20, 21); la parte sugli esperimenti con i
  casi rivisti è riassunta in 15.2. In `docs/` restano quattro file. `MEMORIA.md` non si
  accorcia: traccia tutto quello che è stato fatto. Il codice lo rivedono quattro agenti di
  revisione, una zona ciascuno, con la regola «funziona come prima» (formati delle prove,
  impostazioni, prompt, rotte e testi citati in `COPILOT.md` intoccabili).
  Fatto il 27-11: tolte le copie della stessa logica in tutte e quattro le zone (`cli.py`:
  `leggi` ed `eval campagna` spezzati in funzioni corte; `trials.py`, `blind.py`, controlli,
  servizio, ingest, Redshift). Verificato vecchio contro nuovo: `--help` dei 21 comandi, uscite di
  `leggi` e `confronta`, circa 150 prove inventate (report identici byte per byte), 4000 copie
  cieche, PDF dei test. Una sola correzione che cambia il comportamento: negli esperimenti con
  conoscenza remota (`eval pipeline`) i documenti per tipo (SPM) non si trovavano mai; la
  campagna e il servizio non c'entrano. **Difetti trovati, da correggere dopo la campagna, con un
  test:** (1) `Trial.unusable`: una prova con un ciclo «non eseguito» e il modello che non ha
  risposto non viene buttata e rifatta (il ciclo fallito ha `model_checks=None` e fa usare la
  regola vecchia): la variante risulta scartata; (2) parser: `RIPARAZIONE :` vuoto nella testata
  prende la parola della riga dopo (`\s*` attraversa l'a capo); (3) una sessione con la ricerca
  accesa e nessun file ammesso avrebbe Read e Grep senza il limite ai file (oggi non succede);
  (4) `_summary` di `eval esegui`: il punto diventa virgola anche nel nome della variante.
- **27-11, campagna finita (11:17).** `procedura_dr` **nella base** (toglie il falso errore di
  895167b9 005; i due errori che perde erano trovati per il motivo sbagliato). `lingue_tra_loro`
  scartata: circa 10 errori in più ma 11-13 falsi errori a prova (traduzioni libere). Da qui
  la versione stretta (I15). Tre differenze tra le lingue in stampe «giuste» sono da far
  guardare a Copilot (potrebbero essere errori veri). Dettagli in `MIGLIORIE.md`, sezione 13.
- **27-11, passo 2 scritto da Claude.** I9 nella base (processo speciale senza scheda = WARNING
  `SCHEDA_FORSE_MANCANTE`; motivo nuovo). I8 `fonte_ispezione`: la sezione d'ispezione si cerca
  come task `<sezione> INSPECTION 00N` nel manuale delle fonti (stessa forma dei `REPAIR 00N`,
  con la ricerca nel testo): **è un'ipotesi sul titolo**, non visto sui file veri; se nella
  campagna finale 04ecaabe 050 resta ERRATO, chiedere a Copilot come si chiama la sezione
  d'ispezione di M1 nel testo (solo la forma). I15 `compare_languages_strict` dentro la variante
  `finale`. 737dec71 060 in attesa finché Copilot non risponde alla P10. Corretti i 4 difetti
  della revisione. Campagna finale: base, `fonte_ispezione`, `finale`.
- **27-11, accesso a `knowledge-index` per la guida allo studio:** il tentativo di collegarlo a
  questa sessione è stato negato dai permessi; la parte sull'ingestion della guida si fa da
  MEMORIA e dalla risposta di Copilot (COPILOT 6.3).

- **27-11, risposta di Copilot alla P10** (le quattro differenze tra le lingue in stampe
  «giuste» segnate da `lingue_tra_loro`). **04ecaabe 030: diverse**, errore vero della stampa
  («larghezza» in italiano, «length» in inglese; più avanti l'italiano dice «semi-lunghezza»:
  sbaglia l'italiano). **2d724fba 030** (stesso testo, altro stadio): uguali nell'uso comune
  (per quello stadio il manuale chiede tutte e due le misure), diverse sui bordi: un dubbio.
  **737dec71 060: diverse**, errore vero («superiore a 4X» contro «not to exceed 4X»; vale
  l'inglese). **8bdb25d5 040: uguali** («coating» è lo strato di lubrificante). In
  `eval/errori-noti.yaml`: le tre operazioni diverse o in dubbio **in attesa** (non contano né
  come trovate né come falsi errori: le prove restano confrontabili con quelle di prima); la 040
  di 8bdb25d5 no (un ERRATO lì è falso). Conseguenza: tra i falsi errori di `lingue_tra_loro`
  alcuni erano errori veri; la decisione non cambia. I15 (`finale`) dovrebbe trovare 737dec71
  060 (limite al contrario), non 04ecaabe 030 (una misura cambiata non è né negazione né limite).
  **Copilot era in Agent con «Allow all»** e ha estratto il testo dei PDF in una cartella
  temporanea, poi cancellata: niente file del repository toccati, ma va rimesso su **Ask**.
- **27-11, prime prove dal frontend (12:07)**, conoscenza di prova, v2 in locale contro la
  versione in QA (uguale alla produzione). Ciclo «con errori» MOS A3 (298bc28e): **in locale**
  1 ERRATO, quello giusto (005, il codice del subtask diverso tra italiano e inglese, trovato
  dal codice); la 035 (parole cambiate) esce WARNING, come nelle prove; 2 operazioni CORRETTO, 6
  WARNING «il manuale non ne parla» (presa in carico, collaudi, preservazione: niente da
  confrontare); la fonte OK; le targhe WARNING (macchine non collegate sul PC, normale). **In
  QA**: descrizioni solo in inglese, la 005 non compare tra le operazioni (diventa le righe
  delle fonti), quasi tutto OK, 1 WARNING (030) e **1 ERRORE sulla seconda fonte che si
  contraddice da solo** («codice sbagliato… che è giusto per questo ciclo»): un falso errore
  della v1. Da confermare che la foto della QA sia della stessa stampa. Le WARNING della v2 sono
  oneste (la v1 dice OK senza aver controllato), ma sono tante: idea in MIGLIORIE 10.4 (H15).

- **27-11, seconda prova dal frontend (12:15): stampa MOS A1 dello stadio 6** (senza errori
  messi apposta; dal falso errore della 050 sembra il ciclo vero 2d724fba: da confermare con la
  P11). **In locale:** 1 ERRATO, sulla 050, ed è il **falso errore noto della P7** («4 volte»
  della stampa contro il «3 volte» generico dell'SPM); 2 OK, 6 WARNING «il testo non decide»,
  fonte OK. **In QA:** tutto OK tranne 1 ERRORE sulla **scheda della 040** (il task del
  capitolo 70 scritto accanto alla scheda «non esiste», ne propone un altro con la classe): la
  v2 lì dice OK e quel task non lo controlla. Chi ha ragione: domanda P11 a Copilot.
  **Scoperta per I8:** nelle stampe MOS l'ispezione del manuale del motore **non** è una
  sezione «INSPECTION 001» ma un **task con il codice completo del gruppo 200** (ispezione
  delle pale), citato nella 005 e nella 010 insieme al task SPM della raccordatura; la 050
  (liquidi penetranti) cita solo il task SPM. Con l'ipotesi del 27-11 mattina `fonte_ispezione`
  non avrebbe aggiunto niente. **Corretto subito** (prima della campagna finale): I8 prende
  anche i task d'ispezione con il codice completo citati in qualsiasi punto del ciclo, con un
  test. La base non cambia. **Altra cosa vista:** la fonte della v2 è il manuale del motore
  con il **primo** task della nota della testata, che nelle MOS sembra il task SPM (la riga
  Sources mostra il manuale del motore con il task SPM; la QA mostra due righe, una per
  manuale). Le operazioni senza task ricevono quel task SPM. Da cambiare dopo la produzione,
  con una variante (MIGLIORIE 10.4, H16); prima la P11 dice com'è fatta la nota.

- **27-11, risposta di Copilot alla P11.** La stampa A1 dello stadio 6 è **2d724fba** (ciclo
  vero). (1) La scheda della 040: il task del capitolo 70 accanto alla scheda **esiste** (è la
  parte generale dell'attacco chimico) e la classe dell'etchant è giusta: **l'ERRORE della QA è
  un falso errore della v1**, l'OK della v2 è giusto. (2) La nota della testata ha solo la parola
  della lavorazione e **un task completo del capitolo 70** (niente codice di manuale, niente
  task del motore). Quindi la fonte della v2 (manuale del motore del piè di pagina + task della
  nota) abbina il manuale del motore a un task SPM: H16 aggiornata. Copilot ancora in **Agent
  con «Allow all»** (ha detto di non aver creato file).
- **27-11, l'utente: «perché la v2 dà così tanti warning? quale è più giusta? lo devo
  presentare fra 2 settimane».** Risposta di Claude, dai fatti: sulle due stampe provate la v1
  non ha trovato nessuno dei 2 errori messi apposta nella A3 (legge solo l'inglese, e la 005
  non la mostra come operazione) e ha dato **2 falsi errori** (fonte della A3, scheda della 040
  della A1, confermato dalla P11); la v2 ha trovato 1 errore su 2 e dato 1 falso errore (la 050
  di 2d724fba, già noto, che `fonte_ispezione` deve togliere). I WARNING della v2 vengono da tre
  cose: (a) le **targhe sul PC** (registro non collegato): non sono un dubbio, il controllo è
  spento → da oggi **N/A `CONTROLLO_SPENTO`** nella base (in produzione non cambia niente: lì il
  registro c'è); (b) le operazioni di cui il manuale **non parla** (presa in carico,
  preservazione, collaudo finale): la v1 dice OK senza aver controllato, la v2 WARNING → **I16
  `fuori_tema`**, N/A con la spiegazione, dentro la variante `finale` della campagna finale;
  (c) i dubbi veri (per esempio la classe dell'etchant che il testo non nomina): restano WARNING,
  sono quelli da guardare. Manca la misura della v1 sulle stesse stampe: nuovo passo 4b (COPILOT
  3.9), con le copie rinominate con l'impronta.

- **27-11 sera, campagna finale e v1 sugli stessi cicli.** Foto di `campagna.md` e dei due
  riepiloghi (piccolo 14:05-15:13, grande 16:03-17:02: la campagna è ripartita per il grande).
  **Vince `finale`** su tutti e due gli insiemi, 0 falsi errori, meno WARNING; sul grande 3
  ERRATO da verificare sulla 060 di tre cicli veri (414d85ca, 477abec8, ffadfe16), forse lo
  stesso errore vero della stampa 737dec71 060 («superiore» contro «not to exceed»): P12.
  `fonte_ispezione` non toglie il falso errore P7 (sul piccolo nessun effetto, sul grande solo
  su 04ecaabe): P12. Con `finale` 298bc28e 035 (un errore da trovare) diventa N/A
  `FUORI_TEMA`: prima era un WARNING, quindi I16 può nascondere un errore. Numeri in
  MIGLIORIE 13.
  **La v1:** l'utente ha messo nel repository `docs/CONFRONTO_V1_14_CICLI.md` (risultati della
  v1, cioè la versione di prima del cycle validation, quella in QA e in produzione, sulle
  stesse 14 stampe caricate come MOS; i DR la v1 non li prende; dai suoi CSV e testo originale delle 14 stampe, con i codici veri). Claude ha
  avvisato del repository pubblico; l'utente: **il responsabile ha detto che può stare nel
  repository pubblico** (regola in sezione 7). Cosa dice, confrontato con il testo delle
  stampe:
  - la v1 valida 10 stampe su 14: si ferma sulle 3 A6 (22f586bb, 737dec71, 895167b9: «serial
    e condition mancanti» o «nessun dato DR»), e 298bc28e non si carica. La v2 le fa tutte;
  - **la lista degli errori noti era incompleta** sulle tre stampe senza stampa giusta
    (38960731, 8d3c673c, e9b74c84): il 23-11 veniva solo dal confronto delle lingue. Nel
    testo ci sono cambi a mano che si vedono (una parola minuscola in una stampa tutta
    maiuscola, la stessa operazione con due macchine su due pagine, limiti in inglese più alti
    del totale, codici di scheda e task diversi da tutte le altre stampe). Aggiunte 6
    operazioni in `eval/errori-noti.yaml` (38960731 010, 030, 040; 8d3c673c 100, 110;
    e9b74c84 040). Le stampe copiate da 04ecaabe (5ff17062, f355dc3c) erano già complete per
    operazione (P9); anche lì sono cambiati il task della 030 e la macchina della 050;
  - **la v1 trova 15 operazioni con errori su 19** nelle 6 stampe con errori: tutti i cambi di
    codici (task, schede, macchine: ha il registro delle macchine attive e l'indice delle
    schede con il materiale) e le frasi inglesi. **Manca i cambi solo in italiano** (5ff17062
    010, f355dc3c 010 e 050) e la classe dell'etchant di f355dc3c 040: legge l'inglese;
  - **la v1 dà 8 falsi errori:** 6 sulle 4 stampe giuste (04ecaabe: la fonte, il cui testo dice
    che è giusta, e la scheda della 040, P11; 4e64d49a: la fonte, stesso testo; 8bdb25d5: la
    030, «coating» e «lubrificante applicato» sono la stessa cosa, P10; 2d724fba: la 030, «1,5
    volte la semi-lunghezza» contro «7,5 volte la profondità», che con «lunghezza almeno 10
    volte la profondità» è la stessa regola, e la scheda della 040) e 2 su 8d3c673c (060:
    «opposing» contro «opposite»; 070: una macchina che nel testo della stampa non c'è);
  - **la v2** (`finale`): sulle 13 operazioni della lista di prima ne può giudicare 10 e ne
    trova 8 (manca 5ff17062 010 e f355dc3c 010, tre numeri cambiati in italiano); 0 falsi
    errori contati, ma il falso errore P7 resta (04ecaabe 050, 2d724fba 050). Sulle 6
    operazioni aggiunte non si sa ancora: si ricalcola gratis (`eval riepilogo --attesi`,
    comando nuovo del 27-11 sera). Probabilmente le manca: oggi controlla solo che task e
    scheda esistano, e sul PC le targhe sono spente. Idee H17-H19 (MIGLIORIE 10.4);
  - **il messaggio per la presentazione, da confermare con i numeri ricalcolati:** la v1 trova
    di più sui codici ma su una stampa giusta su due dà un errore falso, e non legge l'italiano
    né le A6 senza serial; la v2 non dà quasi mai errori falsi, legge tutte le stampe e le due
    lingue, e ogni ERRATO ha la frase citata ritrovata dal programma; le manca il controllo dei
    codici (H17-H19, lavoro piccolo).

- **27-11 sera, riepiloghi ricalcolati e P12.** Con le 6 operazioni aggiunte (40 errori sul
  piccolo, 26 sul grande) i trovati non cambiano: **la v2 le mancava tutte**. P12 (Copilot,
  ancora in Agent con «Allow all»): (A) i 3 ERRATO di `finale` sui cicli veri 414d85ca,
  477abec8, ffadfe16 sono la stessa 060 di 737dec71, parola per parola: **errori veri**,
  messi in `eval/errori-noti.yaml`; (B) 04ecaabe 050 con `fonte_ispezione`: la sezione
  d'ispezione c'è sempre tra le evidenze; l'ERRATO del piccolo dice che l'italiano «almeno 4
  volte la larghezza» comprende il caso uguale a 4, mentre l'inglese e il manuale dicono «più di
  4»: una differenza vera ma piccola (resta in attesa, come dubbio). **Decisione:** `finale`
  nella base (le quattro impostazioni accese di default). **Tre controlli nuovi del codice**
  (proposte 1, 2 e 4 del confronto con la v1), provati sul testo delle 14 stampe del file v1
  (il parser della v2 sulle pagine dell'appendice): H17 (task della colonna SP.ORIG contro
  la testata: 38960731 030; il parser ora legge la colonna anche in fondo a una riga di testo,
  prima finiva nella descrizione), la 010 divisa in quattro parti da righe di asterischi
  dentro ogni lingua (`language_blocks`: 38960731, 5ff17062, f355dc3c 010), H19 (stessa
  operazione con due macchine: 38960731 040, e la 050 di 5ff17062 e f355dc3c). **5
  operazioni in più, 0 falsi errori** sulle stampe giuste. Il testo dell'appendice non è
  identico a quello che legge il PC (per esempio 5ff17062 030 lì è rovinato): la misura vera
  è la campagna della base nuova (COPILOT passo 4d).

- **27-11 sera, regole decise, H15 e H18.** L'utente: scheda mancante = avviso con il commento
  «Scheda mancante»; «almeno 4» contro «più di 4» non è un errore; nel confronto con la v1
  contare che la v1 ha documenti che la v2 non ha ancora. Fatti mentre l'utente lancia il 4d:
  **H15** nella base (`warning_kind`: «da guardare» o «non controllabile», nel testo del
  feedback dopo `Warning:` e nei conteggi); **H18** e la regola «almeno N» nella variante
  **`schede_e_limiti`** (spenta nella base, così la campagna del 4d resta quella attesa).
  H18 nasce da un fatto visto sulle 14 stampe del file v1 (parser della v2 sull'appendice):
  le stampe giuste hanno sempre la stessa coppia scheda e task (la scheda dell'attacco
  chimico sempre con lo stesso task, quella dei liquidi penetranti sempre con il suo); le
  stampe con errori 38960731 e 8d3c673c hanno un'altra scheda o un'altra cifra del task. Il
  controllo usa l'indice delle schede della conoscenza (trattamento, famiglie di motore), che
  qui non si vede: per questo si misura (COPILOT passo 4e).

- **27-11 notte, risultati del 4d, EJ200 sul PC, 2900 documenti.** Il 4d (base nuova, 3 prove):
  piccolo 30 su 43 stabili (avevo previsto 28), grande 18 su 29 (previsto 20), 0,011-0,019 $ e
  16-26 s a ciclo; unico falso errore 04ecaabe 050 in 2 prove su 3 (la regola «almeno N» lo
  deve togliere). Da verificare: 8d3c673c 060 e 070 (3 su 3; la v1 le segnala, ma il 27-11 sera
  le avevo contate come falsi errori della v1) e b1261d11 060 (ciclo vero, forse lo stesso
  «superiore a 4X» di 737dec71): domanda **P13**. Dei 4 errori «mai visti» la v2 ne trova 1: un
  limite invertito dato CORRETTO e una negazione tolta in tutte e due le lingue finita N/A
  «fuori tema» (rischio di I16). **2d724fba 050** ha lo stesso testo della 050 di 04ecaabe
  («almeno 4 volte» contro «more than 4 times»): con la regola dell'utente non è più in attesa,
  un ERRATO lì è un falso errore (N1). **L'utente ha l'autorizzazione a provare EJ200 sul PC**
  (sezione 7) e ha già sul PC i documenti RDR, RN e «RI» e alcune stampe EJ200: Claude ha
  scritto `prova-ej200` (COPILOT passo 4f). La v2 conosce RDR, EF e RN: «RI» va chiarito
  (forse è EF, o un tipo nuovo da aggiungere al profilo e all'ingestion). **2900 documenti**
  (la produzione, contro i 75 delle prove): la ricerca è per codice esatto, quindi il modello
  riceve lo stesso testo e qualità e costo per controllo non cambiano; cambiano avvio, disco,
  memoria e le ricerche nel testo. Misura con una conoscenza finta (`eval scala`,
  DOCUMENTAZIONE 20): 559 MB, avvio 4,2 s, 164 MB di memoria, ricerca di un task 6-9 µs. Trovato
  un punto lento: i fratelli di un codice sbagliato del capitolo 70 rileggevano tutti gli SPM
  a ogni codice (0,7 s); ora una cache per documento (0,07 s). I rischi veri restano
  l'ingestion (task tagliati male nei manuali nuovi) e più operazioni controllabili (più costo,
  più occasioni di falsi errori): li misura la prova di controllo sul grande dopo la grande
  ingestion. L'utente vuole poi ragionare su quali migliorie «dopo la produzione» si possono
  fare prima.
  Poi l'utente ha chiesto una lista «pronto per il passo dopo» con soglie: è in
  `docs/V1_CONTRO_V2.md`, sezione 5 (cancelli A QA, B EJ200 in QA, C produzione; soglie
  proposte da Claude, da confermare). Si aggiorna con il resto del file dopo ogni campagna.
- **27-11 notte, documenti più corti e MIGLIORIE in una tabella (l'utente).** «Meno testo, solo
  lo stretto necessario.» Accorciati `V1_CONTRO_V2.md`, la sezione 1 di COPILOT e le parti nuove
  di DOCUMENTAZIONE. `MIGLIORIE.md` era fatto di molte tabelle con sigle diverse (A, B, D, E, F,
  G, H, I, T, N) che non coincidevano: ora è **una tabella sola** con una sigla unica
  (`MG01`…`MG74`, in ordine di quando sono nate), cosa fa, stato, importanza (1-5) e il nome di
  prima. Il registro degli esperimenti è passato qui, sezione 16. Nei documenti nuovi si usano
  le sigle `MGxx`; i nomi vecchi restano nelle note di prima e nei commenti del codice.
- **27-11 notte, campagna 4e: `schede_e_limiti` (MG40 + MG41) vince, nella base.** Piccolo
  34/43 stabili contro 30 (min/medio 34/35), 0 falsi errori contro 2, mai visti 1 su 4 come la
  base, 5,4 WARNING per ciclo contro 5,8, 0,0110 $ e 16 s. Grande 23/29 contro 18 (24/24,3), 0
  falsi contro 2, 8,7 WARNING contro 8,9, 0,0180 $ e 24 s. Trovati in più, dal codice: 8d3c673c
  100 (`SCHEDA_MATERIALE_DIVERSO`) e 110 (`SCHEDA_ALTRO_MOTORE`), 22f586bb e 895167b9 050
  (`SCHEDA_INESISTENTE`) 3 su 3; 04ecaabe 050 e 2d724fba 050 senza ERRATO. **Sulle 19
  operazioni della v1 la v2 arriva a 15, come la v1, con 0 falsi errori contro 6.** Restano:
  ERRATO da verificare 8d3c673c 060 e 070 e b1261d11 060 (3 su 3 in tutte e due: P13); mancati
  22f586bb 030 (DR senza serial), 895167b9 030, 298bc28e 035, e9b74c84 040 (una parola), le 060
  dei cicli veri instabili (414d85ca 4 su 6, ffadfe16 3 su 6, 737dec71 2 su 3: il limite al
  contrario tra le lingue lo trova il modello, non sempre → MG75, dal codice); copie cieche
  `limite_invertito` (CORRETTO), `negazione_due_lingue` (N/A fuori tema), `numero_manuale`
  (non trovato). WARNING della base sul piccolo: `EVIDENZA_NON_TROVATA` 3,0 per ciclo,
  `FONTE_ASSENTE` 1,8, `SCHEDA_FORSE_MANCANTE` 0,6, `DR_NON_VERIFICATA` 0,2. Nella base i
  valori predefiniti `sheet_consistency` e `boundary_limits_note` (veri); i casi inventati
  aggiornati (scheda LEAP su un ciclo GENX ora ERRATO; la copia «scheda inesistente» usa
  lettere che l'indice non ha).

- **27-11 notte, il giro nuovo (chiesto dall'utente): meno campagne, tante migliorie insieme.**
  Una campagna costa all'utente un'ora e qualche dollaro. Da ora: Claude fa tante migliorie
  insieme, le prova lui sul testo vero delle 14 stampe (`docs/CONFRONTO_V1_14_CICLI.md`, test
  `tests/test_real_prints.py`) e con i test; l'utente prova prima gratis con `eval senza-modello`
  (solo i controlli del codice: quello che trova lì lo trova sempre), poi una campagna sola
  quando il sistema è quasi finito. Una campagna serve solo quando cambia qualcosa che tocca il
  modello o prima di un cancello di `V1_CONTRO_V2.md`.
- **27-11 notte, P13 (Copilot).** 8d3c673c 060 e b1261d11 060: falsi errori del controllo dei
  numeri (il codice, non il modello): «nella operazione 70 successiva» in italiano, «refer to
  figure 903» in inglese, presi per un numero cambiato → MG78 (i rimandi si confrontano solo
  con quelli dello stesso tipo). 8d3c673c 070: errore vero (una pagina con la targa cambiata,
  la v1 la segnala) → tra gli errori noti. Decisione dell'utente: 737dec71 060 tra gli errori
  (non più in attesa): 737dec71 non è più una «stampa giusta».
- **27-11 notte, P14 (Copilot sul codice di knowledge-index).** Le voci RDR hanno il numero del
  DR nel campo `reference` (dal nome del file `DR_<codice>[_Final]_revN`); più voci per lo
  stesso DR (una per serial e condizione). Usato da MG76 (lo stesso DR in tutto il ciclo) e
  MG50 (la procedura DR dal numero della stampa, anche senza serial).
- **27-11 notte, versione quasi finale (Claude).** Provate sul testo delle 14 stampe, senza
  modello: limiti al contrario (MG75: 22f586bb, 895167b9, 737dec71 060), azione diversa (MG47:
  e9b74c84 040; 298bc28e 035 grazie a MG77, il parser buttava la riga accanto a «CONTINUA ALLA
  PAGINA SEGUENTE»), un altro DR (MG76: 895167b9 030). Nessun ERRATO fuori dagli errori noti;
  8d3c673c 060 non più ERRATO (MG78). Corretto anche «no less than» (era letto come massimo).
  Prima di provarle sul PC: MG46 (materiale tra le lingue) scartata qui, l'unico caso lo trova
  già la scheda; un numero «solo in una lingua» con unità scartato (troppi casi sulle stampe
  giuste: conversioni). In più MG44 (EJ200 rotta spegne solo EJ200), MG45 (fuori tema prudente,
  tocca il modello), MG53 (480 s per le sessioni di un ciclo). Stima: piccolo circa 39-40 su 45,
  grande 25-26 su 29, 16 su 19 contro la v1, 0 falsi, 0 da verificare.
- **27-11 notte, prima prova senza modello sul PC (`eval senza-modello`, 0 $).** Ricalcolati
  i riepiloghi (piccolo: base 32-34 su 45, `schede_e_limiti` 36-38; grande: base 20-23 su 31,
  `schede_e_limiti` 26). Solo il codice: piccolo 39 su 45, grande 29 su 31, 0 falsi errori;
  16 delle 19 operazioni della v1 (la v1 ne trova 15). Mancate dal codice nel grande: 22f586bb
  e 895167b9 010 («profondità massima» in italiano, «min depth» in inglese, senza numero) →
  MG81, provata sulle 14 stampe: solo quelle due. Ma 4 ERRATO da verificare nei cicli veri del
  grande (64752871 050, 9a66895e 090, d8f8a3bd 100 e 150): non erano ERRATO nella 4e, quindi
  vengono dalle regole nuove (MG75, MG47, MG76, i rimandi di MG78 o la riga di MG77), che sulle 14 stampe non
  davano niente. Lezione: le 14 stampe non bastano, `eval senza-modello` sui cicli veri serve
  sempre prima di una campagna. Domanda P15 a Copilot; la campagna dopo la risposta (se sono
  falsi errori del codice, una campagna lanciata prima andrebbe rifatta). Per capirlo subito la
  prossima volta: MG82, il motivo accanto a ogni ERRATO in più (a schermo e nel riepilogo).
- **27-11 notte, seconda prova senza modello e P15 (Copilot).** Con MG81: piccolo 41 su 45,
  grande 31 su 31, 0 falsi errori; ancora i 4 da verificare, tutti `INCOERENZA_LINGUE`. P15:
  tutti falsi errori di MG47, dallo stesso testo (in 64752871, 9a66895e, d8f8a3bd): «se
  danneggiate durante la sabbiatura ripristinare le protezioni» contro «replace the masks if
  damaged». Il codice leggeva «sabbiatura» come azione (è la condizione) e «replace» come
  «sostituire» (traduce «ripristinare»). Corretto: le azioni dopo «durante», «dopo», «prima
  di» non contano; «ripristinare» vale «sostituire». Decisione: se la prossima prova senza
  modello dà 0 falsi errori e 0 da verificare, la campagna parte subito, senza aspettare
  Claude. Lezione: un sinonimo che manca in una regola delle lingue fa un falso errore su
  tutti i cicli con lo stesso testo; `eval senza-modello` sui cicli veri lo vede gratis.
- **27-11 notte, terza prova senza modello.** Piccolo 41 su 45, grande 31 su 31, 0 falsi
  errori, 0 da verificare: la correzione di MG47 funziona sui cicli veri. Nel piccolo restano
  i 4 «mai visti» che solo il modello può trovare. Via libera alla campagna `quasi_finale`.
- **27-11 notte, metriche più specifiche (chieste dall'utente: «verificare realmente che il
  sistema funzioni»).** Gli errori noti sono una trentina: pochi per dire che una regola
  funziona. Banco di prova (`eval banco`, MG84): il programma mette un errore alla volta su ogni
  operazione possibile delle 14 stampe vere (testo di `CONFRONTO_V1_14_CICLI.md`), 5 giri con
  semi diversi, e conta quanti ne trova il codice. Risultato: 308 su 310 (numeri 38 su 40,
  limiti 12 su 12, massimo/minimo 16 su 16, azioni 223 su 223, DR 1 su 1), 0 falsi allarmi.
  Il banco ha trovato due buchi, corretti (MG86): una data «D.T. gg-mm-aa» in una lingua sola
  disallineava i numeri; lo stesso numero con un limite due volte, uno girato, non si vedeva
  (ora si contano i limiti per verso). Restano 2 limiti noti (un numero scritto due volte per
  sbaglio, un numero in più in una lingua). Lettura della stampa contro la tabella della v1:
  105 operazioni su 105, targhe 104 su 105, schede 21 su 22; le 2 differenze sono errori noti
  (targa cambiata, scheda tolta); 13 operazioni (le 005 della testata) le legge solo la v2.
  Nel riepilogo (MG85) le «Metriche di controllo»: falsi OK (mancati con CORRETTO, i più
  pericolosi), mancati come WARNING o N/A, esiti decisi, errori tecnici, ciclo peggiore.
  Attenzione: il banco misura le regole del codice, non il modello; il modello lo misurano le
  copie cieche e la campagna.
- **27-11 notte, quarta prova senza modello e primo banco sul PC.** Senza modello come prima:
  piccolo 41 su 45, grande 31 su 31, 0 falsi errori, 0 da verificare (le correzioni MG86 non
  rompono niente). Il banco sul PC, con la conoscenza vera, dà gli stessi numeri di quello di
  Claude: numeri 38 su 40 (mancati 8d3c673c 060, e9b74c84 010), limiti 12 su 12,
  massimo/minimo 16 su 16, azioni 223 su 223, DR 1 su 1, 0 falsi allarmi; lettura contro la v1
  105 su 105, targhe 104 su 105, schede 21 su 22, 13 operazioni lette solo dalla v2. Via libera
  alla campagna `quasi_finale`.
- **28-11 notte, campagna `quasi_finale`: si tiene.** Dettagli nel registro (sezione 16). Le
  tabelle «per tipo» e «WARNING per motivo» di `campagna.md` guardavano l'ultima base sul
  piccolo, fatta con il codice di prima: ora guardano l'ultima prova della scelta migliore,
  piccolo e grande (passo 4i per rifare il report). Copilot nelle foto non si vedeva.
- **28-11, migliorie del 28-11 scritte (l'utente le ha chieste tutte prima della campagna).**
  MG48 (task di un altro stadio, dal codice: la v1 lo fa con il modello: sui 14 cicli lo dice
  sulla 140 di 8d3c673c, dove l'errore noto è un numero in una lingua, che la v2 trova già), MG54 (chiamata
  diretta a Bedrock con l'SDK `anthropic`, `AsyncAnthropicBedrock`: Read e Grep li esegue la
  v2 con le regole dell'hook; la risposta con lo strumento `StructuredOutput`, come Claude
  Code; il costo dai token con il listino di Haiku 5.5, 0,10 e 0,50 $ per milione: da
  controllare contro il costo che dava l'SDK nelle prove), MG56 (cache), MG59 (testo comune in
  cache; con Haiku la cache vale solo sopra una lunghezza minima del testo, e le sessioni che
  partono insieme non la trovano ancora scritta: lo dirà la campagna), MG55 (solo il confronto
  tra le lingue, il più semplice da mettere insieme; le differenze si confermano sempre con le
  sessioni di una sola operazione). Tutte spente, una variante ciascuna. MG83: senza sapere
  quali operazioni danno «evidenza non trovata» un taglio alla cieca rischia falsi OK, che la
  campagna ha appena mostrato come il punto debole: prima la tabella «WARNING per operazione»
  (passo 4i), poi la variante. MG49 non serve. La campagna confronta con `quasi_finale`
  (`riferimento` in `eval/campagna.yaml`).
- **28-11, provare senza campagna (chiesto dall'utente: «come ieri sera»).** Decisione: una
  campagna solo per quello che cambia il modello. Tre modi gratis o quasi (DOCUMENTAZIONE 15.3):
  `eval senza-modello --variante` per il codice dei controlli (MG48); `eval rigioca` per le
  regole finali (MG83: nuovo stadio `verdict/final_rules.py`, `agent.final_rules`), che
  rifà il conto delle prove di `quasi_finale` dai loro `report.json` con e senza la regola;
  una prova sola per costo e tempo (la chiamata diretta). `diretta` e `diretta_cache` sono
  diventate una variante sola (la cache non cambia le risposte). Considerazioni: `rigioca` vale
  solo se la variante cambia soltanto le regole finali (il comando lo controlla); le risposte
  del modello sono quelle delle 3 prove di riferimento, quindi la stabilità si misura su quelle.
  Nuova regola della decisione: una variante con più falsi OK della base non si tiene (prima i
  falsi OK si vedevano solo nelle metriche di controllo); nel report della campagna c'è la
  colonna «Falsi OK a prova». La campagna del passo 4j scende da circa 12-14 $ a 6-7 $.
- **28-11 mattina, prima chiamata diretta sul PC.** Aggiornare ✅ (tutti i test passano). `eval
  chiamata-diretta`: `NON riuscita (eu....haiku-5-5): error APIConnectionError`. Vuol dire che
  il client HTTP dell'SDK `anthropic` (httpx) non arriva a Bedrock: la firma AWS si fa prima,
  quindi non sono le credenziali; restano rete, proxy o certificato (Zscaler). Claude Code e
  boto3 (S3) sul PC funzionano. Decisione: la chiamata diretta passa da boto3 (`invoke_model`,
  `agent.direct_transport: boto3`), la stessa rete di S3; httpx resta come opzione e prende il
  certificato da `AWS_CA_BUNDLE`. Gli errori ora dicono i tipi della catena, il codice di AWS e
  la causa probabile (mai il messaggio). Da rifare il punto 2 del passo 4i.
- **28-11, 10:40, passo 4i sul PC.** Aggiornare ✅. `eval chiamata-diretta` con boto3: `ok`,
  risposta giusta, 539+55 token, 0,00008 $, 7,5 s: la strada boto3 funziona sul PC. MG48
  senza modello sul grande: 31 → 31, falsi errori 0 → 0, nessuna differenza (la riga del
  piccolo era scorsa via: da rimandare). Riepiloghi ricalcolati con gli errori noti di adesso:
  `quasi_finale` 42 su 45 (3 volte) e 31 su 31 (3 volte), come ieri notte. `eval rigioca
  --variante quasi_finale`: 42 → 42 e 31 → 31, WARNING per ciclo 4,9 e 8,9 uguali: il comando
  legge bene le prove sul PC. Falsi OK a prova: 1,0 sul piccolo, 0 sul grande (MG87). Mancano
  ancora le tre tabelle di `runs\campagna.md` e la prova di `diretta`. Copilot era su Agent.
- **28-11, 10:50, tabelle e prova di `diretta`.** Prova sola di `diretta` sul piccolo: visti
  31 su 31, mai visti per il modello 1 su 4 (come `quasi_finale`), 0 falsi errori, 0 da
  verificare, **0,22 $** contro 0,35 $ delle prove di `quasi_finale` (-37%). Si va alla
  campagna con `testo_comune` e `lingue_insieme`. Tabella per tipo (piccolo, ultima prova):
  mancati `limite_invertito` (CORRETTO VERIFICATO: il falso OK), `negazione_due_lingue` (N/A
  FUORI_TEMA), `numero_manuale` (WARNING EVIDENZA_NON_TROVATA). WARNING per ciclo senza errori
  noti: piccolo EVIDENZA_NON_TROVATA 3,2, SCHEDA_FORSE_MANCANTE 0,8, FONTE_ASSENTE 0,2;
  grande FONTE_ASSENTE 4,5, EVIDENZA_NON_TROVATA 3,2, SCHEDA_FORSE_MANCANTE 1,0, estrazione
  0,1. Per operazione: sul grande due cicli veri (9a66895e, d8f8a3bd) hanno FONTE_ASSENTE su
  tutte le operazioni (16 e 21: il manuale non è nella conoscenza), più i task code sulle
  stesse operazioni. EVIDENZA_NON_TROVATA torna sulle stesse operazioni (010, 040, 060) negli
  stessi cicli del piccolo e del grande. Decisioni: MG83 = regola finale
  `fonte_assente_una_volta` (un avviso per fonte assente, le altre righe N/A GIA_SEGNALATO);
  MG87 = regola finale `limite_contro_citazione` (il CORRETTO diventa ERRATO se la riga che il
  modello cita dà il limite al contrario). Tutte e due da rigiocare a 0 $. EVIDENZA_NON_TROVATA
  non si toglie con una regola: è anche la risposta su un errore mancato.
- **28-11, 11:05, le due regole rigiocate e MG48 sul piccolo.** `meno_avvisi`: piccolo 42 → 42,
  WARNING per ciclo 4,9 → 4,9; grande 31 → 31, **8,9 → 5,3**, falsi OK e falsi errori uguali:
  si tiene. Decisione: entra nella base dopo la campagna del passo 4j, per non cambiare a metà
  il riferimento (le prove di `quasi_finale` sono senza la regola); poi si rigiocano con la
  regola anche le varianti nuove. `limiti_citati`: non scatta (falsi OK 1,0 → 1,0, niente
  danni): la riga citata dal modello non ha lo stesso numero con un verso che il codice legge.
  `eval rigioca` ora stampa per ogni falso OK che cosa c'è nella riga citata (solo sì/no e
  conteggi). MG48 sul piccolo: 41 → 41, nessuna differenza, come sul grande: resta spenta
  (non c'è un caso nei nostri cicli; nessun danno). La campagna non è ancora partita.

## 13. Da correggere nell'indice (knowledge-index)

**Titoli dei task GE.** `regole.json` (`codice_task`) riconosce solo il codice completo
(`72-00-01-110-001`). I titoli `72-00-01 REPAIR 001` e `CIR 72-00-01, REPAIR 001` l'indice non
li registra: la v2 li trova nel testo, ma l'indice potrebbe registrarli (con la stessa regola di
`kb/task_text.py`), così anche il controllo di Copilot li vedrebbe.

**Targa `90`.** Nel file delle targhe la `90` ha come funzione una frase rimasta dal documento
(«la descrizione breve può essere scelta…») con le lettere accentate rovinate. Nei dati TM la
stessa targa compare in tre righe (pagine 14, 17, 18) con funzioni diverse. Come correggere:

1. aprire il PDF TM alle pagine 14, 17 e 18 e guardare la colonna della funzione;
2. scartare le righe dove la "funzione" è una frase (è una nota della tabella);
3. leggere il testo con la codifica giusta: nei file pubblicati non devono esserci `Ã`, `â€`
   né `�` (25-11: nel file delle targhe le lettere accentate sono diventate `�`);
4. con la stessa targa su più righe, unire le funzioni con `; ` invece di tenere solo la prima;
5. se non c'è tempo: in `uncertainty.json` scrivere
   `{"format": 1, "machine_tags": {"90": ["da_record_parziale"]}}` (la targa esce WARNING
   finché non si corregge);
6. pubblicare la nuova versione e lanciare `kb-check`.

## 14. Come si scrive `COPILOT.md`

- Struttura (riscritta il 24-11-2026, su richiesta dell'utente: «estremamente semplice, non
  dare per scontato nulla»): 0 prima di iniziare (parole, come si lancia un blocco, regole,
  cosa fare se va storto), 1 cosa fare adesso (dal 24-11: la strada con tutte le tappe e ✅ fatta,
  👉 adesso, ⬜ dopo; «dove siamo» in tre righe; i passi di adesso uno per uno, ognuno con titolo,
  costo e tempo, il comando da copiare o il link al blocco, «Deve uscire» e «Mandami»; poi le
  tappe dopo e «Quando hai tempo»),
  2 aggiornare e salvare (2.1, 2.2), 3 le prove (3.1 come funzionano, 3.2 cicli veri, 3.3
  copie cieche, 3.4 gruppo nascosto, 3.5 campagna, 3.6 leggere i risultati, 3.7 prova a mano,
  3.8 togliere, azzerare, archiviare), 4 frontend, 5 ingestion, 6 persone, 7 QA. Riordinato il
  24-11: se si cambia la numerazione, aggiornare i rimandi negli altri documenti e nel codice.
  In «Dove siamo» solo lo stato di oggi: la storia va qui in MEMORIA.
- Prima di ogni blocco: **a cosa serve**, **quando**, se **costa**; per i blocchi lunghi anche
  cosa fa passo per passo.
- Blocchi PowerShell da copiare così come sono, senza niente da cambiare; ognuno comincia con
  `$env:UV_PYTHON = "3.14"` (tranne quelli di solo git o solo apertura di file).
- Dopo ogni blocco: **Deve uscire** e **Manda a Claude**.
- Se un blocco costa (Bedrock), dirlo. Per guardare un PDF senza spendere c'è
  `cycle-validation leggi` (`--pagina N` stampa il testo di una pagina).
- Un blocco che può fare danni (push) ha un controllo che scrive `FERMO` e non fa niente se
  qualcosa non torna.
- Le cose fatte si tolgono (l'utente vuole il file pulito): il riassunto va qui in `MEMORIA.md`,
  sezione 10.
- Scrivere tutto in modo molto semplice.
- Accorgimenti PowerShell: in `Select-String` usare `\S+` al posto di caratteri come `·`;
  `Get-Content -Raw` prima di `ConvertFrom-Json`; in `aws s3 ls` il nome del file comincia alla
  colonna 31; i PDF si cercano con una parte del nome (`Get-ChildItem -Filter`), mai con il
  codice vero nel blocco.
- Il blocco di aggiornamento toglie da solo sul PC i file che nel repository personale non ci
  sono più (`src`, `tests`, `prompts`, `examples`, `eval/casi/sintetici`, `eval/varianti` e i
  `.md` di `docs`); copia anche `eval/errori-noti.yaml` (dal 24-11): un file tolto qui sparisce anche lì al primo aggiornamento, e Salvare lo registra come
  `D`. Il blocco si ferma (`FERMO`) se il download non riesce o il terminale non è nella cartella
  della v2.

## 15. Le stampe PVRM320 viste finora

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

## 16. Registro degli esperimenti (da `MIGLIORIE.md`, 27-11)

Una riga per ogni prova decisa, confrontata con la base dello stesso giro.

- **Decisione:** si tiene, scartata o da ripetere (dal riepilogo).
- **Considerazioni:** cosa si è capito, perché è andata così, cosa fare dopo.
- La proposta (cosa cambia, ipotesi, atteso) sta nel file della variante e compare in cima a
  `prestazioni.md` e nel riepilogo.
- Le considerazioni le scrive Claude qui, dalle foto, quando la variante è decisa.
- Fino al 27-11 stava in `MIGLIORIE.md`, con i nomi vecchi delle migliorie (A1, I8, H17…):
  la tabella di `MIGLIORIE.md` dice a quale sigla `MGxx` corrisponde ognuno.

**Sintesi del 24-11 (campagna Haiku, piccolo).** Nessuna impostazione migliora la base. Gli
errori visti sono identici in tutte le prove, quindi le differenze tra le varianti sono solo
sugli errori mai visti per il modello, dove 1 o 2 su 21 è rumore (una copia trovata o no). Il
limite non sta nelle impostazioni ma nel metodo: il modello confronta la descrizione con il
manuale e non vede un «non» tolto in una lingua sola (18 dei 21 mai visti). Prossimi passi: la
prova con Sonnet (dice se è il modello) e la tappa 3 con una miglioria sul metodo. Con
differenze così piccole conviene alzare le ripetizioni a 3 o avere più errori mai visti
(gruppo nascosto). Queste righe sono con le copie cieche e il conteggio di prima della
rianalisi del 24-11 sera (visti su 12, mai visti su 21): non si confrontano con le prove dopo.

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
| 2026-11-24 | campagna, Haiku, insieme piccolo (41 cicli e copie), 2 prove | `base` | visti stabili 19 su 43 (tutti i 12 visti: 8 sempre, 4 mai); mai visti per il modello 2 su 21 | 0,16 $ a prova | 5 min 10 s a prova | riferimento | i visti sono identici in tutte le 13 prove della campagna: 8 trovati sempre, 4 mai (298bc28e 035, c5ff3cd6 030 = P6, f355dc3c 010 e 040 = documenti mancanti). Le varianti si distinguono solo sui mai visti |
| 2026-11-24 | come sopra | `effort_medio` | stabili 18 (trovati 19 e 18); mai visti 1 su 21 | 0,19-0,20 $ (+20%) | 6 min | non si tiene | più ragionamento non fa trovare le negazioni tolte in una lingua; costa di più |
| 2026-11-24 | come sopra | `conferme_1` | stabili 18 (19 e 19, ma uno diverso); mai visti 1 su 21 | 0,15-0,16 $ | 5 min | non si tiene | stesso costo; la differenza dalla base è una sola copia cieca trovata in una prova su due: rumore |
| 2026-11-24 | come sopra | `testo_lungo` | stabili 18; mai visti 1 su 21 | 0,15-0,16 $ | 5 min | non si tiene | più testo del manuale non aiuta: le negazioni mancate non dipendono dal contesto |
| 2026-11-24 | come sopra | `effort_pieno` | stabili 18; mai visti 1 su 21; da verificare 0 in una prova | 0,19 $ (+20%) | 6 min 20 s | non si tiene | conferma B2: con `low` nei controlli non si perde niente, si spende meno. B2 resta |
| 2026-11-24 | come sopra | `prompt_task_mancante` | stabili 19; mai visti 2 su 21 (come la base) | 0,16-0,17 $ | 5 min 20 s | non si tiene | stessi errori, ma più WARNING per ciclo senza errori (14,7 contro 14,2): B6 resta |
| 2026-11-24 | come sopra | `concorrenza_12` | 19; mai visti 2 su 21 (1 prova) | 0,15 $ | 4 min 33 s (-12%) | da ripetere | prima prova: stessi errori e più veloce. Se la seconda conferma, si tiene (solo tempo) |

**Sintesi del 24-11 sera (campagna Haiku e Sonnet, piccolo, copie cieche nuove).** Insieme
piccolo di 49 cicli e copie (39 copie diverse, non 41: due erano doppie, ora corretto); errori
da trovare 49: visti 10, mai visti per il modello 29, controlli del codice 10. Risultati:
1. **Le due migliorie sul metodo funzionano con Haiku**: `elementi_uno_per_uno` 21 stabili e
   mai visti 4 su 29, `lingue_separate` 20 e 4 su 29, contro 19 e 2 su 29 della base. Sono le
   uniche con più errori stabili; 0 falsi errori, costo uguale.
2. **Sonnet non è meglio di Haiku** e costa circa 12 volte tanto (0,043 $ contro 0,0035 $ a
   ciclo): base 18 stabili e mai visti 1 su 29, più instabile (`f355dc3c` 050 trovato 14 volte
   su 18). Su `298bc28e` 035 risponde CORRETTO VERIFICATO. Solo `lingue_separate` lo porta a 19.
3. **Le impostazioni non contano**: effort, conferme, testo lungo, concorrenza, prompt del task
   mancante danno gli stessi errori della base o meno. Con la regola vecchia quattro
   «si tenevano» per differenze piccole (0,2 WARNING, 3% di costo): ora sono «pari alla base».
4. **I visti mancati sono un problema di testo, non di giudizio**: `298bc28e` 035 e
   `f355dc3c` 010 escono in tutte le 36 prove con WARNING `EVIDENZA_NON_TROVATA` (Haiku): il
   modello non trova nel testo che riceve il passo del manuale da confrontare.
5. **Mai visti ancora bassi** (4 su 29 nel migliore): il prossimo passo si sceglie dalla
   tabella «Errori mai visti per tipo» di `campagna-haiku.md` (cosa risponde la v2 sui
   mancati).

| Data | Esperimento | Variante | Concordanza | Costo | Tempo | Decisione | Considerazioni |
|---|---|---|---|---|---|---|---|
| 2026-11-24 sera | campagna, Haiku, piccolo (49 cicli e copie), 2 prove | `base` | stabili 19 su 49: visti 8 su 10, mai visti per il modello 2 su 29, codice 9 su 10; 0 falsi errori; 1 da verificare | 0,0034 $ a ciclo, 0,17 $ a prova | 8 s a ciclo, 6 min 45 s a prova | riferimento | uguale nelle due prove; visti mancati sempre 298bc28e 035 e f355dc3c 010 (`EVIDENZA_NON_TROVATA`) |
| 2026-11-24 sera | come sopra | `elementi_uno_per_uno` | stabili 21 (21 e 21); mai visti 4 su 29 | 0,0037 $ (+9%) | 8 s | si tiene (più errori stabili) | la migliore: due errori in più in tutte e due le prove, nessun falso errore. Da provare sul grande e insieme a `lingue_separate` |
| 2026-11-24 sera | come sopra | `lingue_separate` | stabili 20 (21 e 20); mai visti 4 su 29 | 0,0038 $ (+12%) | 9 s | si tiene (più errori stabili) | aiuta come atteso; un errore trovato in una prova sola. f355dc3c 050 mancato nella seconda prova |
| 2026-11-24 sera | come sopra | `testo_lungo` | stabili 19 (20 e 19); mai visti 2 su 29 | 0,0035 $ | 8 s | pari alla base (prima «si tiene») | una copia in più in una prova sola: rumore. Il testo in più non fa trovare i visti mancati: il passo che manca non è vicino |
| 2026-11-24 sera | come sopra | `prompt_task_mancante` | stabili 19; mai visti 2 su 29 | 0,0035 $ | 9 s | pari alla base (prima «si tiene») | 13,7 WARNING per ciclo contro 14,5: meno di 1 |
| 2026-11-24 sera | come sopra | `concorrenza_12` | stabili 19; mai visti 2 su 29 | 0,0036 $ | 8 s (massimo 1 min 34 s) | pari alla base (prima «si tiene») | non più veloce a ciclo con due campagne insieme; un ciclo lento. Da rimisurare da sola nella tappa 4 |
| 2026-11-24 sera | come sopra | `conferme_1` | stabili 19; mai visti 2 su 29 | 0,0033 $ (-3%) | 9 s | pari alla base (prima «si tiene») | risparmio troppo piccolo per contare |
| 2026-11-24 sera | come sopra | `effort_medio` | stabili 18; mai visti 1 su 29 | 0,0037 $ | 9 s | non si tiene | come il 24-11: più ragionamento non aiuta |
| 2026-11-24 sera | come sopra | `effort_pieno` | stabili 17; mai visti 1 su 29 | 0,0038 $ | 8 s | non si tiene | B2 confermata un'altra volta |
| 2026-11-24 sera | campagna, Sonnet, piccolo, 2 prove | `base` | stabili 18 su 49 (19 e 18); mai visti 1 su 29; 0 falsi errori | 0,043 $ a ciclo (×12 Haiku), 2,10 $ a prova | 8 s a ciclo | riferimento Sonnet | peggio di Haiku a ×12 il costo. Più instabile (f355dc3c 050 14 su 18 prove; ERRATO su 04ecaabe 050, P7, solo 6 su 18 contro 14 di Haiku) |
| 2026-11-24 sera | come sopra | `lingue_separate` | stabili 19 (19 e 19); mai visti 2 su 29 | 0,049 $ (+15%) | 9 s | si tiene (più errori stabili) | l'unica che aiuta anche Sonnet; arriva al livello della base Haiku |
| 2026-11-24 sera | come sopra | `prompt_task_mancante`, `concorrenza_12`, `conferme_1` | stabili 18; mai visti 1 su 29 | 0,040-0,043 $ | 7-8 s | pari alla base (prima «si tiene») | differenze di rumore |
| 2026-11-24 sera | come sopra | `testo_lungo`, `elementi_uno_per_uno`, `effort_medio`, `effort_pieno` | stabili 18, 17, 17, 16 | 0,042-0,048 $ | 7-8 s | non si tiene | `elementi_uno_per_uno` con Sonnet trova 18 per prova ma non sempre gli stessi |

**25-11 (campagna Haiku, 3 prove per variante; stesse copie cieche del 24-11 sera).**

- **Mattina, prova non valida.** La campagna è partita con l'accesso AWS della sera prima
  scaduto: la prova `base` è uscita con `costo 0.00 $`, visti 7 su 10 (solo quelli che trova il
  codice), mai visti per il modello 0 su 29, WARNING `ERRORE_TECNICO` come ultimo esito. Contava
  come fatta. Corretto nel codice (sezione 9): una prova così non conta e si rifà. **Lezione:**
  prima di ogni campagna `aws sso login`, e dopo la prima prova si guarda che il costo non sia
  0.
- **Le prove del 24-11 di Haiku sono state cancellate per sbaglio.** Al rilancio delle 10 la
  regola nuova «la prova non vale» le ha prese per prove senza risposte: per le prove vecchie
  contava tutti i WARNING per errore tecnico, e sul PC le targhe ne danno circa 8 per ciclo.
  Le prove di Sonnet non sono state toccate. I loro numeri restano nel registro qui sopra; i
  confronti del 25-11 sono tutti tra prove dello stesso giorno, quindi valgono. Regola corretta
  il 26-11 (sezione 6).
- **Piccolo** (49 cicli e copie, 3 prove per variante, dalle 10:19 alle 12:22; 4,13 $ in tutto
  con il grande). Errore per errore: i visti trovati sempre sono gli stessi 7 in tutte le 18
  prove; `298bc28e` 035 e `f355dc3c` 010 mai (WARNING `EVIDENZA_NON_TROVATA`, **anche con la
  seconda ricerca**: l'ipotesi della variante non si è avverata su questi due); `f355dc3c` 050
  (frase al contrario) 12 su 18, instabile, ma 3 su 3 con `tutto_insieme`.
- **Errori mai visti per tipo** (ultima base): limite invertito 0 su 8 (FONTE_ASSENTE 7),
  negazione in due lingue 0 su 9 (FONTE_ASSENTE 9), negazione in una lingua 0 su 9
  (FONTE_ASSENTE 6, EVIDENZA_NON_TROVATA 2), numero del manuale 1 su 3; codice: numero in una
  lingua 4 su 5, task inesistente 5 su 5. **22 dei 26 mancati del modello erano su operazioni
  senza task nella conoscenza**: corretto il 26-11 (sezione 3).
- **WARNING per ciclo senza errori noti** (ultima base): 7,7 `ERRORE_TECNICO` (sul PC: le targhe,
  Redshift non raggiungibile), 6,7 `EVIDENZA_NON_TROVATA`, 0,3 `FONTE_ASSENTE`. In produzione i
  primi non ci sono: restano circa 7 WARNING per ciclo, quasi tutti «evidenza non trovata».
- **Grande** (23 cicli: i 10 noti e 13 veri; 3 prove per variante, dalle 15:17 alle 16:49): tutte
  le varianti trovano gli stessi 8 visti su 10 (stessi mancati del piccolo); `lingue_separate`
  perde `f355dc3c` 050 in 2 prove su 3. Gli ERRATO da verificare (sui cicli veri) salgono con
  i metodi nuovi: base 2, `seconda_ricerca` 2, `elementi_uno_per_uno` 3, `lingue_separate` 3,
  `elementi_e_lingue` 4. Possono essere errori veri o falsi errori: dal 26-11 il riepilogo li
  elenca (ciclo e operazione) per farli guardare a una persona.
- **Decisione:** `elementi_e_lingue` nella base (la scelta migliore della regola: +2 stabili,
  +2 mai visti, 0 falsi errori, +15% di costo). Prossimo giro: `seconda_ricerca` sopra la base
  nuova (cioè `tutto_insieme`), con copie cieche nuove solo su operazioni confrontabili.

| Data | Esperimento | Variante | Concordanza | Costo | Tempo | Decisione | Considerazioni |
|---|---|---|---|---|---|---|---|
| 2026-11-25 mattina | campagna, Haiku, piccolo, accesso AWS scaduto | `base` (prova 3) | visti 7 su 10, mai visti 0 su 29: il modello non ha risposto | 0,00 $ | — | **non valida** (tolta) | da qui la regola «la prova non vale» (sezione 6) |
| 2026-11-25 | campagna, Haiku, piccolo (49 cicli e copie), 3 prove | `base` | stabili 17 su 49 (19, 19, 17); mai visti 1 su 29 (2, 2, 1); 0 falsi errori; precisione 94% | 0,0034 $ a ciclo, 0,16-0,17 $ a prova | 7 s a ciclo (massimo 37 s) | riferimento | la terza prova perde 2 errori: con 3 prove la base è più bassa che con 2 (19 il 24-11) |
| 2026-11-25 | come sopra | `elementi_e_lingue` | stabili **19** (21, 20, 20); mai visti 3 (4, 3, 4); 0 falsi; 14 WARNING per ciclo | 0,0039 $ (+15%) | 7 s (46 s) | **si tiene, scelta migliore → nella base dal 26-11** | le due migliorie del 24-11 insieme non si sommano molto: come `lingue_separate` da sola, un po' più stabile. Sul grande: 8 su 10 come la base ma 4 da verificare contro 2 |
| 2026-11-25 | come sopra | `lingue_separate` | stabili 19 (19, 20, 20); mai visti 3 | 0,0037 $ | 7 s (35 s) | si tiene | sul grande perde `f355dc3c` 050 in 2 prove su 3 (7 stabili contro 8): non si tiene lì |
| 2026-11-25 | come sopra | `elementi_uno_per_uno` | stabili 18 (21, 20, 19); mai visti 2 | 0,0039 $ | 8 s (55 s) | si tiene | il 24-11 era la migliore (21 su 2 prove): con la terza prova scende |
| 2026-11-25 | come sopra | `seconda_ricerca` | stabili 18 (19, 18, 19); mai visti 1 | 0,0065 $ (×1,9) | 12 s (1 min 19 s) | si tiene (di poco) | da sola non trova i due visti che doveva trovare; sul grande costa ×2,3 (scartata lì) |
| 2026-11-25 | come sopra | `tutto_insieme` | stabili **22** (22, 22, 22); mai visti **5** (5, 5, 5); 0 falsi; 13,6 WARNING | 0,0074 $ (×2,2) | 13 s (1 min 18 s) | scartata: costo oltre 2 volte la base | la migliore in errori e la più stabile: la seconda ricerca aiuta solo insieme a elementi e lingue. Sulla base nuova costa 1,9 volte: si riprova come `seconda_ricerca` |
| 2026-11-25 | campagna, Haiku, grande (23 cicli), 3 prove | `base` | 8 su 10 in tutte le prove; 1-2 da verificare; precisione 80%; 19,9 WARNING per ciclo | 0,0086 $ a ciclo, 0,18-0,22 $ a prova | 13 s (39 s) | riferimento | sui cicli veri una prova dura meno di 5 minuti per 23 cicli |
| 2026-11-25 | come sopra | `elementi_e_lingue` | 8 su 10; 3-4 da verificare; precisione 67% | 0,0111 $ (+29%) | 17 s (1 min) | pari alla base | gli ERRATO in più sui cicli veri sono da far guardare a una persona |
| 2026-11-25 | come sopra | `elementi_uno_per_uno`, `lingue_separate` | 8 e 7 su 10; 2-3 da verificare | 0,0101-0,0103 $ | 14 s | pari alla base; non si tiene | come sopra |
| 2026-11-25 | come sopra | `seconda_ricerca` | 8 su 10; 2 da verificare; 19,0 WARNING | 0,0198 $ (×2,3) | 32 s (1 min 05 s) | scartata: costo | sui cicli veri la seconda ricerca parte spesso (molte operazioni «non verificabili»): costa molto più che sul piccolo |

**26-11 (campagna Haiku, 3 prove per variante; base con elementi e lingue; copie cieche del
seme 2: 15, di cui 5 dei tipi del modello).** Due riavvii del PC: la campagna è ripartita da
sola dalle prove mancanti. Spesa 1,53 $ per le ultime 3 prove; in tutto circa 3 $.

- **Piccolo** (25 cicli e copie; errori da trovare 25: visti 10, mai visti per il modello 5,
  codice 10). Visti: gli stessi 7 sempre, **tutti con `INCOERENZA_LINGUE`** (il controllo del
  codice); 298bc28e 035 e f355dc3c 010 mai (`EVIDENZA_NON_TROVATA`); f355dc3c 050 4 prove su 6
  (base 2 su 3, `seconda_ricerca` 2 su 3). Mai visti per tipo (ultima base): limite invertito
  0 su 1 (`CORRETTO VERIFICATO`: il modello vede il passo e non la differenza), negazione in due
  lingue 0 su 1, numero del manuale 0 su 1, negazione in una lingua 1 su 2 (tutti i mancati
  `EVIDENZA_NON_TROVATA`); codice: task inesistente 5 su 5, **numero in una lingua 1 su 5**
  (`FONTE_ASSENTE` 3, `EVIDENZA_NON_TROVATA` 1: il controllo delle lingue non le ha viste,
  corretto con I10). WARNING per ciclo senza errori noti: 7,7 `ERRORE_TECNICO` (targhe), 7,0
  `EVIDENZA_NON_TROVATA`, 0,3 `FONTE_ASSENTE`. Da verificare: solo 5ff17062 050, che per la P9 è
  un errore vero (in lista dal giro dopo).
- **Grande** (23 cicli): visti 7 su 10 stabili per tutte e due (f355dc3c 050 3 su 6). ERRATO da
  verificare: 895167b9 010 (base 2 su 3, `seconda_ricerca` 3 su 3), 030 (3 e 3), 060 (solo
  `seconda_ricerca`, 3 su 3); 2d724fba 050 (3 e 1); 5ff17062 050 (3 e 3, errore vero). In attesa:
  04ecaabe 050 (falso errore P7) ERRATO in 4 prove su 6 sul piccolo e 2 su 6 sul grande.
- **Decisione:** la base resta; `seconda_ricerca` non entra. **Lezione:** il vantaggio di
  `tutto_insieme` del 25-11 (22 contro 19) non si è ripetuto con le copie nuove: era in parte
  sulle copie non confrontabili e su f355dc3c 050, che è instabile. Il modello oggi aggiunge
  poco agli errori trovati: il limite è il testo del manuale che riceve (conoscenza che manca,
  passo giusto in un altro task), non come giudica.
- **26-11 sera, gli ERRATO da verificare del grande (Copilot in Ask, confrontando con la stampa
  originale e i documenti):** 895167b9 non è un ciclo vero, è una copia modificata: 010 errore
  vero trovato per il motivo sbagliato (la v2 dice che il manuale vieta la raccordatura; il
  difetto vero è un limite cambiato in inglese), 030 errore vero per lo stesso motivo
  sbagliato, 060 errore vero per il motivo giusto (negazione tolta in inglese), e la 050
  (materiale cambiato in inglese) la v2 la dava per corretta. 2d724fba 050 **falso errore**: il
  ciclo dice «4 volte la larghezza» come la D.R. e la stampa giusta, la v2 confronta con la
  definizione generica dell'SPM («3 volte»), che vale solo senza limiti specifici e rimanda al
  manuale d'ispezione. 5ff17062 050 errore vero, ma quasi sempre per il motivo «3 o 4 volte»:
  solo 2 prove su 6 vedono la negazione tolta. **Conseguenze:** 895167b9 e 2d724fba in
  `eval/errori-noti.yaml`; variante `definizioni_generali` (I11). La precisione del grande della
  base era 64%: con queste risposte 4 dei 5 ERRATO da verificare sono errori veri. Ma un
  errore «trovato» può esserlo per il motivo sbagliato: oggi la misura non lo vede (lo vede solo
  chi legge il report).
- **26-11 sera, tutte le copie modificate della lista (Copilot):** 895167b9 è 22f586bb con il
  serial nella 005, e 22f586bb è la stampa giusta 737dec71 con 010, 030, 050 e 060 cambiate
  (nella 050 e 060 anche il codice della scheda). Tutte e tre erano nella lista del grande come
  cicli veri: ora 22f586bb è un ciclo con errori e 737dec71 una stampa giusta. Le altre copie
  (f355dc3c, 5ff17062, 298bc28e, c5ff3cd6) erano già in lista con le stesse operazioni. Sul
  grande del 26-11 nessun ERRATO da verificare su 22f586bb, mentre su 895167b9 sì: da guardare
  nella campagna (instabilità o effetto della 005).

| Data | Esperimento | Variante | Concordanza | Costo | Tempo | Decisione | Considerazioni |
|---|---|---|---|---|---|---|---|
| 2026-11-26 | campagna, Haiku, piccolo (25 cicli e copie, seme 2), 3 prove | `base` | stabili 14 su 25 (16, 15, 14); mai visti 1 su 5; 0 falsi; 1 da verificare (5ff17062 050, vero); precisione 93%; 14,7 WARNING | 0,0073 $ a ciclo, 0,17-0,19 $ a prova | 12 s (1 min 03 s) | riferimento | il costo a ciclo è più alto del 25-11 perché le copie (che costano poco) sono meno: non si confronta con il 25-11 |
| 2026-11-26 | come sopra | `seconda_ricerca` | stabili 14 (15, 14, 15); mai visti 1 su 5; 0 falsi; 13,1 WARNING | 0,0140 $ (×1,9) | 21 s (1 min 02 s) | si tiene sul piccolo (solo WARNING -1,6) | stessi errori della base: l'ipotesi «come `tutto_insieme`, 22 e 5» non si è avverata |
| 2026-11-26 | campagna, Haiku, grande (23 cicli), 3 prove | `base` | 7 su 10 stabili (7, 7, 8); 3-4 da verificare; precisione 64%; 19,7 WARNING | 0,0106 $, 0,23-0,25 $ a prova | 14 s (55 s) | riferimento | gli ERRATO da verificare vanno guardati (Copilot, COPILOT sezione 1) |
| 2026-11-26 | come sopra | `seconda_ricerca` | 7 su 10 (7, 8, 8); 4-5 da verificare (895167b9 060 in più); 18,9 WARNING | 0,0221 $ (×2,1) | 26 s (1 min 14 s) | **scartata: costo** | sui cicli veri la seconda sessione parte spesso; non trova errori in più. Chiusa: si riprende solo se la conoscenza cambia molto |

**26-11 sera (campagna Haiku, 3 prove per variante; base del 26-11 con I10; copie cieche del
seme 2; lista nuova degli errori noti: 14 cicli noti, 20 errori che contano).** Dalle 14:31
alle 15:39, 12 prove, 2,77 $.

- **Piccolo** (29 cicli e copie; errori da trovare 35: visti 20, mai visti per il modello 5,
  codice 10). Base 15 stabili (19, 16, 17 trovati), `definizioni_generali` 14 (14, 14, 15). Visti
  trovati sempre da tutte e due: 298bc28e 005, 38960731 050, 5ff17062 030, 8d3c673c 140,
  c5ff3cd6 040, e9b74c84 025, f355dc3c 030, **tutti con `INCOERENZA_LINGUE`** (il codice).
  5ff17062 050: base 3 su 3, `definizioni_generali` 0 su 3 (era trovato per il motivo
  sbagliato). 895167b9 010 e 030: 2 prove su 6, instabili. Mai: 22f586bb 010, 030, 050, 060
  (`FONTE_ASSENTE`: DR senza serial, la v2 non sa quali documenti usare), 298bc28e 035,
  5ff17062 010, 895167b9 050 e 060, f355dc3c 010 (`EVIDENZA_NON_TROVATA`). f355dc3c 050 2 su 6
  (solo base).
- **Mai visti per tipo** (ultima base): limite invertito 0 su 1, negazione in due lingue 0 su 1,
  numero del manuale 0 su 1, negazione in una lingua 1 su 2 (mancati `EVIDENZA_NON_TROVATA`);
  codice: task inesistente 5 su 5, **numero in una lingua ancora 1 su 5** (`FONTE_ASSENTE` 3,
  `GIUDIZIO_INSTABILE` 1): I10 non bastava. Provando le copie del codice su descrizioni di
  esempio: il controllo non confrontava i codici (part number di 5 cifre o più, che le copie
  cambiano) e perdeva il numero vicino a una conversione scritta prima («248 °F (120 °C)»).
  Corretto (I13).
- **WARNING per ciclo senza errori noti** (ultima base, piccolo): 7,8 `ERRORE_TECNICO` (targhe),
  5,2 `EVIDENZA_NON_TROVATA`, 2,0 `FONTE_ASSENTE`, 0,2 `DR_NON_VERIFICATA`.
- **Grande** (23 cicli, 20 errori). Base 10 stabili (10, 10, 11), `definizioni_generali` 8 (8,
  8, 8): perde 5ff17062 050 e 895167b9 030, tutti e due trovati per il motivo sbagliato.
  895167b9 010 qui 6 su 6 (sul piccolo 2 su 6: lo stesso PDF, giudizio instabile). 0 falsi
  errori. ERRATO da verificare: solo 895167b9 005 (il serial aggiunto; base 1 su 3 sul grande,
  `definizioni_generali` 1 su 3 sul piccolo e 2 su 3 sul grande). **Copilot (16:20): falso
  errore.** Il testo della 005 è uguale a 22f586bb e a 737dec71; il manuale dice che per quel
  difetto il pezzo va sostituito, ma vale solo senza deroga, e la deroga citata nella stessa
  005 autorizza la raccordatura (e ha anche quel serial). La v2 stessa scriveva che il
  documento di deroga non le era stato dato: la procedura della D.R. arriva al modello solo se
  nessun task si trova. Da qui `procedura_dr` (I14). Il serial è scritto solo in inglese: non è
  la causa e il controllo dei codici (I13) non lo conta (un codice in più in una lingua sola).
- **In attesa**: 04ecaabe 050 ERRATO in 2 prove su 6 sul piccolo e 1 su 6 sul grande; 2d724fba
  050 in 2 su 6 e 2 su 6. Il riepilogo non dice di quale variante: la nota non toglie del tutto
  il falso errore, o lo toglie solo a volte.
- **Decisione:** `definizioni_generali` non si tiene; la base resta. **Lezione:** dire al modello
  che cosa non è un errore toglie anche gli errori veri trovati per il motivo sbagliato, e non
  gli fa trovare il motivo giusto. Il motivo giusto (una negazione, un limite, un materiale
  cambiati in una lingua) non dipende dal manuale: si vede confrontando le due lingue tra loro.
  Da qui `lingue_tra_loro` (I12). Il controllo dei numeri del codice ora prende anche codici e
  conversioni (I13): la base cambia, le prove si archiviano.

| Data | Esperimento | Variante | Concordanza | Costo | Tempo | Decisione | Considerazioni |
|---|---|---|---|---|---|---|---|
| 2026-11-26 sera | campagna, Haiku, piccolo (29 cicli e copie, seme 2, 14 cicli noti), 3 prove | `base` | stabili 15 su 35 (19, 16, 17); mai visti 1 su 5; 0 falsi; 0 da verificare; precisione 100%; 15,2 WARNING | 0,0078 $ a ciclo, 0,22-0,23 $ a prova | 16 s (1 min 24 s) | riferimento | il primo giro con la lista verificata da Copilot |
| 2026-11-26 sera | come sopra | `definizioni_generali` | stabili 14 (14, 14, 15); mai visti 1 su 5; 0 falsi; 1 da verificare; 15,5 WARNING | 0,0074 $ | 12 s (34 s) | **non si tiene** | perde 5ff17062 050 (trovato per il motivo sbagliato); più veloce perché meno ERRATO da confermare |
| 2026-11-26 sera | campagna, Haiku, grande (23 cicli), 3 prove | `base` | stabili 10 su 20 (10, 10, 11); 0 falsi; 1 da verificare (895167b9 005); precisione 91%; 19,9 WARNING | 0,0107 $, 0,23-0,26 $ a prova | 15 s (1 min 19 s) | riferimento | |
| 2026-11-26 sera | come sopra | `definizioni_generali` | stabili 8 (8, 8, 8); 0 falsi; 1 da verificare; precisione 89%; 20,2 WARNING | 0,0102 $ | 13 s (44 s) | **non si tiene** | perde 5ff17062 050 e 895167b9 030 |

**27-11 (campagna Haiku, 3 prove per variante; base del 26-11 sera con I13; copie cieche del
seme 2).** Iniziata il 26-11 alle 17:18, interrotta (accesso AWS scaduto: la prova senza
risposte buttata da sola) e finita il 27-11 alle 11:17. Nell'ultimo pezzo 5 prove, 1,83 $.

- **Piccolo** (29 cicli e copie, 35 errori). Base 20 stabili (21, 20, 21), mai visti 1 su 5, 0
  falsi errori, 1 da verificare, 0,0078 $ e 13 s a ciclo. `lingue_tra_loro` 30 stabili (31, 31,
  31), mai visti 3-4 su 5, **11 falsi errori in ogni prova**, 13-14 da verificare, 0,0136 $ e 22
  s. `procedura_dr` 20 stabili (20, 20, 20), mai visti 1 su 5, 0 falsi, 0 da verificare,
  0,0073 $ e 12 s.
- **Mai visti per tipo** (ultima base): numero in una lingua **4 su 5** (prima 1 su 5: I13
  funziona; il mancato `FONTE_ASSENTE`), task inesistente 5 su 5, negazione in una lingua 1 su
  2, limite invertito 0 su 1 (CORRETTO VERIFICATO), negazione in due lingue 0 su 1 e numero del
  manuale 0 su 1 (`EVIDENZA_NON_TROVATA`). WARNING per ciclo senza errori: 7,8 `ERRORE_TECNICO`
  (targhe), 4,8 `EVIDENZA_NON_TROVATA`, 2,0 `FONTE_ASSENTE`, 0,2 `DR_NON_VERIFICATA`.
- **Grande** (23 cicli, 20 errori). Base 9 stabili (9, 11, 10), 0 falsi, 1 da verificare
  (895167b9 005, 1 su 3), 0,0109 $ e 15 s. `lingue_tra_loro` 14 stabili (17, 16, 17), **12-13
  falsi errori**, 31-37 da verificare, 0,0239 $ e 39 s. `procedura_dr` 9 stabili (10, 10, 9), 0
  falsi, **0 da verificare**, 0,0107 $ e 15 s.
- **Cosa trova in più `lingue_tra_loro`** (grande): 22f586bb 010, 030, 050, 060 (limite,
  numero di documento, materiale, negazione cambiati in una lingua: nella base `FONTE_ASSENTE`),
  298bc28e 035, 895167b9 050 e 060, f355dc3c 050 sempre. **I suoi falsi errori**: titoli e frasi
  di presa in carico tradotti liberamente («presa in carico da perizia» e «handling of the part
  to the repair area», «collaudo finale, documentale e versamento» e «general visual
  inspection», «prelievo ed identificazione della pala» e «identification of the blade»), un
  codice con o senza la lettera davanti, «carta abrasiva» e «crocus cloth». Tre casi sono da
  far guardare a Copilot perché potrebbero essere **differenze vere** nelle stampe giuste:
  «larghezza» contro «length» (04ecaabe 030, 2d724fba 030), «superiore a 4X» contro «not to
  exceed 4X» (737dec71 060), «sul lubrificante applicato» contro «on the coating» (8bdb25d5
  040). Anche c5ff3cd6 030 e f355dc3c 040 (in attesa) escono ERRATO 3 su 3.
- **Cosa fa `procedura_dr`** (grande): 895167b9 005 non è più ERRATO (era il falso errore
  visto da Copilot); 895167b9 010 e 030 non più trovati (`EVIDENZA_NON_TROVATA`: erano trovati
  per il motivo «il manuale vieta la raccordatura», che la deroga toglie); 895167b9 060 trovato
  3 su 3 (nella base 0 su 3). È quello che la proposta si aspettava.
- **In attesa**: 04ecaabe 050 ERRATO 3 su 3 con tutte (P7: lo toglie I8); 2d724fba 050 2-3 su 3.
- **Decisione:** `procedura_dr` **entra nella base** anche se la regola dice «pari alla base»:
  toglie un falso errore confermato e trova gli errori per il motivo giusto (eccezione scritta
  qui). `lingue_tra_loro` **scartata**. **Lezione:** confrontare le due lingue tra loro trova
  proprio gli errori che mancavano, ma Haiku prende per errore ogni traduzione non letterale.
  Da qui I15: solo negazioni, numeri e limiti al contrario, con un controllo del codice sulle
  parole copiate; il resto al massimo WARNING.

| Data | Esperimento | Variante | Concordanza | Costo | Tempo | Decisione | Considerazioni |
|---|---|---|---|---|---|---|---|
| 2026-11-27 | campagna, Haiku, piccolo (29 cicli e copie, seme 2), 3 prove | `base` | stabili 20 su 35 (21, 20, 21); mai visti 1 su 5; 0 falsi; 1 da verificare; precisione 95%; 15,0 WARNING | 0,0078 $ a ciclo | 13 s (45 s) | riferimento | I13 nella base: numero in una lingua 4 su 5 |
| 2026-11-27 | come sopra | `lingue_tra_loro` | stabili 30 (31, 31, 31); mai visti 3 su 5; **33 falsi**; 14 da verificare; precisione 55% | 0,0136 $ | 22 s (57 s) | **scartata** | traduzioni libere prese per errori |
| 2026-11-27 | come sopra | `procedura_dr` | stabili 20; mai visti 1 su 5; 0 falsi; 0 da verificare; precisione 100% | 0,0073 $ | 12 s (1 min 03 s) | **nella base** (pari, ma toglie un falso errore) | |
| 2026-11-27 | campagna, Haiku, grande (23 cicli), 3 prove | `base` | stabili 9 su 20 (9, 11, 10); 0 falsi; 1 da verificare (895167b9 005); precisione 90%; 19,9 WARNING | 0,0109 $ | 15 s (50 s) | riferimento | |
| 2026-11-27 | come sopra | `lingue_tra_loro` | stabili 14 (17, 16, 17); **38 falsi**; 37 da verificare; precisione 26% | 0,0239 $ | 39 s (1 min 13 s) | **scartata** | |
| 2026-11-27 | come sopra | `procedura_dr` | stabili 9 (10, 10, 9); 0 falsi; 0 da verificare; precisione 100% | 0,0107 $ | 15 s (43 s) | **nella base** | perde 895167b9 010 e 030 (motivo sbagliato), trova 060 |
| 2026-11-27 | campagna finale, Haiku, piccolo (28 cicli e copie, seme 3), 3 prove (14:05-15:13) | `base` | stabili 20 su 34 (20, 20, 21); mai visti 1 su 4; 0 falsi; 0 da verificare; precisione 100%; 7,7 WARNING | 0,0077 $ | 16 s (50 s) | riferimento | targhe N/A: i WARNING per ciclo scendono da 15 a 7,7 |
| 2026-11-27 | come sopra | `fonte_ispezione` | stabili 20 (22, 22, 20); mai visti 1 su 4; 0 falsi; 0 da verificare; 7,7 WARNING | 0,0087 $ | 17 s (59 s) | non si tiene (pari) | non toglie il falso errore P7: 04ecaabe 050 e 2d724fba 050 ERRATO 3 su 3 |
| 2026-11-27 | come sopra | `finale` | stabili **23** (24, 23, 24); mai visti 1 su 4; 0 falsi; 0 da verificare; **5,5 WARNING** | 0,0120 $ | 22 s (1 min 17 s) | **si tiene** | trova in più 22f586bb 010 e 060 (negazione e limite in una lingua); 737dec71 060 ERRATO 3 su 3 (errore vero della stampa, P10) |
| 2026-11-27 | campagna finale, Haiku, grande (23 cicli), 3 prove (16:03-17:02) | `base` | stabili 10 su 20 (10, 10, 10); 0 falsi; 0 da verificare; precisione 100%; 10,8 WARNING | 0,0110 $ | 15 s (47 s) | riferimento | |
| 2026-11-27 | come sopra | `fonte_ispezione` | stabili 9 (9, 10, 10); 0 falsi; 0 da verificare; 10,8 WARNING | 0,0123 $ | 16 s (1 min 04 s) | non si tiene | qui toglie 04ecaabe 050 (0 su 3) ma non 2d724fba 050 (2 su 3): sul piccolo nessun effetto. Da capire (P12) |
| 2026-11-27 | come sopra | `finale` | stabili **12** (12, 13, 13); 0 falsi; **3 da verificare** (060 di tre cicli veri: 2, 2 e 3 prove su 3); precisione 80%; 9,3 WARNING | 0,0193 $ | 28 s (1 min 16 s) | **si tiene** | 298bc28e 035 diventa N/A `FUORI_TEMA` (era un errore da trovare: da guardare); i 3 da verificare forse sono l'errore vero di 737dec71 060 nella stessa stampa tipo (P12) |

**Sintesi della campagna finale (27-11).** `finale` è la configurazione per la produzione,
appena la P12 dice che i 3 ERRATO dei cicli veri sono errori veri. `fonte_ispezione` da sola
non serve, e il falso errore P7 (raccordatura «4 volte») resta anche con `finale`: in
produzione la v2 lo darà sulle stampe A1 (da correggere dopo, H16 e P12). Attenzione: quasi
tutto il guadagno di `finale` viene dal codice che confronta le lingue (I15), non dal modello.
Dalla v1 sugli stessi cicli (sera): la lista degli errori noti era incompleta su 38960731,
8d3c673c ed e9b74c84 (cambi di codici, schede, macchine: H17-H19); 6 operazioni aggiunte,
le prove si ricalcolano senza rifarle.

**Campagna 4e (27-11 notte, seme 3, 3 prove): base contro `schede_e_limiti` (MG40 + MG41).**
Decisione: **si tiene**, nella base. Considerazioni: è il salto più grande da quando ci sono i
controlli del codice (+4 stabili sul piccolo, +5 sul grande) e toglie gli ultimi falsi errori
(la regola «almeno N»); il costo non sale perché le schede le controlla il codice. Le 060 dei
cicli veri restano instabili: il confronto stretto tra le lingue dipende dal modello. Prossimo:
P13, poi MG75 (limiti al contrario tra le lingue dal codice) e MG46 (materiale tra le lingue)
in una campagna.

**Versione quasi finale (27-11 notte, Claude).** Non è una campagna: le regole nuove del codice
provate sul testo delle 14 stampe (`tests/test_real_prints.py`): 5 errori in più (e9b74c84 040,
298bc28e 035, 895167b9 030, 737dec71 060, più la 060 sempre sui cicli veri), 0 ERRATO fuori
dagli errori noti, 8d3c673c 060 tolto. Da misurare sul PC: `eval senza-modello`, poi la
campagna `quasi_finale` (COPILOT passo 4h).

**Prova senza modello (27-11 notte, sul PC, 0 $).** Piccolo 39 su 45, grande 29 su 31, 0 falsi
errori, 4 ERRATO da verificare nei cicli veri del grande (P15). Decisione: la campagna
`quasi_finale` aspetta la P15. Considerazioni: il codice da solo trova più della v1 (16 contro
15 sulle sue 19 operazioni); il modello serve ancora per le copie cieche e per dire OK con la
frase del manuale. Seconda prova con MG81: piccolo 41 su 45, grande 31 su 31; i 4 da
verificare erano falsi errori di MG47 (P15), corretti.

**Campagna `quasi_finale` (27-11 23:41 - 28-11 00:35, 3 prove sul piccolo e 3 sul grande,
2,36 $).** Decisione: **si tiene**, è la base (era già nel codice della base: le prove della
base erano fatte con il codice di prima). Numeri: piccolo 42 su 45 stabili (base 31,
`schede_e_limiti` 35), mai visti per il modello 1 su 4, 0 falsi errori, 0 da verificare,
precisione 100%, 4,9 WARNING per ciclo senza errori, 0,0114 $ e 20 s a ciclo (il più lento
55 s); grande 31 su 31 (base 20, `schede_e_limiti` 24), 0 falsi errori, 0 da verificare, 8,9
WARNING per ciclo, 0,0188 $ e 30 s (il più lento 56 s, il più caro 0,035 $). Errori tecnici 0
su 417 e 0 su 516. Metriche di controllo, piccolo: dei 9 mancati (3 errori in 3 prove) 3 con
CORRETTO (falsi OK), 4 con WARNING, 2 con N/A; grande: nessun mancato. Considerazioni: tutti
gli errori noti (anche le 060 dei cicli veri, 22f586bb 030, 298bc28e 035, e9b74c84 040,
895167b9 030) trovati in 3 prove su 3: il codice ha tolto l'instabilità del modello (MG49 non
serve). I 3 mancati sono copie cieche che trova solo il modello confrontando con il manuale:
nell'ultima base sul piccolo `limite_invertito` CORRETTO VERIFICATO, `negazione_due_lingue`
N/A FUORI_TEMA, `numero_manuale` WARNING EVIDENZA_NON_TROVATA (per `quasi_finale`: passo 4i).
Le 2 ERRATO da verificare della P13 (8d3c673c 060, b1261d11 060) spariscono (MG78). In attesa
(0 su 3 in tutte le varianti, come previsto): 04ecaabe 030, 2d724fba 030, 5ff17062 040, c5ff3cd6
030, f355dc3c 040. Prossimo: report rifatto (passo 4i), poi MG83 (meno avvisi, soprattutto sul
grande) e MG87 (i falsi OK delle copie cieche).
