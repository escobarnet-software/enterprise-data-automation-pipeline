"""Groq-powered extraction with deterministic rule-based fallback (works offline)."""
import json
import re
from .prompts import CLASSIFY_PROMPT, EXTRACT_PROMPT

SCHEMA_HINTS = {
    "invoice": '{"vendor": str, "invoice_number": str, "issue_date": "YYYY-MM-DD", "total": float, "currency": "USD", "line_items": [{"description": str, "qty": float, "unit_price": float}]}',
    "purchase_order": '{"buyer": str, "po_number": str, "items": [], "total": float, "delivery_date": "YYYY-MM-DD"}',
    "receipt": '{"merchant": str, "date": "YYYY-MM-DD", "total": float, "currency": str, "items": []}',
    "email": '{"sender": str, "subject": str, "body": str, "intent": str, "entities": {}}',
    "report": '{"title": str, "period": str, "metrics": {}, "summary": str}',
    "unknown": '{"summary": str, "key_facts": [], "entities": {}}',
}


class RuleBasedExtractor:
    """Heuristic extractor: no API key needed, used for tests / offline."""

    KEYWORDS = {"invoice": ["invoice", "factura", "invoice number", "total due", "orden de compra", "order"],
                "purchase_order": ["purchase order", "p.o.", "po number", "orden de compra", "purchase"],
                "receipt": ["receipt", "recibo", "paid", "change"],
                "email": ["from:", "subject:", "dear ", "best regards"]}

    MONEY = re.compile(r"(?:[$€£]\s?[\d.,]+|[\d.,]+\s?(?:USD|EUR|MXN|COP|GBP|PEN|CLP|ARS|dollars?|pesos?))", re.I)

    def _money_values(self, content: str) -> list:
        vals = []
        for m in self.MONEY.finditer(content):
            num = re.search(r"[\d][\d.,]*", m.group(0))
            if not num:
                continue
            s = num.group(0)
            try:
                if "," in s and "." in s:
                    s = s.replace(",", "") if s.rfind(".") > s.rfind(",") else s.replace(".", "").replace(",", ".")
                elif "," in s and "." not in s:
                    s = s.replace(",", ".") if len(s.split(",")[-1]) == 2 else s.replace(",", "")
                vals.append(float(s))
            except ValueError:
                continue
        return vals

    def classify(self, content: str, source_type: str = "text", source_name: str = "") -> dict:
        low = content.lower()
        scores = {k: sum(1 for kw in v if kw in low) for k, v in self.KEYWORDS.items()}
        best = max(scores, key=scores.get)
        if scores[best] == 0:
            best = "report" if len(content) > 500 else "unknown"
        return {"document_type": best, "confidence": 0.65 if scores.get(best, 0) else 0.3, "reason": "rule-based"}

    def extract(self, content: str, document_type: str) -> dict:
        data: dict = {"_document_type": document_type}
        m_from = re.search(r"^From:\s*(.+)$", content, re.M | re.I)
        if m_from:
            data["sender"] = m_from.group(1).strip()
        m_subj = re.search(r"^Subject:\s*(.+)$", content, re.M | re.I)
        if m_subj:
            data["subject"] = m_subj.group(1).strip()
        m_total = re.search(r"(?:total|amount due|grand total|monto total)\D{0,10}([\d,]+\.\d{2})", content, re.I)
        if m_total:
            data["total"] = float(m_total.group(1).replace(",", ""))
        else:
            money = self._money_values(content)
            if money:
                data["total"] = max(money)
                data["total_candidates"] = money[:10]
        m_cur = re.search(r"\b(USD|EUR|MXN|COP|GBP|PEN|CLP|ARS)\b", content)
        if m_cur:
            data["currency"] = m_cur.group(1)
        m_date = re.search(r"(\d{4}-\d{2}-\d{2})", content)
        if m_date:
            data["issue_date"] = m_date.group(1)
        m_inv = re.search(r"(?:invoice\s*(?:number|no\.?|#)?|factura)\D{0,10}([A-Z0-9\-/]+)", content, re.I)
        if m_inv:
            data["invoice_number"] = m_inv.group(1).strip()
        data["raw_excerpt"] = content[:500]
        return data

    def process(self, content: str, **kw) -> dict:
        cls = self.classify(content, kw.get("source_type", "text"))
        return {"classification": cls, "extracted": self.extract(content, cls["document_type"])}


class GroqExtractor:
    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile"):
        if not api_key:
            raise ValueError("GROQ_API_KEY is required for GroqExtractor")
        from groq import Groq
        self.client = Groq(api_key=api_key)
        self.model = model

    @staticmethod
    def _json(text: str) -> dict:
        m = re.search(r"\{.*\}", text, re.S)
        return json.loads(m.group(0) if m else text)

    def classify(self, content: str, source_type: str = "text", source_name: str = "") -> dict:
        resp = self.client.chat.completions.create(
            model=self.model, temperature=0,
            messages=[{"role": "user", "content": CLASSIFY_PROMPT.format(
                content=content[:12000], source_type=source_type, source_name=source_name)}])
        return self._json(resp.choices[0].message.content or "{}")

    def extract(self, content: str, document_type: str) -> dict:
        resp = self.client.chat.completions.create(
            model=self.model, temperature=0, response_format={"type": "json_object"},
            messages=[{"role": "user", "content": EXTRACT_PROMPT.format(
                content=content[:12000], document_type=document_type,
                schema_hint=SCHEMA_HINTS.get(document_type, SCHEMA_HINTS["unknown"]))}])
        return self._json(resp.choices[0].message.content or "{}")

    def process(self, content: str, **kw) -> dict:
        cls = self.classify(content, kw.get("source_type", "text"), kw.get("source_name", ""))
        dtype = cls.get("document_type", "unknown")
        return {"classification": cls, "extracted": self.extract(content, dtype)}


def get_extractor(api_key: str = "", model: str = "llama-3.3-70b-versatile"):
    if api_key:
        try:
            return GroqExtractor(api_key, model)
        except Exception:
            pass
    return RuleBasedExtractor()
