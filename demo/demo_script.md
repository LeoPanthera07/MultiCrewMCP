# Word-for-Word Demo Script — Operations Assistant (5-Minute Video)

This script is carefully timed and structured to map directly to the requirements in **Section 10 (Your 5-minute clip)** and the **Core Hardening** and **Stretch** rubrics of the mini-project criteria.

---

## ⏱️ SEGMENT 1: The Pitch (0:00 - 1:00)
**Goal**: Explain what you built, why it matters, and how you would open in an interview.
**Visuals**: Facecam on. If using screen share, show your IDE project structure on the left and a welcome slide or your face on the right.

### 🎙️ Word-for-Word Speaking Script:
> *"Hello, my name is Mihir, and today I’m demonstrating the **Operations Assistant**—an automated decision-support system designed to solve support issues and generate operational summaries for a fictional e-commerce store, NovaMart.*
>
> *In daily operations, support staff waste valuable time manually cross-referencing company policy documents with order databases. To solve this, I built a multi-agent system using **CrewAI** that connects to a custom local **Model Context Protocol (MCP)** server.*
>
> *The system coordinates two specialized agents: an **Operations Researcher**, who handles information retrieval, and an **Operations Report Writer**, who compiles the final summaries. The MCP server runs locally via stdio transport. This means there are no open ports, no network exposure, and sensitive customer data stays entirely on the local machine."*

**💡 Rubric Mapping covered in this segment**:
* **MVP Tasks**: Setup / folder structure explanation.
* **Core Hardening**: Defined clear agent roles, goals, and tasks (Researcher vs Writer split).

---

## ⏱️ SEGMENT 2: Show It Run (1:00 - 2:00)
**Goal**: Ask a combined question, show the crew calling MCP tools, show the grounded answer with sources.
**Visuals**: Share your terminal. Run the main application command. Then open the output markdown report in your editor.

### 🎬 Action Cues:
1. Open terminal and run: `python main.py "What is the return policy for electronics and what is the status of ORD-007?"`
2. Let the agent logs scroll. Point with your cursor to the tool execution lines (`search_documents` and `read_record`).
3. Open the newly generated file in `outputs/report_Return_Policy_...md`.

### 🎙️ Word-for-Word Speaking Script:
> *"Let's run a live query: 'What is the return policy for electronics and what is the status of ORD-007?'*
>
> *As the crew starts, watch the console. The Operations Researcher identifies that it needs the return policy, so it calls our MCP tool `search_documents`. It also identifies the order ID ORD-007 and calls our `read_record` tool to fetch the database row from our CSV.*
>
> *The Researcher passes a structured JSON evidence array to the Writer. The Writer then synthesizes this and calls `save_report` to save the final report to our outputs directory.*
>
> *Let's look at the generated report. As you can see, every factual claim is strictly cited: the status of ORD-007 is pending (Source: ORD-007), and support details cite the support tickets. There is no hedging or hallucination. We also list our unique sources clearly in the footer."*

**💡 Rubric Mapping covered in this segment**:
* **MVP Tasks**: Two tools (`search_documents` and `read_record`) called over stdio; grounding (every fact cites its exact source, refuses when no evidence is found).
* **Core Hardening**: Third tool (`save_report`) writes report to outputs; input validation (arguments validated before tool execution).

---

