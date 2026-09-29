"""Smoke tests (offline, rule-based extractor)."""
from src.ingestion.base import IngestedDocument
from src.storage.models import Base, get_engine, get_session
from src.pipeline import Pipeline
from src.transform.cleaner import clean_text
from src.transform.validators import validate_record, ValidationError
import pytest


def make_pipe():
    engine = get_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Pipeline(get_session(engine))


def test_invoice_end_to_end():
    pipe = make_pipe()
    doc = IngestedDocument(
        content="INVOICE #INV-1 Grand Total: 100.00 USD 2026-09-28",
        source_type="text", source_name="test")
    out = pipe.run(doc)
    assert out["document_type"] == "invoice"
    assert out["created"] is True
    out2 = pipe.run(doc)
    assert out2["created"] is False


def test_clean_and_validate():
    assert clean_text("  hello   world  ") == "hello world"
    with pytest.raises(ValidationError):
        validate_record({}, "invoice")
