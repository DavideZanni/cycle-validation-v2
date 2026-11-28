# Migliorie

Tutte le migliorie della v2, provate e da fare, in una tabella sola.

- **Stato:** ✅ fatta, nella v2 · ❌ provata e scartata · 🔶 in prova · ⬜ da fare
- **Importanza:** 5 = serve per la produzione · 4 = molto utile · 3 = utile · 2 = poco · 1 = forse
- **Era:** il nome di prima, quello che si legge in `MEMORIA.md` e nei commenti del codice.
- Come si prova e come si decide: `DOCUMENTAZIONE.md` 15.3. La storia delle prove: `MEMORIA.md`
  sezione 16. Se si è pronti per la produzione: `V1_CONTRO_V2.md` sezione 1.

**27-11 notte, versione quasi finale:** MG44, MG45, MG47, MG50, MG53, MG75-MG80 insieme. Si
provano prima gratis (`eval senza-modello`, MG79), poi con una campagna sola (COPILOT passo 4h).

**27-11 notte, prova senza modello sul PC:** solo il codice trova 39 errori su 45 (piccolo) e
29 su 31 (grande), 0 falsi errori; 4 ERRATO da verificare sui cicli veri del grande (domanda
P15). Dopo: MG81 (le due 010 mancate) e MG82 (il motivo accanto agli ERRATO in più).
Seconda prova: piccolo 41 su 45, grande 31 su 31, 0 falsi errori. P15: i 4 da verificare erano
falsi errori di MG47, tutti dallo stesso testo («sabbiatura» in una condizione, «replace» per
«ripristinare»): corretti, attesi 0.

**28-11, campagna `quasi_finale` (3 prove sul piccolo e 3 sul grande, 2,36 $):** si tiene,
è la base. Piccolo 42 su 45 stabili, grande 31 su 31; 0 falsi errori, 0 da verificare; 0,011 $
e 20 s a ciclo sul piccolo, 0,019 $ e 30 s sul grande. Tutti gli errori noti trovati in 3 prove
su 3 (MG49 non serve più). Restano: 3 copie cieche che trova solo il modello mancate, con 3
falsi OK su 9 (MG87), e gli avvisi (4,9 e 8,9 per ciclo, MG83).

**Prossime, in ordine (28-11, dopo la campagna):** solo quelle che si possono fare davvero e che
migliorano qualcosa di misurabile. L'ingestion si fa più avanti, quando l'utente ha tempo; la
conoscenza prima di pubblicarla per ora la controlla l'utente a mano.

1. Report della campagna rifatto (utente, passo 4i, 0 $): le tabelle per tipo e per motivo
   ora guardano `quasi_finale`, non la base vecchia. Da lì MG83 e MG87.
2. ✅ MG58 risultato già calcolato (28-11): stesso PDF e stessa conoscenza, risposta in un
   secondo e 0 $. Solo nel servizio; non tocca il modello né le prove.
3. MG83 meno avvisi (Claude, dalla tabella «WARNING per motivo» di `quasi_finale`): cancello C.
   Sul piccolo della base vecchia 3,8 dei 4,8 erano «evidenza non trovata».
4. MG87 falsi OK sulle copie cieche (Claude, dalla tabella per tipo di `quasi_finale`): una
   variante della campagna.
5. MG54 chiamata diretta a Bedrock (circa metà del tempo), scritta spenta; poi MG56 cache di
   Bedrock con MG59 (il batch no, non risponde subito). Ognuna come variante contro
   `quasi_finale`, si tiene solo se trova gli stessi errori. MG55 per ultima (rischio: il
   modello mescola le operazioni).
6. MG48 task di un altro stadio: prima una domanda a Copilot, poi il codice.
7. MG42 prova EJ200 (utente, passo 4f): cancello B.

Più avanti, con l'ingestion (utente, quando ha tempo; il codice dell'indice lo scrive Claude se
`knowledge-index` si collega a una sessione): MG73 grande ingestion (la classe dell'acido, meno
avvisi «fonte assente»), MG74 indice (nomi dei manuali, titoli dei task, voci RDR «OTHER»,
targa `90`: MEMORIA 13), MG61 classifica dei manuali che mancano, MG60 macchine attive su S3.

