# v1 contro v2

Il confronto tra la v1 (quella in QA e in produzione) e la v2, aspetto per aspetto. Serve a
vedere sempre dove la v2 è già meglio, dove è ancora peggio e che cosa migliorare.

- **Da dove vengono i numeri.** v1: `docs/CONFRONTO_V1_14_CICLI.md` (la v1 sulle 14 stampe note,
  27-11). v2: la campagna del passo 4d (base nuova, 3 prove, 27-11 sera) e i riepiloghi
  ricalcolati con gli errori noti di adesso.
- **Attenzione.** La v1 ha nella conoscenza documenti che la v2 non ha ancora (l'indice delle
  schede con materiale e motore, una parte del capitolo 70 dell'SPM con le classi dell'acido).
  Quando la v2 manca un errore, la colonna «perché» dice se manca **il documento** (si chiude
  con la grande ingestion) o **il controllo** (si chiude con il codice).
- **Si aggiorna** dopo ogni campagna e dopo la grande ingestion: Claude cambia le righe toccate
  e scrive la data in fondo.

**Simboli:** ✅ meglio · ➖ pari · ❌ peggio · 🔶 in prova.

---

## 1. Il riassunto

| | v1 | v2 (27-11 sera) |
|---|---|---|
| Falsi errori sulle 4 stampe giuste che la v1 valida | **6** | **1-2** (04ecaabe 050 in 2 prove su 3; 2d724fba 050, stesso testo): li deve togliere la regola «almeno N» (passo 4e) |
| Errori trovati nelle 6 stampe con errori che la v1 valida (19 operazioni) | **15 su 19** | **13 su 19**, più c5ff3cd6 030 come avviso «Scheda mancante» |
| Stampe lette (su 14) | 10 | **14** |
| Lingue lette | inglese | **italiano e inglese**, anche tra loro |
| Ogni errore ha la frase del manuale ritrovata dal programma | no | **sì** |
| Dice quello che non ha potuto controllare | no (scrive OK) | **sì**, `[non controllabile]` |
| Stabilità misurata (stessa stampa, più prove) | mai misurata | **misurata**: errori stabili in 3 prove su 3 |
| Costo e tempo a ciclo | non misurati | **0,011-0,019 $, 16-26 s** |
| Avvisi (WARNING) per ciclo | **1-2** | 6-9 (sul PC molti sono «non controllabile»: registro delle macchine e documenti che mancano) |

**In una frase:** la v2 dà molti meno errori falsi, legge tutte le stampe e tutte e due le
lingue, e ogni errore ha la prova; la v1 trova ancora 2 errori in più (schede e una parola
cambiata in inglese) e scrive meno avvisi. Se il controllo delle schede (H18, passo 4e)
funziona, la v2 arriva a 15 su 19 come la v1; con i documenti della grande ingestion a 17.

---

## 2. Aspetto per aspetto

### 2.1 Errori falsi e fiducia

| Aspetto | Chi è meglio | v1 | v2 | Da fare |
|---|---|---|---|---|
| Falsi errori sulle stampe giuste | ✅ **v2** | 6 su 4 stampe giuste: la fonte giusta segnata sbagliata (2 volte), la scheda (2), due frasi con la stessa istruzione scritta in modo diverso (2) | 1-2, sempre la stessa frase (`almeno 4 volte` contro `more than 4 times`) | variante `schede_e_limiti` (regola «almeno N»), passo 4e |
| Falsi errori su stampe con errori | 🔶 da capire | 2 su 8d3c673c (060 e 070) | anche la v2 dà ERRATO su 8d3c673c 060 e 070, 3 prove su 3 | domanda P13: se sono errori veri, la v1 aveva ragione |
| La prova di quello che dice | ✅ **v2** | testo libero del modello, a volte si contraddice («typo» su un codice giusto) | la frase citata la ritrova il programma nel manuale; senza la frase niente ERRATO | — |
| Conferma degli errori | ✅ **v2** | un solo giudizio | un ERRATO del modello si conferma con una seconda domanda | — |
| Stessa risposta ogni volta | ✅ **v2** | mai misurata | misurata con 3 prove: gli errori «stabili» escono 3 volte su 3 | alcuni escono 2 volte su 3 (22f586bb 060, 414d85ca 060): F4 |
| «OK» vuol dire | ✅ **v2** | «non ho trovato contraddizioni» (anche se non ha controllato) | «ho controllato con il manuale» | — |
| Quello che non ha potuto controllare | ✅ **v2** | non lo dice | WARNING `[non controllabile]` (manca il documento, il registro, la DR) separato da `[da guardare]` (un dubbio vero) | il frontend può mostrarli diversi (F7) |
| Quanti avvisi | ❌ v2 | 1-2 per ciclo | 6-9 per ciclo; in produzione meno (registro delle macchine acceso, più documenti) | misurare in QA |

