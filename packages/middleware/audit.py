from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from .models import AuditRecord


class AuditLog:
    """Small append-only audit log for hackathon visibility."""

    def __init__(self, log_path: Path | None = None) -> None:
        self._records: list[AuditRecord] = []
        self._lock = threading.Lock()
        self._log_path = log_path

    def append(
        self,
        *,
        request_id: str,
        tool_name: str,
        outcome: str,
        payment_reference: str | None,
        policy_reasons: list[str],
    ) -> AuditRecord:
        record = AuditRecord(
            audit_id=uuid4().hex,
            request_id=request_id,
            tool_name=tool_name,
            outcome=outcome,
            timestamp=datetime.now(timezone.utc),
            payment_reference=payment_reference,
            policy_reasons=list(policy_reasons),
        )
        with self._lock:
            self._records.append(record)
            if self._log_path is not None:
                self._log_path.parent.mkdir(parents=True, exist_ok=True)
                with self._log_path.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(record.model_dump(mode="json"), sort_keys=True) + "\n")
        return record

    def list_records(self) -> list[AuditRecord]:
        with self._lock:
            return list(self._records)
