import logging
import os

from dotenv import load_dotenv
from fastmcp import FastMCP

from mcp_server.api.client import ApiClient
from mcp_server.cache import CacheManager, MemoryCache, DiskCache, HistoricalCache
from mcp_server.utils.logging import setup_logging

# Load environment variables
load_dotenv()

# Configuration from environment
API_BASE_URL = os.getenv('API_BASE_URL', '')
API_TIMEOUT = float(os.getenv('API_TIMEOUT_SECONDS', '120'))
AVAILABLECONSTRAINT_TIMEOUT = float(
    os.getenv('AVAILABLECONSTRAINT_TIMEOUT_SECONDS', '180')
)
API_MAX_RETRIES = int(os.getenv('API_MAX_RETRIES', '3'))
MAX_CONCURRENT_REQUESTS= int(os.getenv('MAX_CONCURRENT_REQUESTS', '5'))

# Use absolute path for log directory
DEFAULT_LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'log')
LOG_DIR = os.getenv('LOG_DIR', DEFAULT_LOG_DIR)
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

logger = logging.getLogger(__name__)



setup_logging(LOG_LEVEL, log_dir=LOG_DIR)
logger.info(f"Logger ready on dir:{LOG_DIR}")

#Init della cache
manager = CacheManager(
    l1=MemoryCache(),
    l2=DiskCache(cache_dir='./data/cache/disk'),
    l3=HistoricalCache(db_path='./data/cache/historical.duckdb'),
)

#Init api
api_client = ApiClient(
    cache_manager=manager,
    base_url=API_BASE_URL,
    timeout=API_TIMEOUT,
    available_constraint_timeout=AVAILABLECONSTRAINT_TIMEOUT,
    max_retries=API_MAX_RETRIES,
    max_concurrent_requests=MAX_CONCURRENT_REQUESTS

)



# Istanza globale — la importano tutti i tool
mcp = FastMCP(
    'energy-trader-mcp-server',
    host=os.getenv("MCP_HOST", "0.0.0.0"),
    port=int(os.getenv("MCP_PORT", "8000")),
)



"""
AC
 ,--.  
| oo | 
| ~~ |
"""
