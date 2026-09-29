"""Data cleaning and sanitization."""
import re
import html

CONTROL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")


def clean_text(text: str) -> str:
    text = html.unescape(text or "")
    text = CONTROL.sub(" ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _clean_str(v: str, max_len: int = 2000) -> str:
    return clean_text(v)[:max_len]


def sanitize_record(record: dict) -> dict:
    clean: dict = {}
    for k, v in record.items():
        key = re.sub(r"[^a-zA-Z0-9_]", "_", str(k))[:64]
        if isinstance(v, str):
            clean[key] = _clean_str(v)
        elif isinstance(v, (list, dict)):
            import json
            clean[key] = _clean_str(json.dumps(v, ensure_ascii=False))
        elif v is None or isinstance(v, (int, float, bool)):
            clean[key] = v
        else:
            clean[key] = _clean_str(str(v))
    return clean


def coerce_types(record: dict) -> dict:
    out = dict(record)
    for k in ("total", "amount", "subtotal", "tax"):
        if k in out and isinstance(out[k], str):
            try:
                out[k] = float(out[k].replace(",", "").replace("$", "").strip())
            except ValueError:
                pass
    if "currency" in out and isinstance(out["currency"], str):
        out["currency"] = out["currency"].strip().upper()[:3]
    return out
