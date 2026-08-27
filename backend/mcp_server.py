import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastmcp import FastMCP
from backend.db import get_documents_for_client, search_chunks_for_client

mcp = FastMCP("Doc Assistant")

@mcp.tool()
def list_documents(client_id: int) -> str:
    """Get the list of documents a client has uploaded, including filenames."""
    documents = get_documents_for_client(client_id)
    if not documents:
        return "This client has no uploaded documents."
    lines = [f"- {filename} ({file_path})" for filename, file_path in documents]
    return "Documents:\n" + "\n".join(lines)

@mcp.tool()
def search_documents(client_id: int, query: str) -> str:
    """Search the client's uploaded documents for content relevant to a question, and return the most relevant excerpts with citations. Use this whenever the user asks something that requires looking inside their documents."""
    documents = get_documents_for_client(client_id)
    if not documents:
        return "No documents available to search."

    pdf_paths = [file_path for _, file_path in documents]
    rows = search_chunks_for_client(client_id, pdf_paths, query)

    if not rows:
        return "No relevant content found in the client's documents for this query."

    parts = []
    for text, page_number, filename, distance in rows:
        parts.append(f"--- Source: {filename}, page {page_number} ---\n{text}")
    return "\n\n".join(parts)

if __name__ == "__main__":
    mcp.run()