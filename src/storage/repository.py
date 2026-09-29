"""Idempotent repository (dedupe by content_hash)."""
import logging
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from .models import DocumentRecord

log = logging.getLogger(__name__)


class DocumentRepository:
    def __init__(self, session):
        self.session = session

    def save(self, *, content_hash: str, document_type: str, source_type: str,
             source_name: str, data: dict) -> tuple[DocumentRecord, bool]:
        """Insert or return existing. Returns (record, created)."""
        existing = self.session.execute(
            select(DocumentRecord).where(DocumentRecord.content_hash == content_hash)
        ).scalar_one_or_none()
        if existing:
            log.info("Duplicate skipped: %s", content_hash[:12])
            return existing, False
        rec = DocumentRecord(content_hash=content_hash, document_type=document_type,
                             source_type=source_type, source_name=source_name,
                             total=data.get("total"), currency=data.get("currency"), data=data)
        self.session.add(rec)
        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            existing = self.session.execute(
                select(DocumentRecord).where(DocumentRecord.content_hash == content_hash)
            ).scalar_one()
            return existing, False
        self.session.refresh(rec)
        return rec, True

    def list(self, document_type: str | None = None, limit: int = 100) -> list[DocumentRecord]:
        q = select(DocumentRecord).order_by(DocumentRecord.id.desc()).limit(limit)
        if document_type:
            q = q.where(DocumentRecord.document_type == document_type)
        return list(self.session.execute(q).scalars().all())

    def stats(self) -> dict:
        total = self.session.execute(select(func.count(DocumentRecord.id))).scalar() or 0
        by_type = self.session.execute(
            select(DocumentRecord.document_type, func.count()).group_by(DocumentRecord.document_type)
        ).all()
        return {"total_documents": total, "by_type": {k: v for k, v in by_type}}
