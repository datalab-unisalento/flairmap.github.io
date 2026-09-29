# Skill: Using MCP Tools for Zone and Fire‑Weather Data

This skill documents how to interact with the three MCP‑exposed tools defined
in **`flair_mcp/mcp_server/tool/tool_zone.py`** and **`flair_mcp/mcp_server/tool/bollettino_incendi.py`**.

| Tool | Description |
|------|------------|
| **`find_zona(luogo: str) → list[Zona]`** | Search for zones (municipality, province, vehicle registration *sigla*, ISTAT code or *settore AIB*) that match a free‑form location string. |
| **`incendi_meteo_dir(settore_aib: str) → list[IncendioMeteo]`** | Retrieve fire‑weather observations for a given *settore AIB* identifier. |
 | **`bollettino_giornaliero(bollettino_type: Literal["bollettino_incendi", "bollettino_puglia"]) → str | dict`** | Returns the text of the daily civil protection bulletin (fire‑risk or general Puglia). |

## How the tools are exposed

Both functions are decorated with ``@mcp.tool()``. The MCP runtime makes
them callable from:

* a conversational prompt,
* the MCP CLI, or
* any component that can send JSON‑RPC calls to the server.

### Prompt example

```text
find_zona "Bari"
incendi_meteo_dir "A"
```

The server returns a list of model instances or raises a ``ValueError`` if
no matches are found, allowing the client to present a clear error
message.

## Parameters

* **`luogo`** – Any of the following (case‑insensitive, whitespace trimmed):
  * municipality name (`comune`)
  * province name (`provincia`)
  * vehicle registration *sigla*
  * ISTAT code (`codice_istat`)
  * sector identifier (`settore_aib`).

* **`settore_aib`** – The fire‑management sector identifier (e.g., `"A"`, `"B"`).

### Parameters for `bollettino_giornaliero`

* **`bollettino_type`** – Literal indicating which bulletin to retrieve. Accepts:
    * `"bollettino_incendi"` – fire‑risk bulletin.
    * `"bollettino_puglia"` – general Puglia bulletin.
* **`ctx`** – MCP `Context` injected by the runtime (not required by the user).

## Return values

Both functions return a **list** of Pydantic models defined in
``mcp_server/api/models.py``. If the list would be empty, a ``ValueError``
is raised instead of returning an empty list.

### Return values for `bollettino_giornaliero`

* **`str`** – The raw bulletin text when the request succeeds.
* **`dict[str, str]`** – An error mapping ``{"Error": <message>}`` when an invalid type is supplied.

## Environment configuration

CSV paths are built from the ``CSV_PATH`` environment variable; if it is
unset the defaults under ``resources/data`` are used:

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

Set ``CSV_PATH`` to point to an alternative directory when testing with
custom CSV files.

## Example workflow diagram

```mermaid
flowchart TD
    A[User: "find_zona 'Bari'"] --> B[find_zona]
    B --> C{Matches?}
    C -- Yes --> D[Return list of Zona]
    C -- No --> E[Raise ValueError]
    F[User: "incendi_meteo_dir 'A'"] --> G[incendi_meteo_dir]
    G --> H{Matches?}
    H -- Yes --> I[Return list of IncendioMeteo]
    H -- No --> J[Raise ValueError]
    K[User: "bollettino_giornaliero 'bollettino_incendi'"] --> L[bollettino_giornaliero]
    L --> M{Valid type?}
    M -- Yes --> N[Return bulletin text]
    M -- No --> O[Return error dict]
```

## Integration tips

These tools can be chained: the output of ``find_zona`` can provide the
``settore_aib`` argument for ``incendi_meteo_dir`` to fetch fire‑weather
data for the selected zone.

## Further reading

See the full implementation and module‑level docstring in
``flair_mcp/mcp_server/tool/tool_zone.py``.