Da non fare adesso: MG62 (per ora la conoscenza la controlla l'utente a mano prima di
pubblicarla), MG46 (già vista: l'unico caso lo trova la scheda), MG57 (rischio di falsi errori
senza la conoscenza completa), MG51 (collega), MG52, MG63-MG67, MG69-MG72 (poco guadagno o
dipendono da altre persone o dalla produzione). MG68 scartata (27-11, utente: OpenSearch non si
introduce).

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
| MG43 | Domanda P13 | 8d3c673c 070 errore vero (targa); 8d3c673c 060 e b1261d11 060 falsi errori del codice, tolti da MG78 | ✅ | 5 | N3 |
| MG44 | EJ200 rotta non ferma il civile | una conoscenza EJ200 non valida spegne solo EJ200, MOS e DR partono; si riprova alla richiesta dopo | ✅ | 5 | B7 |
| MG45 | Fuori tema più prudente | mai N/A se la descrizione ha un limite o una negazione: WARNING e seconda ricerca (tocca il modello: si misura con la campagna) | 🔶 | 4 | F3 |
| MG46 | Materiale tra le lingue | materiale diverso tra italiano e inglese, dal codice | ⬜ | 4 | F1 |
| MG47 | Azione diversa tra le lingue | dal codice: rimuovere, raccordare, sostituire, lucidare, sabbiare, saldare, pulire (e9b74c84 040, 298bc28e 035). P15: un'azione in una condizione («durante la sabbiatura») non conta; «ripristinare» = «replace» | ✅ | 4 | F1 |
| MG48 | Task di un altro stadio | il task cita un pezzo diverso da quello del ciclo | ⬜ | 3 | F2 |
| MG49 | Errori più stabili | errori che escono 2 volte su 3 (28-11: con `quasi_finale` tutti gli errori noti 3 su 3, non serve) | ✅ | 3 | F4 |
| MG50 | DR senza serial | la procedura DR dal numero «D.R. CASE #» della stampa (P14); le recommendation restano da decidere con le persone | 🔶 | 3 | F5 |
| MG51 | Frontend con i due WARNING | colori diversi per `[da guardare]` e `[non controllabile]` (collega) | ⬜ | 3 | F7 |
| MG52 | Fonte della nota | la fonte giusta per il task della nota nelle MOS | ⬜ | 3 | H16 |
| MG53 | Tempo massimo della validazione | 480 s per le sessioni di un ciclo: chiude con quello che ha | ✅ | 3 | T1 |
| MG54 | Chiamata diretta a Bedrock | niente avvio dell'agente per ogni operazione: circa metà del tempo | ⬜ | 3 | B1 |
| MG55 | Più operazioni insieme | dopo MG54: meno tempo | ⬜ | 2 | B4 |
| MG56 | Cache e batch di Bedrock | meno costo | ⬜ | 2 | H10 |
| MG57 | Numeri contro il manuale | numeri e classi della descrizione confrontati dal codice con il manuale | ⬜ | 3 | I4, H12 |
| MG58 | Risultato già calcolato | stesso PDF e stessa conoscenza: risposta subito e 0 $ (28-11: nel servizio, in memoria, 200 risultati per 6 ore; DOCUMENTAZIONE 13.3) | ✅ | 2 | H13 |
| MG59 | Più operazioni in una sessione | stesso testo mandato una volta | ⬜ | 1 | H14 |
| MG60 | Macchine attive su S3 | file notturno con le macchine attive, leggibile anche dal PC | ⬜ | 3 | H1 |
| MG61 | Ingestion guidata | classifica dei manuali più chiesti che mancano | ⬜ | 2 | H2 |
| MG62 | `kb-check` nell'ingestion | una conoscenza rotta non si pubblica mai | ⬜ | 4 | H3 |
| MG63 | Prova ombra in QA | la v2 riceve una copia delle richieste della v1 e si confrontano | ⬜ | 3 | H4 |
| MG64 | Validazione in coda | risposta subito con un numero, stato «operazione 12 di 40» | ⬜ | 2 | H5 |
| MG65 | Ciclo dai dati strutturati | il ciclo da una tabella invece che dal PDF | ⬜ | 2 | H6 |
| MG66 | Prove dentro AWS | gli stessi comandi `eval` in AWS | ⬜ | 2 | H7 |
| MG67 | Feedback come caso di prova | una risposta segnata sbagliata diventa un caso | ⬜ | 2 | H8 |
| MG68 | OpenSearch come riserva | ricerca per somiglianza solo quando il task non c'è (scartata dall'utente il 27-11: non si introduce) | ❌ | 1 | H9 |
| MG69 | Python 3.14 nel progetto | niente più `$env:UV_PYTHON` nei blocchi | ⬜ | 1 | H11 |
| MG70 | Casi aziendali rivisti | cicli veri con esito atteso riga per riga | ⬜ | 2 | — |
| MG71 | Varianti proposte dal modello | il modello propone, la classifica decide | ⬜ | 1 | E1 |
| MG72 | Pulizia | golden in parallelo; togliere le rotte storiche quando il frontend è pronto | ⬜ | 1 | B8, D |
| MG73 | Grande ingestion | tutti i documenti civili, con quelli che ha la v1 (schede con materiale, SPM) | ⬜ | 5 | — |
| MG74 | Indice (knowledge-index) | nomi dei manuali (`aliases.json`), intervalli dei task, voci RDR «OTHER» | ⬜ | 3 | — |
| MG75 | Limiti al contrario tra le lingue, dal codice | «superiore a 4X» contro «not to exceed 4X»: prima lo trovava il modello 3-4 volte su 6 | ✅ | 5 | — |
| MG76 | Lo stesso DR in tutto il ciclo | un «D.R. CASE #» diverso da quello del ciclo: ERRATO `DR_DIVERSO` (895167b9 030) | ✅ | 4 | — |
| MG77 | Riga accanto a «continua» | il parser non butta più la descrizione scritta accanto a «CONTINUA ALLA PAGINA SEGUENTE» | ✅ | 4 | — |
| MG78 | Rimandi a operazioni e figure | «operazione 70» contro «figure 903» non è un numero cambiato (2 falsi errori della P13) | ✅ | 5 | — |
| MG79 | Prova senza modello | `eval senza-modello`: i controlli del codice su piccolo e grande, 0 $, pochi minuti | ✅ | 4 | — |
| MG80 | Test sulle 14 stampe vere | le regole del codice sul testo di `CONFRONTO_V1_14_CICLI.md`, a ogni `pytest` | ✅ | 4 | — |
| MG81 | Massimo contro minimo tra le lingue | «profondità massima» in italiano, «min depth» in inglese, anche senza un numero: ERRATO dal codice (22f586bb e 895167b9 010) | ✅ | 4 | — |
| MG82 | Motivo degli ERRATO in più | a schermo e nel riepilogo, accanto a ogni ERRATO da verificare, il motivo (quale controllo): si capisce subito da dove viene | ✅ | 3 | — |
| MG83 | Meno avvisi per ciclo | tagliare le cause più frequenti dei WARNING (tabella «WARNING per motivo»), per il cancello C | ⬜ | 4 | — |
| MG84 | Banco di prova | `eval banco`: errori messi dal programma su ogni operazione delle 14 stampe vere (numero, limite, massimo/minimo, azione, DR): 310 copie, trovate 308, 0 falsi allarmi; lettura della stampa uguale alla v1 | ✅ | 4 | — |
| MG85 | Metriche di controllo | nel riepilogo: falsi OK, mancati come WARNING o N/A, esiti decisi, errori tecnici, ciclo più lento e più caro | ✅ | 4 | — |
| MG86 | Date e limiti ripetuti | trovati dal banco: una data in una lingua sola disallineava i numeri; «massimo 2 … massimo 2» con uno girato non si vedeva | ✅ | 3 | — |
| MG87 | Falsi OK sulle copie cieche | il modello dice CORRETTO su un errore che solo lui può trovare, confrontando con il manuale (campagna del 28-11: 3 su 9 mancati, piccolo). Quale tipo: dalla tabella per tipo del report rifatto | ⬜ | 4 | — |
