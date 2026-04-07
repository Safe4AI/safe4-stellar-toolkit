from __future__ import annotations

import base64
import json
from datetime import timezone
from typing import Any

from packages.middleware.models import PaymentRequirement, ToolExecutionResponse


def _base64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def _canonical_header_payload(payload: dict[str, Any]) -> str:
    return _base64url_encode(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def build_x402_required_header(*, requirement: PaymentRequirement) -> str:
    payload = {
        "scheme": "x402-stellar-preview",
        "request_id": requirement.request_id,
        "network": requirement.network,
        "asset_code": requirement.asset_code,
        "asset_issuer": requirement.asset_issuer,
        "amount": requirement.amount,
        "destination": requirement.destination,
        "memo": requirement.memo,
        "expires_at": requirement.expires_at.astimezone(timezone.utc).isoformat(),
        "verification_mode": requirement.verification_mode,
        "settle_endpoint": requirement.settle_endpoint,
    }
    return _canonical_header_payload(payload)


def build_x402_response_header(*, response: ToolExecutionResponse) -> str:
    payload = {
        "scheme": "x402-stellar-preview",
        "request_id": response.request_id,
        "tool": response.tool,
        "payment_reference": response.payment["payment_reference"],
        "network": response.payment["network"],
        "asset_code": response.payment["asset_code"],
        "amount": response.payment["amount"],
        "destination": response.payment["destination"],
        "payer": response.payment["payer"],
        "policy_decision": response.policy.decision,
        "receipt_timestamp": response.receipt.timestamp.astimezone(timezone.utc).isoformat(),
    }
    return _canonical_header_payload(payload)


def protocol_status(*, verification_mode: str) -> dict[str, Any]:
    x402_status = {
        "status": "preview",
        "implemented": [
            "402 payment-required response",
            "PAYMENT-REQUIRED header",
            "PAYMENT-RESPONSE header",
            "request binding",
            "policy enforcement before execution",
            f"{verification_mode} proof path",
        ],
        "missing": [
            "stellar facilitator integration",
            "auth-entry signing client flow",
            "PAYMENT-SIGNATURE retry format",
            "production-grade settlement service",
        ],
    }
    mpp_charge_status = {
        "status": "planned",
        "implemented": [
            "payment auth style retry model",
            "request-bound challenge and receipt model",
        ],
        "missing": [
            "@stellar/mpp charge flow",
            "pull credential mode",
            "push/hash credential mode",
            "sponsored-fee flow",
        ],
    }
    mpp_session_status = {
        "status": "planned",
        "implemented": [],
        "missing": [
            "session channels",
            "cumulative payment commitments",
            "channel settlement receipts",
        ],
    }
    return {
        "primary_demo_target": "x402",
        "fallback_demo_target": verification_mode,
        "x402": x402_status,
        "mpp_charge": mpp_charge_status,
        "mpp_session": mpp_session_status,
    }

