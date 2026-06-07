"""Crew definition setting up agents, tasks, and flow control for execution."""

import sys
import os
import json
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
    """Pydantic v2 compatible custom tool wrapper that logs structured JSON
    trace entries for every tool call (Option D stretch feature)."""
    orig: Any = Field(description="Original tool instance")
    trace_file_path: str = Field(description="Path to the text log file")
    json_trace_path: str = Field(description="Path to the structured JSON trace file")

    def _run(self, *args: Any, **kwargs: Any) -> Any:
        # Determine the agent calling the tool via stack inspection
        agent_name = "Unknown Agent"
        for frame_info in inspect.stack():
            frame = frame_info.frame
            if 'self' in frame.f_locals:
                obj = frame.f_locals['self']
                if isinstance(obj, Agent):
                    agent_name = obj.role or obj.name
                    break
            for var_name, var_val in frame.f_locals.items():
                if isinstance(var_val, Agent):
                    agent_name = var_val.role or var_val.name
                    break
            if agent_name != "Unknown Agent":
                break
        # Fallback to thread name
        if agent_name == "Unknown Agent":
            import threading
            thread_name = threading.current_thread().name
            if thread_name not in ("MainThread", "Thread-1"):
                agent_name = thread_name

        timestamp_str = time.strftime("%Y-%m-%d %H:%M:%S")
        tool_name = self.name
        input_str = f"args={args}, kwargs={kwargs}"

        # Estimate token count (rough: ~4 chars per token)
        input_token_est = len(input_str) // 4

        start_time = time.time()
        try:
            output = self.orig.run(*args, **kwargs)
            duration_ms = int((time.time() - start_time) * 1000)
            output_str = str(output)
            output_token_est = len(output_str) // 4

            # Write human-readable log
            log_msg = f"[{timestamp_str}] Agent: {agent_name} | Tool: {tool_name} | Input: {input_str} | Output: {output} | Duration: {duration_ms}ms\n"
            with open(self.trace_file_path, "a", encoding="utf-8") as f:
                f.write(log_msg)

            # Write structured JSON trace entry
            trace_entry = {
                "timestamp": timestamp_str,
                "agent": agent_name,
                "tool_name": tool_name,
                "input": input_str,
                "output": output_str[:2000],  # Truncate very long outputs
                "duration_ms": duration_ms,
                "token_estimate": input_token_est + output_token_est,
                "status": "success"
            }
            with open(self.json_trace_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(trace_entry) + "\n")

            return output
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)

            # Write human-readable log
            log_msg_err = f"[{timestamp_str}] Agent: {agent_name} | Tool: {tool_name} | Input: {input_str} | Error: {str(e)} | Duration: {duration_ms}ms\n"
            with open(self.trace_file_path, "a", encoding="utf-8") as f:
                f.write(log_msg_err)

            # Write structured JSON trace entry
            trace_entry = {
                "timestamp": timestamp_str,
                "agent": agent_name,
                "tool_name": tool_name,
                "input": input_str,
                "output": None,
                "error": str(e),
                "duration_ms": duration_ms,
                "token_estimate": input_token_est,
                "status": "error"
            }
            with open(self.json_trace_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(trace_entry) + "\n")

            raise e


