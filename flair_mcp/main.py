import logging
import os

from mcp_server.server import mcp
import mcp_server.tool
import mcp_server.prompt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
def main():
    transport = os.getenv("MCP_TRANSPORT")

    logger.info(f"Starting FLAIR MCP Server [transport={transport}]")

    if transport == "streamable-http":
        mcp.run(transport="streamable-http", host="0.0.0.0", port=8000) #TODO usa il .env
    else:
        mcp.run(transport="stdio")

if __name__ == '__main__':
    main()