"""Common ingestion models."""
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class IngestedDocument:
    content: str
    source_type: str  # pdf | csv | email | text | webhook | api
    source_name: str = "unknown"
    content_hash: str = ""
    metadata: dict = field(default_factory=dict)
    ingested_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self):
        if not self.content_hash:
            self.content_hash = hashlib.sha256(self.content.encode("utf-8")).hexdigest()


def detect_source_type(filename: str) -> str:
    name = filename.lower()
    if name.endswith(".pdf"):
        return "pdf"
    if name.endswith(".csv"):
        return "csv"
    if name.endswith((".eml", ".msg")):
        return "email"
    if name.endswith((".txt", ".md")):
        return "text"
    return "unknown"
