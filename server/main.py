"""Main entry point for running the Operations Assistant MCP server."""

import sys
from pathlib import Path

# Add project root directory to sys.path to resolve absolute imports
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from mcp.server.fastmcp import FastMCP
from server.tools.search import search_documents as search_docs_impl
from server.tools.records import read_record as read_record_impl
from server.tools.report import save_report as save_report_impl

mcp = FastMCP("ops-assistant")

@mcp.tool()
def search_documents(query: str) -> list[dict] | dict:
    """Search synthetic documents in the data/docs directory matching the query."""
    return search_docs_impl(query)

@mcp.tool()
def read_record(id: str) -> dict:
    """Retrieve an order record by its ID from the CSV file."""
    return read_record_impl(id)

@mcp.tool()
def save_report(title: str, content: str) -> str | dict:
    """Save an operational report to the outputs directory."""
    return save_report_impl(title, content)

@mcp.resource("documents://list")
def list_documents() -> str:
    """List all available policy and support documents in the data/docs directory."""
    import os
    from pathlib import Path
    data_dir = os.getenv("DATA_DIR", "./data")
    docs_path = Path(data_dir) / "docs"
    if not docs_path.is_dir():
        return "No documents directory found."
    files = sorted(docs_path.glob("*.txt"))
    if not files:
        return "No documents found."
    
    lines = ["Available Policy and Support Documents:"]
    for f in files:
        lines.append(f"- {f.name} ({f.stat().st_size} bytes)")
    return "\n".join(lines)

if __name__ == "__main__":
    mcp.run()

