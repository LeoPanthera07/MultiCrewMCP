"""Unit tests for the MCP server search, records, and report tools."""

import os
import shutil
from pathlib import Path
from server.tools.search import search_documents
from server.tools.records import read_record
from server.tools.report import save_report

# Ensure env variables are configured for tests
os.environ["DATA_DIR"] = "./data"
os.environ["OUTPUTS_DIR"] = "./outputs"
os.environ["TRACES_DIR"] = "./traces"

def test_document_search() -> None:
    """Verify that document search tool behaves correctly on different queries."""
    # empty query -> error dict
    res_empty = search_documents("")
    assert isinstance(res_empty, dict)
    assert "error" in res_empty

    # no-match query -> []
    res_nomatch = search_documents("completelyunmatchedwordquery")
    assert res_nomatch == []

    # real query "return policy" -> list with at least 1 result with doc_id and snippet
    res_real = search_documents("return policy")
    assert isinstance(res_real, list)
    assert len(res_real) >= 1
    first = res_real[0]
    assert "doc_id" in first
    assert "snippet" in first
    assert "score" in first
    assert "return_policy" in [r["doc_id"] for r in res_real]

def test_query_records() -> None:
    """Verify that records query correctly reads the CSV file and filters by order ID."""
    # empty id -> error dict
    res_empty = read_record("")
    assert isinstance(res_empty, dict)
    assert "error" in res_empty

    # id with spaces -> error dict
    res_spaces = read_record("ORD 001")
    assert isinstance(res_spaces, dict)
    assert "error" in res_spaces

    # existing id (ORD-001) -> full record dict
    res_exist = read_record("ORD-001")
    assert isinstance(res_exist, dict)
    assert "error" not in res_exist
    assert res_exist["id"] == "ORD-001"
    assert res_exist["customer"] == "John Doe"
    assert res_exist["status"] == "delivered"

    # non-existing id (ORD-999) -> error dict with id field
    res_nonexist = read_record("ORD-999")
    assert isinstance(res_nonexist, dict)
    assert "error" in res_nonexist
    assert res_nonexist["id"] == "ORD-999"

def test_save_report() -> None:
    """Verify report saving logic, validation, and path traversal protection."""
    # empty title -> error dict
    res_empty_title = save_report("", "some content")
    assert isinstance(res_empty_title, dict)
    assert "error" in res_empty_title

    # path traversal attempt (../../../etc/passwd) -> saved inside outputs/ only
    traversal_title = "../../../etc/passwd"
    res_traversal = save_report(traversal_title, "content")
    assert isinstance(res_traversal, str)
    
    saved_path = Path(res_traversal)
    outputs_dir = Path("./outputs").resolve()
    
    # Assert that the path resides strictly inside outputs_dir
    assert saved_path.is_relative_to(outputs_dir)
    assert saved_path.name.startswith("report_")
    assert "passwd" in saved_path.name
    
    # Clean up the created test file if it exists
    if saved_path.is_file():
        saved_path.unlink()

    # valid title + content -> returns a path inside outputs/
    res_valid = save_report("valid-title", "valid content")
    assert isinstance(res_valid, str)
    
    valid_path = Path(res_valid)
    assert valid_path.is_relative_to(outputs_dir)
    assert valid_path.is_file()
    assert valid_path.read_text(encoding="utf-8") == "valid content"
    
    # Clean up
    valid_path.unlink()
