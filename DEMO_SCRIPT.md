# Demo Script

## Demo Goal

Show that Safe4 lets developers monetize AI tools on Stellar safely: payment is
required, policy is enforced, and receipts are returned.

## Start The API

```powershell
python -m uvicorn apps.api.main:app --host 0.0.0.0 --port 8080
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

## Option B: Curl Demo

### 1. Request a paid tool

```powershell
curl -X POST http://127.0.0.1:8080/tools/summarise ^
  -H "Content-Type: application/json" ^
  -d "{\"client_id\":\"demo-agent\",\"text\":\"Safe4 stands between agent intent and payment execution. It verifies payment, enforces policy, and returns a receipt.\",\"max_sentences\":1,\"risk_flag\":\"low\"}"
```

Capture `request_id` from the `402` response.

### 2. Mock settle the payment

```powershell
curl -X POST http://127.0.0.1:8080/payments/mock/settle ^
  -H "Content-Type: application/json" ^
  -d "{\"request_id\":\"<REQUEST_ID>\",\"payer\":\"GDEMO_PAYER_ACCOUNT\"}"
```

Capture `payment_token`.

### 3. Retry the same tool with payment proof

```powershell
curl -X POST http://127.0.0.1:8080/tools/summarise ^
  -H "Content-Type: application/json" ^
  -H "X-Request-Id: <REQUEST_ID>" ^
  -H "Authorization: Payment <PAYMENT_TOKEN>" ^
  -d "{\"client_id\":\"demo-agent\",\"text\":\"Safe4 stands between agent intent and payment execution. It verifies payment, enforces policy, and returns a receipt.\",\"max_sentences\":1,\"risk_flag\":\"low\"}"
```

### 4. Show audit visibility

```powershell
curl http://127.0.0.1:8080/audit/entries
```

## Fallback

If live Stellar testnet verification is not configured, use the mock settlement
path above. The repo labels that clearly and keeps the Stellar transaction-hash
verification seam separate.
