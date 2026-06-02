"""Crew definition setting up agents, tasks, and flow control for execution."""

import sys
import os
import time
from pathlib import Path
from dotenv import load_dotenv
from mcp import StdioServerParameters
from crewai_tools import MCPServerAdapter
from crewai import Crew, Process, Agent
from crewai.tools import BaseTool
from pydantic import Field
from typing import Any
import inspect

from crew.agents import build_researcher, build_writer
from crew.tasks import build_research_task, build_write_task

load_dotenv()

class TeeStream:
    """Stream wrapper that writes to both the original stream (e.g. stdout) and a log file."""
    def __init__(self, original_stream, log_file):
        self.original_stream = original_stream
        self.log_file = log_file

    def write(self, data):
        self.original_stream.write(data)
        try:
            self.log_file.write(data)
            self.log_file.flush()
        except ValueError:
            pass

    def flush(self):
        self.original_stream.flush()
        try:
            self.log_file.flush()
        except ValueError:
            pass

class LoggedTool(BaseTool):
    """Pydantic v2 compatible custom tool wrapper to intercept tool execution and log detailed outputs."""
    orig: Any = Field(description="Original tool instance")
    trace_file_path: str = Field(description="Path to log file")

    def _run(self, *args: Any, **kwargs: Any) -> Any:
        # Determine the agent calling the tool via stack inspection
        agent_name = "Unknown Agent"
        # Method 1: Walk stack frames looking for an Agent instance
        for frame_info in inspect.stack():
            frame = frame_info.frame
            if 'self' in frame.f_locals:
                obj = frame.f_locals['self']
                if isinstance(obj, Agent):
                    agent_name = obj.role or obj.name
                    break
            # Also check for agent references in local variables
            for var_name, var_val in frame.f_locals.items():
                if isinstance(var_val, Agent):
                    agent_name = var_val.role or var_val.name
                    break
            if agent_name != "Unknown Agent":
                break
        # Method 2: Fallback to thread name (CrewAI may set it)
        if agent_name == "Unknown Agent":
            import threading
            thread_name = threading.current_thread().name
            if thread_name not in ("MainThread", "Thread-1"):
                agent_name = thread_name

        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        tool_name = self.name
        
        # Serialize the inputs to string safely
        input_str = f"args={args}, kwargs={kwargs}"

        try:
            output = self.orig.run(*args, **kwargs)
            # Log after successful execution
            log_msg = f"[{timestamp}] Agent: {agent_name} | Tool: {tool_name} | Input: {input_str} | Output: {output}\n"
            with open(self.trace_file_path, "a", encoding="utf-8") as f:
                f.write(log_msg)
            return output
        except Exception as e:
            # Log failure
            log_msg_err = f"[{timestamp}] Agent: {agent_name} | Tool: {tool_name} | Input: {input_str} | Error: {str(e)}\n"
            with open(self.trace_file_path, "a", encoding="utf-8") as f:
                f.write(log_msg_err)
            raise e

def build_and_run(question: str) -> str:
    """Build the MCP tools connection, compile the crew and tasks, run the crew, log trace data, and return results."""
    # 1. Load env vars
    load_dotenv()
    
    traces_dir_str = os.getenv("TRACES_DIR", "./traces")
    traces_dir = Path(traces_dir_str)
    traces_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = int(time.time())
    trace_file_path = traces_dir / f"run_{timestamp}.log"
    
    # Write start message to log file
    with open(trace_file_path, "w", encoding="utf-8") as f:
        f.write(f"--- Crew Run Start: {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")
        f.write(f"Question: {question}\n\n")

    # 2. Build StdioServerParameters pointing to server/main.py
    # Use sys.executable to run inside the same python environment
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["server/main.py"]
    )

    # 3. Connect to local MCP server via MCPServerAdapter
    with MCPServerAdapter(server_params) as mcp_tools:
        # Wrap each tool with custom logger
        wrapped_tools = []
        for tool in mcp_tools:
            wrapped_tools.append(LoggedTool(
                name=tool.name,
                description=tool.description,
                orig=tool,
                trace_file_path=str(trace_file_path),
                args_schema=tool.args_schema
            ))

        # 4. Build agents passing mcp_tools
        researcher = build_researcher(wrapped_tools)
        writer = build_writer(wrapped_tools)

        # 5. Build tasks
        research_task = build_research_task(researcher, question)
        write_task = build_write_task(writer, question, [research_task])

        # 6. Instantiate Crew with Process.sequential and verbose=True
        crew_obj = Crew(
            agents=[researcher, writer],
            tasks=[research_task, write_task],
            process=Process.sequential,
            verbose=True
        )

        # 7. Setup trace logging (capture standard output to both console and trace log)
        original_stdout = sys.stdout
        original_stderr = sys.stderr

        try:
            with open(trace_file_path, "a", encoding="utf-8") as f:
                sys.stdout = TeeStream(original_stdout, f)
                sys.stderr = TeeStream(original_stderr, f)

                # 8. Kickoff crew execution
                result = crew_obj.kickoff(inputs={"question": question})
                
                # Close the run log marker
                f.write(f"\n--- Crew Run Completed: {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")
                
                return str(result)
        finally:
            # Make sure stdout/stderr are restored even if execution fails
            sys.stdout = original_stdout
            sys.stderr = original_stderr
