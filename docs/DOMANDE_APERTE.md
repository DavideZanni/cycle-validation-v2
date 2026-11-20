# Domande aperte

Decisioni e dati che servono da chi conosce i cicli e l'indice. Per rispondere basta scrivere
sotto ogni domanda. I valori negli esempi sono inventati (il repository è pubblico).
Aggiornato il 20-11-2026.

## Da cui dipende il funzionamento

### 1. Targhe della stampa e targhe dell'indice

Nella stampa PVRM320 la colonna TARGA ha due righe per operazione: sopra valori come `XX/123`,
`PREC01`, `IM0001`, sotto valori come `AVM700` (centro responsabile). In `machine_tags.json`
le targhe hanno un'altra forma: `A01000`, `500010`, `1200`, `A 0100`.

- Sono la stessa cosa scritta in due modi, o due codici diversi?
- La targa da verificare è la riga sopra (oggi si usa questa) o quella sotto?
- Se sono codici diversi, esiste una tabella di corrispondenza?

Perché conta: oggi una targa della stampa che non si trova nel registro delle macchine attive
dà **ERRATO**. Se le due forme non coincidono, rischiano di uscire ERRATO quasi tutte le righe.

Risposta:

### 2. Registro delle macchine attive

La query predefinita su Redshift legge `work_centers` con `work_center_usage_cd = 'TO'`, scelta
senza dati veri. È la tabella giusta? In che forma scrive le targhe (come la stampa o come
`machine_tags.json`)?

Risposta:

### 3. Schede dei cicli MOS

La stampa scrive le schede come `PG 300`, `PG 100`, `16`. In `process_sheets.json` i codici sono
`10`, `16`, `6`, `CPEC 100-BR`, e nelle foto viste non c'è nessun `PG …`. Una scheda stampata
`PG 300` nell'indice è `PG 300` o `300`? Se è `300`, oggi risulta "non presente" (WARNING).
Per EJ200 non conta, perché lì le schede non si verificano.

Risposta:

### 4. `current.json`

Tutti gli altri file sono stati visti e vanno bene. Manca la conferma che `current.json` esista
in `knowledge/civil/` e in `knowledge/ej200/`: senza, il servizio non trova la conoscenza.
Basta lanciare `kb-check` sulla fotografia (guida, 6.1).

Risposta:

## Regole da confermare

### 5. Fonti EJ200

Oggi le fonti di un ciclo EJ200 sono solo i codici RDR citati nel testo (`... DELLA RDR
EJ00010X-01`). RN ed EF non vengono cercati nel testo. Va bene così, o i cicli citano anche
RN/EF da confrontare?

Risposta:

### 6. DR con `conditions: []`

Se un serial number ha una sola recommendation, questa vale per qualunque condition. Se ne ha
più di una e una di queste ha `conditions: []`, quella non viene mai scelta. Una lista vuota
vuol dire "vale per tutte le condition" o "condition non indicata"?

Risposta:

### 7. Voci strane nell'indice

In `machine_tags.json` c'è una voce con targa `90` e come funzione una frase che sembra una nota
rimasta da un documento ("In questo caso la descrizione breve può essere scelta..."). È un
errore dell'indice da correggere lato knowledge-index?

Risposta:

### 8. Issue vecchia citata dal ciclo

Se il ciclo cita una RDR con una issue precisa (`EJ00020L-01`) e nel catalogo c'è anche una
issue più recente (`-02`), oggi il confronto si fa sulla issue citata e la fonte risulta
corretta, senza avvisi. Va bene così, o deve uscire un WARNING ("esiste una issue più
recente")?

Risposta:

## Repository

### 9. Visibilità

Il repository `cycle-validation-v2` è pubblico. Lo rendiamo privato (GitHub, Settings →
General → Danger Zone → Change visibility)?

Risposta:

### 10. Un codice vero in un messaggio di commit

Il messaggio di un commit già pubblicato su `main` contiene un codice RDR vero. Toglierlo
richiede di riscrivere la storia di `main` con un push forzato. Lo facciamo, oppure basta
rendere privato il repository?

Risposta:

## Già decise (per memoria)

- Descrizione: copiata dal PDF così com'è, parole spezzate comprese; nessuna ricucitura.
- Op. `005` (riga NOTE): resta in tabella.
- RC dell'operazione: la `RIPARAZIONE :` della testata della pagina.
- Feedback EJ200: esiti reali; la Scheda è sempre N/A.
- `needs_review`: promemoria per chi cura l'indice, ignorato dal programma.
- Il frontend (badge, «-» sotto la scheda, minuscole) lo gestisce un collega.
- Si lavora direttamente su `main`.
