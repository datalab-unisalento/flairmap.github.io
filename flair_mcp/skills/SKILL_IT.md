# Abilità: Utilizzo degli Strumenti MCP per Dati di Zona e Meteo‑Incendio

Questa abilità documenta come interagire con i tre strumenti esposti da MCP definiti
in **`flair_mcp/mcp_server/tool/tool_zone.py`** e **`flair_mcp/mcp_server/tool/bollettino_incendi.py`**.

| Strumento | Descrizione |
|-----------|-------------|
| **`find_zona(luogo: str) → list[Zona]`** | Cerca le zone (comune, provincia, sigla di immatricolazione, codice ISTAT o *settore AIB*) che corrispondono a una stringa di posizione libera. |
| **`incendi_meteo_dir(settore_aib: str) → list[IncendioMeteo]`** | Recupera le osservazioni di fuoco‑meteo per un identificatore di *settore AIB* fornito. |
| **`bollettino_giornaliero(bollettino_type: Literal["bollettino_incendi", "bollettino_puglia"]) → str | dict`** | Restituisce il testo del bollettino quotidiano della Protezione Civile (rischio incendio o generale Puglia). |

## Come vengono esposti gli strumenti

Entrambe le funzioni sono decorate con ``@mcp.tool()``. Il runtime MCP le rende invocabili da:

* un prompt conversazionale,
* la CLI MCP, oppure
* qualsiasi componente che possa inviare chiamate JSON‑RPC al server.

### Esempio di prompt

```text
find_zona "Bari"
incendi_meteo_dir "A"
```

Il server restituisce una lista di istanze del modello o solleva un ``ValueError`` se non trova corrispondenze, consentendo al client di mostrare un messaggio d'errore chiaro.

## Parametri

* **`luogo`** – Uno dei seguenti (case‑insensitive, spazi bianchi rimossi):
  * nome del comune (`comune`)
  * nome della provincia (`provincia`)
  * sigla di immatricolazione del veicolo
  * codice ISTAT (`codice_istat`)
  * identificatore del settore (`settore_aib`).

* **`settore_aib`** – L'identificatore del settore di gestione incendi (es. `"A"`, `"B"`).

### Parametri per `bollettino_giornaliero`

* **`bollettino_type`** – Literal che indica quale bollettino recuperare. Accetta:
    * `"bollettino_incendi"` – bollettino di rischio incendio.
    * `"bollettino_puglia"` – bollettino generale della Puglia.
* **`ctx`** – Contesto MCP `Context` iniettato dal runtime (non richiesto all'utente).

## Valori di ritorno

Entrambe le funzioni restituiscono una **lista** di modelli Pydantic definiti in
``mcp_server/api/models.py``. Se la lista dovesse essere vuota, viene sollevato un ``ValueError`` invece di restituire una lista vuota.

### Valori di ritorno per `bollettino_giornaliero`

* **`str`** – Il testo grezzo del bollettino quando la richiesta ha successo.
* **`dict[str, str]`** – Un mapping di errore ``{"Error": <messaggio>}`` quando viene fornito un tipo non valido.

## Configurazione dell'ambiente

I percorsi CSV sono costruiti dalla variabile d'ambiente ``CSV_PATH``; se non è impostata, vengono usati i percorsi di default sotto ``resources/data``:

```python
CSV_PATH_MAPPING = Path(
    os.getenv("CSV_PATH")
    or BASE_DIR / "resources" / "data" / "tutti_comuni_puglia_settori_aib.csv"
)
CSV_INCENDI = Path(
    os.getenv("CSV_PATH")
    or BASE_DIR / "resources" / "data" / "incendi_meteo_dir_zone.csv"
)
```

Impostare ``CSV_PATH`` per puntare a una directory alternativa quando si testano file CSV personalizzati.

## Diagramma di flusso di esempio

```mermaid
flowchart TD
    A[Utente: "find_zona 'Bari'"] --> B[find_zona]
    B --> C{Corrispondenze?}
    C -- Sì --> D[Restituisci lista di Zona]
    C -- No --> E[Solleva ValueError]
    F[Utente: "incendi_meteo_dir 'A'"] --> G[incendi_meteo_dir]
    G --> H{Corrispondenze?}
    H -- Sì --> I[Restituisci lista di IncendioMeteo]
    H -- No --> J[Solleva ValueError]
    K[Utente: "bollettino_giornaliero 'bollettino_incendi'"] --> L[bollettino_giornaliero]
    L --> M{Tipo valido?}
    M -- Sì --> N[Restituisci testo del bollettino]
    M -- No --> O[Restituisci dict di errore]
```

## Suggerimenti per l'integrazione

Questi strumenti possono essere concatenati: l'output di ``find_zona`` può fornire l'argomento ``settore_aib`` per ``incendi_meteo_dir`` al fine di recuperare i dati meteo‑incendio per la zona selezionata.

## Ulteriori letture

Vedi l'implementazione completa e la docstring a livello di modulo in
``flair_mcp/mcp_server/tool/tool_zone.py``.
