import asyncio
import hashlib
import json
import logging
from enum import Enum
from dataclasses import dataclass, field
from typing import Any

from mcp_server.cache.memory_cache import MemoryCache
from mcp_server.cache.disk_cache import DiskCache
from mcp_server.cache.historical_cache import HistoricalCache

from enum import Enum

logger = logging.getLogger(__name__)

class DataType(Enum):
    """Categorie di dati cachati, ognuna con un proprio ciclo di vita.

    Serve a far sì che il CacheManager scelga il TTL giusto in automatico
    in base a *cosa* sta cachando, senza che il chiamante debba specificarlo
    ogni volta a mano.
    """

    INDICE_PERICOLO = "indice_pericolo"
    # Es. FWI, umidità, indici di pericolo calcolati per comune/giorno.
    # Dipendono dal bollettino meteo: restano validi finché non esce
    # un nuovo bollettino, non hanno senso oltre quella finestra.

    SIMULAZIONE = "simulazione"
    # Risultato di una simulazione di propagazione per un dato innesco.
    # Dipende dal meteo del momento in cui è stata lanciata: se il meteo
    # cambia, la simulazione andrebbe rifatta, quindi TTL più breve

    STATICO = "statico"
    # Layer che cambiano raramente.
    # Non dipendono dal meteo: restano validi per settimane/mesi,
    # finché non si aggiorna il dataset sorgente.
    
    BOLLETTINO_INCENDI = "bollettino_incendi"
    BOLLETTINO_PUGLIA = "bollettino_puglia"

TTL_BY_TYPE: dict[DataType, int] = {
    # 3 ore: un compromesso ragionevole se il bollettino meteo aggiorna
    # 2-3 volte al giorno. In produzione andrebbe calcolato dinamicamente
    # sull'orario reale di emissione del bollettino, non fisso.
    DataType.INDICE_PERICOLO: 3 * 3600,
    # 1 ora: una simulazione ha senso restare valida solo per una finestra
    # breve, perché il vento e l'umidità possono cambiare rapidamente
    # e invalidare lo scenario calcolato.
    DataType.SIMULAZIONE: 3600,
    # 30 giorni: i layer statici cambiano su scala di mesi o anni.
    # Un TTL lungo evita di rileggere/ricalcolare dati che nella pratica
    # non cambiano mai durante la vita del prototipo.
    DataType.STATICO: 30 * 24 * 3600,
    # 1 giorno: i bollettini vengono emessi quotidianamente.
    DataType.BOLLETTINO_INCENDI: 24 * 3600,
    DataType.BOLLETTINO_PUGLIA: 24 * 3600,
}


@dataclass
class CacheStats:
    l1_hits: int = 0
    l2_hits: int = 0
    l3_hits: int = 0
    misses: int = 0
    api_latencies_ms: list[float] = field(default_factory=list)


class CacheManager:
    """Orchestrates L1 (memory) -> L2 (diskcache) -> L3 (DuckDB), async interface."""

    def __init__(self, l1: MemoryCache, l2: DiskCache, l3: HistoricalCache):
        self._l1 = l1
        self._l2 = l2
        self._l3 = l3
        self.stats = CacheStats()

    @staticmethod
    def _build_key(data_type: DataType, identifier: str, **params) -> str:
        raw = f"{data_type.value}:{identifier}:{json.dumps(params, sort_keys=True)}"
        return hashlib.sha256(raw.encode()).hexdigest()

    async def get(self, data_type: DataType, identifier: str, **params) -> Any | None:
        key = self._build_key(data_type, identifier, **params)

        value = self._l1.get(key)
        if value is not None:
            self.stats.l1_hits += 1
            return value

        value = self._l2.get(key)
        if value is not None:
            self.stats.l2_hits += 1
            self._l1.set(key, value)
            return value

        # DuckDB è I/O bloccante: girala su un thread per non fermare l'event loop
        value = await asyncio.to_thread(self._l3.get, key)
        if value is not None:
            self.stats.l3_hits += 1
            self._l2.set(key, value)
            self._l1.set(key, value)
            return value

        self.stats.misses += 1
        return None

    async def set(self, data_type: DataType, identifier: str, data: Any, **params) -> None:
        key = self._build_key(data_type, identifier, **params)
        ttl = TTL_BY_TYPE.get(data_type, 3600)

        self._l1.set(key, data, ttl=ttl)
        self._l2.set(key, data, ttl=ttl)
        await asyncio.to_thread(self._l3.set, key, data, ttl)

    def record_api_call(self, latency_ms: float) -> None:
        self.stats.api_latencies_ms.append(latency_ms)