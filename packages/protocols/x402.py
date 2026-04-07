from __future__ import annotations

import base64
import json
from datetime import timezone
from typing import Any

import httpx

from packages.middleware.models import PaymentRequirement, ToolExecutionResponse


def _base64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def _canonical_header_payload(payload: dict[str, Any]) -> str:
    return _base64url_encode(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def protocol_network_id(value: str) -> str:
    normalized = value.strip().lower()
    if normalized in {"stellar-testnet", "testnet", "stellar:testnet"}:
        return "stellar:testnet"
    if normalized in {"stellar-mainnet", "stellar-pubnet", "mainnet", "pubnet", "stellar:mainnet"}:
        return "stellar:mainnet"
    return value


def build_x402_payment_requirements(*, requirement: PaymentRequirement) -> dict[str, Any]:
    timeout_seconds = max(
        1,
        int((requirement.expires_at.astimezone(timezone.utc) - __import__("datetime").datetime.now(timezone.utc)).total_seconds()),
    )
    payment_requirement = {
        "scheme": "exact",
        "network": protocol_network_id(requirement.network),
        "maxAmountRequired": requirement.amount,
        "asset": requirement.asset_code,
        "payTo": requirement.destination,
        "resource": requirement.resource_url,
        "description": requirement.description or "Paid AI tool request",
        "mimeType": "application/json",
        "maxTimeoutSeconds": timeout_seconds,
        "extra": {
            "assetCode": requirement.asset_code,
            "assetIssuer": requirement.asset_issuer,
            "memo": requirement.memo,
            "verificationMode": requirement.verification_mode,
        },
    }
    return {
        "x402Version": 2,
        "error": "PAYMENT-SIGNATURE header is required",
        "accepts": [payment_requirement],
    }


def build_x402_required_header(*, requirement: PaymentRequirement) -> str:
    return _canonical_header_payload(build_x402_payment_requirements(requirement=requirement))


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
            "auth-entry signing client flow",
            "wallet-driven PAYMENT-SIGNATURE generation",
            "production-grade facilitator settlement service",
        ],
    }
    if verification_mode == "x402_facilitator_preview":
        x402_status["implemented"].append("facilitator verify and settle preview seam")
    mpp_charge_status = {
        "status": "preview" if verification_mode == "mpp_charge_preview" else "planned",
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
    if verification_mode == "mpp_charge_preview":
        mpp_charge_status["implemented"].append("mpp charge guide and preview challenge surface")
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
        "primary_demo_target": "mpp_charge" if verification_mode == "mpp_charge_preview" else "x402",
        "fallback_demo_target": verification_mode,
        "x402": x402_status,
        "mpp_charge": mpp_charge_status,
        "mpp_session": mpp_session_status,
    }


class X402FacilitatorClient:
    def __init__(self, *, url: str | None, api_key: str | None = None, timeout_seconds: float = 10.0) -> None:
        self.url = (url or "").rstrip("/")
        self.api_key = (api_key or "").strip() or None
        self.timeout_seconds = timeout_seconds

    @property
    def configured(self) -> bool:
        return bool(self.url)

    @property
    def api_key_configured(self) -> bool:
        return bool(self.api_key)

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def supported(self) -> dict[str, Any]:
        if not self.configured:
            return {"configured": False, "status": "not_configured"}
        response = httpx.get(f"{self.url}/supported", headers=self._headers(), timeout=self.timeout_seconds)
        response.raise_for_status()
        body = response.json()
        if isinstance(body, dict):
            body["configured"] = True
            return body
        return {"configured": True, "status": "ok", "body": body}

    def verify(self, *, payment_payload: dict[str, Any], payment_requirements: dict[str, Any]) -> dict[str, Any]:
        response = httpx.post(
            f"{self.url}/verify",
            headers=self._headers(),
            json={"paymentPayload": payment_payload, "paymentRequirements": payment_requirements},
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        body = response.json()
        if not self._is_valid_response(body):
            raise ValueError("Facilitator verification rejected the x402 payment payload.")
        return body

    def settle(self, *, payment_payload: dict[str, Any], payment_requirements: dict[str, Any]) -> dict[str, Any]:
        response = httpx.post(
            f"{self.url}/settle",
            headers=self._headers(),
            json={"paymentPayload": payment_payload, "paymentRequirements": payment_requirements},
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _is_valid_response(body: Any) -> bool:
        if isinstance(body, dict):
            return bool(body.get("isValid") or body.get("valid") or body.get("success"))
        return False


def build_x402_settlement_header(*, settlement_response: dict[str, Any]) -> str:
    return _canonical_header_payload(settlement_response)
