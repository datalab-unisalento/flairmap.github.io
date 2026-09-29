import logging
import os
from pathlib import Path

from mcp_server.api.models import Zona, IncendioMeteo
from mcp_server.server import mcp
from mcp_server.utils.csv_utils import leggi_zone, get_incendi_meteo

logger = logging.getLogger(__name__)

COLONNE_MAPPING_ZONA = {
    "codice_istat": "codice_istat",
    "comune": "comune",
    "provincia": "provincia",
    "sigla": "sigla",
    "settore_aib": "settore_aib",
}

COLONNE_INCENDI_METEO = {
    "id_riga": "id_riga",
    "data": "data",
    "anno": "anno",
    "mese": "mese",
    "comune": "comune",
    "comune_istat": "comune_istat",
    "provincia": "provincia",
    "zona": "zona",
    "zona_certezza": "zona_certezza",
    "località": "località",
    "lat": "lat",
    "lon": "lon",
    "tipologia": "tipologia",
    "codice_colore": "codice_colore",
    "dist_comune_km": "dist_comune_km",
    "comune_da_coordinate": "comune_da_coordinate",
    "flag_coord": "flag_coord",
    "flag_coord_bassa_precisione": "flag_coord_bassa_precisione",
    "flag_possibile_duplicato": "flag_possibile_duplicato",
    "gruppo_duplicato": "gruppo_duplicato",
    "flag_località_incompleta": "flag_località_incompleta",
    "meteo_punto": "meteo_punto",
    "meteo_lat": "meteo_lat",
    "meteo_lon": "meteo_lon",
    "fwi_cella_lat": "fwi_cella_lat",
    "fwi_cella_lon": "fwi_cella_lon",
    "fwi_dist_cella_km": "fwi_dist_cella_km",
    "fwi": "fwi",
    "fwi_classe": "fwi_classe",
    "temp_max_c": "temp_max_c",
    "temp_ore12_c": "temp_ore12_c",
    "umidita_min_pct": "umidita_min_pct",
    "umidita_media_pct": "umidita_media_pct",
    "umidita_ore12_pct": "umidita_ore12_pct",
    "vento_max_kmh": "vento_max_kmh",
    "vento_ore12_kmh": "vento_ore12_kmh",
    "raffica_max_kmh": "raffica_max_kmh",
    "dir_vento_ore12_gradi": "dir_vento_ore12_gradi",
    "dir_vento_max_gradi": "dir_vento_max_gradi",
    "pioggia_giorno_mm": "pioggia_giorno_mm",
    "pioggia_giorno_prima_mm": "pioggia_giorno_prima_mm",
    "meteo_quota_m": "meteo_quota_m",
    "vento_ore12_nome": "vento_ore12_nome",
    "fuoco_spinto_verso": "fuoco_spinto_verso",
}

BASE_DIR = Path(__file__).resolve().parents[1]   # /app/mcp_server

CSV_PATH_MAPPING = Path(
    os.getenv("CSV_PATH")
    or BASE_DIR / "resources" / "data" / "tutti_comuni_puglia_settori_aib.csv"
)
CSV_INCENDI = Path(
    os.getenv("CSV_PATH")
    or BASE_DIR / "resources" / "data" / "incendi_meteo_dir_zone.csv"
)

def _norm(s: str) -> str:
    return s.strip().casefold()

def _filter_zona(CSV_PATH,COLONNE,luogo:str):
    q = _norm(luogo)
    if not q:
        raise ValueError("Parametro 'luogo' vuoto")

    zone = leggi_zone(CSV_PATH,COLONNE)  # CSV_PATH = percorso del tuo file
    trovate = [
        z for z in zone
        if q in (_norm(z.comune), _norm(z.provincia), _norm(z.sigla), _norm(z.codice_istat),_norm(z.settore_aib))
    ]

    if not trovate:
        raise ValueError(f"Nessuna zona trovata per '{luogo}'")
    return trovate

@mcp.tool()
def find_zona(luogo: str) -> list[Zona]:
    """Cerca le zone per comune, provincia, sigla o codice ISTAT.

    Restituisce l'elenco delle Zona corrispondenti (vuoto se nessuna trovata).
    """
    return _filter_zona(CSV_PATH_MAPPING,COLONNE_MAPPING_ZONA,luogo)


@mcp.tool()
def incendi_meteo_dir(settore_aib:str)-> list[IncendioMeteo]:
    incendi_meteo = get_incendi_meteo(
        CSV_INCENDI,
        COLONNE_INCENDI_METEO,
        settore_aib=settore_aib,
        delimiter=",",
    )
    norm = _norm(settore_aib)
    incendi = [
        incendio for incendio in incendi_meteo
        if norm in (_norm(incendio.zona))
    ]
    logger.info(f'zona trovata')
    if not incendi:
        raise ValueError(f"Nessuna zona trovata per '{settore_aib}'")
    return incendi


        
            
            

