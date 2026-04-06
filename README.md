# Safe4 Stellar Toolkit

Safe4 Stellar Toolkit is a minimal, open-source hackathon extraction of Safe4:
Stripe-like safety middleware for paid AI tools on Stellar. Every tool call is
payment-aware, policy-aware, and receipt-backed.

## What It Does

- protects paid AI tool endpoints with a `402` payment requirement
- binds payment proof to a specific tool call and request ID
- enforces explicit policy before tool execution
- returns a Safe4 receipt and append-only audit record with every decision
- adapts Safe4's payment-firewall model to a Stellar-first demo flow

## Why Stellar

Stellar is actively investing in agentic payment rails such as x402 on Stellar
and MPP. That makes it a strong venue for showing that paid AI tools should not
execute on payment alone: they also need policy checks, request binding, and
receipts.

## What Is Implemented

- three paid tool endpoints:
  - `POST /tools/summarise`
  - `POST /tools/fetch-url`
  - `POST /tools/risk-check`
- a thin Stellar payment adapter
- a reliable mock settlement flow for hackathon demos
- a real transaction-hash verification seam for future testnet hardening
- visible policy controls:
  - max spend per request
  - deny on high risk flag
  - simple rate limiting
- receipt and audit output
- a tiny browser demo at `GET /demo`

## Quickstart

Requirements:
- Python 3.13 recommended

Install:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Run:

```powershell
python -m uvicorn apps.api.main:app --host 0.0.0.0 --port 8080
```

Or:

```powershell
python apps/api/main.py
```

Test:

```powershell
python -m unittest -q
```

## Demo Flow

1. Call a paid tool with no payment proof.
2. Receive `402` plus a Stellar payment requirement.
3. Settle the challenge through the demo settlement path.
4. Retry the exact same tool call with `Authorization: Payment <token>`.
5. Safe4 verifies the payment context and runs policy checks.
6. Tool output, receipt, and audit record are returned.

## Primary Endpoints

- `GET /health`
- `GET /tools`
- `POST /payments/mock/settle`
- `POST /tools/summarise`
- `POST /tools/fetch-url`
- `POST /tools/risk-check`
- `GET /audit/entries`
- `GET /demo`

## Repo Layout

- `apps/api/`
  - FastAPI app and demo endpoints
- `apps/demo/`
  - lightweight demo UI
- `packages/middleware/`
  - Safe4 request binding, receipts, audit, and payment-gating flow
- `packages/stellar/`
  - thin Stellar adapter
- `packages/policies/`
  - explicit policy engine and rate limiting
- `docs/`
  - hackathon packaging docs

## Reading Order

1. `README.md`
2. `HACKATHON_SUBMISSION.md`
3. `STELLAR_ADAPTATION.md`
4. `DEMO_SCRIPT.md`
5. `apps/api/main.py`
6. `packages/middleware/firewall.py`
7. `packages/stellar/adapter.py`
