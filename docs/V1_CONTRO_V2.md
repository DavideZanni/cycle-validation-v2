# v1 contro v2

Numeri: v1 da `CONFRONTO_V1_14_CICLI.md`; v2 dalla campagna 4e (base con `schede_e_limiti`, 3
prove, 27-11) e dalla prova senza modello del 27-11 notte (solo i controlli del codice: quello
che trovano lo trovano sempre). La v1 ha documenti che la v2 non ha ancora: per ogni errore mancato si dice se
manca il **documento** o il **controllo**. Claude aggiorna il file dopo ogni campagna.

✅ v2 meglio · ❌ v2 peggio · ➖ pari · 🔶 in prova (atteso con le migliorie del 27-11 notte, da
misurare al passo 4h) · ⬜ non misurato

## 1. Pronti per il passo dopo?

Si passa quando tutte le righe del cancello sono ✅. Soglie proposte da Claude.

**A · QA**

| | Cosa | Soglia | Oggi |
|:-:|---|---|---|
| ✅ | Falsi errori sulle stampe giuste | 0 | 0 |
| ✅ | Errori trovati sulle 19 operazioni della v1 | ≥ 15 | 16, dal solo codice (prova senza modello) |
| ✅ | Errori stabili, piccolo | ≥ 70% | 79% (34/43) |
| ✅ | Errori stabili, grande | ≥ 60% | 79% (23/29) |
| ✅ | ERRATO da verificare | 0 | 0 senza modello, piccolo e grande (dopo la correzione di MG47, P15); da confermare con la campagna |
| ✅ | Stampe lette | 14/14 | 14/14 |
| ✅ | Costo per ciclo | ≤ 0,05 $ | 0,011-0,018 $ |
| ✅ | Tempo per ciclo | ≤ 2 min | 16-24 s |
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
| ✅ | EJ200 rotta non ferma MOS e DR (MG44) | sì | sì (test) |

**C · Produzione**

| | Cosa | Soglia | Oggi |
|:-:|---|---|---|
| ❌ | Cancelli A (e B, se va EJ200) | tutto ✅ | no |
| ⬜ | QA: un MOS e un DR veri, con e senza serial | nessun errore tecnico | — |
| ⬜ | QA: targhe vere (Redshift) | 0 targhe giuste ERRATO | — |
| ⬜ | Esperto su 5-10 risultati QA | 0 falsi, ≥ 80% trovati | — |
| ⬜ | Avvisi per ciclo in QA | ≤ 5, `[da guardare]` ≤ 2 | 5,4-8,7 sul PC |
| ⬜ | Accessi EJ200 in QA | solo `cv_ej200` e `all` | ok nei test |
| ⬜ | Ritorno alla v1 (`qa --torna-alla-v1`) | provato | — |

## 2. Aspetto per aspetto

