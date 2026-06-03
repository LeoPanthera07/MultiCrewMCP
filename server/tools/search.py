"""MCP tool for searching through the synthetic document store."""

import os
import re
from pathlib import Path
from dotenv import load_dotenv
from server.utils.validators import require_non_empty_string

# Global cache for the document index
_INDEX = None
_INDEX_MTIME = None  # Track docs directory modification time for cache invalidation
MAX_FILE_SIZE = 1_000_000  # 1MB limit per file to prevent memory exhaustion

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

    # 2. Build index if not cached, or invalidate if docs directory was modified
    global _INDEX, _INDEX_MTIME
    current_mtime = docs_path.stat().st_mtime
    if _INDEX is None or _INDEX_MTIME != current_mtime:
        _INDEX = []
        _INDEX_MTIME = current_mtime
        for file_path in docs_path.glob("*.txt"):
            try:
                # Skip files larger than MAX_FILE_SIZE to prevent memory exhaustion
                if file_path.stat().st_size > MAX_FILE_SIZE:
                    continue
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

    # Sort query tokens by length (longest/most specific first)
    sorted_query_tokens = sorted(list(query_tokens), key=len, reverse=True)
    # Filter out short/common stop words for snippet matching if they are too short
    specific_tokens = [t for t in sorted_query_tokens if len(t) >= 4]
    if not specific_tokens:
        specific_tokens = sorted_query_tokens

    matches = []
    for doc in _INDEX:
        # Score is the count of query tokens that appear in the document tokens
        score = len(query_tokens & doc["tokens"])
        if score > 0:
            content = doc["content"]
            # Split into paragraphs to prevent bridging unrelated sections
            paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
            
            best_overall_score = (-1, -1)
            best_snippet = ""
            
            # Filter out extremely common stop words to prioritize specific query terms
            stop_words = {'what', 'is', 'the', 'for', 'at', 'of', 'in', 'and', 'a', 'to', 'policy', 'policies', 'novamart', 'document', 'documents', 'question'}
            scoring_tokens = query_tokens - stop_words
            if not scoring_tokens:
                scoring_tokens = query_tokens
                
            for para in paragraphs:
                para_lower = para.lower()
                para_len = len(para)
                
                if para_len <= 200:
                    # Score the whole paragraph
                    window_tokens = re.findall(r"[a-z0-9]+", para_lower)
                    matched_query_tokens = set()
                    for q in scoring_tokens:
                        if len(q) >= 4:
                            if any(w.startswith(q) for w in window_tokens):
                                matched_query_tokens.add(q)
                        else:
                            if q in window_tokens:
                                matched_query_tokens.add(q)
                    unique_score = len(matched_query_tokens)
                    occurrence_score = sum(len(w) for w in window_tokens if any(w.startswith(q) if len(q) >= 4 else w == q for q in scoring_tokens))
                    
                    win_score = (unique_score, occurrence_score)
                    if win_score > best_overall_score:
                        best_overall_score = win_score
                        best_snippet = para
                else:
                    # Slide window of size 200 with step size 5 within the paragraph
                    for start in range(0, para_len - 199, 5):
                        window_lower = para_lower[start:start+200]
                        window_tokens = re.findall(r"[a-z0-9]+", window_lower)
                        
                        matched_query_tokens = set()
                        for q in scoring_tokens:
                            if len(q) >= 4:
                                if any(w.startswith(q) for w in window_tokens):
                                    matched_query_tokens.add(q)
                            else:
                                if q in window_tokens:
                                    matched_query_tokens.add(q)
                        unique_score = len(matched_query_tokens)
                        occurrence_score = sum(len(w) for w in window_tokens if any(w.startswith(q) if len(q) >= 4 else w == q for q in scoring_tokens))
                        
                        win_score = (unique_score, occurrence_score)
                        if win_score > best_overall_score:
                            best_overall_score = win_score
                            best_snippet = para[start:start+200]
            
            snippet = best_snippet if best_snippet else content[:200]

            matches.append({
                "doc_id": doc["doc_id"],
                "filename": doc["filename"],
                "snippet": snippet,
                "score": score
            })

    # 4. Sort descending by score, and select top 5
    matches.sort(key=lambda x: x["score"], reverse=True)
    return matches[:5]