def _generate_run_report(
    question: str,
    json_trace_path: Path,
    outputs_dir: Path,
    wall_time_s: float,
    result: str
) -> str:
    """Generate a structured run_report.md from the JSON trace data (Option D)."""
    # Parse JSON trace entries
    trace_entries = []
    if json_trace_path.is_file():
        for line in json_trace_path.read_text(encoding="utf-8").strip().splitlines():
            try:
                trace_entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    # Count tool calls by type
    tool_counts: dict[str, int] = {}
    total_tokens = 0
    slowest_call = {"tool_name": "N/A", "duration_ms": 0, "agent": "N/A"}

    for entry in trace_entries:
        name = entry.get("tool_name", "unknown")
        tool_counts[name] = tool_counts.get(name, 0) + 1
        total_tokens += entry.get("token_estimate", 0)
        if entry.get("duration_ms", 0) > slowest_call["duration_ms"]:
            slowest_call = {
                "tool_name": name,
                "duration_ms": entry["duration_ms"],
                "agent": entry.get("agent", "Unknown")
            }

    # Build report
    lines = [
        "# Run Report",
        "",
        f"**Question**: {question}",
        f"**Timestamp**: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Final Answer",
        "",
        "\n".join(f"> {line}" if line.strip() else ">" for line in result.splitlines()),
        "",
        "## Summary",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total wall time | {wall_time_s:.1f}s |",
        f"| Total tool calls | {len(trace_entries)} |",
        f"| Estimated tokens | {total_tokens} |",
        f"| Slowest tool call | {slowest_call['tool_name']} ({slowest_call['duration_ms']}ms by {slowest_call['agent']}) |",
        "",
        "## Tool Calls by Type",
        "",
        "| Tool | Count |",
        "|------|-------|",
    ]
    for tool_name, count in sorted(tool_counts.items()):
        lines.append(f"| {tool_name} | {count} |")

    lines.extend([
        "",
        "## Trace Details",
        "",
        "| # | Timestamp | Agent | Tool | Duration | Tokens | Status |",
        "|---|-----------|-------|------|----------|--------|--------|",
    ])
    for i, entry in enumerate(trace_entries, 1):
        lines.append(
            f"| {i} | {entry.get('timestamp', '')} | {entry.get('agent', '')} "
            f"| {entry.get('tool_name', '')} | {entry.get('duration_ms', 0)}ms "
            f"| {entry.get('token_estimate', 0)} | {entry.get('status', '')} |"
        )

    lines.append("")

    report_content = "\n".join(lines)

    # Save to outputs/
    report_path = outputs_dir / f"run_report_{int(time.time())}.md"
    report_path.write_text(report_content, encoding="utf-8")

    return str(report_path)


def build_and_run(question: str) -> str:
    """Build the MCP tools connection, compile the crew and tasks, run the crew, log trace data, and return results."""
    # 1. Load env vars
    load_dotenv()

    traces_dir_str = os.getenv("TRACES_DIR", "./traces")
    traces_dir = Path(traces_dir_str)
    traces_dir.mkdir(parents=True, exist_ok=True)

    outputs_dir_str = os.getenv("OUTPUTS_DIR", "./outputs")
    outputs_dir = Path(outputs_dir_str).resolve()
    outputs_dir.mkdir(parents=True, exist_ok=True)

    run_timestamp = int(time.time())
    trace_file_path = traces_dir / f"run_{run_timestamp}.log"
    json_trace_path = traces_dir / f"run_{run_timestamp}.jsonl"

    # Write start message to log file
    with open(trace_file_path, "w", encoding="utf-8") as f:
        f.write(f"--- Crew Run Start: {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")
        f.write(f"Question: {question}\n\n")

    # Initialize empty JSON trace file
    json_trace_path.touch()

    wall_start = time.time()

    # 2. Build StdioServerParameters pointing to server/main.py
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["server/main.py"]
    )

    # 3. Connect to local MCP server via MCPServerAdapter
    with MCPServerAdapter(server_params) as mcp_tools:
        # Wrap each tool with structured logger
        wrapped_tools = []
        for tool in mcp_tools:
            wrapped_tools.append(LoggedTool(
                name=tool.name,
                description=tool.description,
                orig=tool,
                trace_file_path=str(trace_file_path),
                json_trace_path=str(json_trace_path),
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

                result_str = str(result)
        finally:
            # Make sure stdout/stderr are restored even if execution fails
            sys.stdout = original_stdout
            sys.stderr = original_stderr

    # 9. Generate structured run report (Option D)
    wall_time = time.time() - wall_start
    report_path = _generate_run_report(
        question=question,
        json_trace_path=json_trace_path,
        outputs_dir=outputs_dir,
        wall_time_s=wall_time,
        result=result_str
    )
    print(f"\n[Observability] Run report saved to: {report_path}")

    return result_str
