from __future__ import annotations

import base64
import json
from datetime import timezone
from typing import Any

import httpx

from packages.middleware.models import PaymentRequirement
from packages.protocols.x402 import protocol_network_id


def _base64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def _canonical_header_payload(payload: dict[str, Any]) -> str:
    return _base64url_encode(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def build_mpp_charge_request(*, requirement: PaymentRequirement) -> dict[str, Any]:
    return {
        "protocol": "mpp-charge-preview",
        "network": protocol_network_id(requirement.network),
        "asset": {
            "code": requirement.asset_code,
            "issuer": requirement.asset_issuer or None,
        },
        "charge": {
            "amount": requirement.amount,
            "destination": requirement.destination,
            "memo": requirement.memo,
            "expiresAt": requirement.expires_at.astimezone(timezone.utc).isoformat(),
        },
        "resource": requirement.resource_url,
        "description": requirement.description or "Paid AI tool request",
        "supportedModes": ["pull", "push", "sponsored-fee-preview"],
        "sdk": "@stellar/mpp",
    }


def build_mpp_charge_required_header(*, requirement: PaymentRequirement) -> str:
    payload = build_mpp_charge_request(requirement=requirement)
    payload["status"] = "preview"
    payload["error"] = "MPP charge settlement is required before retry."
    return _canonical_header_payload(payload)


def build_mpp_charge_guide(*, requirement: PaymentRequirement | None = None) -> dict[str, Any]:
    base = {
        "status": "preview",
        "protocol": "mpp-charge-preview",
        "sdk": "@stellar/mpp",
        "supportedModes": ["pull", "push", "sponsored-fee-preview"],
        "notes": [
            "This is a preview integration surface for Stellar MPP Charge.",
            "The toolkit does not yet run a full @stellar/mpp server verifier in Python.",
            "Use transaction_hash mode for the strongest live proof path today.",
        ],
    }
    if requirement is not None:
        base["request"] = build_mpp_charge_request(requirement=requirement)
    return base


class MppChargeServiceClient:
    def __init__(self, *, url: str | None, timeout_seconds: float = 10.0) -> None:
        self.url = (url or "").rstrip("/")
        self.timeout_seconds = timeout_seconds

    @property
    def configured(self) -> bool:
        return bool(self.url)

    def health(self) -> dict[str, Any]:
        if not self.configured:
            return {"configured": False, "status": "not_configured"}
        response = httpx.get(f"{self.url}/health", timeout=self.timeout_seconds)
        response.raise_for_status()
        body = response.json()
        if isinstance(body, dict):
            body["configured"] = True
            return body
        return {"configured": True, "status": "ok", "body": body}
