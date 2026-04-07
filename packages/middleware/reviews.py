from __future__ import annotations

import threading
from datetime import datetime, timezone
from uuid import uuid4

from packages.middleware.models import ReviewRecord


class ReviewQueue:
    def __init__(self) -> None:
        self._records: dict[str, ReviewRecord] = {}
        self._lock = threading.Lock()

    def create_pending(
        self,
        *,
        request_id: str,
        tool_name: str,
        reasons: list[str],
        payment_reference: str | None,
        payment: dict | None,
        receipt: dict | None,
        external_risk: dict | None,
    ) -> ReviewRecord:
        with self._lock:
            existing = self._records.get(request_id)
            if existing is not None and existing.status == "pending":
                return existing
            record = ReviewRecord(
                review_id=uuid4().hex,
                request_id=request_id,
                tool_name=tool_name,
                status="pending",
                created_at=datetime.now(timezone.utc),
                reasons=list(reasons),
                payment_reference=payment_reference,
                payment=payment,
                receipt=receipt,
                external_risk=external_risk,
            )
            self._records[request_id] = record
            return record

    def decide(self, *, request_id: str, decision: str, note: str | None = None) -> ReviewRecord | None:
        with self._lock:
            record = self._records.get(request_id)
            if record is None:
                return None
            status = "approved" if decision == "allow" else "rejected"
            updated = record.model_copy(
                update={
                    "status": status,
                    "resolved_at": datetime.now(timezone.utc),
                    "note": note,
                }
            )
            self._records[request_id] = updated
            return updated

    def get(self, request_id: str) -> ReviewRecord | None:
        with self._lock:
            return self._records.get(request_id)

    def get_override(self, request_id: str) -> str | None:
        with self._lock:
            record = self._records.get(request_id)
            if record is None:
                return None
            if record.status == "approved":
                return "allow"
            if record.status == "rejected":
                return "deny"
            return None

    def list_records(self) -> list[ReviewRecord]:
        with self._lock:
            return sorted(
                self._records.values(),
                key=lambda record: record.created_at,
                reverse=True,
            )
