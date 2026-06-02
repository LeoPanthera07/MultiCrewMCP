"""MCP tool for compiling and formatting operational reports."""

import os
import re
import time
from pathlib import Path
from dotenv import load_dotenv
from server.utils.validators import require_non_empty_string

def save_report(title: str, content: str) -> str | dict:
    """Save a report to the outputs directory."""
    load_dotenv()

    # 1. Validate title and content
    title_error = require_non_empty_string(title, "title", 100)
    if title_error:
        return {"error": title_error}

    content_error = require_non_empty_string(content, "content", 50000)
    if content_error:
        return {"error": content_error}

    # Resolve outputs directory path safely
    outputs_dir_str = os.getenv("OUTPUTS_DIR", "./outputs")
    outputs_dir = Path(outputs_dir_str).resolve()

    # 2. Sanitise title to be file-safe
    sanitised_title = re.sub(r'[^a-zA-Z0-9_\-]', '_', title)

    # 3. Build path with timestamp
    timestamp = int(time.time())
    filename = f"report_{sanitised_title}_{timestamp}.md"
    
    # Secure resolution to absolute path
    report_path = (outputs_dir / filename).resolve()

    # Path traversal check: must resolve inside outputs_dir
    # In case outputs_dir or filename contains traversal sequences (like ..)
    if not report_path.is_relative_to(outputs_dir):
        return {"error": "Path traversal attempt detected"}

    # 4. Write content to file
    try:
        outputs_dir.mkdir(parents=True, exist_ok=True)
        report_path.write_text(content, encoding="utf-8")
    except Exception as e:
        return {"error": f"Failed to save report: {str(e)}"}

    # 5. Return the absolute file path as a string
    return str(report_path)
