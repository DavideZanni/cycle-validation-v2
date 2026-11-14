# Esperimenti

Qui si provano le alternative del sistema (un'impostazione diversa, un altro modello, più
avanti codice nuovo) sugli stessi casi, e si mettono in classifica. **Un esperimento è un file,
non un ramo git.**

## In due comandi

```bash
uv run cycle-validation eval esegui --variante eval/varianti/effort_low.yaml --ripetizioni 3
uv run cycle-validation eval classifica
```

Il primo fa girare la variante su tutti i casi, tre volte, e scrive un file in
`eval/risultati/`. Il secondo legge tutti i risultati e scrive `eval/classifica.md`.

Per una prima misura completa: lanciare `baseline` e poi le altre varianti, con le stesse
ripetizioni, poi `classifica`.

## Cosa c'è nella cartella

| Cosa | A cosa serve | In git |
|---|---|---|
| `varianti/` | un file YAML per esperimento | sì |
| `casi/sintetici/` | casi inventati con l'esito atteso (MOS, DR, EJ200): provano la meccanica | sì |
| `casi/aziendali/` | cicli veri annotati da chi li conosce | **no** |
| `casi/mutazioni/` | cicli veri con un difetto messo apposta (prossimo giro) | **no** |
| `risultati/` | un file JSON per ogni prova, con tutti i dati grezzi | **no** |
| `classifica.md` | la classifica, scritta dal comando | sì |

## Una variante

Cambia solo quello che le serve; il resto lo eredita dalla variante `base`.

```yaml
nome: effort_low                 # uguale al nome del file
descrizione: meno ragionamento del modello
base: baseline
agent:                           # le stesse chiavi di config/settings.yaml
  effort: low
```

- Si possono cambiare `agent`, `paths` e `module_check`, come in `config/settings.yaml`.
- `baseline.yaml` è la radice: dice da quale file di impostazioni si parte (`config:`).
- `sessione:` sceglie l'implementazione del modello. Oggi c'è solo `sdk` (Claude Agent SDK);
  quando arriverà la chiamata diretta a Bedrock sarà `sessione: diretta`, e il codice vecchio
  resterà, così si potranno sempre confrontare.
- Per provare un prompt diverso: una cartella con i tre prompt e `paths: {prompts_dir: ...}`.

Opzioni utili di `eval esegui`:

- `--config`: sostituisce il file di impostazioni di partenza, per tutte le varianti. Sul PC
  personale, per esempio, una copia con `use_bedrock: false` (**solo con i casi sintetici**).
- `--casi eval/casi/sintetici/mos`: una sola suite.
- `--ambiente`: l'etichetta dell'ambiente. Se manca si deduce: `bedrock-<regione>` oppure
  `login-locale`.

## I casi

Una suite è una cartella con `suite.yaml` e un caso per sottocartella (`ciclo.json`,
`expected.json` e, se c'è, `ciclo.pdf` vero). Lo stesso formato del golden set.

```yaml
conoscenza: ../../../../examples/sintetico/knowledge   # relativo a questa cartella
tipo_conoscenza: locale                                # locale | ej200
macchine: ../../../../examples/sintetico/macchine_attive.json
```

Per EJ200 la conoscenza è una cartella con la stessa struttura delle chiavi S3 (catalogo e
testi delle pubblicazioni).

## Cosa si misura

| Voce | Che cosa | Perché conta |
|---|---|---|
| Concordanza | righe con l'esito atteso, in totale e per controllo | la qualità del giudizio |
| ERRATO falsi | il sistema dice ERRATO e non lo è | l'errore peggiore: fa perdere tempo e fiducia |
| Errori mancati | c'era un ERRATO atteso e il sistema non lo dà | pericoloso |
| Righe instabili | stesso caso, esito diverso tra le ripetizioni | un sistema affidabile risponde sempre uguale |
| Esiti tecnici | errore tecnico, budget esaurito, estrazione non confermata, guasti | robustezza |
| Tempo per ciclo | mediano e caso peggiore, più le fasi lettura, estrazione, controlli | velocità |
| Avvio agente | tempo della sessione meno tempo del modello, per sessione | quanto si guadagnerebbe senza l'agente |
| Costo e token | medi per ciclo | spesa |
| Citazioni verificate | citazioni del modello ritrovate davvero nel manuale | il modello non inventa |

ERRATO falsi, errori mancati ed esiti tecnici sono **medie per ripetizione**. La stabilità
serve almeno due ripetizioni.

## Come si decide

Si confrontano solo prove dello **stesso ambiente** (il PC personale e Bedrock aziendale hanno
tempi e prezzi diversi). Per ogni variante conta la sua prova più recente, contro la prova più
recente di `baseline`.

Prima i paletti. Una variante è **scartata**, anche se è più veloce, se ha:

1. più ERRATO falsi;
2. più errori mancati;
3. concordanza più bassa;
4. più righe instabili;
5. più esiti tecnici;

oppure se è stata provata su casi diversi dalla baseline.

Poi l'obiettivo: tra le ammesse vince la più veloce (tempo mediano per ciclo), a parità la
meno cara. Accanto c'è il caso peggiore, perché una media buona può nascondere un caso lento.

Test, `ruff` e `mypy` devono restare verdi: è un requisito per tenere una modifica, non un
punteggio.

## Quando una variante vince

Si porta la modifica in `config/settings.yaml` (o nel codice), si rilancia `baseline` per avere
il nuovo riferimento, e si scrive la decisione nel registro di `docs/BASELINE.md`.

## Prossimo giro

- Mutazioni: da un ciclo vero, un programma genera copie con un difetto noto (45 mm che diventa
  46 mm, una targa sbagliata, un task inesistente) e copie con modifiche innocue che non devono
  cambiare l'esito.
- Guasti simulati: Bedrock lento, throttling, risposta storta, un file della conoscenza che
  manca. La regola da verificare: un guasto dà WARNING, mai ERRATO.
- Varianti con codice nuovo: `prompt_task_mancante` (dire al modello che il task citato non
  esiste, `docs/MIGLIORIE.md` A2) e `bedrock_diretto` (niente avvio dell'agente).
