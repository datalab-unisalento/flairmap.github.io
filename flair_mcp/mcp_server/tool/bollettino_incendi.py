"""Utility tools for fire‑risk indices and daily bulletins.

This module defines two MCP‑exposed tools that interact with the external
API client provided by :class:`mcp_server.server.AppContext`:

* :func:`get_indice_pericolo` – Retrieves the fire‑danger index for a
    given municipality and date.
* :func:`get_bollettino_incendi` – Returns the text of a daily bulletin
    (either the forest‑fire bulletin *bollettino_incendi* or the general
    Puglia bulletin *bollettino_puglia*).

Both functions are decorated with ``@mcp.tool()`` so they become
available via the MCP runtime. The implementation relies on the cached
request helpers in ``mcp_server.cache``.
"""

import datetime
import logging
from datetime import date

from mcp.server.mcpserver import Context
from urllib3.util import url

from mcp_server.api.models import RischioZona
from mcp_server.cache.cache_manager import DataType
from mcp_server.server import mcp, AppContext

@mcp.tool()
async def get_indice_pericolo(comune: str, giorno: str, ctx: Context) -> dict:
    """Restituisce l'indice di pericolo incendio per un comune in un dato giorno.

    Args:
        comune: Nome del comune pugliese (es. "peschici")
        giorno: Data in formato YYYY-MM-DD
    """
    app: AppContext = ctx.request_context.lifespan_context
    client = app.api_client

    url = f'{client._base_url}/indice-pericolo/{comune}?giorno={giorno}'  # vedi nota sotto

    result = await client.make_cached_request(
        url=url,
        data_type=DataType.INDICE_PERICOLO,
        cache_key=comune,
        ctx=ctx,
        giorno=giorno,  # finisce in **cache_params, quindi nella chiave
    )

    if isinstance(result, dict) and 'Error' in result:
        # Errore esplicito verso l'LLM invece di un dato che sembra valido
        raise ValueError(f"Impossibile recuperare l'indice per {comune}: {result['Error']}")

    return result


from datetime import date
from typing import Literal

from mcp.server.mcpserver import Context

from mcp_server.cache.cache_manager import DataType
from mcp_server.server import mcp, AppContext

logger = logging.getLogger(__name__)

@mcp.tool(
    name="bollettino_giornaliero",
    description=(
        "Restituisce il testo del bollettino giornaliero della protezione civile. "
        "`bollettino_type` può essere 'bollettino_incendi' per il rischio incendi "
        "boschivi o 'bollettino_puglia' per il bollettino generale della Puglia."
    ),
)
async def get_bollettino_incendi(
    bollettino_type: Literal["bollettino_incendi", "bollettino_puglia"],
    ctx: Context,
) -> str | dict[str, str]:
    """Fetch the daily bulletin text.

    Parameters
    ----------
    bollettino_type:
        Literal indicating which bulletin to retrieve. ``"bollettino_incendi"``
        returns the fire‑risk bulletin, while ``"bollettino_puglia"`` returns
        the general Puglia bulletin.
    ctx:
        MCP :class:`~mcp.server.mcpserver.Context` injected by the runtime.

    Returns
    -------
    str
        The raw bulletin text when the request succeeds.
    dict[str, str]
        An error mapping ``{"Error": <message>}`` when an invalid type is
        supplied.
    """
    app: AppContext = ctx.request_context.lifespan_context

    try:
        data_type = DataType(bollettino_type)  # "bollettino_incendi" -> DataType.BOLLETTINO_INCENDI
        logg
    except ValueError:
        return {"Error": f"Tipo di bollettino non valido: {bollettino_type}"}

    return await app.api_client.crawl_bollettini_cached(
        data_type=data_type,
        cache_key=date.today().isoformat(),
    )
