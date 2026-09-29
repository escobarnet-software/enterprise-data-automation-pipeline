"""Email parsing: raw .eml strings and dict payloads."""
import email
from email import policy
from .base import IngestedDocument


def parse_email_raw(raw: str, source_name: str = "email.eml") -> IngestedDocument:
    msg = email.message_from_string(raw, policy=policy.default)
    subject = str(msg.get("Subject", ""))
    sender = str(msg.get("From", ""))
    body = msg.get_body(preferencelist=("plain",))
    body_text = body.get_content() if body else msg.as_string()[:8000]
    content = f"From: {sender}\nSubject: {subject}\n\n{body_text.strip()}"
    return IngestedDocument(content=content, source_type="email", source_name=source_name,
                            metadata={"sender": sender, "subject": subject})


def parse_email_dict(payload: dict) -> IngestedDocument:
    sender = payload.get("from", payload.get("sender", ""))
    subject = payload.get("subject", "")
    body = payload.get("body", payload.get("text", ""))
    content = f"From: {sender}\nSubject: {subject}\n\n{str(body).strip()}"
    return IngestedDocument(content=content, source_type="email",
                            source_name=payload.get("id", "email"),
                            metadata={"sender": sender, "subject": subject})
