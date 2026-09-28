"""API client for REST API with rate limiting and retry logic."""

import asyncio
import time
from typing import Any

import httpx
import logging

from mcp.server import MCPServer
from mcp.server.context import Context

from mcp_server.cache import CacheManager
from mcp_server.cache.cache_manager import DataType
from mcp_server.utils.crawler_bollettino import CrawlerBollettino
from mcp_server.utils.load_bollettino_pdf import LoadBollettinoPdf

logger = logging.getLogger(__name__)


class ApiClient:
    """HTTP client for REST API, with cache-aside caching and retry logic."""

    def __init__(
        self,
        cache_manager: CacheManager,
        base_url: str = '',
        timeout: float = 120.0,
        available_constraint_timeout: float = 300.0,
        max_retries: int = 3,
        max_concurrent_requests: int = 5,
    ):
        """Initialize API client.

        Args:
            cache_manager: Cache manager instance (L1/L2/L3 cache-aside)
            base_url: Base URL of the API
            timeout: Default request timeout in seconds
            available_constraint_timeout: Timeout for availableconstraint endpoint in seconds
            max_retries: Maximum retry attempts on transient failures
            max_concurrent_requests: Max concurrent outbound requests (rate limiting)
        """
        self.cache_manager = cache_manager
        self._base_url = base_url.rstrip('/')
        self._timeout = timeout
        self._availableconstraint_timeout = available_constraint_timeout
        self._max_retries = max_retries

        # Rate limiter: limita n richieste max in parallelo
        self._rate_limiter = asyncio.Semaphore(max_concurrent_requests)

        self._client = httpx.AsyncClient(timeout=timeout)

        logger.info(f'ApiClient initialized: {base_url}')

    async def aclose(self) -> None:
        """Chiude la connessione HTTP sottostante. Da chiamare allo shutdown del server."""
        await self._client.aclose()

    async def get_available_constraints(self, ticker: str) -> dict[str, str] | None | Any:
        """Get available constraints for a given ticker.

        Passa dalla cache come STATICO: i vincoli disponibili per un ticker
        cambiano raramente, quindi non ha senso richiederli all'API ogni volta.
        """
        url = f"{self._base_url}/availableconstraint/{ticker}"
        return await self.make_cached_request(
            url=url,
            data_type=DataType.STATICO,
            cache_key=f"constraints_{ticker}",
            ctx=None,
            timeout_override=self._availableconstraint_timeout,
        )

    async def _request_with_retry(self, url: str, timeout: float) -> httpx.Response:
        """Esegue la richiesta HTTP con retry e backoff esponenziale sui fallimenti transitori."""
        last_exception: Exception | None = None

        for attempt in range(1, self._max_retries + 1):
            try:
                async with self._rate_limiter:
                    response = await self._client.get(url, timeout=timeout)
                response.raise_for_status()
                return response

            except httpx.HTTPStatusError as e:
                # Non chiamare chi è morto (4xx):3
                if 400 <= e.response.status_code < 500:
                    raise
                last_exception = e
            except (httpx.TimeoutException, httpx.TransportError) as e:
                last_exception = e

            if attempt < self._max_retries:
                backoff = 2 ** (attempt - 1)  # 1s, 2s, 4s, ...
                logger.warning(
                    f'Request to {url} failed (attempt {attempt}/{self._max_retries}), '
                    f'retrying in {backoff}s: {last_exception}'
                )
                await asyncio.sleep(backoff)

        raise last_exception

    async def make_cached_request(
        self,
        url: str,
        data_type: DataType,
        cache_key: str,
        ctx: Context | None, #TODO questa la tenevo per la key, ma forse si può levare
        timeout_override: float | None = None,
        **cache_params,
    ) -> dict[str, str] | None | Any:
        """Make an API request with intelligent caching.

        Implements L1 -> L2 -> L3 -> API fallback.

        Returns:
            dict: Response data, or {"Error": ...} on failure.
        """
        logger.info(f"requesting {url} - data_type: {data_type.value} - cache_key: {cache_key}")
        start_time = time.time()

        # Try to get from cache
        cached_data = await self.cache_manager.get(
            data_type=data_type, identifier=cache_key, **cache_params
        )

        # Confronto esplicito con None: un dato cachato "falsy" (dict vuoto,
        # lista vuota, 0) è comunque un hit valido, non va ricalcolato.
        if cached_data is not None:
            logger.info(f"Cache hit for {data_type.value}:{cache_key}")
            return cached_data

        # Cache miss - fetch from API
        try:
            logger.debug(f"making request to {url}")

            response = await self._request_with_retry(
                url, timeout=timeout_override or self._timeout
            )
            data = response.json()
            logger.debug(f"API response: {data}")

            # Track API call latency
            api_latency = (time.time() - start_time) * 1000
            self.cache_manager.record_api_call(api_latency)
            logger.info(f"API call latency: {api_latency:.2f}ms")

            # Cache the response
            await self.cache_manager.set(
                data_type=data_type, identifier=cache_key, data=data, **cache_params
            )
            logger.debug(f"API call for {data_type.value}:{cache_key} ({api_latency:.2f}ms)")
            return data

        except Exception as e:
            logger.error(f"API request failed: {type(e).__name__}: {e}", exc_info=True)
            return {"Error": str(e)}


    async def crawl_bollettini_cached(
            self,
            data_type: DataType,
            cache_key: str,
            **cache_params,
    ):
        logger.info(f"requesting bolletino - data_type: {data_type.value} - cache_key: {cache_key}")
        start_time = time.time()
        # Try to get from cache
        cached_data = await self.cache_manager.get(
            data_type=data_type, identifier=cache_key, **cache_params
        )

        if cached_data is not None:
            logger.info(f"Cache hit for {data_type.value}:{cache_key}")
            return cached_data

        try:
            logger.debug(f"making request")
            load_bollettino = LoadBollettinoPdf(data_type.value)
            response = await load_bollettino.get_bollettino()

            logger.debug(f"Bollettino response: {response}")

            # Track API call latency
            api_latency = (time.time() - start_time) * 1000
            self.cache_manager.record_api_call(api_latency)
            logger.info(f"API call latency: {api_latency:.2f}ms")

            # Cache the response
            await self.cache_manager.set(
                data_type=data_type, identifier=cache_key, data=response, **cache_params
            )
            logger.debug(f"API call for {data_type.value}:{cache_key} ({api_latency:.2f}ms)")
            return response

        except Exception as e:
            logger.error(f"API request failed: {type(e).__name__}: {e}", exc_info=True)
            return {"Error": str(e)}

