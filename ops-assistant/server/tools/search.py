"""MCP tool for searching through the synthetic document store."""

import os
import re
from pathlib import Path
from dotenv import load_dotenv
from server.utils.validators import require_non_empty_string

# Global cache for the document index
_INDEX = None

def search_documents(query: str) -> list[dict] | dict:
    """Search synthetic documents in the data/docs directory matching the query."""
    load_dotenv()

    # 1. Validate query
    validation_error = require_non_empty_string(query, "query", 200)
    if validation_error:
        return {"error": validation_error}

    data_dir = os.getenv("DATA_DIR", "./data")
    docs_path = Path(data_dir) / "docs"

    # 6. Check if directory exists
    if not docs_path.is_dir():
        return {"error": "document directory not found"}

    # 2. Build index if not cached
    global _INDEX
    if _INDEX is None:
        _INDEX = []
        for file_path in docs_path.glob("*.txt"):
            try:
                content = file_path.read_text(encoding="utf-8")
                # Get lowercase alphanumeric tokens for searching
                tokens = set(re.findall(r"[a-z0-9]+", content.lower()))
                _INDEX.append({
                    "doc_id": file_path.stem,
                    "filename": file_path.name,
                    "content": content,
                    "tokens": tokens
                })
            except Exception:
                # Silently skip file read failures for robustness
                pass

    # 3. Score each document
    query_tokens = set(re.findall(r"[a-z0-9]+", query.lower()))
    if not query_tokens:
        return []

    matches = []
    for doc in _INDEX:
        # Score is the count of query tokens that appear in the document tokens
        score = len(query_tokens & doc["tokens"])
        if score > 0:
            matches.append({
                "doc_id": doc["doc_id"],
                "filename": doc["filename"],
                "snippet": doc["content"][:200],
                "score": score
            })

    # 4. Sort descending by score, and select top 5
    matches.sort(key=lambda x: x["score"], reverse=True)
    return matches[:5]
