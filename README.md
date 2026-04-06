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
- a real Stellar transaction-hash verification path against Horizon data
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

For the simplest real testnet demo, keep:

```powershell
SAFE4_STELLAR_ASSET_CODE=XLM
SAFE4_STELLAR_ASSET_ISSUER=
```

and set `SAFE4_STELLAR_DESTINATION` to a funded Stellar testnet receiving account.

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
python -m unittest discover -s tests -q
```

Optional screenshot capture for the submission:

```powershell
npm install
npm run capture:screenshots
```

## Real Testnet Helpers

Create and fund a payer account:

```powershell
python scripts/create_testnet_account.py
```

Run the real end-to-end testnet demo:

```powershell
python scripts/run_testnet_payment_demo.py --source-secret <STELLAR_SECRET>
```

## Demo Flow

1. Call a paid tool with no payment proof.
2. Receive `402` plus a Stellar payment requirement.
3. Either settle through the mock path or pay on Stellar testnet and create a transaction-hash proof.
4. Retry the exact same tool call with `Authorization: Payment <token>` and the original `X-Request-Id`.
5. Safe4 verifies the payment context and runs policy checks.
6. Tool output, receipt, and audit record are returned.

## Primary Endpoints

- `GET /health`
- `GET /tools`
- `POST /payments/mock/settle`
- `POST /payments/transaction-hash-proof`
- `POST /tools/summarise`
- `POST /tools/fetch-url`
- `POST /tools/risk-check`
- `GET /audit/entries`
- `GET /demo`

## Real Testnet Path

Set:

```powershell
$env:SAFE4_STELLAR_VERIFICATION_MODE="transaction_hash"
```

Then:
1. call a paid tool and capture the returned `request_id`, destination, amount, asset, and memo
2. submit a matching Stellar testnet payment with that memo
3. exchange the tx hash for a Safe4 payment token at `POST /payments/transaction-hash-proof`
4. retry the tool call with `Authorization: Payment <token>` and `X-Request-Id`

Safe4 verifies:
- transaction success
- memo binding
- challenge expiry
- destination account
- asset code and issuer
- paid amount
- payer binding

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
- `scripts/`
  - testnet account setup and real payment demo helpers

## Reading Order

1. `README.md`
2. `HACKATHON_SUBMISSION.md`
3. `STELLAR_ADAPTATION.md`
4. `DEMO_SCRIPT.md`
5. `apps/api/main.py`
6. `packages/middleware/firewall.py`
7. `packages/stellar/adapter.py`
