# Migliorie

Tutte le migliorie della v2, provate e da fare, in una tabella sola.

- **Stato:** ✅ fatta, nella v2 · ❌ provata e scartata · 🔶 in prova · ⬜ da fare
- **Importanza:** 5 = serve per la produzione · 4 = molto utile · 3 = utile · 2 = poco · 1 = forse
- **Era:** il nome di prima, quello che si legge in `MEMORIA.md` e nei commenti del codice.
- Come si prova e come si decide: `DOCUMENTAZIONE.md` 15.3. La storia delle prove: `MEMORIA.md`
  sezione 16. Se si è pronti per la produzione: `V1_CONTRO_V2.md` sezione 1.

**Prossime, in ordine:** MG43 domanda P13 · MG44 · MG45 · MG75 e MG46 (una campagna) · MG73
grande ingestion · MG42 prova EJ200.

| Sigla | Miglioria | Cosa fa | Stato | Imp. | Era |
|---|---|---|:-:|:-:|---|
| MG01 | Ricerca nel manuale sbloccata | il controllo di sicurezza delle sessioni non blocca più lo strumento con cui il modello risponde | ✅ | 4 | A1 |
| MG02 | Targa sconosciuta | targa che non c'è da nessuna parte: WARNING, non ERRATO | ✅ | 3 | A3 |
| MG03 | Tempi massimi | 90 s per sessione, 300 s per leggere il PDF, poi errore tecnico | ✅ | 3 | A4 |
| MG04 | Prova con il modello vero | `pytest -m live` dopo ogni aggiornamento del modello | ✅ | 2 | A5 |
| MG05 | DR letto dal parser | anche il DR si legge senza modello, come MOS ed EJ200 | ✅ | 4 | A6, B5 |
| MG06 | Ragionamento ridotto | `effort` basso nei controlli, alto nella lettura del PDF: -30% di costo, stessi errori | ✅ | 3 | B2 |
| MG07 | Pagine fotografate in parallelo | trascrizione di 4 pagine alla volta | ✅ | 2 | B3 |
| MG08 | Task mancante senza modello | task citato che il manuale non ha: WARNING subito, gratis | ✅ | 3 | B6 (A2 scartata) |
| MG09 | Conoscenza scaricata all'avvio | un file non valido ferma il servizio prima di validare | ✅ | 3 | B7 |
| MG10 | Pulizia del servizio | esecutori, testo delle sessioni non salvato, codice inutile tolto, mypy | ✅ | 2 | D |
| MG11 | Voci incerte dell'indice | `DATO_INCERTO` su targa, scheda o fonte | ✅ | 3 | F1 |
| MG12 | Trattamento della scheda per motore | controllato solo per la famiglia del motore del ciclo | ✅ | 2 | F2 |
| MG13 | Task dei DR | cercati nei manuali citati dall'operazione | ✅ | 3 | F3 |
| MG14 | Documento LEAP intero | come contesto quando la fonte non ha task (da vedere su un LEAP vero) | ✅ | 2 | F4 |
| MG15 | Conferma degli errori | un ERRATO del modello si rifà con 2 sessioni; se non torna, WARNING | ✅ | 5 | G1 |
| MG16 | Regole DR della v1 | `Accept as is` e `Reject` ERRATO; serial e condition facoltativi, serial dalla stampa | ✅ | 4 | G2, G3 |
| MG17 | Risposta per il frontend di oggi | stesso payload della v1 (N/A, Info, esito DR) | ✅ | 5 | G4 |
| MG18 | Stampe modificate a mano | righe fuori ordine rimesse in ordine, «OPERAZIONE EVENTUALE», serial in più forme | ✅ | 4 | G5, G8, G10 |
| MG19 | Comandi di prova | `confronta`, `leggi --struttura`, `macchine` | ✅ | 3 | G6, G7, G9 |
| MG20 | Accesso come la v1 | login e permessi dalla libreria della v1 | ✅ | 5 | G11 |
| MG21 | Impostazioni | più ragionamento, meno conferme, testo più lungo, più operazioni insieme: stessi errori | ❌ | 1 | `effort_medio`, `effort_pieno`, `conferme_1`, `testo_lungo`, `prompt_task_mancante`, `concorrenza_12` |
| MG22 | Modello più grande (Sonnet) | stessi errori di Haiku, 12 volte il costo | ❌ | 1 | `sonnet` |
| MG23 | Lingue separate | italiano e inglese confrontati con il manuale uno alla volta | ✅ | 5 | I5 |
| MG24 | Elementi uno per uno | la descrizione scomposta in valori, limiti, divieti, materiali | ✅ | 5 | I6 |
| MG25 | Seconda ricerca | dopo un «non verificabile» cerca in tutti i documenti: stessi errori, 2 volte il costo | ❌ | 2 | I7, `seconda_ricerca`, `tutto_insieme` |
| MG26 | Misura delle prove | campagne, copie cieche, errori in attesa, prove non valide, ricalcolo | ✅ | 5 | — |
| MG27 | Numeri tra le lingue | confronto dei numeri corretto (conversioni, codici) | ✅ | 5 | I10, I13 |
| MG28 | Definizioni generali | le regole generali dell'SPM non contano come limite: perde errori | ❌ | 1 | I11 |
| MG29 | Lingue tra loro, larga | il modello confronta le due lingue: molti errori in più, ma 11-13 falsi errori | ❌ | 2 | I12 |
| MG30 | Procedura della DR | nei DR la deroga va al modello con i task | ✅ | 4 | I14 |
| MG31 | Scheda mancante | processo speciale senza scheda: avviso «Scheda mancante», mai ERRATO | ✅ | 3 | I9, P6 |
| MG32 | Sezione d'ispezione | nelle ispezioni anche il capitolo d'ispezione del manuale del motore | ✅ | 4 | I8 |
| MG33 | Lingue tra loro, stretta | solo negazioni e limiti al contrario tra le lingue | ✅ | 5 | I15 |
| MG34 | Fuori tema | operazione di cui il manuale non parla: N/A spiegato invece di WARNING | ✅ | 3 | I16 |
| MG35 | Due tipi di WARNING | `[da guardare]` e `[non controllabile]` | ✅ | 4 | H15 |
| MG36 | Task contro testata | task accanto all'operazione diverso da quello della testata: ERRATO dal codice | ✅ | 5 | H17 |
| MG37 | Due macchine | la stessa operazione con due targhe su due pagine: ERRATO dal codice | ✅ | 4 | H19 |
| MG38 | Limiti su più pagine | i limiti della 010 cambiati in una lingua, anche su pagine diverse | ✅ | 4 | — |
| MG39 | Codici e 2900 documenti | cache dei codici per documento; misura `eval scala` | ✅ | 4 | N5 |
| MG40 | Scheda coerente | scheda di un altro motore o materiale, task della scheda inesistente: ERRATO (campagna 4e: +4 stabili sul piccolo, +5 sul grande) | ✅ | 5 | H18 |
| MG41 | Regola «almeno N» | «almeno 4» contro «più di 4» non è un errore (toglie gli ultimi 2 falsi errori) | ✅ | 5 | N1, N2 |
| MG42 | EJ200 sul PC | `prova-ej200`: conoscenza da S3, niente tracce sul PC | 🔶 | 5 | N4 |
| MG43 | Domanda P13 | 8d3c673c 060 e 070, b1261d11 060: errori veri o falsi? | 🔶 | 5 | N3 |
| MG44 | EJ200 rotta non ferma il civile | una conoscenza EJ200 non valida spegne solo EJ200, MOS e DR partono | ⬜ | 5 | B7 |
| MG45 | Fuori tema più prudente | mai N/A se la descrizione ha un limite o una negazione | ⬜ | 4 | F3 |
| MG46 | Materiale tra le lingue | materiale diverso tra italiano e inglese, dal codice | ⬜ | 4 | F1 |
| MG47 | Parola cambiata in una lingua | una parola che cambia il significato (non numero, non negazione) | ⬜ | 3 | F1 |
| MG48 | Task di un altro stadio | il task cita un pezzo diverso da quello del ciclo | ⬜ | 3 | F2 |
| MG49 | Errori più stabili | errori che escono 2 volte su 3 | ⬜ | 3 | F4 |
| MG50 | DR senza serial | quali documenti usare (regola da decidere con le persone) | ⬜ | 3 | F5 |
| MG51 | Frontend con i due WARNING | colori diversi per `[da guardare]` e `[non controllabile]` (collega) | ⬜ | 3 | F7 |
| MG52 | Fonte della nota | la fonte giusta per il task della nota nelle MOS | ⬜ | 3 | H16 |
| MG53 | Tempo massimo della validazione | sotto i 600 s del backend: chiude con quello che ha | ⬜ | 3 | T1 |
| MG54 | Chiamata diretta a Bedrock | niente avvio dell'agente per ogni operazione: circa metà del tempo | ⬜ | 3 | B1 |
| MG55 | Più operazioni insieme | dopo MG54: meno tempo | ⬜ | 2 | B4 |
| MG56 | Cache e batch di Bedrock | meno costo | ⬜ | 2 | H10 |
| MG57 | Numeri contro il manuale | numeri e classi della descrizione confrontati dal codice con il manuale | ⬜ | 3 | I4, H12 |
| MG58 | Risultato già calcolato | stesso PDF e stessa conoscenza: risposta subito | ⬜ | 2 | H13 |
| MG59 | Più operazioni in una sessione | stesso testo mandato una volta | ⬜ | 1 | H14 |
| MG60 | Macchine attive su S3 | file notturno con le macchine attive, leggibile anche dal PC | ⬜ | 3 | H1 |
| MG61 | Ingestion guidata | classifica dei manuali più chiesti che mancano | ⬜ | 2 | H2 |
| MG62 | `kb-check` nell'ingestion | una conoscenza rotta non si pubblica mai | ⬜ | 4 | H3 |
| MG63 | Prova ombra in QA | la v2 riceve una copia delle richieste della v1 e si confrontano | ⬜ | 3 | H4 |
| MG64 | Validazione in coda | risposta subito con un numero, stato «operazione 12 di 40» | ⬜ | 2 | H5 |
| MG65 | Ciclo dai dati strutturati | il ciclo da una tabella invece che dal PDF | ⬜ | 2 | H6 |
| MG66 | Prove dentro AWS | gli stessi comandi `eval` in AWS | ⬜ | 2 | H7 |
| MG67 | Feedback come caso di prova | una risposta segnata sbagliata diventa un caso | ⬜ | 2 | H8 |
| MG68 | OpenSearch come riserva | ricerca per somiglianza solo quando il task non c'è | ⬜ | 1 | H9 |
| MG69 | Python 3.14 nel progetto | niente più `$env:UV_PYTHON` nei blocchi | ⬜ | 1 | H11 |
| MG70 | Casi aziendali rivisti | cicli veri con esito atteso riga per riga | ⬜ | 2 | — |
| MG71 | Varianti proposte dal modello | il modello propone, la classifica decide | ⬜ | 1 | E1 |
| MG72 | Pulizia | golden in parallelo; togliere le rotte storiche quando il frontend è pronto | ⬜ | 1 | B8, D |
| MG73 | Grande ingestion | tutti i documenti civili, con quelli che ha la v1 (schede con materiale, SPM) | ⬜ | 5 | — |
| MG74 | Indice (knowledge-index) | nomi dei manuali (`aliases.json`), intervalli dei task, voci RDR «OTHER» | ⬜ | 3 | — |
| MG75 | Limiti al contrario tra le lingue, dal codice | «superiore a N» contro «not to exceed N»: oggi lo trova il modello, 3-4 volte su 6 | ⬜ | 4 | — |
