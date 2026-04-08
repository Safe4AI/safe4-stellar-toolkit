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
from packages.middleware.models import PaymentRequirement, PolicyDecision, ReceiptRecord, ToolExecutionResponse
from packages.middleware.reviews import ReviewQueue
from packages.policies.engine import PolicyEngine
from packages.protocols.mpp import build_mpp_charge_required_header
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
        review_queue: ReviewQueue,
    ) -> None:
        self.policy_engine = policy_engine
        self.stellar_adapter = stellar_adapter
        self.audit_log = audit_log
        self.review_queue = review_queue
        self._pending: dict[str, PendingToolCall] = {}
        self._lock = threading.Lock()

    def summarize_external_risk(self, external_risk: dict[str, Any] | None) -> dict[str, Any] | None:
        if not external_risk:
            return None
        summary: dict[str, Any] = {
            "provider": external_risk.get("provider"),
            "operation": external_risk.get("operation"),
            "status": external_risk.get("status"),
        }
        recommendation = external_risk.get("recommendation")
        if isinstance(recommendation, dict):
            summary["decision"] = recommendation.get("decision")
            summary["reasons"] = list(recommendation.get("reasons", []))
        checks = external_risk.get("checks")
        if isinstance(checks, dict):
            summarized_checks: dict[str, Any] = {}
            for check_name, check in checks.items():
                item: dict[str, Any] = {"status": check.get("status")}
                check_recommendation = check.get("recommendation")
                if isinstance(check_recommendation, dict):
                    item["decision"] = check_recommendation.get("decision")
                    item["reasons"] = list(check_recommendation.get("reasons", []))
                result = check.get("result")
                if isinstance(result, dict):
                    if "overall_risk_level" in result:
                        item["level"] = result.get("overall_risk_level")
                    if "riskScore" in result:
                        item["score"] = result.get("riskScore")
                    if "is_ofac_sanctioned" in result:
                        item["ofac"] = bool(result.get("is_ofac_sanctioned"))
                    if "is_token_blacklisted" in result:
                        item["blacklisted"] = bool(result.get("is_token_blacklisted"))
                summarized_checks[check_name] = item
            summary["checks"] = summarized_checks
        return summary

    def merge_policy(
        self,
        *,
        local_policy: PolicyDecision,
        external_policy: PolicyDecision | None = None,
    ) -> PolicyDecision:
        if external_policy is None:
            return local_policy
        merged_reasons = list(local_policy.reasons) + list(external_policy.reasons)
        if local_policy.decision == "deny" or external_policy.decision == "deny":
            decision = "deny"
        elif local_policy.decision == "review" or external_policy.decision == "review":
            decision = "review"
        else:
            decision = "allow"
        return PolicyDecision(
            decision=decision,
            reasons=merged_reasons,
            rate_limit_remaining=local_policy.rate_limit_remaining,
        )

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
        resource_url: str | None = None,
        description: str | None = None,
    ) -> PendingToolCall:
        request_id = uuid4().hex
        requirement = self.stellar_adapter.build_requirement(
            request_id=request_id,
            amount=format(amount, "f"),
            settle_endpoint=settle_endpoint,
            resource_url=resource_url,
            description=description,
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
        external_policy: PolicyDecision | None = None,
        external_risk: dict[str, Any] | None = None,
    ) -> ToolExecutionResponse:
        pending = self.get_pending(request_id)
        if pending is None:
            raise ValueError("Unknown request_id.")
        if pending.tool_name != tool_name:
            raise ValueError("Tool mismatch for pending payment request.")
        if pending.request_digest != self.build_request_digest(tool_name=tool_name, payload=payload):
            raise ValueError("Request body mismatch for pending payment request.")
        proof = self.stellar_adapter.verify(requirement=pending.requirement, token=payment_token)
        local_policy = self.policy_engine.evaluate(
            tool_name=tool_name,
            client_id=pending.client_id,
            amount=pending.amount,
            risk_flag=pending.risk_flag,
        )
        policy = self.merge_policy(local_policy=local_policy, external_policy=external_policy)
        review_override = self.review_queue.get_override(request_id)
        if policy.decision == "review" and review_override == "allow":
            policy = PolicyDecision(
                decision="allow",
                reasons=list(policy.reasons) + ["manual_review_approved"],
                rate_limit_remaining=policy.rate_limit_remaining,
            )
        elif policy.decision == "review" and review_override == "deny":
            policy = PolicyDecision(
                decision="deny",
                reasons=list(policy.reasons) + ["manual_review_rejected"],
                rate_limit_remaining=policy.rate_limit_remaining,
            )
        risk_summary = self.summarize_external_risk(external_risk)
        payment = {
            "network": pending.requirement.network,
            "asset_code": pending.requirement.asset_code,
            "amount": pending.requirement.amount,
            "destination": pending.requirement.destination,
            "memo": pending.requirement.memo,
            "payment_reference": proof.payment_reference,
            "payer": proof.payer,
        }
        receipt = ReceiptRecord(
            request_id=request_id,
            payment_reference=proof.payment_reference,
            tool_name=tool_name,
            timestamp=datetime.now(timezone.utc),
            policy_decision=policy,
            payment_mode=proof.mode,
            payer=proof.payer,
            risk_summary=risk_summary,
        )
        audit = self.audit_log.append(
            request_id=request_id,
            tool_name=tool_name,
            outcome="authorized" if policy.decision == "allow" else policy.decision,
            payment_reference=proof.payment_reference,
            policy_reasons=policy.reasons,
            risk_summary=risk_summary,
        )
        if policy.decision != "allow":
            review_record = None
            if policy.decision == "review":
                review_record = self.review_queue.create_pending(
                    request_id=request_id,
                    tool_name=tool_name,
                    reasons=policy.reasons,
                    payment_reference=proof.payment_reference,
                    payment=payment,
                    receipt=receipt.model_dump(mode="json"),
                    external_risk=external_risk,
                )
            raise PermissionError(
                json.dumps(
                    {
                        "audit_id": audit.audit_id,
                        "decision": policy.decision,
                        "reasons": policy.reasons,
                        "payment": payment,
                        "receipt": receipt.model_dump(mode="json"),
                        "external_risk": external_risk,
                        "review": review_record.model_dump(mode="json") if review_record is not None else None,
                    }
                )
            )
        result = execute_tool()
        return ToolExecutionResponse(
            status="AUTHORIZED",
            request_id=request_id,
            tool=tool_name,
            policy=policy,
            payment=payment,
            receipt=receipt,
            audit=audit,
            external_risk=external_risk,
            result=result,
        )

    def payment_required_response(self, pending: PendingToolCall) -> JSONResponse:
        body = {
            "status": "payment_required",
            "request_id": pending.request_id,
            "tool": pending.tool_name,
            "payment_requirement": pending.requirement.model_dump(mode="json"),
        }
        verification_mode = pending.requirement.verification_mode
        header_value = (
            'Payment realm="safe4-stellar", '
            f'request_id="{pending.request_id}", '
            f'network="{pending.requirement.network}", '
            f'asset="{pending.requirement.asset_code}", '
            f'amount="{pending.requirement.amount}", '
            f'destination="{pending.requirement.destination}", '
            f'memo="{pending.requirement.memo}"'
        )
        headers = {
            "WWW-Authenticate": header_value,
            "X-Request-Id": pending.request_id,
        }
        if verification_mode == "mpp_charge_preview":
            headers["MPP-CHARGE-REQUIRED"] = build_mpp_charge_required_header(requirement=pending.requirement)
            headers["X-Payment-Protocol"] = "mpp-charge-preview"
        else:
            headers["PAYMENT-REQUIRED"] = build_x402_required_header(requirement=pending.requirement)
            headers["X-Payment-Protocol"] = "x402-stellar-preview"
        return JSONResponse(
            status_code=402,
            content=body,
            headers=headers,
        )
