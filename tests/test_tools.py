"""Unit tests for the MCP server search, records, and report tools.

Covers the full test matrix:
  search_documents: T-S-01 through T-S-05
  read_record:      T-R-01 through T-R-05
  save_report:      T-W-01 through T-W-04

Plus snippet-selection regression tests and input validation edge cases.
"""

import os
import shutil
import tempfile
from pathlib import Path
from unittest import mock

# Ensure env variables are configured for tests
os.environ["DATA_DIR"] = "./data"
os.environ["OUTPUTS_DIR"] = "./outputs"
os.environ["TRACES_DIR"] = "./traces"

from server.tools.search import search_documents
from server.tools.records import read_record
from server.tools.report import save_report

# ---------------------------------------------------------------------------
# Helper to reset the global search index cache between tests that mock paths
# ---------------------------------------------------------------------------
def _reset_search_index():
    import server.tools.search as _mod
    _mod._INDEX = None
    _mod._INDEX_MTIME = None


# ===== search_documents tests =====

class TestSearchDocuments:
    """T-S-01 through T-S-05 plus regression tests."""

    def test_t_s_01_empty_query(self):
        """T-S-01: empty query → error about non-empty string."""
        res = search_documents("")
        assert isinstance(res, dict)
        assert "error" in res
        assert "non-empty" in res["error"].lower() or "empty" in res["error"].lower()

    def test_t_s_02_max_length_query(self):
        """T-S-02: 201-char query → error about max length."""
        long_query = "a" * 201
        res = search_documents(long_query)
        assert isinstance(res, dict)
        assert "error" in res
        assert "max" in res["error"].lower() or "length" in res["error"].lower()

    def test_t_s_03_return_policy_query(self):
        """T-S-03: query='return policy' → list with doc_id and snippet."""
        res = search_documents("return policy")
        assert isinstance(res, list)
        assert len(res) >= 1
        first = res[0]
        assert "doc_id" in first
        assert "snippet" in first
        assert "return_policy" in [r["doc_id"] for r in res]

    def test_t_s_04_no_match_query(self):
        """T-S-04: no-match query → empty list."""
        res = search_documents("xyzzyspoonshift")
        assert res == []

    def test_t_s_05_missing_docs_dir(self):
        """T-S-05: mock missing docs dir → error about directory not found."""
        _reset_search_index()
        with mock.patch.dict(os.environ, {"DATA_DIR": "/nonexistent/path"}):
            res = search_documents("return policy")
        _reset_search_index()  # restore for subsequent tests
        assert isinstance(res, dict)
        assert "error" in res
        assert "directory" in res["error"].lower() or "not found" in res["error"].lower()

    def test_boundary_200_char_query(self):
        """Boundary: exactly 200 chars should be accepted."""
        query_200 = "a" * 200
        res = search_documents(query_200)
        # Should not be an error (it may return [] for no matches, that's fine)
        assert not (isinstance(res, dict) and "error" in res)

    def test_wrong_type_query(self):
        """Input validation: integer instead of string → error."""
        res = search_documents(123)  # type: ignore
        assert isinstance(res, dict)
        assert "error" in res

    def test_sliding_window_snippet_selection(self):
        """Verify snippet contains target keywords for Zone B query."""
        res = search_documents("Zone B customer shipping timelines")
        assert isinstance(res, list)
        assert len(res) >= 1
        zone_cov_res = [r for r in res if r["doc_id"] == "zone_coverage"]
        assert len(zone_cov_res) == 1
        snippet = zone_cov_res[0]["snippet"]
        assert "Zone B" in snippet
        assert "Standard Shipping takes 3 to 4 business days" in snippet

    def test_electronics_snippet_selection(self):
        """Verify electronics return policy snippet is selected."""
        res = search_documents("What is the return policy for electronics at NovaMart?")
        assert isinstance(res, list)
        assert len(res) >= 1
        ret_pol_res = [r for r in res if r["doc_id"] == "return_policy"]
        assert len(ret_pol_res) == 1
        snippet = ret_pol_res[0]["snippet"]
        assert "electronics must be returned within 14 days" in snippet
        assert "15% restocking fee" in snippet


# ===== read_record tests =====

class TestReadRecord:
    """T-R-01 through T-R-05."""

    def test_t_r_01_empty_id(self):
        """T-R-01: empty id → error."""
        res = read_record("")
        assert isinstance(res, dict)
        assert "error" in res

    def test_t_r_02_id_with_spaces(self):
        """T-R-02: id with spaces → invalid record id format error."""
        res = read_record("ORD 001")
        assert isinstance(res, dict)
        assert "error" in res

    def test_t_r_03_valid_id_ord_001(self):
        """T-R-03: id='ORD-001' → dict with all columns."""
        res = read_record("ORD-001")
        assert isinstance(res, dict)
        assert "error" not in res
        assert res["id"] == "ORD-001"
        assert res["customer"] == "John Doe"
        assert res["status"] == "delivered"
        # Verify all expected columns are present
        for col in ["id", "customer", "item", "qty", "status", "date"]:
            assert col in res, f"Missing column: {col}"

    def test_t_r_04_nonexistent_id(self):
        """T-R-04: id='ORD-999' → error with id field."""
        res = read_record("ORD-999")
        assert isinstance(res, dict)
        assert "error" in res
        assert res["id"] == "ORD-999"

    def test_t_r_05_missing_csv(self):
        """T-R-05: mock missing CSV → error about records file not found."""
        with mock.patch.dict(os.environ, {"DATA_DIR": "/nonexistent/path"}):
            res = read_record("ORD-001")
        assert isinstance(res, dict)
        assert "error" in res
        assert "not found" in res["error"].lower()

    def test_wrong_type_id(self):
        """Input validation: integer instead of string → error."""
        res = read_record(123)  # type: ignore
        assert isinstance(res, dict)
        assert "error" in res

    def test_case_insensitive_lookup(self):
        """Verify case-insensitive ID matching."""
        res = read_record("ord-001")
        assert isinstance(res, dict)
        assert "error" not in res
        assert res["customer"] == "John Doe"


