# v1 contro v2

Numeri: v1 da `CONFRONTO_V1_14_CICLI.md`; v2 dalla campagna 4d (3 prove, 27-11). La v1 ha
documenti che la v2 non ha ancora: per ogni errore mancato si dice se manca il **documento** o
il **controllo**. Claude aggiorna il file dopo ogni campagna.

✅ v2 meglio · ❌ v2 peggio · ➖ pari · 🔶 in prova · ⬜ non misurato

## 1. Pronti per il passo dopo?

Si passa quando tutte le righe del cancello sono ✅. Soglie proposte da Claude.

**A · QA**

| | Cosa | Soglia | Oggi |
|:-:|---|---|---|
| ❌ | Falsi errori sulle stampe giuste | 0 | 1 (04ecaabe 050) |
| ❌ | Errori trovati sulle 19 operazioni della v1 | ≥ 15 | 13 + 1 avviso |
| ✅ | Errori stabili, piccolo | ≥ 70% | 70% (30/43) |
| ✅ | Errori stabili, grande | ≥ 60% | 62% (18/29) |
| ❌ | ERRATO da verificare | 0 | 3 (P13) |
| ✅ | Stampe lette | 14/14 | 14/14 |
| ✅ | Costo per ciclo | ≤ 0,05 $ | 0,011-0,019 $ |
| ✅ | Tempo per ciclo | ≤ 2 min | 16-26 s |
| ✅ | Test | 0 `failed` | 0 |
| ⬜ | `kb-check` dopo la grande ingestion | nessun `Errore:` | — |
| ⬜ | Prova di controllo sul grande | 0 falsi errori, errori stabili non in calo | — |
| ✅ | Avvio con 2900 documenti | ≤ 2 min | 4,2 s (finto) |

**B · EJ200 in QA**

| | Cosa | Soglia | Oggi |
|:-:|---|---|---|
| ❌ | Cancello A | tutto ✅ | no |
| ⬜ | `prova-ej200`: stampe validate | tutte | — |
| ⬜ | `prova-ej200`: cartella temporanea cancellata | sempre | — |
| ⬜ | ERRATO EJ200 visti da un esperto | 0 falsi | — |
| ❌ | EJ200 rotta non ferma MOS e DR (B7) | sì | no |

**C · Produzione**

| | Cosa | Soglia | Oggi |
|:-:|---|---|---|
| ❌ | Cancelli A (e B, se va EJ200) | tutto ✅ | no |
| ⬜ | QA: un MOS e un DR veri, con e senza serial | nessun errore tecnico | — |
| ⬜ | QA: targhe vere (Redshift) | 0 targhe giuste ERRATO | — |
| ⬜ | Esperto su 5-10 risultati QA | 0 falsi, ≥ 80% trovati | — |
| ⬜ | Avvisi per ciclo in QA | ≤ 5, `[da guardare]` ≤ 2 | 6-9 sul PC |
| ⬜ | Accessi EJ200 in QA | solo `cv_ej200` e `all` | ok nei test |
| ⬜ | Ritorno alla v1 (`qa --torna-alla-v1`) | provato | — |

## 2. Aspetto per aspetto

