from mcp.server.fastmcp import FastMCP
from constants import JSON_FORMAT

import signal
import sys


def cleanup(signum, frame):
    # Clean up resources
    print("Shutting down gracefully...")
    sys.exit(0)


signal.signal(signal.SIGTERM, cleanup)
signal.signal(signal.SIGINT, cleanup)


# Create an MCP server
mcp = FastMCP("NapkinWire")


# Add an addition tool
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

@mcp.tool()
def get_ticket_format() -> str:
    """Get the ticket format from the resource"""
    print("Called fetch ticketing format")
    
    
    return "Ticket format example:\n" +JSON_FORMAT


@mcp.resource("file://tickets/format.json")
def get_ticketing_format():
    
    """ Sample resource """
   
    return "Reference format for project tickets" + JSON_FORMAT


# Add a prompt
@mcp.prompt()
def greet_user(name: str, style: str = "friendly") -> str:
    """Generate a greeting prompt"""
    styles = {
        "friendly": "Please write a warm, friendly greeting",
        "formal": "Please write a formal, professional greeting",
        "casual": "Please write a casual, relaxed greeting",
    }

    return f"{styles.get(style, styles['friendly'])} for someone named {name}."
