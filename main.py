"""CLI entrypoint: process a file or run the API server."""
import argparse
from pathlib import Path
from config.settings import get_settings
from src.ingestion.base import IngestedDocument, detect_source_type
from src.storage.models import Base, get_engine, get_session
from src.pipeline import Pipeline
from src.utils.logging import setup_logging


def process_file(path: str):
    settings = get_settings()
    setup_logging(settings.log_level)
    engine = get_engine(settings.database_url)
    Base.metadata.create_all(engine)
    session = get_session(engine)
    pipe = Pipeline(session, settings.groq_api_key, settings.groq_model)
    p = Path(path)
    stype = detect_source_type(p.name)
    if stype == "pdf":
        from src.ingestion.pdf_parser import parse_pdf
        doc = parse_pdf(p)
    elif stype == "csv":
        from src.ingestion.csv_parser import parse_csv
        doc = parse_csv(p)
    elif stype == "email":
        from src.ingestion.email_parser import parse_email_raw
        doc = parse_email_raw(p.read_text(encoding="utf-8", errors="replace"), p.name)
    else:
        doc = IngestedDocument(content=p.read_text(encoding="utf-8", errors="replace"),
                               source_type="text", source_name=p.name)
    import json
    print(json.dumps(pipe.run(doc), indent=2, default=str))


def main():
    ap = argparse.ArgumentParser(description="Enterprise Data Automation Pipeline")
    sub = ap.add_subparsers(dest="cmd", required=True)
    pf = sub.add_parser("process", help="Process a single file")
    pf.add_argument("path")
    sv = sub.add_parser("serve", help="Run the API server")
    args = ap.parse_args()
    if args.cmd == "process":
        process_file(args.path)
    elif args.cmd == "serve":
        import uvicorn
        s = get_settings()
        uvicorn.run("src.api:app", host=s.api_host, port=s.api_port, reload=False)


if __name__ == "__main__":
    main()
