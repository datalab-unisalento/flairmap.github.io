from mcp_server.api.models import Zona
from mcp_server.server import mcp
from mcp_server.utils.csv_utils import leggi_zone

def _norm(s: str) -> str:
    return s.strip().casefold()


@mcp.tool()
def find_zona(luogo: str) -> list[Zona]:
    """Cerca le zone per comune, provincia, sigla o codice ISTAT.

    Restituisce l'elenco delle Zona corrispondenti (vuoto se nessuna trovata).
    """
    q = _norm(luogo)
    if not q:
        raise ValueError("Parametro 'luogo' vuoto")

    zone = leggi_zone()  # CSV_PATH = percorso del tuo file
    trovate = [
        z for z in zone
        if q in (_norm(z.comune), _norm(z.provincia), _norm(z.sigla), _norm(z.codice_istat))
    ]

    if not trovate:
        raise ValueError(f"Nessuna zona trovata per '{luogo}'")
    return trovate

        
            
            

