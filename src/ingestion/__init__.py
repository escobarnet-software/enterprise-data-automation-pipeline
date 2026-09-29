"""Ingestion layer: parse PDFs, CSVs, emails, raw text, webhooks."""
from .base import IngestedDocument, detect_source_type
from .pdf_parser import parse_pdf
from .csv_parser import parse_csv
from .email_parser import parse_email_raw, parse_email_dict
from .webhook import normalize_webhook_payload

__all__ = ["IngestedDocument", "detect_source_type", "parse_pdf", "parse_csv",
           "parse_email_raw", "parse_email_dict", "normalize_webhook_payload"]
