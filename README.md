# ⚙️ Enterprise Data Automation Pipeline

> **Engineered by Escobar NET** — B2B Automation · AI Integration · Backend Architecture
> *Transform unstructured data into actionable insights — instantly.*

Badges: Python 3.12 · FastAPI 0.115 · Groq LPU (llama-3.3-70b) · SQLAlchemy 2.0 · PostgreSQL 16 · Docker Ready · pytest passing

Arquitectura backend empresarial creada por **Escobar NET** que elimina la captura manual de datos: ingiere PDFs, emails, CSVs, APIs y webhooks, extrae JSON preciso con LLMs ultrarrapidos (Groq), normaliza/valida en Python y sincroniza de forma idempotente en SQL.

## Indice

1. Problema · 2. Caracteristicas · 3. Arquitectura y flujo · 4. Stack completo · 5. Estructura · 6. Instalacion · 7. Uso · 8. API · 9. Motor IA · 10. Datos · 11. Seguridad · 12. Tests · 13. Docker · 14. Env · 15. Roadmap · 16. Autor Escobar NET

## 1. El problema que resuelve

Las empresas pierden miles de horas transcribiendo facturas PDF a Excel, reenviando ordenes de compra por chat y normalizando CSVs a mano. Costo triple: horas-hombre, errores de tipeo, decisiones tardias. Objetivo Escobar NET: cero intervencion humana — Python + LLMs leen, clasifican y almacenan automaticamente, con validacion estricta, deduplicacion y trazabilidad total.

Finanzas: facturas PDF/recibos -> vendor, invoice_number, total, currency, line_items. Compras: ordenes por email -> buyer, po_number, items, delivery_date. SaaS: webhooks CRM, CSVs -> registros normalizados. Management: reportes -> title, period, metrics, summary.

## 2. Caracteristicas

- Ingesta multi-fuente: PDF (pypdf + pdfplumber fallback), CSV, email .eml/dicts, texto, webhooks → un objeto IngestedDocument.
- Motor IA Groq llama-3.3-70b-versatile en LPU + extractor heuristico offline (sin API key) para CI/tests.
- Transformacion: limpieza, sanitizacion, coercion de tipos (montos, ISO-4217, ISO-8601), 100% compatible SQL.
- Storage idempotente SHA-256: mismo documento jamas se duplica; validacion por tipo; logging.
- API FastAPI con API key, OpenAPI en /docs, limite 25 MB. Docker + Postgres 16 listos; SQLite en dev.


## 3. Arquitectura y flujo de datos

Etapa 1 INGESTION (src/ingestion/): pdf_parser (pypdf + pdfplumber), csv_parser (headers, conteo, preview), email_parser (stdlib email .eml y dicts), webhook.normalize (cualquier JSON). Todo produce IngestedDocument(content, source_type, source_name, content_hash SHA-256, metadata, ingested_at). detect_source_type mapea extension a pdf/csv/email/text.

Etapa 2 IA (src/ai/): GroqExtractor clasifica (CLASSIFY_PROMPT a invoice/purchase_order/receipt/email/report/unknown + confidence) y extrae (EXTRACT_PROMPT + schema hint a solo JSON, fechas ISO, numeros sin simbolos, monedas ISO, null si falta, nunca inventa). Sin GROQ_API_KEY entra RuleBasedExtractor (keywords + regex de totales/monedas/fechas/folios y From:/Subject:).

Etapa 3 TRANSFORM (src/transform/): clean_text (HTML entities, control chars, espacios), sanitize_record (claves a [a-z0-9_], strings max 2000, listas/dicts a JSON), coerce_types ("$1,250.50" a 1250.5, currency ISO-3), validate_record (invoice/receipt exigen total numerico >=0; si falla, ValidationError y nada sucio llega a BD).

## 4. Stack tecnologico completo

Python 3.12 (base + argparse CLI process/serve en main.py). FastAPI 0.115.6 + Uvicorn 0.34.0 standard (API REST, validacion, OpenAPI /docs, servidor ASGI en src/api.py). Pydantic 2.10.4 + pydantic-settings 2.7.0 (modelo TextIn; Settings desde .env en config/settings.py). Groq 0.11.0 con llama-3.3-70b-versatile en LPU (clasificacion + extraccion JSON; modelo cambiable con GROQ_MODEL). SQLAlchemy 2.0.36 + Alembic 1.14.0 (ORM DeclarativeBase, sesiones, migraciones futuras). SQLite dev / PostgreSQL 16 + psycopg2-binary prod. pypdf 5.1.0 + pdfplumber 0.11.4 (PDF con fallback). pandas 2.2.3 (ecosistema CSV). email-validator 2.2.0. python-multipart 0.0.20 (uploads). python-dotenv 1.0.1 (.env). structlog 24.4.0 + logging stdlib ("timestamp | level | name | msg"). tenacity 9.0.0 (reintentos). pyyaml 6.0.2 (schemas.yaml). pytest 8.3.4 + pytest-asyncio 0.24.0 + httpx 0.28.1 (tests offline + cliente HTTP). Docker + compose (despliegue reproducible API + Postgres).

## 5. Estructura del proyecto

## 6. Instalacion y configuracion

