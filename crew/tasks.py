"""Definition of CrewAI tasks for the agents to execute."""

from crewai import Task

def build_research_task(agent, question: str) -> Task:
    """Answer this question using only tool results: {question}
    Call search_documents to find relevant document snippets.
    Call read_record if the question mentions a specific order ID.
    IMPORTANT: If the question mentions an order ID, you MUST call read_record with that ID and include the order details (customer name, item, quantity, status, date) in the final evidence list with the source set to the order ID.
    Return a structured evidence list: each item must have source (doc_id or record_id)
    and excerpt. If nothing found, return the string 'no evidence found'."""
    
    import re
    order_id_match = re.search(r"ORD-\d+", question, re.IGNORECASE)
    
    if order_id_match:
        order_id = order_id_match.group(0).upper()
        description = (
            f"Answer this question using only tool results: {question}\n"
            f"IMPORTANT: The question mentions order ID {order_id}. You MUST call the 'read_record' tool with argument id='{order_id}' to retrieve the order details.\n"
            "Do NOT call search_documents to find the order details. Only call search_documents if the question also asks about store policies or shipping rules.\n"
            f"Your final output MUST be a JSON array of evidence objects. The first object MUST have the 'source' set to '{order_id}' and 'excerpt' set to a string containing the order details (customer, item, qty, status, date).\n"
            "Format the output strictly as a JSON array of objects, like: [{\"source\": \"doc_id_or_order_id\", \"excerpt\": \"text\"}]. "
            "Do NOT duplicate keys or output nested objects. If nothing found, return the string 'no evidence found'."
        )
    else:
        description = (
            f"Answer this question using only tool results: {question}\n"
            "Call search_documents to find relevant document snippets.\n"
            "CRITICAL RULES FOR SOURCES:\n"
            "1. For any search_documents results, the 'source' must be the specific 'doc_id' returned by the tool (e.g., 'return_policy', 'support_ticket_002'). Do NOT use 'search_documents' as a source.\n"
            "Return a structured evidence list: each item must have 'source' (doc_id) and 'excerpt'. "
            "Format the output strictly as a JSON array of objects, like: [{\"source\": \"id\", \"excerpt\": \"text\"}]. "
            "Do NOT duplicate keys or output nested objects. If nothing found, return the string 'no evidence found'."
        )
    
    research_tools = [t for t in agent.tools if t.name in ["search_documents", "read_record"]] if hasattr(agent, 'tools') and agent.tools else []
    
    return Task(
        description=description,
        expected_output="A JSON array of evidence dicts [{\"source\": \"doc_id_or_order_id\", \"excerpt\": \"text\"}] or 'no evidence found'",
        agent=agent,
        tools=research_tools
    )

def build_write_task(agent, question: str, context_tasks: list) -> Task:
    """Write a concise business report answering: {question}
    Use only the evidence provided. Rules:
    (1) Every factual sentence must cite its source as (Source: <id>).
    (2) If evidence is insufficient, state what is unknown.
    (3) End with a Sources section.
    (4) Call save_report to save the report to disk."""
    
    description = (
        f"Write a concise business report answering: {question}\n"
        "Use only the evidence provided. Rules:\n"
        "(1) Every factual sentence must cite its source as (Source: <id>). Do NOT map source IDs to numbers or footnotes (like '1'). You must use the exact source ID string directly, e.g. (Source: return_policy) or (Source: ORD-007).\n"
        "(2) If evidence is insufficient, state what is unknown.\n"
        "(3) End with a Sources section listing each unique source ID at the end.\n"
        "(4) Call save_report to save the report to disk."
    )
    
    save_report_tools = [t for t in agent.tools if t.name == "save_report"] if hasattr(agent, 'tools') and agent.tools else []
    
    return Task(
        description=description,
        expected_output="A markdown report with inline citations using exact source IDs (e.g. (Source: ORD-007)), a Sources section listing unique IDs, and the file path returned by save_report.",
        agent=agent,
        context=context_tasks,
        tools=save_report_tools
    )

