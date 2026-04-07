from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


MONEY_SCALE = Decimal("0.000001")


def parse_money(value: Any) -> Decimal:
    return Decimal(str(value)).quantize(MONEY_SCALE)


class PolicyDecision(BaseModel):
    decision: Literal["allow", "deny", "review"]
    reasons: list[str] = Field(default_factory=list)
    rate_limit_remaining: int | None = None


class PaymentRequirement(BaseModel):
    request_id: str
    amount: str
    asset_code: str
    asset_issuer: str
    network: str
    destination: str
    memo: str
    expires_at: datetime
    verification_mode: str
    settle_endpoint: str
    resource_url: str | None = None
    description: str | None = None


class PaymentProof(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    mode: Literal["mock", "transaction_hash", "x402_facilitator"]
    request_id: str
    payer: str = Field(..., min_length=3)
    payment_reference: str = Field(..., min_length=3)
    memo: str = Field(..., min_length=1)
    tx_hash: str | None = None
    raw_payload: dict[str, Any] | None = None
    settlement_response: dict[str, Any] | None = None


class ReceiptRecord(BaseModel):
    request_id: str
    payment_reference: str
    tool_name: str
    timestamp: datetime
    policy_decision: PolicyDecision
    payment_mode: str
    payer: str


class AuditRecord(BaseModel):
    audit_id: str
    request_id: str
    tool_name: str
    outcome: str
    timestamp: datetime
    payment_reference: str | None = None
    policy_reasons: list[str] = Field(default_factory=list)


class ReviewRecord(BaseModel):
    review_id: str
    request_id: str
    tool_name: str
    status: Literal["pending", "approved", "rejected"]
    created_at: datetime
    resolved_at: datetime | None = None
    reasons: list[str] = Field(default_factory=list)
    payment_reference: str | None = None
    payment: dict[str, Any] | None = None
    receipt: dict[str, Any] | None = None
    external_risk: dict[str, Any] | None = None
    note: str | None = None


class ToolExecutionResponse(BaseModel):
    status: Literal["AUTHORIZED"]
    request_id: str
    tool: str
    policy: PolicyDecision
    payment: dict[str, Any]
    receipt: ReceiptRecord
    audit: AuditRecord
    external_risk: dict[str, Any] | None = None
    result: dict[str, Any]


class SummariseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    client_id: str = Field(..., min_length=1)
    text: str = Field(..., min_length=1, max_length=5000)
    max_sentences: int = Field(default=2, ge=1, le=5)
    risk_flag: Literal["low", "medium", "high"] = "low"
    sender_address: str | None = Field(default=None, min_length=3)
    recipient_address: str | None = Field(default=None, min_length=3)
    sender_network: str = "stellar"
    recipient_network: str = "stellar"
    sender_token: str | None = None
    recipient_token: str | None = None
    payment_timestamp: str | None = None


class FetchUrlRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    client_id: str = Field(..., min_length=1)
    url: str = Field(..., min_length=8, max_length=1000)
    risk_flag: Literal["low", "medium", "high"] = "low"
    sender_address: str | None = Field(default=None, min_length=3)
    recipient_address: str | None = Field(default=None, min_length=3)
    sender_network: str = "stellar"
    recipient_network: str = "stellar"
    sender_token: str | None = None
    recipient_token: str | None = None
    payment_timestamp: str | None = None


class RiskCheckRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    client_id: str = Field(..., min_length=1)
    subject: str = Field(..., min_length=1, max_length=255)
    amount: Decimal = Field(default=Decimal("1.000000"))
    risk_flag: Literal["low", "medium", "high"] = "low"
    sender_address: str | None = Field(default=None, min_length=3)
    recipient_address: str | None = Field(default=None, min_length=3)
    sender_network: str = "stellar"
    recipient_network: str = "stellar"
    sender_token: str | None = None
    recipient_token: str | None = None
    payment_timestamp: str | None = None

    @field_validator("amount", mode="before")
    @classmethod
    def normalize_amount(cls, value: Any) -> Decimal:
        return parse_money(value)


class MockSettlementRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    request_id: str = Field(..., min_length=1)
    payer: str = Field(..., min_length=3)


class TransactionHashProofRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    request_id: str = Field(..., min_length=1)
    payer: str = Field(..., min_length=3)
    tx_hash: str = Field(..., min_length=8)
    payment_reference: str | None = Field(default=None, min_length=3)


class ReviewDecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    note: str | None = Field(default=None, max_length=500)
