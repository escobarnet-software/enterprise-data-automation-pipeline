"""CSV ingestion → normalized text + structured preview."""
from pathlib import Path
import csv
from .base import IngestedDocument


def parse_csv(path: str | Path, max_preview_rows: int = 50) -> IngestedDocument:
    path = Path(path)
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        headers = reader.fieldnames or []
    preview = rows[:max_preview_rows]
    lines = [f"CSV file: {path.name}", f"Columns: {', '.join(headers)}", f"Rows: {len(rows)}"]
    for r in preview:
        lines.append(" | ".join(f"{k}={v}" for k, v in r.items()))
    return IngestedDocument(content="\n".join(lines), source_type="csv",
                            source_name=path.name,
                            metadata={"headers": headers, "row_count": len(rows), "preview": preview})
