# AI Usage Log

This file tracks the usage of AI coding assistants and models during the development of this project.

## Phase 1 — Project Scaffold (2026-06-01)
- **Model**: Antigravity (powered by Gemini)
- **Tasks**: Scaffolded directory structure, generated 10 short synthetic policy/support documents for NovaMart, created the 20-row order dataset in CSV, configured pyproject.toml and env files.

## Phase 2 — MCP Server Implementation (2026-06-01)
- **Model**: Antigravity (powered by Gemini)
- **Tasks**: Implemented search_documents (token overlap with sliding window snippet selection), read_record (CSV lookup with validation), save_report (path-safe file writing with traversal protection), and validator helpers.

## Phase 3 — CrewAI Crew (2026-06-01 – 2026-06-02)
- **Model**: Antigravity (powered by Gemini)
- **Tasks**: Built Researcher and Writer agents with strict citation backstories, dynamic research/write task builders, MCPServerAdapter integration with context manager, TeeStream trace logging, and LoggedTool wrapper. Iteratively refined agent backstories to fix source misattribution and citation format issues.

## Phase 4 — Hardening (2026-06-03)
- **Model**: Antigravity (powered by Gemini)
- **Tasks**: Wrote 23 unit tests covering the full T-S/T-R/T-W test matrix, E2E test with 6 assertions, max_iter verification test. Implemented security fixes from AI red-team review (file size limit, cache invalidation). Wrote decision_log.md and reflection.md.

## Phase 5 — Stretch Features & Submission (2026-06-03)
- **Model**: Antigravity (powered by Gemini)
- **Tasks**: Implemented Option A (prompt injection test with malicious_doc.txt, 3 unit tests, 1 E2E test) and Option D (structured JSON observability traces with run_report.md generation). Updated README, prepared demo script.

## AI Red-Team Review (2026-06-03)
- **Model**: Antigravity (powered by Gemini)
- **Task**: Prompted the AI to act as a security red-teamer and review all MCP server code. Identified 5 security risks and implemented fixes for 2 (file size limit, cache invalidation). Documented all findings in decision_log.md.