| Aspetto | | v1 | v2 |
|---|:-:|---|---|
| Falsi errori, stampe giuste | ✅ | 6 | 1-2 (stessa frase, «almeno 4» contro «more than 4») |
| Errori trovati (19 op.) | ❌ | 15 | 13 + 1 avviso; 15 se H18 funziona, 17 con la grande ingestion |
| Prova di ogni errore | ✅ | testo libero | frase del manuale ritrovata dal programma |
| «OK» vuol dire | ✅ | nessuna contraddizione vista | controllato con il manuale |
| Cosa non ha controllato | ✅ | non lo dice | `[non controllabile]` separato da `[da guardare]` |
| Avvisi per ciclo | ❌ | 1-2 | 6-9 (sul PC registro spento e documenti mancanti) |
| Stabilità | ✅ | non misurata | misurata su 3 prove |
| **Codici di task sbagliati** | ✅ | col modello, a volte «incompleto» su codici giusti | dal codice, senza modello: codice assente e fratelli presenti |
| Task dell'operazione contro la testata | ➖ | sì | sì (H17) |
| Task di un altro stadio | ❌ | sì | no (F2) |
| Numeri o limiti cambiati in una lingua | ✅ | solo inglese | due lingue, dal codice |
| Negazioni e frasi al contrario | ✅ | solo inglese | due lingue; 2 errori veri trovati in stampe «giuste» |
| Parola o materiale cambiati in una lingua | ❌ | la parola sì | no (F1) |
| Scheda sbagliata (motore, materiale) | ❌ 🔶 | sì (indice schede) | H18 in prova (4e) |
| Scheda tolta | ➖ | errore | avviso «Scheda mancante» (regola decisa) |
| Macchine non attive | ➖ | registro | stesso registro in produzione |
| Due macchine per un'operazione | ✅ | non sempre | sì (H19) |
| Classe dell'acido | ❌ | sì | manca il documento |
| Stampe DR senza serial (A6) | ✅ | si ferma | le legge |
| Stampe lette | ✅ | 10/14 | 14/14 |
| Lettura della stampa | ✅ | modello | parser, gratis e sempre uguale |
| Ricerca nel manuale | ✅ | per somiglianza (OpenSearch) | per codice esatto |
| 2900 documenti | ✅ | non misurato | stesso testo al modello; 4,2 s, 164 MB (finto) |
| Costo e tempo | ✅ | non misurati | 0,011-0,019 $, 16-26 s |
| Prove automatiche e test | ✅ | no | campagne, copie cieche, oltre 1000 test |
| Frontend e accessi | ➖ | — | stesso payload, stesse regole |
| Conoscenza nuova senza riavvio | ✅ | — | sì, ogni 5 minuti |
| Conoscenza rotta all'avvio | ❌ | — | il servizio non parte (B7) |
| EJ200 | ❌ | in produzione | mai provata (passo 4f) |

## 3. Errore per errore

Le 6 stampe con errori che la v1 valida. ✔ trovato · — mancato.

| Stampa · op. | Errore | v1 | v2 | Manca |
|---|---|:-:|:-:|---|
| c5ff3cd6 030 | scheda tolta | ✔ | avviso | regola |
| c5ff3cd6 040 | un numero | ✔ | ✔ | |
| f355dc3c 010 | tre numeri, in italiano | — | ✔ | |
| f355dc3c 030 | numeri e parole | ✔ | ✔ | |
| f355dc3c 040 | la classe | — | — | documento |
| f355dc3c 050 | frase al contrario, in italiano | — | ✔ | |
| 38960731 010 | limiti in inglese | ✔ | ✔ | |
| 38960731 030 | task, una cifra | ✔ | ✔ | |
| 38960731 040 | macchina, scheda, task | ✔ | ✔ | |
| 38960731 050 | numero, parola, scheda | ✔ | ✔ | |
| 5ff17062 010 | tre numeri, in italiano | — | ✔ | |
| 5ff17062 030 | numeri e parole | ✔ | ✔ | |
| 5ff17062 040 | la classe | ✔ | — | documento |
| 5ff17062 050 | limiti e negazioni | ✔ | ✔ | |
| 8d3c673c 100 | scheda e task | ✔ | — | controllo (H18) |
| 8d3c673c 110 | scheda e task | ✔ | — | controllo (H18) |
| 8d3c673c 140 | numero in una lingua | ✔ | ✔ | |
| e9b74c84 025 | numero e task | ✔ | ✔ | |
| e9b74c84 040 | una parola in inglese | ✔ | — | controllo (F1) |
| **Totale** | | **15** | **13** | 2 documento, 3 controllo |

**Falsi errori sulle stampe giuste**

| Stampa · op. | v1 | v2 | Perché è falso |
|---|:-:|:-:|---|
| 04ecaabe fonte | ✘ | | il testo dice che è giusta |
| 04ecaabe 040 | ✘ | | scheda giusta |
| 04ecaabe 050 | | ✘ 2/3 | «almeno 4» = «più di 4» (regola) |
| 4e64d49a fonte | ✘ | | come 04ecaabe |
| 8bdb25d5 030 | ✘ | | stessa istruzione |
| 2d724fba 030 | ✘ | | stessa regola |
| 2d724fba 040 | ✘ | | scheda giusta |
| 2d724fba 050 | | da contare | come 04ecaabe 050 |

**Fuori dal confronto** (la v1 non dà risultati)

| Stampa | v2 |
|---|---|
| 22f586bb, 895167b9 (DR senza serial) | parte degli errori; mancati per DR senza serial (F5) e materiale (F1) |
| 737dec71 060; 414d85ca, 477abec8, ffadfe16 060 | errore vero trovato |
| 298bc28e 035 | N/A «fuori tema» (F3) |
| b1261d11 060 | da verificare (P13) |

*Aggiornato il 27-11 notte, dopo il 4d. Prossimo: dopo il 4e e la P13.*
