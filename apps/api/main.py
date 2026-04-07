from __future__ import annotations

import json
import os
import re
from decimal import Decimal
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse

from packages.middleware.audit import AuditLog
from packages.middleware.firewall import FirewallService
from packages.middleware.models import (
    FetchUrlRequest,
    MockSettlementRequest,
    RiskCheckRequest,
    SummariseRequest,
    TransactionHashProofRequest,
)
from packages.policies.engine import PolicyConfig, PolicyEngine
from packages.protocols.mpp import build_mpp_charge_guide
from packages.protocols.x402 import (
    build_x402_required_header,
    build_x402_response_header,
    build_x402_settlement_header,
    protocol_status,
)
from packages.stellar.adapter import StellarConfig, StellarPaymentAdapter


ROOT = Path(__file__).resolve().parents[2]
DEMO_PAGE = ROOT / "apps" / "demo" / "index.html"
AUDIT_LOG_PATH = ROOT / "audit_log.jsonl"
URL_PATTERN = re.compile(r"^https?://", re.IGNORECASE)


def _env_decimal(name: str, default: str) -> Decimal:
    return Decimal(os.getenv(name, default)).quantize(Decimal("0.000001"))


def build_app() -> FastAPI:
    app = FastAPI(title="Safe4 Stellar Toolkit", version="0.1.0")
    asset_code = os.getenv("SAFE4_STELLAR_ASSET_CODE", "USDC").strip() or "USDC"
    asset_issuer = os.getenv(
        "SAFE4_STELLAR_ASSET_ISSUER",
        "GBRPYHIL2CEXAMPLETESTNETISSUERPLACEHOLDERXXXXXXXXXXXX",
    ).strip()
    if asset_code.upper() == "XLM":
        asset_issuer = ""

    stellar_adapter = StellarPaymentAdapter(
        StellarConfig(
            verification_mode=os.getenv("SAFE4_STELLAR_VERIFICATION_MODE", "mock").strip() or "mock",
            network=os.getenv("SAFE4_STELLAR_NETWORK", "stellar-testnet").strip() or "stellar-testnet",
            asset_code=asset_code,
            asset_issuer=asset_issuer,
            destination=os.getenv(
                "SAFE4_STELLAR_DESTINATION",
                "GCR2XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
            ).strip(),
            horizon_url=os.getenv("SAFE4_STELLAR_HORIZON_URL", "https://horizon-testnet.stellar.org").strip(),
            proof_secret=os.getenv("SAFE4_STELLAR_PROOF_SECRET", "change-me").strip() or "change-me",
            x402_facilitator_url=os.getenv("SAFE4_X402_FACILITATOR_URL"),
            x402_facilitator_api_key=os.getenv("SAFE4_X402_FACILITATOR_API_KEY"),
        )
    )
    policy_engine = PolicyEngine(
        PolicyConfig(
            max_spend_per_request=_env_decimal("SAFE4_STELLAR_MAX_SPEND_PER_REQUEST", "2.000000"),
            rate_limit_requests=int(os.getenv("SAFE4_STELLAR_RATE_LIMIT_REQUESTS", "5")),
            rate_limit_window_seconds=int(os.getenv("SAFE4_STELLAR_RATE_LIMIT_WINDOW_SECONDS", "60")),
        )
    )
    firewall = FirewallService(
        policy_engine=policy_engine,
        stellar_adapter=stellar_adapter,
        audit_log=AuditLog(log_path=AUDIT_LOG_PATH),
    )

    tool_prices = {
        "summarise": Decimal("0.500000"),
        "fetch-url": Decimal("0.750000"),
        "risk-check": Decimal("1.250000"),
    }

    def _payment_token_from_headers(authorization: str | None, payment_signature: str | None) -> str | None:
        token = None
        if authorization is not None and authorization.startswith("Payment "):
            token = authorization[len("Payment ") :].strip()
        elif payment_signature is not None:
            token = payment_signature.strip()
        return token or None

    def _tool_payment_response(
        *,
        request: Request,
        tool_name: str,
        amount: Decimal,
        client_id: str,
        risk_flag: str,
        payload: dict[str, Any],
        execute_tool,
        authorization: str | None,
        payment_signature: str | None,
        request_id_header: str | None,
    ) -> JSONResponse:
        token = _payment_token_from_headers(authorization, payment_signature)
        if not token:
            if stellar_adapter.config.verification_mode == "mock":
                settle_path = "/payments/mock/settle"
            elif stellar_adapter.config.verification_mode == "mpp_charge_preview":
                settle_path = "/payments/mpp/charge/guide"
            elif stellar_adapter.config.verification_mode == "x402_facilitator_preview":
                settle_path = "/payments/x402/guide"
            else:
                settle_path = "/payments/transaction-hash-proof"
            pending = firewall.ensure_payment(
                tool_name=tool_name,
                amount=amount,
                client_id=client_id,
                risk_flag=risk_flag,
                payload=payload,
                settle_endpoint=str(request.base_url).rstrip("/") + settle_path,
                resource_url=str(request.url),
                description=f"Access to {tool_name}",
            )
            return firewall.payment_required_response(pending)
        request_id = request_id_header or ""
        if not request_id:
            raise HTTPException(status_code=400, detail="X-Request-Id is required on the paid retry.")
        try:
            response = firewall.authorize(
                request_id=request_id,
                tool_name=tool_name,
                payload=payload,
                payment_token=token,
                execute_tool=execute_tool,
            )
        except PermissionError as exc:
            details = json.loads(str(exc))
            return JSONResponse(
                status_code=403,
                content={
                    "status": "denied",
                    "request_id": request_id,
                    "tool": tool_name,
                    "policy": {"decision": "deny", "reasons": details["reasons"]},
                    "audit": {"audit_id": details["audit_id"]},
                },
            )
        except ValueError as exc:
            return JSONResponse(
                status_code=402,
                content={"status": "payment_invalid", "request_id": request_id, "detail": str(exc)},
            )
        headers = {
            "PAYMENT-RESPONSE": build_x402_response_header(response=response),
            "X-Payment-Protocol": "x402-stellar-preview",
        }
        if response.receipt.payment_mode == "x402_facilitator":
            proof_settlement = response.payment.get("settlement_response") if isinstance(response.payment, dict) else None
            if isinstance(proof_settlement, dict):
                headers["PAYMENT-RESPONSE"] = build_x402_settlement_header(settlement_response=proof_settlement)
        return JSONResponse(
            status_code=200,
            content=response.model_dump(mode="json"),
            headers=headers,
        )

    @app.get("/")
    def root() -> dict[str, Any]:
        return {
            "name": "safe4-stellar-toolkit",
            "tagline": "Stripe-like safety middleware for paid AI tools on Stellar.",
            "demo": "/demo",
            "tools": "/tools",
        }

    @app.get("/health")
    def health() -> dict[str, Any]:
        return {
            "status": "ok",
            "verification_mode": stellar_adapter.config.verification_mode,
            "network": stellar_adapter.config.network,
            "asset_code": stellar_adapter.config.asset_code,
            "x402_facilitator_configured": stellar_adapter.facilitator.configured,
        }

    @app.get("/demo")
    def demo_page() -> FileResponse:
        return FileResponse(DEMO_PAGE)

    @app.get("/tools")
    def list_tools() -> dict[str, Any]:
        return {
            "tools": [
                {
                    "name": "summarise",
                    "price": format(tool_prices["summarise"], "f"),
                    "asset_code": stellar_adapter.config.asset_code,
                    "description": "Summarise supplied text in a small number of sentences.",
                },
                {
                    "name": "fetch-url",
                    "price": format(tool_prices["fetch-url"], "f"),
                    "asset_code": stellar_adapter.config.asset_code,
                    "description": "Return safe metadata about a URL without fetching remote content.",
                },
                {
                    "name": "risk-check",
                    "price": format(tool_prices["risk-check"], "f"),
                    "asset_code": stellar_adapter.config.asset_code,
                    "description": "Run a simple risk classification on a subject string.",
                },
            ]
        }

    @app.get("/protocols/status")
    def get_protocol_status() -> dict[str, Any]:
        status = protocol_status(verification_mode=stellar_adapter.config.verification_mode)
        status["x402"]["facilitator_configured"] = stellar_adapter.facilitator.configured
        if stellar_adapter.facilitator.configured:
            status["x402"]["facilitator_url"] = stellar_adapter.facilitator.url
        return status

    @app.get("/protocols/x402/facilitator")
    def get_x402_facilitator_status() -> dict[str, Any]:
        try:
            supported = stellar_adapter.facilitator_supported()
        except Exception as exc:
            supported = {
                "configured": stellar_adapter.facilitator.configured,
                "status": "unreachable",
                "error": str(exc),
            }
        return {
            "configured": stellar_adapter.facilitator.configured,
            "api_key_configured": stellar_adapter.facilitator.api_key_configured,
            "verification_mode": stellar_adapter.config.verification_mode,
            "facilitator_url": stellar_adapter.facilitator.url if stellar_adapter.facilitator.configured else None,
            "supported": supported,
        }

    @app.get("/payments/x402/guide")
    def x402_guide() -> dict[str, Any]:
        return {
            "status": "preview",
            "verification_mode": stellar_adapter.config.verification_mode,
            "network": stellar_adapter.config.network,
            "client_retry_headers": ["PAYMENT-SIGNATURE", "X-Request-Id"],
            "facilitator": {
                "configured": stellar_adapter.facilitator.configured,
                "api_key_configured": stellar_adapter.facilitator.api_key_configured,
                "url": stellar_adapter.facilitator.url if stellar_adapter.facilitator.configured else None,
            },
            "deployment_options": {
                "hosted_channels": {
                    "base_url": "https://channels.openzeppelin.com/x402/testnet",
                    "requires_api_key": True,
                },
                "self_hosted_relayer_plugin": {
                    "base_url_pattern": "http://localhost:8080/api/v1/plugins/x402-facilitator/call",
                    "requires_hosted_channels_api_key": False,
                    "may_require_relayer_api_key": True,
                    "notes": [
                        "This path expects you to run the OpenZeppelin Relayer plugin yourself.",
                        "The plugin exposes /verify, /settle, and /supported under the /call router.",
                        "Set SAFE4_X402_FACILITATOR_API_KEY to your Relayer API key if the plugin route is bearer-protected.",
                    ],
                },
            },
            "notes": [
                "This preview expects a client or wallet that can produce an x402 PAYMENT-SIGNATURE payload.",
                "For live Stellar x402, use an auth-entry-signing wallet and either a hosted facilitator or a self-hosted OpenZeppelin Relayer x402 plugin.",
                "The current strongest live proof path in this deployment remains transaction_hash mode unless x402_facilitator_preview is enabled.",
            ],
        }

    @app.get("/protocols/mpp/charge")
    def get_mpp_charge_status() -> dict[str, Any]:
        return {
            "status": "preview",
            "verification_mode": stellar_adapter.config.verification_mode,
            "sdk": "@stellar/mpp",
            "supported_modes": ["pull", "push", "sponsored-fee-preview"],
            "notes": [
                "MPP Charge is exposed here as a preview protocol surface.",
                "The toolkit does not yet run a full @stellar/mpp verification backend in Python.",
                "Use transaction_hash mode for the strongest live demo proof today.",
            ],
        }

    @app.get("/protocols/mpp/session")
    def get_mpp_session_status() -> dict[str, Any]:
        return {
            "status": "planned",
            "notes": [
                "MPP Session is intentionally deferred.",
                "The next protocol milestone after x402 is MPP Charge, not payment channels.",
            ],
        }

    @app.get("/payments/mpp/charge/guide")
    def mpp_charge_guide(request_id: str | None = None) -> dict[str, Any]:
        pending = firewall.get_pending(request_id) if request_id else None
        requirement = pending.requirement if pending is not None else None
        body = build_mpp_charge_guide(requirement=requirement)
        body["verification_mode"] = stellar_adapter.config.verification_mode
        return body

    @app.get("/audit/entries")
    def list_audit_entries() -> dict[str, Any]:
        return {"entries": [record.model_dump(mode="json") for record in firewall.audit_log.list_records()]}

    @app.post("/payments/mock/settle")
    def mock_settle(body: MockSettlementRequest) -> dict[str, Any]:
        if stellar_adapter.config.verification_mode != "mock":
            raise HTTPException(
                status_code=409,
                detail="Mock settlement is disabled unless SAFE4_STELLAR_VERIFICATION_MODE=mock.",
            )
        pending = firewall.get_pending(body.request_id)
        if pending is None:
            raise HTTPException(status_code=404, detail="Unknown request_id.")
        token = stellar_adapter.build_mock_payment_token(requirement=pending.requirement, payer=body.payer)
        return {
            "status": "settled",
            "verification_mode": "mock",
            "request_id": body.request_id,
            "payment_token": token,
            "authorization_header": f"Payment {token}",
        }

    @app.post("/payments/transaction-hash-proof")
    def transaction_hash_proof(body: TransactionHashProofRequest) -> dict[str, Any]:
        pending = firewall.get_pending(body.request_id)
        if pending is None:
            raise HTTPException(status_code=404, detail="Unknown request_id.")
        token = stellar_adapter.build_transaction_hash_payment_token(
            requirement=pending.requirement,
            payer=body.payer,
            tx_hash=body.tx_hash,
            payment_reference=body.payment_reference,
        )
        return {
            "status": "proof_created",
            "verification_mode": "transaction_hash",
            "request_id": body.request_id,
            "payment_token": token,
            "authorization_header": f"Payment {token}",
            "tx_hash": body.tx_hash,
        }

    @app.post("/tools/summarise")
    def summarise(
        body: SummariseRequest,
        request: Request,
        authorization: str | None = Header(default=None, alias="Authorization"),
        payment_signature: str | None = Header(default=None, alias="PAYMENT-SIGNATURE"),
        x_request_id: str | None = Header(default=None, alias="X-Request-Id"),
    ) -> JSONResponse:
        def execute_tool() -> dict[str, Any]:
            sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", body.text) if part.strip()]
            summary = " ".join(sentences[: body.max_sentences]) if sentences else body.text.strip()
            return {"summary": summary, "sentence_count": min(len(sentences), body.max_sentences)}

        return _tool_payment_response(
            request=request,
            tool_name="summarise",
            amount=tool_prices["summarise"],
            client_id=body.client_id,
            risk_flag=body.risk_flag,
            payload=body.model_dump(mode="json"),
            execute_tool=execute_tool,
            authorization=authorization,
            payment_signature=payment_signature,
            request_id_header=x_request_id,
        )

    @app.post("/tools/fetch-url")
    def fetch_url(
        body: FetchUrlRequest,
        request: Request,
        authorization: str | None = Header(default=None, alias="Authorization"),
        payment_signature: str | None = Header(default=None, alias="PAYMENT-SIGNATURE"),
        x_request_id: str | None = Header(default=None, alias="X-Request-Id"),
    ) -> JSONResponse:
        def execute_tool() -> dict[str, Any]:
            normalized = body.url.strip()
            if not URL_PATTERN.match(normalized):
                raise HTTPException(status_code=422, detail="url must start with http:// or https://")
            return {
                "url": normalized,
                "host": normalized.split("/")[2],
                "safe4_note": "Demo mode returns URL metadata only; no remote fetch occurs.",
            }

        return _tool_payment_response(
            request=request,
            tool_name="fetch-url",
            amount=tool_prices["fetch-url"],
            client_id=body.client_id,
            risk_flag=body.risk_flag,
            payload=body.model_dump(mode="json"),
            execute_tool=execute_tool,
            authorization=authorization,
            payment_signature=payment_signature,
            request_id_header=x_request_id,
        )

    @app.post("/tools/risk-check")
    def risk_check(
        body: RiskCheckRequest,
        request: Request,
        authorization: str | None = Header(default=None, alias="Authorization"),
        payment_signature: str | None = Header(default=None, alias="PAYMENT-SIGNATURE"),
        x_request_id: str | None = Header(default=None, alias="X-Request-Id"),
    ) -> JSONResponse:
        def execute_tool() -> dict[str, Any]:
            lowered = body.subject.lower()
            score = 15
            flags: list[str] = []
            if "sanction" in lowered or "blocked" in lowered:
                score = 92
                flags.append("entity_keyword_match")
            elif "exchange" in lowered or "wallet" in lowered:
                score = 48
                flags.append("crypto_activity_detected")
            return {"subject": body.subject, "risk_score": score, "flags": flags}

        return _tool_payment_response(
            request=request,
            tool_name="risk-check",
            amount=tool_prices["risk-check"],
            client_id=body.client_id,
            risk_flag=body.risk_flag,
            payload=body.model_dump(mode="json"),
            execute_tool=execute_tool,
            authorization=authorization,
            payment_signature=payment_signature,
            request_id_header=x_request_id,
        )

    return app


app = build_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "apps.api.main:app",
        host=os.getenv("SAFE4_STELLAR_HOST", "0.0.0.0"),
        port=int(os.getenv("SAFE4_STELLAR_PORT", "8080")),
        proxy_headers=True,
        forwarded_allow_ips="*",
        reload=False,
    )
