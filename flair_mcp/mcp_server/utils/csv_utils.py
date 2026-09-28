import csv
import os
from pathlib import Path

from mcp_server.api.models import Zona

COLONNE = {
    "codice_istat": "codice_istat",
    "comune": "comune",
    "provincia": "provincia",
    "sigla": "sigla",
    "settore_aib": "settore_aib",
}

from pathlib import Path

# se questo codice sta in mcp_server/qualcosa/file.py, regola i parents

BASE_DIR = Path(__file__).resolve().parents[1]   # /app/mcp_server
CSV_PATH = Path(
    os.getenv("CSV_PATH")
    or BASE_DIR / "resources" / "data" / "tutti_comuni_puglia_settori_aib.csv"
)

def leggi_zone(delimiter: str = ";", encoding: str = "utf-8-sig") -> list[Zona]:
    zone: list[Zona] = []
    path = CSV_PATH
    with open(Path(path), newline="", encoding=encoding) as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        print(f'reader: {reader.fieldnames}')
        for riga in reader:
            zone.append(
                Zona(**{campo: (riga[col] or "").strip() for campo, col in COLONNE.items()})
            )
    return zone
