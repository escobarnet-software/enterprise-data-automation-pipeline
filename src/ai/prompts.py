"""Prompt templates for classification and extraction."""
CLASSIFY_PROMPT = """You are a document classifier for an enterprise data pipeline.
Classify the document into exactly one of: invoice, purchase_order, receipt, email, report, unknown.
Respond with ONLY valid JSON: {{"document_type": "<type>", "confidence": 0.0-1.0, "reason": "<short>"}}.

Document (source={source_type}, name={source_name}):
\"\"\"
{content}
\"\"\""""

EXTRACT_PROMPT = """You are a precise data-extraction engine. Extract structured data from the document below.
Document type: {document_type}
Return ONLY valid JSON matching this schema hint: {schema_hint}
Rules: use ISO dates (YYYY-MM-DD), numbers without currency symbols, uppercase ISO currency codes.
If a field is missing, use null. Never invent values.

Document:
\"\"\"
{content}
\"\"\""""
