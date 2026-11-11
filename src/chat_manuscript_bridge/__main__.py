"""python -m chat_manuscript_bridge starts a local stdio MCP service."""
import os

os.environ["BRIDGE_TRANSPORT"] = "stdio"
from .server import main

main()
