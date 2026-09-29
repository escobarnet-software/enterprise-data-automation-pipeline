"""Orchestrator: ingestion → AI → transform → storage."""
import logging
from src.ingestion.base import IngestedDocument
from src.ai.groq_client import get_extractor
from src.transform.cleaner import clean_text, sanitize_record, coerce_types
from src.transform.validators import validate_record
from src.storage.repository import DocumentRepository

log = logging.getLogger(__name__)


class Pipeline:
    def __init__(self, session, groq_api_key: str = "", groq_model: str = "llama-3.3-70b-versatile"):
        self.repo = DocumentRepository(session)
        self.extractor = get_extractor(groq_api_key, groq_model)

    def run(self, doc: IngestedDocument) -> dict:
        content = clean_text(doc.content)
        if not content:
            raise ValueError("Empty document content.")
        result = self.extractor.process(content, source_type=doc.source_type, source_name=doc.source_name)
        dtype = result["classification"].get("document_type", "unknown")
        record = coerce_types(sanitize_record(result.get("extracted", {})))
        validate_record(record, dtype)
        saved, created = self.repo.save(content_hash=doc.content_hash, document_type=dtype,
                                        source_type=doc.source_type, source_name=doc.source_name,
                                        data={**record, "_classification": result["classification"]})
        log.info("Processed %s → %s (created=%s)", doc.source_name, dtype, created)
        return {"id": saved.id, "created": created, "document_type": dtype,
                "classification": result["classification"], "data": record}
