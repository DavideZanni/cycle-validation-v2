# Esperimenti

Qui si provano le alternative del sistema (un'impostazione diversa, un altro modello, più
avanti codice nuovo) sugli stessi casi, e si mettono in classifica. **Un esperimento è un file,
non un ramo git.**

## Un comando

```bash
uv run cycle-validation eval pipeline --ripetizioni 3
```

Fa tutto in ordine: verifiche del codice (test, ruff, formato, mypy; se una fallisce si ferma
senza chiamare il modello), poi `baseline` e ogni variante di `eval/varianti/` su tutti i casi
rivisti, poi la classifica in `eval/risultati/classifica.md`. Con `--variante effort_low` (anche
più volte) fa girare solo quelle, più la baseline che c'è sempre.

I passi si possono fare anche uno per uno:

```bash
uv run cycle-validation eval esegui --variante eval/varianti/effort_low.yaml --ripetizioni 3
uv run cycle-validation eval classifica
```

Il primo scrive un file in `eval/risultati/`, il secondo legge tutti i risultati e scrive la
classifica.

**Sui dati veri, in azienda:** la guida passo passo è `docs/ESPERIMENTI_AZIENDA.md` (fotografia della
conoscenza, bozza e revisione dei casi, pipeline).

## Cosa c'è nella cartella

| Cosa | A cosa serve | In git |
|---|---|---|
| `varianti/` | un file YAML per esperimento | sì |
| `casi/sintetici/` | casi inventati con l'esito atteso (MOS, DR, EJ200): provano la meccanica | sì |
| `casi/aziendali/` | cicli veri annotati da chi li conosce | **no** |
| `casi/mutazioni/` | copie dei casi veri con un difetto messo apposta, scritte da `eval mutazioni` | **no** |
| `risultati/` | un file JSON per ogni prova, con tutti i dati grezzi | **no** |
| `modelli/aziendali/` | i `suite.yaml` da copiare in `casi/aziendali/` | sì |
| `risultati/classifica.md` | la classifica, scritta dal comando | **no** (può contenere nomi di casi veri) |

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
- `guasti:` simula guasti del modello e della conoscenza (vedi sotto). Una variante con guasti
  non entra in classifica: si giudica a parte.

Opzioni utili di `eval esegui`:

- `--config`: sostituisce il file di impostazioni di partenza, per tutte le varianti. Sul PC
  personale, per esempio, una copia con `use_bedrock: false` (**solo con i casi sintetici**).
- `--casi eval/casi/sintetici/mos`: una sola suite.
- `--ambiente`: l'etichetta dell'ambiente. Se manca si deduce: `bedrock-<regione>` oppure
  `login-locale`.

## I casi

Una suite è una cartella con `suite.yaml` e un caso per sottocartella: `expected.json` più
`ciclo.json` oppure `ciclo.pdf` (meglio entrambi: il PDF è l'ingresso, `ciclo.json` il
riferimento controllato). Lo stesso formato del golden set.

```yaml
conoscenza: ../../../../examples/sintetico/knowledge   # relativo a questa cartella
tipo_conoscenza: locale        # locale | fotografia | ej200
macchine: ../../../../examples/sintetico/macchine_attive.json
estrazione: ciclo_json         # ciclo_json | dal_pdf
```

- `locale`: la cartella di conoscenza del programma (`examples/sintetico/knowledge`).
- `fotografia`: una copia di S3 fatta con `eval fotografia`, letta con lo stesso codice di
  produzione. Servono i prefissi `manuali`, `targhe`, `schede`, `dr` (vedi
  `modelli/aziendali/`).
- `ej200`: la stessa struttura delle chiavi S3 delle pubblicazioni EJ200 (`catalogo`, `testi`).
- `dal_pdf`: il ciclo si legge dal PDF a ogni prova, e la colonna "Estrazione" misura quanto la
  lettura somiglia a `ciclo.json`.

Un caso con `"rivisto": false` in `expected.json` è una bozza (`eval prepara`) e viene saltato.

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
| Estrazione | operazioni e fonti lette dal PDF uguali a `ciclo.json` (solo `dal_pdf`) | separa gli errori di lettura da quelli di giudizio |

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
6. estrazione dal PDF peggiore (solo con `estrazione: dal_pdf`);

