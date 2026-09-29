# models.py

from pydantic import BaseModel
from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, Field

Livello = Literal["BASSO", "MEDIO", "MODERATO", "ELEVATO", "ESTREMO"]


class RischioZona(BaseModel):
    """Pericolosità incendi per una zona omogenea AIB in una data di previsione."""

    data_emissione: date = Field(description="Data di emissione del bollettino")
    data_previsione: date = Field(description="Giorno a cui si riferisce la previsione (24/48/72h)")
    zona: str = Field(description="Zona omogenea AIB")
    livello: Livello = Field(description="Livello di pericolosità")
    livello_num: int = Field(ge=1, le=5, description="Livello numerico: 1=BASSO ... 5=ESTREMO")
    file: str = Field(description="PDF di origine")

class Zona(BaseModel):
    codice_istat: str = Field(description="Codice ISTAT")
    comune: str = Field(description="Comune associato")
    provincia: str = Field(description="Provincia")
    sigla: str = Field(description="Sigla")
    settore_aib: str = Field(
        description="Settore AIB, zona territoriale da usare per ricerca nei report"
    )


class IncendioMeteo(BaseModel):
    # ----------------------------------------------------------------------
    # Identificativi
    # ----------------------------------------------------------------------
    id_riga: int = Field(..., description="Identificatore univoco della riga")
    data: date = Field(..., description="Data dell'evento")
    anno: int = Field(..., ge=1900, le=2100)
    mese: int = Field(..., ge=1, le=12)

    # ----------------------------------------------------------------------
    # Localizzazione
    # ----------------------------------------------------------------------
    comune: str
    comune_istat: str = Field(..., alias="comune_istat")
    provincia: str
    zona: str
    zona_certezza: Optional[str] = Field(None, description="Indice di certezza della zona")
    localita: Optional[str] = Field(..., alias="localita")
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)

    # ----------------------------------------------------------------------
    # Caratteristiche incendio
    # ----------------------------------------------------------------------
    tipologia: str
    codice_colore: str
    dist_comune_km: Optional[float] = Field(None, ge=0)
    comune_da_coordinate: Optional[str] = None
    flag_coord: Optional[str] = None #valore da mappare
    flag_coord_bassa_precisione: Optional[bool] = None
    flag_possibile_duplicato: Optional[bool] = None
    gruppo_duplicato: Optional[int] = None
    flag_localita_incompleta: Optional[bool] = None

    # ----------------------------------------------------------------------
    # Meteo (punto)
    # ----------------------------------------------------------------------
    meteo_punto: Optional[str] = None
    meteo_lat: Optional[float] = Field(None, ge=-90, le=90)
    meteo_lon: Optional[float] = Field(None, ge=-180, le=180)

    # ----------------------------------------------------------------------
    # FWI (Fire Weather Index)
    # ----------------------------------------------------------------------
    fwi_cella_lat: Optional[float] = None
    fwi_cella_lon: Optional[float] = None
    fwi_dist_cella_km: Optional[float] = Field(None, ge=0)
    fwi: Optional[float] = None
    fwi_classe: Optional[str] = None

    # ----------------------------------------------------------------------
    # Variabili meteo
    # ----------------------------------------------------------------------
    temp_max_c: Optional[float] = None
    temp_ore12_c: Optional[float] = None
    umidita_min_pct: Optional[float] = Field(None, ge=0, le=100)
    umidita_media_pct: Optional[float] = Field(None, ge=0, le=100)
    umidita_ore12_pct: Optional[float] = Field(None, ge=0, le=100)
    vento_max_kmh: Optional[float] = None
    vento_ore12_kmh: Optional[float] = None
    raffica_max_kmh: Optional[float] = None
    dir_vento_ore12_gradi: Optional[int] = Field(None, ge=0, le=360)
    dir_vento_max_gradi: Optional[int] = Field(None, ge=0, le=360)
    pioggia_giorno_mm: Optional[float] = None
    pioggia_giorno_prima_mm: Optional[float] = None
    meteo_quota_m: Optional[int] = None
    vento_ore12_nome: Optional[str] = None
    fuoco_spinto_verso: Optional[str] = None