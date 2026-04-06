from __future__ import annotations

import base64
import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from packages.middleware.models import PaymentProof, PaymentRequirement


def _base64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def _base64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


@dataclass(frozen=True)
class StellarConfig:
    verification_mode: str
    network: str
    asset_code: str
    asset_issuer: str
    destination: str
    horizon_url: str
    proof_secret: str


class StellarPaymentAdapter:
    """Thin Stellar adapter with a reliable mock flow and a tx-hash seam."""

    def __init__(self, config: StellarConfig) -> None:
        self.config = config

    def build_requirement(self, *, request_id: str, amount: str, settle_endpoint: str) -> PaymentRequirement:
        memo = f"safe4-{request_id[:12]}"
        return PaymentRequirement(
            request_id=request_id,
            amount=amount,
            asset_code=self.config.asset_code,
            asset_issuer=self.config.asset_issuer,
            network=self.config.network,
            destination=self.config.destination,
            memo=memo,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
            verification_mode=self.config.verification_mode,
            settle_endpoint=settle_endpoint,
        )

    def build_mock_payment_token(self, *, requirement: PaymentRequirement, payer: str) -> str:
        proof = {
            "mode": "mock",
            "request_id": requirement.request_id,
            "payer": payer,
            "payment_reference": f"mockpay_{requirement.request_id[:8]}",
            "memo": requirement.memo,
        }
        canonical = json.dumps(proof, sort_keys=True, separators=(",", ":"))
        signature = hmac.new(
            self.config.proof_secret.encode("utf-8"),
            canonical.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        envelope = {"proof": proof, "signature": signature}
        return _base64url_encode(json.dumps(envelope, separators=(",", ":")).encode("utf-8"))

    def parse_payment_token(self, token: str) -> PaymentProof:
        payload = json.loads(_base64url_decode(token).decode("utf-8"))
        if isinstance(payload, dict) and "proof" in payload and "signature" in payload:
            proof = payload["proof"]
            canonical = json.dumps(proof, sort_keys=True, separators=(",", ":"))
            expected = hmac.new(
                self.config.proof_secret.encode("utf-8"),
                canonical.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()
            if not hmac.compare_digest(payload.get("signature", ""), expected):
                raise ValueError("Invalid payment proof signature.")
            return PaymentProof.model_validate(proof)

        proof = PaymentProof.model_validate(payload)
        if proof.mode != "transaction_hash":
            raise ValueError("Unsigned payment proof is only allowed for transaction_hash mode.")
        return proof

    def verify(self, *, requirement: PaymentRequirement, token: str) -> PaymentProof:
        proof = self.parse_payment_token(token)
        if proof.request_id != requirement.request_id:
            raise ValueError("Payment proof request binding mismatch.")
        if proof.memo != requirement.memo:
            raise ValueError("Payment memo mismatch.")
        if proof.mode == "mock":
            return proof
        return self._verify_transaction_hash(requirement=requirement, proof=proof)

    def _verify_transaction_hash(self, *, requirement: PaymentRequirement, proof: PaymentProof) -> PaymentProof:
        if not proof.tx_hash:
            raise ValueError("transaction_hash verification requires tx_hash.")
        response = httpx.get(
            f"{self.config.horizon_url.rstrip('/')}/transactions/{proof.tx_hash}",
            timeout=10.0,
        )
        response.raise_for_status()
        payload: dict[str, Any] = response.json()
        memo = payload.get("memo")
        if memo != requirement.memo:
            raise ValueError("Transaction memo does not match the Safe4 request.")
        return proof
