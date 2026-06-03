# Demo Script — Operations Assistant (5 minutes)

## MINUTE 1 — The Pitch (talk, no code)

"I built an Operations Assistant: a CrewAI crew of agents that share tools
exposed by a local MCP server. The crew answers business questions by searching
real documents and records, and writes a sourced report where every fact
cites its origin.

The system has two agents — a Researcher who retrieves evidence using
search_documents and read_record tools, and a Writer who synthesises
that evidence into a cited markdown report and saves it using save_report.

The MCP server runs locally via stdio transport — no open ports, no API keys,
no network exposure."

## MINUTE 2 — Show It Run (live terminal)

```bash
python main.py "What is the return policy for electronics and what is the status of ORD-007?"
```

Point out:
1. The tool calls appearing in the terminal (search_documents, read_record)
2. The Researcher's JSON evidence array output
3. The Writer's final report with inline (Source: ...) citations
4. The saved report file path in outputs/
5. The run_report.md generated automatically (Option D observability)

Open the saved report file and show:
- Every factual sentence has a (Source: <id>) citation
- Sources section at the end
- No hedging language ("I believe", "probably")

Open the run_report.md and show:
- Total wall time, tool call counts, token estimates
- Slowest tool call identification

## MINUTE 3 — One Decision and One Failure

Decision: "I used a context manager for MCPServerAdapter instead of manual
start/stop because the server is a subprocess — if the crew raises an
exception, the context manager ensures the process is cleaned up. Without it,
orphaned server processes would accumulate on every failed run."

Failure: "The first time I connected the crew, the Researcher agent returned
the tool name 'search_documents' as the source ID instead of the actual
document ID from the tool's response. This caused every report to cite
'(Source: search_documents)' which is meaningless. I fixed it by adding
explicit CRITICAL RULES to the Researcher's backstory that forbid using
tool names as source IDs and require extracting the doc_id field from
the tool response."

## MINUTE 4 — What You Learned

"MCP is a protocol that lets AI agents connect to external tools and data
sources through a standardised interface, similar to how USB standardised
hardware connections.

CrewAI is a framework for orchestrating multiple AI agents that work
sequentially or in parallel, each with defined roles and shared tool access.

The biggest security risk I took seriously was prompt injection through
document content — an attacker could embed instructions in a .txt file
that the Researcher retrieves and the Writer might follow. I added a
malicious_doc.txt test to verify the system resists this.

The two sources I used most were the CrewAI documentation for agent/task
configuration and the FastMCP tutorial for building the stdio server."

## MINUTE 5 — What's Next (30 seconds)

"Before this touches real company data, I would:
(1) Move transport to authenticated HTTP with API keys and rate limiting,
(2) Replace CSV with a real database with row-level access controls,
(3) Add a human approval gate before save_report writes to disk,
(4) Replace token-overlap search with a vector database for semantic search,
(5) Add a Fact-Checker agent that cross-references every citation."

## Recording Instructions

- Record one continuous take
- Face or voice on throughout
- Screen share for the live demo part (Minutes 2-3)
- Save recording to demo/ folder or upload as unlisted YouTube link
- Add the link to demo/demo_link.txt
