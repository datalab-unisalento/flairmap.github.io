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
import logging

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

    except ValueError:
        return {"Error": f"Tipo di bollettino non valido: {bollettino_type}"}

    return await app.api_client.crawl_bollettini_cached(
        data_type=data_type,
        cache_key=date.today().isoformat(),
    )
