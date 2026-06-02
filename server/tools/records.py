"""MCP tool for querying and retrieving customer order records from the CSV."""

import os
import csv
from pathlib import Path
from dotenv import load_dotenv
from server.utils.validators import validate_record_id

def read_record(id: str) -> dict:
    """Retrieve an order record by its ID from the CSV file."""
    load_dotenv()

    # 1. Validate ID format
    validation_error = validate_record_id(id)
    if validation_error:
        return {"error": validation_error}

    data_dir = os.getenv("DATA_DIR", "./data")
    csv_path = Path(data_dir) / "records.csv"

    # 5. Handle missing file
    if not csv_path.is_file():
        return {"error": "records file not found"}

    # 2 & 3. Load CSV and search for record
    try:
        with open(csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            
            # Check for empty file or malformed header
            if reader.fieldnames is None or "id" not in reader.fieldnames:
                return {"error": "malformed CSV: missing 'id' column"}
                
            for row in reader:
                # Handle potentially missing or empty 'id' field in a row
                row_id = row.get("id")
                if row_id and row_id.upper() == id.upper():
                    return dict(row)
    except csv.Error as e:
        return {"error": f"malformed CSV file: {str(e)}"}
    except Exception as e:
        return {"error": f"failed to read records file: {str(e)}"}

    # 4. Return error if not found
    return {"error": "record not found", "id": id}
