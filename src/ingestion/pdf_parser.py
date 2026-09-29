"""PDF text extraction (pypdf with pdfplumber fallback)."""
from pathlib import Path
from .base import IngestedDocument


def parse_pdf(path: str | Path) -> IngestedDocument:
    path = Path(path)
    text = ""
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        text = "\n".join((p.extract_text() or "") for p in reader.pages)
    except Exception:
        text = ""
    if not text.strip():
        try:
            import pdfplumber
            with pdfplumber.open(str(path)) as pdf:
                text = "\n".join((p.extract_text() or "") for p in pdf.pages)
        except Exception as e:
            raise ValueError(f"Could not extract text from PDF {path}: {e}")
    if not text.strip():
        raise ValueError(f"No extractable text found in PDF: {path}")
    return IngestedDocument(content=text.strip(), source_type="pdf",
                            source_name=path.name, metadata={"pages": "unknown"})
