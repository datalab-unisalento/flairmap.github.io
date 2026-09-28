# This is a sample Python script.
import logging
import os

from mcp_server.server import mcp


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
def main():
    transport = os.getenv("MCP_TRANSPORT", "stdio")

    logger.info(f"Starting energy-trader MCP Server [transport={transport}]")

    if transport == "streamable-http":
        mcp.run(transport="streamable-http")
    else:
        mcp.run(transport="stdio")

if __name__ == '__main__':
    main()

    import pydevd_pycharm

    pydevd_pycharm.settrace('localhost', port=5679, stdout_to_server=True, stderr_to_server=True)