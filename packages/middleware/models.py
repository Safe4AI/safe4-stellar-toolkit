from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


MONEY_SCALE = Decimal("0.000001")


def parse_money(value: Any) -> Decimal:
    return Decimal(str(value)).quantize(MONEY_SCALE)


class PolicyDecision(BaseModel):
    decision: Literal["allow", "deny"]
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


class PaymentProof(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    mode: Literal["mock", "transaction_hash"]
    request_id: str
    payer: str = Field(..., min_length=3)
    payment_reference: str = Field(..., min_length=3)
    memo: str = Field(..., min_length=1)
    tx_hash: str | None = None


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


class ToolExecutionResponse(BaseModel):
    status: Literal["AUTHORIZED"]
    request_id: str
    tool: str
    policy: PolicyDecision
    payment: dict[str, Any]
    receipt: ReceiptRecord
    audit: AuditRecord
    result: dict[str, Any]


class SummariseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    client_id: str = Field(..., min_length=1)
    text: str = Field(..., min_length=1, max_length=5000)
    max_sentences: int = Field(default=2, ge=1, le=5)
    risk_flag: Literal["low", "medium", "high"] = "low"


class FetchUrlRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    client_id: str = Field(..., min_length=1)
    url: str = Field(..., min_length=8, max_length=1000)
    risk_flag: Literal["low", "medium", "high"] = "low"


class RiskCheckRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    client_id: str = Field(..., min_length=1)
    subject: str = Field(..., min_length=1, max_length=255)
    amount: Decimal = Field(default=Decimal("1.000000"))
    risk_flag: Literal["low", "medium", "high"] = "low"

    @field_validator("amount", mode="before")
    @classmethod
    def normalize_amount(cls, value: Any) -> Decimal:
        return parse_money(value)


class MockSettlementRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    request_id: str = Field(..., min_length=1)
    payer: str = Field(..., min_length=3)
