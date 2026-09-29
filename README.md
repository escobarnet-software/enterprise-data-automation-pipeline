# Enterprise Data Automation Pipeline

> **Engineered by Escobar NET** — B2B Automation · AI Integration · Backend Architecture
> *Transform unstructured data into actionable insights — instantly.*

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![Groq](https://img.shields.io/badge/LLM-Groq_LPU-F55036)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)
![Tests](https://img.shields.io/badge/Tests-pytest_passing-4BC51D)

An enterprise-grade Python backend architecture created by **Escobar NET** that eliminates manual data entry. It ingests PDFs, emails, CSVs, APIs and webhooks, extracts precise JSON schemas with ultra-fast LLMs (**Groq**), normalizes and validates every record in Python, and syncs it **idempotently** into SQL.

## Table of Contents

1. [The Problem](#1-the-problem-it-solves) · 2. [Features](#2-features) · 3. [Architecture & Flow](#3-architecture--data-flow) · 4. [Tech Stack](#4-complete-technology-stack) · 5. [Project Structure](#5-project-structure) · 6. [Installation](#6-installation--configuration) · 7. [Usage](#7-usage-guide) · 8. [API Reference](#8-rest-api-reference) · 9. [AI Engine](#9-ai-engine) · 10. [Data Model](#10-data-model) · 11. [Security](#11-security-validation--data-quality) · 12. [Testing](#12-testing) · 13. [Docker](#13-docker-deployment) · 14. [Env Vars](#14-environment-variables) · 15. [Roadmap](#15-roadmap) · 16. [Author](#16-author--escobar-net)

## 1. The Problem It Solves

Businesses lose thousands of hours every year to manual extraction: PDF invoices retyped into Excel, purchase orders forwarded over chat, CSV reports nobody normalizes. Triple cost: labor hours, typos, late decisions. Goal by Escobar NET: zero human touch — Python + LLMs read, classify and store unstructured text automatically, with strict validation, deduplication and full traceability.

Finance: PDF invoices/receipts -> vendor, invoice_number, total, currency, line_items. Procurement: email orders -> buyer, po_number, items, delivery_date. SaaS: CRM webhooks, CSVs -> normalized records. Management: reports -> title, period, metrics, summary.

## 2. Features

- Multi-source ingestion: PDF (pypdf + pdfplumber fallback), CSV, .eml/dict emails, free text, webhooks → one IngestedDocument object.
- Groq AI engine (llama-3.3-70b-versatile on LPU) + offline heuristic fallback (no API key) for CI/tests.
- Deterministic transformation: cleaning, sanitization, type coercion (amounts, ISO-4217, ISO-8601), 100% SQL-compatible.
- Idempotent SHA-256 storage: same document never duplicated; per-type validation; structured logging.
- Professional FastAPI REST API with API key, OpenAPI at /docs, 25 MB limit. Docker + PostgreSQL 16 ready; SQLite for dev.

## 3. Architecture & Data Flow

```text
PDF ──┐
CSV ──┼──▶ INGESTION ──▶ AI ENGINE ──▶ TRANSFORM ──▶ STORAGE ──▶ SQL
Email ┤     (parsers)     (Groq or        (clean +      (idempotent
Webhook┘                   rules)         validate)      save)
```

Stage 1 INGESTION (src/ingestion/): pdf_parser (pypdf + pdfplumber fallback), csv_parser (headers, row count, preview), email_parser (stdlib email for .eml + dicts with from/subject/body), webhook.normalize (any JSON). Everything produces IngestedDocument(content, source_type, source_name, content_hash SHA-256, metadata, ingested_at). detect_source_type maps extension to pdf/csv/email/text.

Stage 2 AI (src/ai/): GroqExtractor classifies (CLASSIFY_PROMPT → invoice/purchase_order/receipt/email/report/unknown + confidence) and extracts (EXTRACT_PROMPT + schema hint → JSON only, ISO dates, bare numbers, ISO currencies, null if missing, never hallucinates). Without GROQ_API_KEY, RuleBasedExtractor kicks in (keywords + regex for totals/currencies/dates/numbers and From:/Subject:).

Stage 3 TRANSFORM (src/transform/): clean_text (HTML entities, control chars, whitespace), sanitize_record (keys to [a-z0-9_], strings capped at 2000, lists/dicts to JSON), coerce_types ("$1,250.50" → 1250.5, currency to ISO-3), validate_record (invoice/receipt require numeric total ≥ 0; on failure, ValidationError — dirty data never reaches the DB).


## 4. Complete Technology Stack

Every dependency from `requirements.txt`, what it does, and where it lives in the codebase:

| Technology | Version | Role in this project | Used in |
|---|---|---|---|
| Python | 3.12 | Base language; argparse CLI (`process` / `serve`) | `main.py`, everything |
| FastAPI | 0.115.6 | REST API, request validation, auto OpenAPI docs | `src/api.py` |
| Uvicorn (standard) | 0.34.0 | ASGI server running the API | `main.py serve`, `Dockerfile` |
| Pydantic | 2.10.4 | Data models (`TextIn`) and response validation | `src/api.py` |
| pydantic-settings | 2.7.0 | Loads `Settings` from `.env` (keys, DB URL, ports) | `config/settings.py` |
| Groq SDK | 0.11.0 | Client for LPU-hosted LLMs, JSON-mode extraction | `src/ai/groq_client.py` |
| llama-3.3-70b-versatile | (model) | Classification + precise JSON extraction (ms latency); swappable via `GROQ_MODEL` | `src/ai/prompts.py` |
| SQLAlchemy | 2.0.36 | ORM (`DeclarativeBase`), engine, sessions, idempotent writes | `src/storage/` |
| Alembic | 1.14.0 | Versioned DB migrations (future schema evolution) | migrations (roadmap) |
| SQLite | stdlib | Zero-dependency dev database | default `DATABASE_URL` |
| PostgreSQL 16 + psycopg2-binary | 16 / 2.9.10 | Production database + driver | `docker-compose.yml` |
| pypdf | 5.1.0 | Primary PDF text extraction | `src/ingestion/pdf_parser.py` |
| pdfplumber | 0.11.4 | Fallback PDF extraction (scanned/complex layouts) | `src/ingestion/pdf_parser.py` |
| pandas | 2.2.3 | CSV ecosystem / analytics-ready frames | `src/ingestion/csv_parser.py` |
| email-validator | 2.2.0 | Email address validation | ingestion layer |
| python-multipart | 0.0.20 | Multipart file-upload handling | `POST /ingest/file` |
| python-dotenv | 1.0.1 | `.env` file loading | `config/settings.py` |
| structlog + stdlib logging | 24.4.0 | Structured logs (`timestamp \| level \| name \| msg`) | `src/utils/logging.py` |
| tenacity | 9.0.0 | Retries with backoff for flaky I/O / LLM calls | pipeline / clients |
| PyYAML | 6.0.2 | Parses `schemas.yaml` (document types + expected schemas) | `config/schemas.yaml` |

## 5. Project Structure

```text
enterprise-data-pipeline/
├── main.py               # CLI: process <file> | serve
├── run.bat               # Windows launcher (project .venv)
├── requirements.txt      # 20 pinned dependencies
├── Dockerfile            # python:3.12-slim API image
├── docker-compose.yml    # API + PostgreSQL 16
├── .env.example          # Safe template (no secrets)
├── config/
│   ├── settings.py       # pydantic Settings from .env
│   └── schemas.yaml      # Document types + expected schemas
├── src/
│   ├── api.py            # FastAPI endpoints
│   ├── pipeline.py       # Pipeline.run() orchestrator
│   ├── ingestion/        # base, pdf/csv/email parsers, webhook
│   ├── ai/               # prompts.py, groq_client.py
│   ├── transform/        # cleaner.py, validators.py
│   ├── storage/          # models.py (DocumentRecord), repository.py
│   └── utils/            # logging.py
├── examples/             # sample_invoice.txt, sample_email.eml, sample.csv
└── tests/                # test_pipeline.py (offline)
```

## 9. AI Engine

Two prompts in `src/ai/prompts.py`; per-type `SCHEMA_HINTS` in `groq_client.py`. With a key: Groq (temperature 0, `response_format: json_object`). Without a key: automatic `RuleBasedExtractor` (great for CI). `GROQ_MODEL` lets you trade cost vs. accuracy (e.g. `llama-3.1-8b-instant`).

## 10. Data Model

`documents` table: id (PK, autoincrement), content_hash String(64) UNIQUE (SHA-256, idempotency key), document_type String(32) indexed, source_type/source_name, total Float + currency String(8) queryable, data JSON (payload + _classification), created_at UTC.

## 11. Security, Validation & Data Quality

Per-type validation, sanitization (control chars, HTML, normalized keys, 2000-char cap), `x-api-key` auth except `/health`, 25 MB cap, atomic transactions, hash+origin+timestamp traceability, configurable `LOG_LEVEL`. Change `API_KEY` before exposing the service.

## 12. Testing

`.\.venv\Scripts\python -m pytest tests -v` from the folder (2 passed): end-to-end invoice→DB + idempotency (second run returns created=false), fully offline with in-memory SQLite + rules engine, no API key needed.

## 13. Docker Deployment

`docker compose up --build` → API :8000 + Postgres :5432. Production: `DATABASE_URL=postgresql+psycopg2://pipeline:pipeline@db:5432/pipeline_db`. `Dockerfile` uses `python:3.12-slim`.

## 14. Environment Variables

`GROQ_API_KEY` ("" = offline mode), `GROQ_MODEL` (llama-3.3-70b-versatile), `DATABASE_URL` (sqlite:///./pipeline.db), `API_HOST` 0.0.0.0, `API_PORT` 8000, `API_KEY` (change it!), `LOG_LEVEL` INFO, `MAX_FILE_MB` 25, `WATCH_DIR` ./inbox.

## 15. Roadmap

Inbox watcher with auto-ingest, Gmail/S3/GCS/IMAP connectors, versioned Alembic migrations, Celery/Redis queue, Prometheus metrics + dashboard, ERP/CRM export (SAP, NetSuite, HubSpot), multi-tenant + RBAC.

## 16. Author — Escobar NET

Designed, built and owned by **Escobar NET** (B2B Automation · AI Integration · Backend Architecture). *"Transform unstructured data into actionable insights — instantly."* © 2026 Escobar NET. All rights reserved.


## 6. Installation & Configuration

Requirements: Windows/Linux/macOS + Python 3.12 + (optional) a Groq key from console.groq.com. This repo ships with `.venv` ready; from a fresh clone: `python -m venv .venv`, activate (`.venv/Scripts/activate` on Windows, `source .venv/bin/activate` otherwise), `pip install -r requirements.txt`, copy `.env.example` to `.env` and set `GROQ_API_KEY`, `API_KEY` (change it!), `DATABASE_URL=sqlite:///./pipeline.db` for dev.

## 7. Usage Guide

A) Server: `.\run.bat serve` (or `python main.py serve`) → http://localhost:8000, interactive docs at `/docs` (Try it out button, `x-api-key` header = your API_KEY). B) CLI: `.\run.bat process examples/sample_invoice.txt` (also .csv and .eml) prints the saved JSON {id, created, document_type, data}. C) Python SDK: get_engine + Base.metadata.create_all + get_session + Pipeline(session, key, model) + pipe.run(IngestedDocument(content=..., source_type="text", source_name="demo")). D) Quick tries in /docs: POST /ingest/text with {"content":"INVOICE #INV-0042 Grand Total: 1450.58 USD 2026-09-28"}; POST /ingest/file uploading examples/sample.csv; POST /webhook/crm with {"text":"New lead Acme $5000 USD"}; GET /records?limit=10 and /stats.

## 8. REST API Reference

GET /health (no auth, {status:ok}). POST /ingest/text {content, source_name?, source_type?} (auth). POST /ingest/file multipart PDF/CSV/TXT up to 25 MB (auth, 413 if exceeded). POST /ingest/email {from, subject, body} (auth). POST /webhook/{source} any JSON (auth). GET /records?document_type=&limit=50 (auth). GET /stats {total_documents, by_type} (auth). Auth = x-api-key header; failure → 401 {"detail":"Invalid API key"}. Ingest response: {id, created, document_type, classification{type, confidence}, data{...}}.

| pytest + pytest-asyncio + httpx | 8.3.4 / 0.24.0 / 0.28.1 | Offline test suite + async + HTTP client | `tests/` |
| Docker + Compose | — | Reproducible deploy (API + Postgres) | `Dockerfile`, `docker-compose.yml` |

Stage 4 STORAGE (src/storage/): DocumentRecord (SQLAlchemy) + DocumentRepository.save idempotent on content_hash (SELECT → INSERT → commit; IntegrityError returns the existing row). list() and stats() for reads. Pipeline.run() in src/pipeline.py chains all 4 stages and returns {id, created, document_type, classification, data}; re-ingesting the same content returns created=false.

