from __future__ import annotations

import base64
import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
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

    def build_transaction_hash_payment_token(
        self,
        *,
        requirement: PaymentRequirement,
        payer: str,
        tx_hash: str,
        payment_reference: str | None = None,
    ) -> str:
        proof = {
            "mode": "transaction_hash",
            "request_id": requirement.request_id,
            "payer": payer,
            "payment_reference": payment_reference or tx_hash,
            "memo": requirement.memo,
            "tx_hash": tx_hash,
        }
        return _base64url_encode(json.dumps(proof, sort_keys=True, separators=(",", ":")).encode("utf-8"))

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
        transaction_payload = self._horizon_get_json(f"/transactions/{proof.tx_hash}")
        if not bool(transaction_payload.get("successful")):
            raise ValueError("Transaction hash did not resolve to a successful Stellar payment.")
        memo = str(transaction_payload.get("memo") or "")
        if memo != requirement.memo:
            raise ValueError("Transaction memo does not match the Safe4 request.")
        created_at = str(transaction_payload.get("created_at") or "")
        if created_at:
            if self._parse_horizon_timestamp(created_at) > requirement.expires_at:
                raise ValueError("Transaction was submitted after the Safe4 payment challenge expired.")

        operations_payload = self._horizon_get_json(f"/transactions/{proof.tx_hash}/operations")
        records = self._extract_operation_records(operations_payload)
        if not records:
            raise ValueError("No payment operations were found for the supplied transaction hash.")

        required_amount = Decimal(requirement.amount)
        for operation in records:
            if not self._operation_matches_payment_requirement(
                operation=operation,
                payer=proof.payer,
                requirement=requirement,
                required_amount=required_amount,
            ):
                continue
            return proof
        raise ValueError("No Stellar payment operation matched the Safe4 request requirements.")
        return proof

    def _horizon_get_json(self, path: str) -> dict[str, Any]:
        response = httpx.get(f"{self.config.horizon_url.rstrip('/')}{path}", timeout=10.0)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _parse_horizon_timestamp(value: str) -> datetime:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    @staticmethod
    def _extract_operation_records(payload: dict[str, Any]) -> list[dict[str, Any]]:
        embedded = payload.get("_embedded")
        if isinstance(embedded, dict):
            records = embedded.get("records")
            if isinstance(records, list):
                return [item for item in records if isinstance(item, dict)]
        records = payload.get("records")
        if isinstance(records, list):
            return [item for item in records if isinstance(item, dict)]
        return []

    def _operation_matches_payment_requirement(
        self,
        *,
        operation: dict[str, Any],
        payer: str,
        requirement: PaymentRequirement,
        required_amount: Decimal,
    ) -> bool:
        operation_type = str(operation.get("type") or "")
        if operation_type not in {"payment", "path_payment_strict_receive", "path_payment_strict_send"}:
            return False
        if str(operation.get("to") or "") != requirement.destination:
            return False
        sender = str(operation.get("from") or operation.get("source_account") or "")
        if payer and sender and sender != payer:
            return False
        if not self._operation_matches_asset(operation=operation, requirement=requirement):
            return False
        operation_amount = self._operation_amount(operation)
        if operation_amount is None or operation_amount < required_amount:
            return False
        return True

    @staticmethod
    def _operation_amount(operation: dict[str, Any]) -> Decimal | None:
        raw = operation.get("amount")
        if raw is None:
            return None
        try:
            return Decimal(str(raw))
        except Exception:
            return None

    def _operation_matches_asset(self, *, operation: dict[str, Any], requirement: PaymentRequirement) -> bool:
        required_code = requirement.asset_code.upper()
        if required_code == "XLM":
            return str(operation.get("asset_type") or "").lower() == "native"
        return (
            str(operation.get("asset_code") or "").upper() == required_code
            and str(operation.get("asset_issuer") or "") == requirement.asset_issuer
        )
