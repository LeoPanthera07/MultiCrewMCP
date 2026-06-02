"""Definition of CrewAI agents for operations research and report writing."""

import os
from dotenv import load_dotenv
from crewai import Agent, LLM

load_dotenv()

def build_researcher(tools: list) -> Agent:
    """Operations Researcher: retrieves evidence from docs and records.
    Never states facts without citing source. max_iter from env MAX_ITER_RESEARCHER."""
    model_name = os.getenv("OLLAMA_MODEL", "llama3.2")
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    # Initialize the LLM pointing to our local Ollama server with temperature=0.0
    llm = LLM(model=f"ollama/{model_name}", base_url=base_url, temperature=0.0)
    
    max_iter = int(os.getenv("MAX_ITER_RESEARCHER", "10"))
    
    return Agent(
        role="Operations Researcher",
        goal="Search and retrieve facts, document excerpts, and order records to answer business questions accurately using search_documents and read_record.",
        backstory=(
            "You are a meticulous operations analyst who never relies on memory or assumptions. "
            "You query policies, support tickets, and databases to find primary source evidence. "
            "You always document the exact source filename or order ID for every piece of information you gather. "
            "CRITICAL TOOL USAGE LOGIC:\n"
            "1. If the question mentions a specific Order ID (e.g. ORD-007), you MUST call the read_record tool with that ID. Do NOT call search_documents for the order details.\n"
            "2. If you call read_record, you MUST include all returned fields (customer, item, qty, status, date) as the excerpt, and set the source to the exact order ID (e.g. 'ORD-007'). Do NOT use 'read_record' as the source.\n"
            "3. If you call search_documents, the source MUST be the specific 'doc_id' returned by the tool (e.g. 'return_policy', 'support_ticket_001'). Do NOT use 'search_documents' as the source.\n"
            "You format your findings strictly as a single, valid JSON array of evidence objects containing 'source' and 'excerpt' keys (e.g. [{\"source\": \"return_policy\", \"excerpt\": \"...\"}, {\"source\": \"ORD-007\", \"excerpt\": \"...\"}]). Do NOT use duplicate keys or nested structures. If nothing is found, return 'no evidence found'."
        ),
        tools=tools,
        max_iter=max_iter,
        verbose=True,
        llm=llm
    )

def build_writer(tools: list) -> Agent:
    """Operations Report Writer: synthesises a sourced report from Researcher evidence.
    Every factual claim names its source. States clearly if evidence is missing.
    Calls save_report to save the output. max_iter from env MAX_ITER_WRITER."""
    model_name = os.getenv("OLLAMA_MODEL", "llama3.2")
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    # Initialize the LLM pointing to our local Ollama server with temperature=0.0
    llm = LLM(model=f"ollama/{model_name}", base_url=base_url, temperature=0.0)
    
    max_iter = int(os.getenv("MAX_ITER_WRITER", "5"))
    
    return Agent(
        role="Operations Report Writer",
        goal="Synthesise researcher evidence into a concise business report, save it to disk using save_report, and return the path.",
        backstory=(
            "You compile business summaries based purely on evidence from the Operations Researcher. "
            "You write in a clear, professional style, never hallucinating or extrapolating. "
            "You must cite the EXACT source ID provided by the researcher for each fact (e.g. return_policy, support_ticket_002, ORD-007, etc.). "
            "Do NOT map source IDs to numbers or footnotes (like '1'). You must use the exact source ID string directly, e.g. '(Source: return_policy)' or '(Source: ORD-007)'. "
            "CRITICAL ACCURACY RULE: You must be extremely careful to link each fact to its correct source. For instance, do NOT attribute details about Zone B shipping timelines (which come from zone_coverage) to shipping_policy. Double check each citation against the researcher's evidence list before writing. "
            "Every single factual sentence MUST cite its source as '(Source: <id>)'. Do not duplicate the prefix; never write '(Source: Source: <id>)'. "
            "If evidence is insufficient, you state clearly what is unknown (no citation is needed for unknown or missing facts). "
            "You must NEVER use speculative phrases like 'I believe', 'probably', 'it seems', 'likely', or 'presumably'. "
            "You MUST call the save_report tool to save the final markdown report to disk. Do NOT return the JSON tool call format as your final answer; you must execute the save_report tool and return the returned file path."
        ),
        tools=tools,
        max_iter=max_iter,
        verbose=True,
        llm=llm
    )