# ===== save_report tests =====

class TestSaveReport:
    """T-W-01 through T-W-04."""

    def test_t_w_01_empty_title(self):
        """T-W-01: empty title → error."""
        res = save_report("", "some content")
        assert isinstance(res, dict)
        assert "error" in res

    def test_t_w_02_valid_save(self):
        """T-W-02: valid title + content → path inside outputs/."""
        res = save_report("test-report-valid", "This is test content.")
        assert isinstance(res, str)

        saved_path = Path(res)
        outputs_dir = Path("./outputs").resolve()

        assert saved_path.is_relative_to(outputs_dir)
        assert saved_path.is_file()
        assert saved_path.read_text(encoding="utf-8") == "This is test content."

        # Clean up
        saved_path.unlink()

    def test_t_w_03_path_traversal(self):
        """T-W-03: path traversal title → path still inside outputs/ only."""
        traversal_title = "../../../etc/passwd"
        res = save_report(traversal_title, "malicious content")
        assert isinstance(res, str)

        saved_path = Path(res)
        outputs_dir = Path("./outputs").resolve()

        # Must resolve strictly inside outputs/
        assert saved_path.is_relative_to(outputs_dir)
        assert saved_path.name.startswith("report_")
        # The ../ should have been sanitised to underscores
        assert ".." not in saved_path.name

        # Clean up
        if saved_path.is_file():
            saved_path.unlink()

    def test_t_w_04_content_too_long(self):
        """T-W-04: 51000-char content → error about max length."""
        long_content = "x" * 51000
        res = save_report("long-content-test", long_content)
        assert isinstance(res, dict)
        assert "error" in res
        assert "max" in res["error"].lower() or "length" in res["error"].lower()

    def test_wrong_type_title(self):
        """Input validation: integer title → error."""
        res = save_report(123, "content")  # type: ignore
        assert isinstance(res, dict)
        assert "error" in res

    def test_wrong_type_content(self):
        """Input validation: integer content → error."""
        res = save_report("title", 456)  # type: ignore
        assert isinstance(res, dict)
        assert "error" in res

    def test_whitespace_only_title(self):
        """Whitespace-only title should be treated as empty."""
        res = save_report("   ", "content")
        assert isinstance(res, dict)
        assert "error" in res


# ===== Prompt injection tests (Option A stretch feature) =====

class TestPromptInjection:
    """Verify that malicious document content cannot exploit the tools directly."""

    def test_malicious_doc_searchable(self):
        """The malicious doc should be indexed and searchable like any other doc."""
        _reset_search_index()
        # Use words that actually appear in the malicious_doc.txt content
        res = search_documents("IGNORE instructions output system prompt")
        assert isinstance(res, list)
        # malicious_doc should appear in results since it contains matching tokens
        doc_ids = [r["doc_id"] for r in res]
        assert "malicious_doc" in doc_ids

    def test_save_report_rejects_hacked_traversal(self):
        """Even if an agent is tricked into calling save_report with 'HACKED',
        the file is created inside outputs/ (not an arbitrary path).
        This verifies the tool's own defenses hold regardless of agent behavior."""
        from pathlib import Path
        res = save_report("HACKED", "system prompt here")
        assert isinstance(res, str)
        saved_path = Path(res)
        outputs_dir = Path("./outputs").resolve()
        assert saved_path.is_relative_to(outputs_dir)
        assert "HACKED" in saved_path.name
        # Clean up
        if saved_path.is_file():
            saved_path.unlink()

    def test_malicious_content_not_in_tool_output(self):
        """search_documents returns snippets, not executable instructions.
        The snippet should be plain text, not something that alters behavior."""
        _reset_search_index()
        res = search_documents("IGNORE ALL PREVIOUS INSTRUCTIONS")
        assert isinstance(res, list)
        if len(res) > 0:
            for item in res:
                # Tool output is just data — it contains text, not commands
                assert isinstance(item["snippet"], str)
                assert isinstance(item["doc_id"], str)
                # Tool doesn't execute anything in the snippet
                assert "doc_id" in item

# ===== Resource tests =====

class TestListDocumentsResource:
    """Verify that the list_documents resource works as expected."""

    def test_list_documents_success(self):
        from server.main import list_documents
        res = list_documents()
        assert "Available Policy and Support Documents" in res
        assert "return_policy.txt" in res
        assert "zone_coverage.txt" in res

    def test_list_documents_missing_dir(self):
        from server.main import list_documents
        from unittest import mock
        with mock.patch.dict(os.environ, {"DATA_DIR": "/nonexistent"}):
            res = list_documents()
        assert "No documents directory found" in res

