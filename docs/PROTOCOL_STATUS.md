# Protocol Status

This repo is intentionally narrow. It is focused on one clear story:

- paid AI tools on Stellar
- payment proof bound to a specific request
- policy enforcement before execution
- receipt and audit output after execution

## Current State

### Real and working now

- request-bound `402` payment challenge flow
- `Authorization: Payment` retry flow
- real Stellar testnet transaction-hash verification via Horizon
- receipt and append-only audit output
- visible policy controls:
  - max spend per request
  - deny on high risk
  - simple rate limit

### x402 status

Status:
- `preview`

Implemented now:
- `PAYMENT-REQUIRED` response header
- `PAYMENT-SIGNATURE` preview retry header
- `PAYMENT-RESPONSE` success header
- request-bound payment requirement data
- payment + policy + receipt flow in one middleware boundary

Not yet implemented:
- Stellar facilitator integration
- auth-entry-signing client flow
- `PAYMENT-SIGNATURE` retry format
- production-grade x402 settlement path

### MPP Charge status

Status:
- `planned`

Implemented now:
- the repo already uses a payment-auth shaped request/retry model
- the current request binding and receipt model is compatible with a later MPP path

Not yet implemented:
- `@stellar/mpp` charge flow
- pull credential mode
- push/hash credential mode through the MPP SDK
- sponsored-fee flow

### MPP Session status

Status:
- `planned`

Not yet implemented:
- payment channels
- off-chain cumulative payment commitments
- channel settlement receipts

## Recommended Demo Path

### Primary live demo

- real Stellar testnet `transaction_hash` mode

This is the strongest currently implemented proof path in the repo.

### Reliable fallback

- mock settlement mode

This is still useful for live demos where external network conditions are risky.

## Why The Repo Still Matters Before Full Protocol Coverage

The core claim is already real:

- the tool does not execute just because payment exists
- payment proof must match the original request
- policy still has veto power
- successful calls return receipts and audit output

That is the main Safe4 differentiation, regardless of which Stellar payment rail
is used underneath.