### 2.2 Errori trovati, per tipo

| Tipo di errore | Chi è meglio | v1 | v2 | Da fare |
|---|---|---|---|---|
| **Codice di task sbagliato** (una cifra cambiata, un task che il manuale non ha) | ✅ **v2** | lo trova con il modello, a volte con la correzione giusta, a volte dà «codice incompleto» su codici giusti | lo trova **il codice, senza modello**: il codice non c'è nel manuale ma ci sono i suoi fratelli (`TASK_INESISTENTE`), con l'elenco dei fratelli. Sempre uguale, gratis | — |
| Task accanto all'operazione diverso da quello della testata | ➖ pari | lo trova | lo trova il codice (H17, dal 27-11 sera) | — |
| Task di un altro pezzo (stadio 6 invece di 7) | ❌ v2 | lo trova (8d3c673c 140, con il nome del motivo) | trova la 140 per un altro motivo (un numero in una lingua) | F2 |
| Numeri cambiati in una lingua sola | ✅ **v2** | non li trova se sono in italiano (5ff17062 010, f355dc3c 010) | li trova il codice, confrontando i numeri delle due lingue | — |
| Limiti cambiati in una lingua (la 010 su più pagine) | ✅ **v2** | in parte | li trova il codice (dal 27-11 sera) | — |
| Negazione tolta o frase che dice il contrario | ✅ **v2** | solo in inglese | in tutte e due le lingue; trova anche 2 errori veri in stampe che si credevano giuste (737dec71 060, 04ecaabe 030) | una negazione tolta in **tutte e due** le lingue è finita N/A «fuori tema» in una copia cieca (F3) |
| Limite al contrario («al massimo» invece di «almeno») | 🔶 da capire | non misurato | lo trova tra le lingue; una copia cieca con il limite invertito in tutte e due le lingue è uscita CORRETTO | guardare le copie cieche della campagna 4e |
| Una parola cambiata in una lingua (non numero, non negazione) | ❌ v2 | la trova (e9b74c84 040, «raccordato» invece di «rimosso») | non la trova | F1 |
| Materiale cambiato in una lingua | ❌ v2 | non misurato (895167b9 è una A6: la v1 non la legge) | 895167b9 050 esce CORRETTO | F1 |
| **Scheda di processo sbagliata** (altro motore, altro materiale) | ❌ v2, 🔶 in prova | la trova: ha l'indice delle schede con materiale e motore | oggi controlla solo che la scheda esista; H18 (stesso controllo, dal codice) è nella variante `schede_e_limiti` | passo 4e; poi l'indice delle schede con il materiale nella grande ingestion |
| Scheda tolta in un processo speciale | ➖ pari | errore | avviso «Scheda mancante» (regola decisa dall'utente il 27-11) | — |
| Macchina che non esiste o non è attiva | ➖ pari (in produzione) | registro delle macchine attive (Redshift) | lo stesso registro in produzione; sul PC è spento (N/A) | provarlo in QA |
| La stessa operazione con due macchine su due pagine | ✅ **v2** | non sempre | lo trova il codice (H19, dal 27-11 sera) | — |
| Classe dell'acido (una lettera) | ❌ v2 (documento) | la trova: ha il capitolo dell'SPM | manca il documento (f355dc3c 040, 5ff17062 040 in attesa) | grande ingestion |
| Errori nelle stampe DR | ✅ **v2** | si ferma senza serial e condition | le legge; usa la procedura della DR come deroga (`procedura_dr`) | DR senza serial: F5 |

### 2.3 Stampe, lingue, documenti

| Aspetto | Chi è meglio | v1 | v2 |
|---|---|---|---|
| Stampe DR senza serial o condition (A6) | ✅ **v2** | si ferma (3 stampe su 14) | le legge; il serial, se c'è, lo prende dalla stampa |
| Stampe che si caricano | ✅ **v2** | una non si carica (298bc28e) | 14 su 14 |
| Lettura della stampa | ✅ **v2** | modello | parser PVRM320 senza modello (gratis, sempre uguale); il modello solo se il layout non si riconosce |
| Italiano | ✅ **v2** | legge l'inglese | legge le due lingue e le confronta |
| Documenti nella conoscenza | ❌ v2 | più documenti (indice delle schede con materiale, parte dell'SPM) | 75 documenti oggi; la grande ingestion li porta a circa 2900 |
| Come trova il testo del manuale | ✅ **v2** (in teoria) | ricerca per somiglianza (indice OpenSearch, i primi K pezzi) | ricerca per codice esatto: il manuale citato, il task citato, le sue righe |
| Con 2900 documenti | ✅ **v2** (misurato in finto) | non misurato: con più documenti la ricerca per somiglianza può prendere pezzi di altri manuali | il modello riceve lo stesso testo di oggi; avvio 4,2 s, 164 MB, ricerca di un task 6-9 µs con 2900 documenti finti (`eval scala`) |

### 2.4 Servizio, costo, sicurezza

| Aspetto | Chi è meglio | v1 | v2 |
|---|---|---|---|
| Costo per ciclo | ✅ **v2** (misurato) | non misurato | 0,011-0,019 $ |
| Tempo per ciclo | ✅ **v2** (misurato) | non misurato | 16-26 s |
| Prove automatiche (campagne, copie cieche, errori noti) | ✅ **v2** | nessuna | campagne con varianti, copie cieche, gruppo nascosto, riepiloghi ricalcolati |
| Test del codice | ✅ **v2** | pochi | più di 1000 test, controlli di tipo e di stile prima di ogni salvataggio |
| Frontend | ➖ pari | — | stesso payload e stesse rotte della v1 (`Warning:` davanti al testo) |
| Accessi (chi vede EJ200) | ➖ pari | `cv`, `cv_ej200`, `all` | le stesse regole |
| Conoscenza aggiornata senza riavvio | ✅ **v2** | — | ogni 5 minuti rilegge il puntatore; una versione rotta non sostituisce quella buona |
| Una conoscenza rotta all'avvio | ❌ v2 | — | il servizio non parte (B7): per questo EJ200 si accende dopo il civile |
| **EJ200** | ❌ v2 (per ora) | in produzione | mai provata con i dati veri: dal 27-11 si prova sul PC con `prova-ej200` (passo 4f), poi in QA |

---

## 3. Errore per errore

Le 6 stampe con errori che la v1 valida, 19 operazioni. «✔» trovato, «—» non trovato,
«avviso» WARNING al posto dell'ERRATO.

| Stampa · op. | Che errore è | v1 | v2 | Se la v2 lo manca, perché |
|---|---|:-:|:-:|---|
| c5ff3cd6 030 | scheda tolta | ✔ | avviso | regola decisa: avviso «Scheda mancante» |
| c5ff3cd6 040 | un numero cambiato | ✔ | ✔ | |
| f355dc3c 010 | tre numeri cambiati (in italiano) | — | ✔ | |
| f355dc3c 030 | numeri e parole cambiati | ✔ | ✔ | |
| f355dc3c 040 | una lettera cambiata (la classe) | — | — | **documento** (in attesa) |
| f355dc3c 050 | una frase che dice il contrario (in italiano) | — | ✔ | |
| 38960731 010 | limiti cambiati in inglese | ✔ | ✔ | |
| 38960731 030 | task cambiato (una cifra) | ✔ | ✔ | |
| 38960731 040 | macchina cambiata in una pagina, scheda e suo task | ✔ | ✔ | |
| 38960731 050 | un numero, una parola al contrario, la scheda | ✔ | ✔ | |
| 5ff17062 010 | tre numeri cambiati (in italiano) | — | ✔ | |
| 5ff17062 030 | numeri in una lingua, parole nell'altra | ✔ | ✔ | |
| 5ff17062 040 | la classe cambiata | ✔ | — | **documento** (in attesa) |
| 5ff17062 050 | frase dei limiti sostituita, negazioni tolte | ✔ | ✔ | |
| 8d3c673c 100 | scheda e suo task cambiati | ✔ | — | **controllo**: H18 in prova (passo 4e) |
| 8d3c673c 110 | scheda e suo task cambiati | ✔ | — | **controllo**: H18 in prova (passo 4e) |
| 8d3c673c 140 | un numero in una lingua (la v1: task di un altro stadio) | ✔ | ✔ | |
| e9b74c84 025 | un numero in una lingua, task cambiato | ✔ | ✔ | |
| e9b74c84 040 | una parola cambiata in inglese | ✔ | — | **controllo**: F1 |
| **Totale** | | **15** | **13** + 1 avviso | 2 documento, 3 controllo |

**Falsi errori sulle stampe giuste** (04ecaabe, 4e64d49a, 8bdb25d5, 2d724fba):

| Stampa · op. | v1 | v2 | Nota |
|---|:-:|:-:|---|
| 04ecaabe fonte | errore | — | il testo dice che la fonte è giusta |
| 04ecaabe 040 (scheda) | errore | — | |
| 04ecaabe 050 | — | errore in 2 prove su 3 | «almeno 4» contro «più di 4»: non è un errore (regola dell'utente) |
| 4e64d49a fonte | errore | — | come 04ecaabe |
| 8bdb25d5 030 | errore | — | «coating» e «lubrificante applicato» sono la stessa cosa |
| 2d724fba 030 | errore | — | la stessa regola scritta in due modi |
| 2d724fba 040 (scheda) | errore | — | |
| 2d724fba 050 | — | da contare (era in attesa) | stesso testo di 04ecaabe 050 |
| **Totale** | **6** | **1-2** | |

**Fuori dal confronto** (la v1 non dà risultati):

| Stampa | Perché la v1 no | v2 |
|---|---|---|
| 22f586bb, 895167b9 (A6, DR) | si ferma: serial e condition | trova una parte dei 4 errori; 22f586bb 030 e 050 «manca la fonte» (DR senza serial, F5); 895167b9 050 CORRETTO (F1) |
| 737dec71 (A6, giusta) | si ferma | trova l'errore vero della 060 («superiore» contro «not to exceed») |
| 298bc28e | non si carica | 035 diventa N/A «fuori tema» (F3) |
| 414d85ca, 477abec8, ffadfe16 (cicli veri) | non provati | trovano la stessa 060 sbagliata di 737dec71 (errore vero, P12) |
| b1261d11 (ciclo vero) | non provato | ERRATO sulla 060 da verificare (P13) |

---

## 4. Cosa migliorare, in ordine

| # | Cosa | Chiude | Quando |
|---|---|---|---|
| 1 | Regola «almeno N» (variante `schede_e_limiti`) | i falsi errori di 04ecaabe 050 e 2d724fba 050 | passo 4e |
| 2 | H18, la scheda coerente con l'operazione | 8d3c673c 100 e 110 | passo 4e |
| 3 | Grande ingestion (indice delle schede con il materiale, capitolo 70 dell'SPM) | f355dc3c 040, 5ff17062 040; meno avvisi «manca la fonte» | passo 5 |
| 4 | P13: 8d3c673c 060 e 070, b1261d11 060 | sapere se la v1 aveva ragione | passo 4e |
| 5 | Una parola o un materiale cambiati in una lingua (F1) | e9b74c84 040, 895167b9 050 | da decidere |
| 6 | «Fuori tema» più prudente (F3) | 298bc28e 035, la copia cieca con la negazione | da decidere |
| 7 | Task di un altro pezzo (F2) | la v1 lo trova per il motivo giusto | da decidere |
| 8 | Meno avvisi per ciclo | la v1 ne scrive meno | in QA, con il registro delle macchine |
| 9 | EJ200 provata (passo 4f, poi QA) | la v1 è in produzione su EJ200 | dopo l'ingestion EJ200 |

---

*Ultimo aggiornamento: 27-11 notte, dopo la campagna del passo 4d. Prossimo: dopo la campagna
del passo 4e e la risposta alla P13.*
