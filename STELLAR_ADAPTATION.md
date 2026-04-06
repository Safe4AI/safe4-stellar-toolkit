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
- the transaction-hash verifier is a real seam that can query Horizon

### Mocked

- the default demo settlement path is mock by design
- the mock flow produces a signed payment token rather than submitting an onchain payment

## Why This Tradeoff

Hackathon demos need to be reliable in under two minutes. The mock flow keeps
the story crisp while preserving the exact control point Safe4 cares about:
payment alone does not unlock execution; verified payment plus policy does.

## Next Step To Harden

- wire the `transaction_hash` mode to a real Stellar testnet payment flow
- verify destination, asset, amount, and memo against Horizon operation data
- add a real client path that signs and submits Stellar testnet payments
