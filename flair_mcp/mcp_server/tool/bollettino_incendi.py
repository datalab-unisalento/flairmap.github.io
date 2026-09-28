import datetime
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


@mcp.tool(
    name="bollettino_giornaliero",
    description=(
        "Restituisce il testo del bollettino giornaliero della protezione civile. "
        "bollettino_type: 'bollettino_incendi' per il rischio incendi boschivi, "
        "'bollettino_puglia' per il bollettino generale della Puglia."
    ),
)
async def get_bollettino_incendi(
    bollettino_type: Literal["bollettino_incendi", "bollettino_puglia"],
    ctx: Context,
) -> str | dict[str, str]:
    app: AppContext = ctx.request_context.lifespan_context

    try:
        data_type = DataType(bollettino_type)  # "bollettino_incendi" -> DataType.BOLLETTINO_INCENDI
    except ValueError:
        return {"Error": f"Tipo di bollettino non valido: {bollettino_type}"}

    return await app.api_client.crawl_bollettini_cached(
        data_type=data_type,
        cache_key=date.today().isoformat(),
    )
