"""FastAPI service: upload files, webhooks, query records."""
from fastapi import FastAPI, UploadFile, File, Depends, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from config.settings import get_settings
from src.ingestion.base import IngestedDocument, detect_source_type
from src.ingestion.csv_parser import parse_csv
from src.ingestion.email_parser import parse_email_dict
from src.ingestion.webhook import normalize_webhook_payload
from src.storage.models import Base, get_engine, get_session
from src.pipeline import Pipeline
from src.utils.logging import setup_logging
import tempfile, os

settings = get_settings()
setup_logging(settings.log_level)
engine = get_engine(settings.database_url)
Base.metadata.create_all(engine)

app = FastAPI(title="Enterprise Data Automation Pipeline", version="1.0.0",
              description="Escobar NET — unstructured data → structured DB records.")


@app.exception_handler(Exception)
async def unhandled_handler(request: Request, exc: Exception):
    from src.transform.validators import ValidationError
    if isinstance(exc, ValidationError):
        return JSONResponse(422, {"detail": str(exc), "hint": "No total/amount found. Try the Groq AI extractor (set GROQ_API_KEY) or /ingest/text."})
    if isinstance(exc, HTTPException):
        return JSONResponse(exc.status_code, {"detail": exc.detail})
    import logging
    logging.getLogger("pipeline").exception("Unhandled error on %s", request.url.path)
    return JSONResponse(500, {"detail": f"{type(exc).__name__}: {exc}"})


def get_pipeline():
    session = get_session(engine)
    try:
        yield Pipeline(session, settings.groq_api_key, settings.groq_model)
    finally:
        session.close()


def check_key(x_api_key: str = Header(default="")):
    if x_api_key != settings.api_key:
        raise HTTPException(401, "Invalid API key")


class TextIn(BaseModel):
    content: str
    source_name: str = "api-text"
    source_type: str = "text"


@app.get("/health")
def health():
    return {"status": "ok", "service": "enterprise-data-pipeline"}


@app.post("/ingest/text", dependencies=[Depends(check_key)])
def ingest_text(body: TextIn, pipe: Pipeline = Depends(get_pipeline)):
    doc = IngestedDocument(content=body.content, source_type=body.source_type, source_name=body.source_name)
    return pipe.run(doc)


@app.post("/ingest/file", dependencies=[Depends(check_key)])
async def ingest_file(file: UploadFile = File(...), pipe: Pipeline = Depends(get_pipeline)):
    stype = detect_source_type(file.filename or "")
    raw = await file.read()
    if len(raw) > settings.max_file_mb * 1024 * 1024:
        raise HTTPException(413, "File too large")
    suffix = "." + (file.filename or "bin").split(".")[-1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(raw)
        tmp_path = tmp.name
    try:
        if stype == "csv":
            doc = parse_csv(tmp_path)
            doc.source_name = file.filename or doc.source_name
        elif stype == "pdf":
            from src.ingestion.pdf_parser import parse_pdf
            doc = parse_pdf(tmp_path)
            doc.source_name = file.filename or doc.source_name
        else:
            doc = IngestedDocument(content=raw.decode("utf-8", "replace"),
                                   source_type=stype, source_name=file.filename or "upload")
        return pipe.run(doc)
    finally:
        os.unlink(tmp_path)


@app.post("/ingest/email", dependencies=[Depends(check_key)])
def ingest_email(payload: dict, pipe: Pipeline = Depends(get_pipeline)):
    return pipe.run(parse_email_dict(payload))


@app.post("/webhook/{source}", dependencies=[Depends(check_key)])
def webhook(source: str, payload: dict, pipe: Pipeline = Depends(get_pipeline)):
    return pipe.run(normalize_webhook_payload(payload, source_name=f"webhook:{source}"))


@app.get("/records", dependencies=[Depends(check_key)])
def records(document_type: str | None = None, limit: int = 50, pipe: Pipeline = Depends(get_pipeline)):
    recs = pipe.repo.list(document_type, limit)
    return [{"id": r.id, "document_type": r.document_type, "source_name": r.source_name,
             "total": r.total, "currency": r.currency, "data": r.data} for r in recs]


@app.get("/stats", dependencies=[Depends(check_key)])
def stats(pipe: Pipeline = Depends(get_pipeline)):
    return pipe.repo.stats()
