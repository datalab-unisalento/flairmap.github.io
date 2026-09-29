import csv
import logging
import os
from pathlib import Path

from mcp_server.api.models import Zona, IncendioMeteo
#Classe che estrae dati dai csv, al momento prendiamo dai dataset, un domani possiamo prendere da api



from pathlib import Path

# se questo codice sta in mcp_server/qualcosa/file.py, regola i parents
logger = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parents[1]   # /app/mcp_server


def leggi_zone(CSV_PATH,COLONNE,delimiter: str = ",", encoding: str = "utf-8-sig") -> list[Zona]:
    zone: list[Zona] = []
    path = CSV_PATH
    with open(Path(path), newline="", encoding=encoding) as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        logger.info(f'reader: {reader.fieldnames}')
        for riga in reader:
            zone.append(
                Zona(**{campo: (riga[col] or "").strip() for campo, col in COLONNE.items()})
            )
    return zone



def get_incendi_meteo(
    csv_path,
    colonne,
    settore_aib: str,
    delimiter: str = ",",
    encoding: str = "utf-8-sig",
) -> list[IncendioMeteo]:
    risultati = []
    with open(csv_path, newline="", encoding=encoding) as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        reader.fieldnames = [h.strip() for h in (reader.fieldnames or [])]
        for riga in reader:
            if (riga.get("zona") or "").strip().casefold() != settore_aib.strip().casefold():
                continue
            dati = {
                campo: (riga.get(col) or "").strip() or None
                for campo, col in colonne.items()
            }
            risultati.append(IncendioMeteo.model_validate(dati))
    return risultati