Requisitos: Windows/Linux/macOS + Python 3.12 + (opcional) clave Groq desde console.groq.com. Este repo ya trae .venv listo; si lo clonas de cero: python -m venv .venv, activar (.venv/Scripts/activate en Windows o source .venv/bin/activate), pip install -r requirements.txt, copiar .env.example a .env y editar GROQ_API_KEY, API_KEY (cambiarla!), DATABASE_URL=sqlite:///./pipeline.db en dev.

## 7. Guia de uso

A) Servidor: .\run.bat serve (o python main.py serve) → http://localhost:8000, docs en /docs (boton Try it out, header x-api-key = tu API_KEY). B) CLI: .\run.bat process examples/sample_invoice.txt (tambien .csv y .eml) imprime el JSON guardado {id, created, document_type, data}. C) SDK Python: get_engine + Base.metadata.create_all + get_session + Pipeline(session, key, model) + pipe.run(IngestedDocument(content=..., source_type="text", source_name="demo")). D) Ejemplos rapidos: en /docs prueba POST /ingest/text con {"content":"INVOICE #INV-0042 Grand Total: 1450.58 USD 2026-09-28"}; POST /ingest/file subiendo examples/sample.csv; POST /webhook/crm con {"text":"Nuevo lead Acme $5000 USD"}; GET /records?limit=10 y /stats.

## 8. Referencia API REST

GET /health (sin auth, {status:ok}). POST /ingest/text {content, source_name?, source_type?} (auth). POST /ingest/file multipart PDF/CSV/TXT max 25 MB (auth, 413 si excede). POST /ingest/email {from, subject, body} (auth). POST /webhook/{source} cualquier JSON (auth). GET /records?document_type=&limit=50 (auth). GET /stats {total_documents, by_type} (auth). Auth = header x-api-key; error → 401 {"detail":"Invalid API key"}. Respuesta ingesta: {id, created, document_type, classification{type, confidence}, data{...}}.

## 9. Motor de IA

Dos prompts en src/ai/prompts.py; SCHEMA_HINTS por tipo en groq_client.py. Con key: Groq (temperature 0, response_format json_object). Sin key: RuleBasedExtractor automatico (ideal CI). GROQ_MODEL permite abaratar (llama-3.1-8b-instant) o subir precision.

## 10. Modelo de datos

Tabla documents: id PK autoincremental; content_hash String(64) UNIQUE (SHA-256, clave idempotencia); document_type String(32) index; source_type/source_name; total Float + currency String(8) consultables; data JSON (payload + _classification); created_at UTC.

## 11. Seguridad y calidad

Validacion por tipo, sanitizacion (control chars, HTML, claves normalizadas, max 2000), auth x-api-key salvo /health, limite 25 MB, transacciones atomicas, trazabilidad hash+origen+timestamp, LOG_LEVEL configurable. Cambia API_KEY antes de exponer el servicio.

## 12. Testing

.\.venv\Scripts\python -m pytest tests -v (desde la carpeta, 2 passed): end-to-end factura→BD + idempotencia (created=false la 2a vez), todo offline con SQLite memoria + reglas, sin API key.

## 13. Docker

docker compose up --build → API :8000 + Postgres :5432. Prod: DATABASE_URL=postgresql+psycopg2://pipeline:pipeline@db:5432/pipeline_db. Dockerfile python:3.12-slim.

## 14. Variables de entorno

GROQ_API_KEY ("" = offline), GROQ_MODEL (llama-3.3-70b-versatile), DATABASE_URL (sqlite:///./pipeline.db), API_HOST 0.0.0.0, API_PORT 8000, API_KEY (cambiar!), LOG_LEVEL INFO, MAX_FILE_MB 25, WATCH_DIR ./inbox.

## 15. Roadmap Escobar NET

Watcher inbox/ con auto-ingesta, conectores Gmail/S3/GCS/IMAP, migraciones Alembic versionadas, cola Celery/Redis, metricas Prometheus + dashboard, export ERP/CRM (SAP, NetSuite, HubSpot), multi-tenant y RBAC.

## 16. Autor — Escobar NET

Disenado y construido por **Escobar NET** (B2B Automation · AI Integration · Backend Architecture). "Transform unstructured data into actionable insights — instantly." Uso libre educativo y comercial; mencion a Escobar NET bienvenida. Contacto/proyectos B2B: Escobar NET.


main.py (CLI), run.bat (launcher venv Windows), requirements.txt, Dockerfile, docker-compose.yml, .env.example. config/settings.py (Settings) + schemas.yaml (tipos y esquemas). src/api.py (endpoints), src/pipeline.py (orquestador). src/ingestion/: base, pdf_parser, csv_parser, email_parser, webhook. src/ai/: prompts.py, groq_client.py. src/transform/: cleaner.py, validators.py. src/storage/: models.py DocumentRecord, repository.py. src/utils/logging.py. examples/: sample_invoice.txt, sample_email.eml, sample.csv. tests/test_pipeline.py.


Etapa 4 STORAGE (src/storage/): DocumentRecord (SQLAlchemy) + DocumentRepository.save idempotente por content_hash (SELECT, INSERT, commit; IntegrityError retorna existente). list() y stats() para consulta. Pipeline.run() en src/pipeline.py encadena las 4 etapas y retorna {id, created, document_type, classification, data}; 2a ingesta igual da created=false.
