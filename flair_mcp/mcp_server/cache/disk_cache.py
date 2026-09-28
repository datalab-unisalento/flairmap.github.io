import json
import logging
import tempfile
from pathlib import Path
from typing import Any
from diskcache import Cache

logger = logging.getLogger(__name__)

class DiskCache:
    def __init__(self, cache_dir: str = './cache'):
        """Initialize persistent cache.

        Args:
            cache_dir: Directory for cache files
        """
        self._cache_dir = Path(cache_dir)

        # Try to create the cache directory
        try:
            self._cache_dir.mkdir(parents=True, exist_ok=True)
            # Test if we can write to the directory
            test_file = self._cache_dir / '.test_write'
            test_file.touch()
            test_file.unlink()
            logger.info(f'DiskCache initialized at {self._cache_dir}')
        except (PermissionError, OSError) as e:
            # Fallback to temp directory
            logger.warning(
                f'Cannot create cache directory at {self._cache_dir}: {e}. '
                f'Using temp directory instead.'
            )
            self._cache_dir = Path(tempfile.gettempdir()) / 'istat_mcp_cache'
            self._cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f'DiskCache using fallback directory: {self._cache_dir}')

        self._cache = Cache(str(self._cache_dir))

    def get(self, key: str) -> Any | None:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        value = self._cache.get(key)
        if value is not None:
            logger.debug(f'DiskCache HIT: {key}')
            # Deserialize if it's JSON-serialized data
            if isinstance(value, str):
                try:
                    value = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    pass
        else:
            logger.debug(f'DiskCache MISS: {key}')
        return value