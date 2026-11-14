# Baseline ed esperimenti

**Stato: base di partenza.** Il metodo e i numeri ci sono; lo strumento di misura e il registro
li completiamo nel prossimo passo.

## A cosa serve

La baseline è una versione del programma che sappiamo funzionare, con i suoi numeri misurati.
Ogni modifica (un esperimento, un aggiornamento, una miglioria di `docs/MIGLIORIE.md`) si prova
contro di lei: stesse prove, stessi casi, prima e dopo. Si tiene la modifica solo se non
peggiora niente.

## La baseline di oggi

Codice: ramo `main` più le correzioni del 14 novembre 2026 (hook di `StructuredOutput`, extra
`aws`, `.gitignore` per le cartelle di esempio). Quando le correzioni sono nel repository, la
versione si fissa con un'etichetta git `baseline-v1`.

Numeri misurati sul computer personale, modello Claude Haiku con login locale (non Bedrock),
impostazioni predefinite (`effort` predefinito, concorrenza 6, soglia "in linea" 150 righe).

| Prova | Concordanza | Costo | Tempo |
|---|---|---|---|
| Test automatici (modello finto) | 558 su 558 | 0 | 22 s |
| Golden MOS, in linea | 19 su 19 (a volte 18: caso ambiguo, vedi MIGLIORIE A2) | 0,0038 USD | 31 s |
| Golden MOS, ricerca forzata | 19 su 19 | 0,0050 USD | 33 s |
| Golden DR | 29 su 29 | 0,0008 USD | 5 s |
| Golden EJ200 | 22 su 22 | 0,0065 USD | 39 s |
| Ciclo di esempio da 4 operazioni | esiti attesi | 0,0038 USD | 12,7 s |

**I numeri valgono solo nello stesso ambiente.** In azienda il modello passa da Bedrock, con
altre latenze e altri prezzi: la prima cosa da fare lì è rifare questa tabella. Quella diventa
la baseline aziendale.

## Come si fa un esperimento

1. Parti dalla baseline: `git switch -c exp/<nome-breve>` da `baseline-v1`.
2. Cambia **una sola cosa**.
3. Lancia i test: `uv run pytest`. Devono passare tutti.
4. Lancia le stesse prove della tabella, con lo stesso file di impostazioni, **tre volte**: il
   modello non risponde sempre uguale, una sola prova può ingannare.
5. Scrivi i numeri nel registro qui sotto.
6. Tieni la modifica solo se:
   - la concordanza non scende su nessun caso;
   - tempo e costo non salgono (salvo che l'esperimento serva proprio ad altro, per esempio
     all'affidabilità, e lo si scrive);
   - nessun nuovo WARNING "errore tecnico".
7. Se la tieni, la si unisce a `main` e la baseline avanza (`baseline-v2`, con i nuovi numeri).

I comandi delle prove sono quelli del Passo 6 di `docs/IMPORTAZIONE_AZIENDA.md`. Per la
modalità ricerca forzata si usa una copia delle impostazioni con `inline_max_lines: 0`.

## Registro degli esperimenti

| Data | Esperimento | Ramo | Concordanza | Costo | Tempo | Decisione |
|---|---|---|---|---|---|---|
| 2026-11-14 | `effort: low` (prova veloce, una volta sola) | — | MOS 18-19 su 19 | -30% | -27% per sessione | da ripetere con il metodo sopra |

## Da fare nel prossimo passo

1. **Uno strumento di misura unico**: un comando che lancia tutte le prove della tabella N
   volte e stampa media e peggior caso, così ogni esperimento si misura allo stesso modo.
2. **La prova con il modello vero** (`pytest -m live`, MIGLIORIE A5).
3. **Un esempio di ciclo DR.** Davide lo fornirà. Andrà in `docs/Esempio ciclo DR/` (cartella
   ignorata da git) con il risultato atteso scritto da chi conosce il ciclo. Serve a:
   - confermare come si riconosce un DR dalla testata (`module_check.dr_markers`);
   - provare il parser di layout anche sul DR (MIGLIORIE A6 e B5);
   - aggiungere un caso DR vero alle prove della baseline.
4. **Casi veri** per MOS ed EJ200, con gli esiti attesi campo per campo: i casi di oggi sono
   inventati e dicono se la meccanica regge, non se il giudizio tecnico è giusto.
