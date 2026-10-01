import logging
from pathlib import Path

from mcp_server.server import mcp

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent

@mcp.prompt()
def flair_operator() -> list:
    """Istruzioni per il trader analyst."""

    template = (PROMPTS_DIR / "Flair-operator.md").read_text()
    return [{"role": "assistant", "content": template}]
