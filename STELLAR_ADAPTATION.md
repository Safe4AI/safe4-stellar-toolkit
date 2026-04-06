# Stellar Adaptation

## What Came From Safe4

- the `payment required -> verify proof -> enforce policy -> execute -> receipt`
  flow
- the idea that payment proof must be bound to a specific request
- explicit policy controls as part of the authorization path
- receipt + audit output as first-class outputs of the system

## What Is New Here

- a thin Stellar-specific payment requirement format
- mock settlement for reliable hackathon demos
- a real transaction-hash verification seam for future testnet use
- a much smaller repo focused only on paid AI tool middleware

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

### Mocked Fallback

- the default demo settlement path is mock by design
- the mock flow produces a signed payment token rather than submitting an onchain payment

## Why This Tradeoff

Hackathon demos need to be reliable in under two minutes. The mock flow keeps
the story crisp while preserving the exact control point Safe4 cares about:
payment alone does not unlock execution; verified payment plus policy does.

## Remaining Hardening

- add a first-class client script that constructs and submits the Stellar testnet payment
- support richer Stellar payment operation variants beyond the current payment-focused checks
- capture a real testnet walkthrough artifact for the public submission
