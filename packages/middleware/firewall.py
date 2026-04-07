from __future__ import annotations

import hashlib
import json
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Callable
from uuid import uuid4

from fastapi.responses import JSONResponse

from packages.middleware.audit import AuditLog
from packages.middleware.models import PaymentRequirement, ReceiptRecord, ToolExecutionResponse
from packages.policies.engine import PolicyEngine
from packages.protocols.x402 import build_x402_required_header
from packages.stellar.adapter import StellarPaymentAdapter


@dataclass
class PendingToolCall:
    request_id: str
    tool_name: str
    amount: Decimal
    client_id: str
    risk_flag: str
    request_digest: str
    requirement: PaymentRequirement


class FirewallService:
    def __init__(
        self,
        *,
        policy_engine: PolicyEngine,
        stellar_adapter: StellarPaymentAdapter,
        audit_log: AuditLog,
    ) -> None:
        self.policy_engine = policy_engine
        self.stellar_adapter = stellar_adapter
        self.audit_log = audit_log
        self._pending: dict[str, PendingToolCall] = {}
        self._lock = threading.Lock()

    def build_request_digest(self, *, tool_name: str, payload: dict[str, Any]) -> str:
        canonical = json.dumps({"tool_name": tool_name, "payload": payload}, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def ensure_payment(
        self,
        *,
        tool_name: str,
        amount: Decimal,
        client_id: str,
        risk_flag: str,
        payload: dict[str, Any],
        settle_endpoint: str,
    ) -> PendingToolCall:
        request_id = uuid4().hex
        requirement = self.stellar_adapter.build_requirement(
            request_id=request_id,
            amount=format(amount, "f"),
            settle_endpoint=settle_endpoint,
        )
        pending = PendingToolCall(
            request_id=request_id,
            tool_name=tool_name,
            amount=amount,
            client_id=client_id,
            risk_flag=risk_flag,
            request_digest=self.build_request_digest(tool_name=tool_name, payload=payload),
            requirement=requirement,
        )
        with self._lock:
            self._pending[request_id] = pending
        return pending

    def get_pending(self, request_id: str) -> PendingToolCall | None:
        with self._lock:
            return self._pending.get(request_id)

    def authorize(
        self,
        *,
        request_id: str,
        tool_name: str,
        payload: dict[str, Any],
        payment_token: str,
        execute_tool: Callable[[], dict[str, Any]],
    ) -> ToolExecutionResponse:
        pending = self.get_pending(request_id)
        if pending is None:
            raise ValueError("Unknown request_id.")
        if pending.tool_name != tool_name:
            raise ValueError("Tool mismatch for pending payment request.")
        if pending.request_digest != self.build_request_digest(tool_name=tool_name, payload=payload):
            raise ValueError("Request body mismatch for pending payment request.")
        proof = self.stellar_adapter.verify(requirement=pending.requirement, token=payment_token)
        policy = self.policy_engine.evaluate(
            tool_name=tool_name,
            client_id=pending.client_id,
            amount=pending.amount,
            risk_flag=pending.risk_flag,
        )
        audit = self.audit_log.append(
            request_id=request_id,
            tool_name=tool_name,
            outcome="denied" if policy.decision == "deny" else "authorized",
            payment_reference=proof.payment_reference,
            policy_reasons=policy.reasons,
        )
        if policy.decision == "deny":
            raise PermissionError(json.dumps({"audit_id": audit.audit_id, "reasons": policy.reasons}))
        result = execute_tool()
        receipt = ReceiptRecord(
            request_id=request_id,
            payment_reference=proof.payment_reference,
            tool_name=tool_name,
            timestamp=datetime.now(timezone.utc),
            policy_decision=policy,
            payment_mode=proof.mode,
            payer=proof.payer,
        )
        return ToolExecutionResponse(
            status="AUTHORIZED",
            request_id=request_id,
            tool=tool_name,
            policy=policy,
            payment={
                "network": pending.requirement.network,
                "asset_code": pending.requirement.asset_code,
                "amount": pending.requirement.amount,
                "destination": pending.requirement.destination,
                "memo": pending.requirement.memo,
                "payment_reference": proof.payment_reference,
                "payer": proof.payer,
            },
            receipt=receipt,
            audit=audit,
            result=result,
        )

    def payment_required_response(self, pending: PendingToolCall) -> JSONResponse:
        body = {
            "status": "payment_required",
            "request_id": pending.request_id,
            "tool": pending.tool_name,
            "payment_requirement": pending.requirement.model_dump(mode="json"),
        }
        header_value = (
            'Payment realm="safe4-stellar", '
            f'request_id="{pending.request_id}", '
            f'network="{pending.requirement.network}", '
            f'asset="{pending.requirement.asset_code}", '
            f'amount="{pending.requirement.amount}", '
            f'destination="{pending.requirement.destination}", '
            f'memo="{pending.requirement.memo}"'
        )
        return JSONResponse(
            status_code=402,
            content=body,
            headers={
                "WWW-Authenticate": header_value,
                "PAYMENT-REQUIRED": build_x402_required_header(requirement=pending.requirement),
                "X-Payment-Protocol": "x402-stellar-preview",
                "X-Request-Id": pending.request_id,
            },
        )
