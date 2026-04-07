# Demo Script

## Demo Goal

Show that developers can monetize AI tools on Stellar safely: payment is
required, policy is enforced, and receipts are returned.

Recommended protocol framing for the demo:

- primary live proof path: real Stellar testnet `transaction_hash`
- x402: preview header surface plus optional facilitator status endpoints
- MPP Charge: preview guide and challenge surface
- MPP Session: planned, not implemented

Preview x402 retry note:

- the server currently accepts both:
  - `Authorization: Payment <token>`
  - `PAYMENT-SIGNATURE: <token>`
- preview guide endpoint:
  - `GET /payments/x402/guide`

## Start The API

```powershell
python -m uvicorn apps.api.main:app --host 0.0.0.0 --port 8080
```

For the cleanest real testnet demo, configure:

```powershell
$env:SAFE4_STELLAR_VERIFICATION_MODE="transaction_hash"
$env:SAFE4_STELLAR_ASSET_CODE="XLM"
$env:SAFE4_STELLAR_ASSET_ISSUER=""
$env:SAFE4_STELLAR_DESTINATION="<FUNDED_TESTNET_RECEIVER>"
```

## Option A: Browser Demo

Open:

```text
http://127.0.0.1:8080/demo
```

Click:
1. Request payment challenge
2. Mock settle
3. Retry paid call

Reference screenshots:
- `docs/assets/demo-home.png`
- `docs/assets/demo-payment-required.png`
- `docs/assets/demo-authorized.png`

## Option B: Curl Demo

### 1. Request a paid tool

```powershell
curl -X POST http://127.0.0.1:8080/tools/summarise ^
  -H "Content-Type: application/json" ^
  -d "{\"client_id\":\"demo-agent\",\"text\":\"This middleware requires payment proof, applies policy checks, and returns a receipt-backed response.\",\"max_sentences\":1,\"risk_flag\":\"low\"}"
```

Capture `request_id` from the `402` response.

### 2A. Mock settle the payment

```powershell
curl -X POST http://127.0.0.1:8080/payments/mock/settle ^
  -H "Content-Type: application/json" ^
  -d "{\"request_id\":\"<REQUEST_ID>\",\"payer\":\"GDEMO_PAYER_ACCOUNT\"}"
```

Capture `payment_token`.

### 2B. Real Stellar testnet payment path

Create and fund a payer account if you do not already have one:

```powershell
python scripts/create_testnet_account.py
```

Then run the end-to-end testnet demo:

```powershell
python scripts/run_testnet_payment_demo.py --source-secret <FUNDED_TESTNET_SECRET>
```

This script will:
1. request a Safe4 paid-tool challenge
2. submit the matching Stellar testnet payment
3. exchange the tx hash for a payment token
4. retry the tool call and print the authorized result

### 2C. Optional x402 facilitator preview

If `SAFE4_STELLAR_VERIFICATION_MODE=x402_facilitator_preview`, inspect:

```powershell
curl http://127.0.0.1:8080/protocols/x402/facilitator
curl http://127.0.0.1:8080/payments/x402/guide
```

This is the judge-friendly way to show that the repo already has a facilitator-aware
x402 seam without overclaiming complete wallet integration.

### 2D. Optional MPP Charge preview

If `SAFE4_STELLAR_VERIFICATION_MODE=mpp_charge_preview`, inspect:

```powershell
curl http://127.0.0.1:8080/protocols/mpp/charge
curl http://127.0.0.1:8080/payments/mpp/charge/guide
```

Then request a paid tool and show that the `402` response now carries:
- `X-Payment-Protocol: mpp-charge-preview`
- `MPP-CHARGE-REQUIRED`

### 2E. Optional real local MPP Charge sidecar

If you want to show a real official-SDK MPP path locally:

```powershell
npm install
Copy-Item .env.mpp.example .env.mpp
npm run mpp:server
npm run mpp:client
```

This sidecar is local-only today. It exists to demonstrate a real `@stellar/mpp`
route without changing the main deployed Python app.

### 3. Retry the same tool with payment proof

```powershell
curl -X POST http://127.0.0.1:8080/tools/summarise ^
  -H "Content-Type: application/json" ^
  -H "X-Request-Id: <REQUEST_ID>" ^
  -H "Authorization: Payment <PAYMENT_TOKEN>" ^
  -d "{\"client_id\":\"demo-agent\",\"text\":\"This middleware requires payment proof, applies policy checks, and returns a receipt-backed response.\",\"max_sentences\":1,\"risk_flag\":\"low\"}"
```

### 4. Show audit visibility

```powershell
curl http://127.0.0.1:8080/audit/entries
```

## Fallback

If live Stellar testnet verification is not configured, use the mock settlement
path above, but only after switching `SAFE4_STELLAR_VERIFICATION_MODE=mock`.
The repo does not accept mock settlement while running in `transaction_hash`
mode.
