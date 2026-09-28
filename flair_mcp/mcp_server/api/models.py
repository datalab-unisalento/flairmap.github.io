# models.py

from pydantic import BaseModel
from datetime import date
from typing import Literal

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