from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

import httpx


@dataclass(frozen=True)
class RangeRiskConfig:
    api_key: str | None
    base_url: str = "https://api.range.org"
    address_deny_score: int = 8
    address_review_score: int = 5
    deny_payment_levels: tuple[str, ...] = ("high",)
    review_payment_levels: tuple[str, ...] = ("medium", "unknown")
    sanctions_deny: bool = True

    @property
    def enabled(self) -> bool:
        return bool((self.api_key or "").strip())


class RangeRiskClient:
    def __init__(self, config: RangeRiskConfig, *, timeout_seconds: float = 12.0) -> None:
        self.config = config
        self.timeout_seconds = timeout_seconds

    def _headers(self) -> dict[str, str]:
        if not self.config.enabled:
            raise ValueError("Range Risk API is not configured.")
        return {"Authorization": f"Bearer {self.config.api_key}"}

    def address_risk(self, *, address: str, network: str) -> dict[str, Any]:
        response = httpx.get(
            f"{self.config.base_url.rstrip('/')}/v1/risk/address",
            headers=self._headers(),
            params={"address": address, "network": network},
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        return response.json()

    def payment_risk(
        self,
        *,
        sender_address: str,
        recipient_address: str,
        amount: Decimal | float | int | str,
        sender_network: str,
        recipient_network: str,
        sender_token: str | None = None,
        recipient_token: str | None = None,
        timestamp: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "sender_address": sender_address,
            "recipient_address": recipient_address,
            "amount": str(amount),
            "sender_network": sender_network,
            "recipient_network": recipient_network,
        }
        if sender_token:
            params["sender_token"] = sender_token
        if recipient_token:
            params["recipient_token"] = recipient_token
        if timestamp:
            params["timestamp"] = timestamp
        response = httpx.get(
            f"{self.config.base_url.rstrip('/')}/v1/risk/payment",
            headers=self._headers(),
            params=params,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        return response.json()

    def sanctions(self, *, address: str, network: str | None = None, include_details: bool = True) -> dict[str, Any]:
        params: dict[str, Any] = {"include_details": str(include_details).lower()}
        if network:
            params["network"] = network
        response = httpx.get(
            f"{self.config.base_url.rstrip('/')}/v1/risk/sanctions/{address}",
            headers=self._headers(),
            params=params,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        return response.json()

    def recommend_address_action(self, result: dict[str, Any]) -> dict[str, Any]:
        score = int(result.get("riskScore") or 0)
        reasons = [f"range_address_score_{score}"]
        if score >= self.config.address_deny_score:
            return {"decision": "deny", "reasons": reasons}
        if score >= self.config.address_review_score:
            return {"decision": "review", "reasons": reasons}
        return {"decision": "allow", "reasons": reasons}

    def recommend_payment_action(self, result: dict[str, Any]) -> dict[str, Any]:
        level = str(result.get("overall_risk_level") or "unknown").lower()
        reasons = [f"range_payment_risk_{level}"]
        if level in self.config.deny_payment_levels:
            return {"decision": "deny", "reasons": reasons}
        if level in self.config.review_payment_levels:
            return {"decision": "review", "reasons": reasons}
        return {"decision": "allow", "reasons": reasons}

    def recommend_sanctions_action(self, result: dict[str, Any]) -> dict[str, Any]:
        blacklisted = bool(result.get("is_token_blacklisted"))
        sanctioned = bool(result.get("is_ofac_sanctioned"))
        reasons: list[str] = []
        if blacklisted:
            reasons.append("range_token_blacklisted")
        if sanctioned:
            reasons.append("range_ofac_sanctioned")
        if self.config.sanctions_deny and (blacklisted or sanctioned):
            return {"decision": "deny", "reasons": reasons}
        return {"decision": "allow", "reasons": reasons or ["range_sanctions_clear"]}
