# Stellar Adaptation

## What This Repo Focuses On

- a thin Stellar-specific payment requirement format
- mock settlement for reliable hackathon demos
- a real transaction-hash verification path for testnet use
- an optional facilitator-aware x402 preview seam
- an optional MPP Charge preview seam
- a small repo focused only on paid AI tool middleware

## Real vs Mocked

### Real

- the request lifecycle and payment binding are real application behavior
- tool calls, policy enforcement, receipts, and audit records are real
- the transaction-hash verifier queries Horizon and checks:
  - transaction success
  - memo binding
  - expiry
  - destination
  - asset
  - amount
  - payer binding
- the repo now includes client-side helper scripts for:
  - testnet account funding
  - real paid-tool demo execution
- the real path has been exercised locally against a Stellar testnet XLM payment

### Mocked Fallback

- the default demo settlement path is mock by design
- the mock flow produces a signed payment token rather than submitting an onchain payment

### Preview x402 Layer

- the repo can now expose facilitator-aware x402 payment requirements and status endpoints
- it does not yet claim a full auth-entry-signing wallet flow
- this keeps the public submission honest while still showing protocol direction

### Preview MPP Charge Layer

- the repo can now expose an MPP Charge guide and preview challenge framing
- it does not yet claim a live `@stellar/mpp` verification backend
- this keeps MPP visible in the submission without overstating what is shipped

## Why This Tradeoff

Hackathon demos need to be reliable in under two minutes. The mock flow keeps
the story crisp while preserving the main control point:
payment alone does not unlock execution; verified payment plus policy does.

## Remaining Hardening

- support richer Stellar payment operation variants beyond the current payment-focused checks
- broaden payment asset coverage beyond the current XLM-first demo path
