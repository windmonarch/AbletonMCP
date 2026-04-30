# server_arrangement.py
# AbletonMCP server entry point.
# Run via: uv run --with mcp[cli] server_arrangement.py
import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator, Dict, Any

from mcp.server.fastmcp import FastMCP

from ableton.connection import get_ableton_connection, shutdown_connection
import ableton.tools_session as tools_session
import ableton.tools_arrangement as tools_arrangement
import ableton.tools_browser as tools_browser
import ableton.tools_devices as tools_devices

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("AbletonMCPServer")


@asynccontextmanager
async def server_lifespan(server: FastMCP) -> AsyncIterator[Dict[str, Any]]:
    logger.info("AbletonMCP server starting up")
    try:
        get_ableton_connection()
        logger.info("Connected to Ableton on startup")
    except Exception as e:
        logger.warning(f"Could not connect to Ableton on startup: {str(e)}")
    try:
        yield {}
    finally:
        shutdown_connection()
        logger.info("AbletonMCP server shut down")


mcp = FastMCP("AbletonMCP", lifespan=server_lifespan)

# Register all tool groups
tools_session.register(mcp)
tools_arrangement.register(mcp)
tools_browser.register(mcp)
tools_devices.register(mcp)


def main():
    mcp.run()


if __name__ == "__main__":
    main()
