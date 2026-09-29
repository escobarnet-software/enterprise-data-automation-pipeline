"""Normalize webhook / API payloads into IngestedDocument."""
from .base import IngestedDocument


def normalize_webhook_payload(payload: dict, source_name: str = "webhook") -> IngestedDocument:
    text = payload.get("text") or payload.get("content") or payload.get("body") or ""
    if not text and payload:
        text = "\n".join(f"{k}: {v}" for k, v in payload.items() if not isinstance(v, (dict, list)))
        for k, v in payload.items():
            if isinstance(v, (dict, list)):
                text += f"\n{k}: {v}"
    hints = payload.get("source_type", payload.get("type", "webhook"))
    return IngestedDocument(content=str(text).strip() or str(payload), source_type=str(hints),
                            source_name=source_name, metadata={"raw_keys": list(payload.keys())})