oppure se è stata provata su casi diversi, o su una conoscenza diversa, dalla baseline.

Poi l'obiettivo: tra le ammesse vince la più veloce (tempo mediano per ciclo), a parità la
meno cara. Accanto c'è il caso peggiore, perché una media buona può nascondere un caso lento.

Test, `ruff` e `mypy` devono restare verdi: è un requisito per tenere una modifica, non un
punteggio. `eval pipeline` li controlla prima di ogni giro.

## Mutazioni

I cicli veri con un errore sono pochi, ma sono quelli che misurano gli errori mancati.

```bash
uv run cycle-validation eval mutazioni          # da eval/casi/aziendali a eval/casi/mutazioni
uv run cycle-validation eval pipeline --casi eval/casi/mutazioni
```

Da ogni caso rivisto che ha `ciclo.json` il comando scrive copie con un difetto di cui il
**codice** sa l'esito, e copie con modifiche che non devono cambiare niente:

| Mutazione | Cosa cambia | Atteso |
|---|---|---|
| `targa_non_attiva` | la targa di un'operazione diventa una macchina che non esiste | ERRATO `MACCHINA_NON_ATTIVA` |
| `task_inesistente` | i task di un'operazione diventano codici che il manuale non ha | WARNING |
| `scheda_inesistente` | la scheda di un'operazione diventa una scheda che non esiste | WARNING `FONTE_ASSENTE` |
| `spazi_doppi` | spazi doppi nelle descrizioni | come l'originale |
| `targhe_minuscole` | targhe in minuscolo | come l'originale |

Il difetto si mette solo dove l'originale è CORRETTO e verificato. Le altre righe
dell'operazione toccata (per esempio il giudizio sulla descrizione) si tolgono dagli attesi, e
anche lo stato del ciclo: si confronta solo ciò che è certo. Ogni copia ha un `mutazione.json`
che dice da dove viene e cosa è cambiato. Le copie leggono `ciclo.json` (il PDF non è mutato) e
la stessa conoscenza della suite di partenza. Il comando riscrive solo cartelle scritte da lui.

Un difetto numerico (45 mm che diventa 46 mm) non c'è: l'esito lo decide il modello, non il
codice, e l'atteso andrebbe scritto da un esperto.

## Guasti simulati

```yaml
nome: guasti
base: baseline
guasti:
  errore: 0.3          # sessioni che falliscono (rete, throttling, servizio giù)
  risposta_storta: 0.2 # risposte che non rispettano lo schema
  budget: 0.1          # sessioni che finiscono i passi
  conoscenza: 0.1      # letture della conoscenza che non riescono
  ritardo_s: 0         # attesa in più per sessione
  seme: 1              # stessi guasti a ogni prova
```

La regola da verificare: **un guasto dà WARNING, mai ERRATO**. Nella classifica la variante
compare sotto "Prove con guasti simulati": *regge* se nessun guasto è diventato ERRATO e tutti
i casi sono arrivati in fondo, altrimenti *NON regge* con il motivo. Una sessione guasta non
chiama il modello, quindi la prova costa meno della baseline.

## Quando una variante vince

Si porta la modifica in `config/settings.yaml` (o nel codice), si rilancia `baseline` per avere
il nuovo riferimento, e si scrive la decisione nel registro di `docs/BASELINE.md`.

## Varianti di questo giro

| Variante | Cosa prova |
|---|---|
| `effort_low` | meno ragionamento ovunque |
| `effort_low_controlli` | meno ragionamento nei controlli, pieno nella lettura del PDF (`agent.extraction_effort`) |
| `prompt_task_mancante` | dire al modello che il task citato non è nel manuale (`docs/MIGLIORIE.md` A2) |
| `guasti` | robustezza, giudicata a parte |

## Prossimo giro

- `bedrock_diretto`: una chiamata diretta a Bedrock per le sessioni in linea, senza avvio
  dell'agente (`docs/MIGLIORIE.md` B1), con `sessione: diretta`. Va provata in azienda: dal PC
  personale non si raggiunge Bedrock.
