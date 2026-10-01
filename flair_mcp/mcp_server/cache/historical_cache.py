import json
import logging
from datetime import datetime, timedelta
from typing import Any

import duckdb
logger = logging.getLogger(__name__)

class HistoricalCache:
    """L3: shared, queryable cache backed by DuckDB. Also serves historical queries."""
    #TODO le table sql ancora non sono ben definite, ma le ho messe per prova

    def __init__(self, db_path: str = './data/duck/historical.duckdb'):
        self._conn = duckdb.connect(db_path)
        self._conn.execute('''
                           CREATE TABLE IF NOT EXISTS cache
                           (
                               chiave    VARCHAR PRIMARY KEY,
                               valore    VARCHAR,
                               creato_il TIMESTAMP,
                               scade_il  TIMESTAMP
                           )
                           ''')

    def get(self, key: str) -> Any | None:
        row = self._conn.execute(
            'SELECT valore FROM cache WHERE chiave = ? AND scade_il > ?',
            [key, datetime.now()]
        ).fetchone()
        if row is None:
            return None
        return json.loads(row[0])['v']

    def set(self, key: str, value: Any, ttl: int) -> None:
        now = datetime.now()
        payload = json.dumps({'v': value})
        self._conn.execute(
            'INSERT OR REPLACE INTO cache VALUES (?, ?, ?, ?)',
            [key, payload, now, now + timedelta(seconds=ttl)]
        )