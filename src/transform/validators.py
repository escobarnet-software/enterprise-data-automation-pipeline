"""Strict validation before storage."""


class ValidationError(ValueError):
    pass


REQUIRED_BY_TYPE = {
    "invoice": ["total"],
    "purchase_order": [],
    "receipt": ["total"],
    "email": [],
    "report": [],
    "unknown": [],
}


def validate_record(record: dict, document_type: str = "unknown") -> dict:
    if not isinstance(record, dict) or not record:
        raise ValidationError("Record must be a non-empty object.")
    required = REQUIRED_BY_TYPE.get(document_type, [])
    missing = [f for f in required if record.get(f) in (None, "")]
    if missing:
        raise ValidationError(f"Missing required fields for {document_type}: {missing}")
    if "total" in record and record["total"] is not None:
        try:
            total = float(record["total"])
        except (TypeError, ValueError):
            raise ValidationError("Field 'total' must be numeric.")
        if total < 0:
            raise ValidationError("Field 'total' must be >= 0.")
    return record