## ⏱️ SEGMENT 3: Decisions & Failures (2:00 - 3:30)
**Goal**: Discuss one engineering decision, one failure, and how you fixed it.
**Visuals**: Show your IDE. Open [crew/crew.py](file:///Users/mihir/Programming/Projects_Local/Week-14Project/crew/crew.py) and highlight the `MCPServerAdapter` context manager (line 251). Open [server/main.py](file:///Users/mihir/Programming/Projects_Local/Week-14Project/server/main.py) and show the `@mcp.resource("documents://list")` resource.

### 🎬 Action Cues:
1. Highlight the `with MCPServerAdapter(server_params) as mcp_tools:` block in [crew/crew.py](file:///Users/mihir/Programming/Projects_Local/Week-14Project/crew/crew.py).
2. Show the `documents://list` resource in [server/main.py](file:///Users/mihir/Programming/Projects_Local/Week-14Project/server/main.py).
3. Open [crew/agents.py](file:///Users/mihir/Programming/Projects_Local/Week-14Project/crew/agents.py) and show the researcher's backstory.

### 🎙️ Word-for-Word Speaking Script:
> *"For my architectural decision, I chose to manage the MCP server lifecycle using a Python context manager via `MCPServerAdapter`. Because the stdio server runs as a subprocess, if the crew raises an exception, the context manager guarantees the subprocess is terminated. This prevents orphaned background Python processes from accumulating.*
>
> *To satisfy the core hardening resource requirement, I also built a FastMCP resource decorated at `documents://list` which allows the client to inspect all available files in `data/docs`.*
>
> *Regarding failures: when first connecting the crew, the Researcher agent started citing the tool name itself—meaning facts were marked as '(Source: search_documents)' instead of citing the actual document ID. This is a common multi-agent coordination bug.*
>
> *I fixed this by hardening the Researcher's backstory in `agents.py` with strict instructions: it must extract the specific `doc_id` field from the tool's JSON return, and it must cite the exact Order ID for database records."*

**💡 Rubric Mapping covered in this segment**:
* **Core Hardening**: Added `save_report` and a resource that lists documents. Verbose mode + trace file logging.
* **AI-Assisted Eng.**: Decision log and architecture review.

---

## ⏱️ SEGMENT 4: What You Learned & Security (3:30 - 4:30)
**Goal**: Explain MCP and CrewAI, the prompt injection security risk, and references.
**Visuals**: Open [data/docs/malicious_doc.txt](file:///Users/mihir/Programming/Projects_Local/Week-14Project/data/docs/malicious_doc.txt) in the IDE. Then switch to the terminal and run `pytest tests/test_tools.py -v`.

### 🎬 Action Cues:
1. Show the contents of [malicious_doc.txt](file:///Users/mihir/Programming/Projects_Local/Week-14Project/data/docs/malicious_doc.txt) in your editor.
2. Run unit tests in terminal to show 28 tests passing.

### 🎙️ Word-for-Word Speaking Script:
> *"From this project, I learned that MCP serves as a standard adapter for LLMs, allowing tools to be defined once and reused by any client. CrewAI allows us to orchestrate sequential role-playing agents to divide concerns.*
>
> *The biggest security risk I took seriously is prompt injection through document content. An attacker could place instructions inside a support document to hijack the crew. We simulated this in `malicious_doc.txt`.*
>
> *We mitigate this in three ways: First, the tools do not execute text; they return plain JSON. Second, agent backstories have overriding rules that lock their output formats. Third, the `save_report` tool uses path traversal checks to ensure files are written strictly inside the outputs folder.*
>
> *Running the test suite, you can see all unit and prompt injection tests pass successfully. The resources I used most were the CrewAI MCP documentation and the FastMCP tutorials."*

**💡 Rubric Mapping covered in this segment**:
* **Stretch Feature A**: Full Prompt Injection Test suite (3 unit tests + E2E test).
* **Core Hardening**: Security unit tests verifying path traversal and input types.

---

## ⏱️ SEGMENT 5: What is Next & Observability (4:30 - 5:00)
**Goal**: Explain what is next and highlight the observability stretch feature.
**Visuals**: Open an observability report under `outputs/run_report_*.md`. Show your facecam for final remarks.

### 🎬 Action Cues:
1. Open one of the generated run reports in the editor. Point to the "Total wall time" and "Tool Calls by Type" tables.
2. Look at the camera for the wrap-up.

### 🎙️ Word-for-Word Speaking Script:
> *"Before letting this touch real company data, I would implement:
> 1. Authenticated HTTP/SSE transport with API keys and rate limits.
> 2. A proper database in place of the flat CSV.
> 3. A Fact-Checker agent to cross-verify the Writer's claims against raw tool outputs.
> 
> *We also built structured observability—Option D. This run report automatically logs timings, tool counts, and token usage, giving us full visibility.*
>
> *Thank you for your time!"*

**💡 Rubric Mapping covered in this segment**:
* **Stretch Feature D**: Observability traces (JSONL) and automatically generated markdown run reports.