| Aspetto | | v1 | v2 |
|---|:-:|---|---|
| Falsi errori, stampe giuste | ✅ | 6 | 0 |
| Errori trovati (19 op.) | ✅ | 15 | 16 dal solo codice; 18 con la grande ingestion (la classe) |
| Prova di ogni errore | ✅ | testo libero | frase del manuale ritrovata dal programma |
| «OK» vuol dire | ✅ | nessuna contraddizione vista | controllato con il manuale |
| Cosa non ha controllato | ✅ | non lo dice | `[non controllabile]` separato da `[da guardare]` |
| Avvisi per ciclo | ❌ | 1-2 | 5,4 piccolo, 8,7 grande (sul PC registro spento, documenti mancanti) |
| Stabilità | ✅ | non misurata | misurata su 3 prove |
| **Codici di task sbagliati** | ✅ | col modello, a volte «incompleto» su codici giusti | dal codice, senza modello: codice assente e fratelli presenti |
| Task dell'operazione contro la testata | ➖ | sì | sì (MG36) |
| Task di un altro stadio | ❌ | sì | no (MG48) |
| Numeri o limiti cambiati in una lingua | ✅ | solo inglese | due lingue, dal codice |
| Negazioni e frasi al contrario | ✅ | solo inglese | due lingue; 2 errori veri trovati in stampe «giuste» |
| Parola o materiale cambiati in una lingua | ➖ | la parola sì | azione diversa e «massimo» contro «minimo» dal codice (MG47, MG81); il materiale lo trova la scheda |
| Scheda sbagliata (motore, materiale, codice) | ➖ | sì (indice schede) | sì, dal codice (MG40); anche nelle stampe DR che la v1 non legge |
| Scheda tolta | ➖ | errore | avviso «Scheda mancante» (regola decisa) |
| Macchine non attive | ➖ | registro | stesso registro in produzione |
| Due macchine per un'operazione | ✅ | non sempre | sì (MG37) |
| Classe dell'acido | ❌ | sì | manca il documento |
| Stampe DR senza serial (A6) | ✅ | si ferma | le legge |
| Stampe lette | ✅ | 10/14 | 14/14 |
| Lettura della stampa | ✅ | modello | parser, gratis e sempre uguale |
| Ricerca nel manuale | ✅ | per somiglianza (OpenSearch) | per codice esatto |
| 2900 documenti | ✅ | non misurato | stesso testo al modello; 4,2 s, 164 MB (finto) |
| Costo e tempo | ✅ | non misurati | 0,011-0,018 $, 16-24 s |
| Prove automatiche e test | ✅ | no | campagne, copie cieche, oltre 1000 test |
| Frontend e accessi | ➖ | — | stesso payload, stesse regole |
| Conoscenza nuova senza riavvio | ✅ | — | sì, ogni 5 minuti |
| Conoscenza rotta all'avvio | ✅ | — | civile: non parte e dice quale file; EJ200: si spegne solo EJ200 (MG44) |
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
| 8d3c673c 100 | scheda e task | ✔ | ✔ | |
| 8d3c673c 110 | scheda e task | ✔ | ✔ | |
| 8d3c673c 140 | numero in una lingua | ✔ | ✔ | |
| e9b74c84 025 | numero e task | ✔ | ✔ | |
| e9b74c84 040 | una parola in inglese | ✔ | ✔ | azione diversa, dal codice (MG47) |
| **Totale** | | **15** | **16** | 2 documento |

**Falsi errori sulle stampe giuste**

| Stampa · op. | v1 | v2 | Perché è falso |
|---|:-:|:-:|---|
| 04ecaabe fonte | ✘ | | il testo dice che è giusta |
| 04ecaabe 040 | ✘ | | scheda giusta |
| 04ecaabe 050 | | tolto (era 2/3) | «almeno 4» = «più di 4» (regola) |
| 4e64d49a fonte | ✘ | | come 04ecaabe |
| 8bdb25d5 030 | ✘ | | stessa istruzione |
| 2d724fba 030 | ✘ | | stessa regola |
| 2d724fba 040 | ✘ | | scheda giusta |
| 2d724fba 050 | | tolto (era 2/3) | come 04ecaabe 050 |

**Fuori dal confronto** (la v1 non dà risultati)

| Stampa | v2 |
|---|---|
| 22f586bb, 895167b9 (DR) | senza modello trovati tutti: 010 («massima» contro «min», MG81), 030 (un altro DR, MG76), 050, 060 |
| 737dec71 060; 414d85ca, 477abec8, ffadfe16 060 | errore vero; senza modello trovati tutti e quattro, sempre (MG75) |
| 298bc28e 035 | senza modello trovato: la riga cambiata ora si legge (MG77), azione diversa (MG47) |
| 64752871 050, 9a66895e 090, d8f8a3bd 100 e 150 (cicli veri) | falsi errori del codice (P15: «sabbiatura» in una condizione, «replace» per «ripristinare»), corretti in MG47 |
| 8d3c673c 070 | errore vero (P13): una targa cambiata, trovato |
| 8d3c673c 060, b1261d11 060 | falsi errori del codice (P13), tolti (MG78) |

*Aggiornato il 27-11 notte, dopo la terza prova senza modello (piccolo 41 su 45, grande 31 su
31, 0 falsi errori, 0 da verificare). Prossimo: dopo la campagna del passo 4h.*
