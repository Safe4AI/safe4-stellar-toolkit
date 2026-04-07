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
- optional facilitator-aware preview seam
- public facilitator inspection path wired to a live sidecar we control
- payment + policy + receipt flow in one middleware boundary

Not yet implemented:
- auth-entry-signing client flow
- production-grade x402 settlement path
- full end-to-end wallet integration on the public demo deploy

Preview visibility endpoints:
- `GET /protocols/x402/facilitator`
- `GET /payments/x402/guide`

Public inspection URLs:
- `https://toolkit-api-production-a04c.up.railway.app/protocols/x402/facilitator`
- `https://x402-facilitator-demo-production.up.railway.app/supported`

### MPP Charge status

Status:
- `preview`

Implemented now:
- the repo already uses a payment-auth shaped request/retry model
- the current request binding and receipt model is compatible with a later MPP path
- `GET /protocols/mpp/charge`
- `GET /protocols/mpp/charge/service`
- `GET /payments/mpp/charge/guide`
- `mpp_charge_preview` challenge framing
- local Node sidecar demo based on `@stellar/mpp`
- public Node sidecar demo returning a real MPP `402` challenge

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

### Optional x402 preview path

- `x402_facilitator_preview`

Use this when you have:
- an x402-capable wallet or client that can produce `PAYMENT-SIGNATURE`
- a configured facilitator URL
- optionally an API key for facilitator-backed verify and settle

Facilitator deployment options:
- hosted OpenZeppelin Channels
- self-hosted OpenZeppelin Relayer x402 plugin

Self-hosted demo scaffold:
- [`docs/X402_RELAYER_DEMO.md`](X402_RELAYER_DEMO.md)

### Optional MPP Charge preview path

- `mpp_charge_preview`

Use this when you want to show:
- Safe4 can frame a one-time MPP charge challenge
- request-bound payment metadata for a future `@stellar/mpp` flow
- a clean path toward pull, push, and sponsored-fee support without claiming it is done

Public inspection URLs:
- `https://toolkit-api-production-a04c.up.railway.app/protocols/mpp/charge`
- `https://toolkit-api-production-a04c.up.railway.app/protocols/mpp/charge/service`
- `https://mpp-charge-demo-production.up.railway.app/health`
- `https://mpp-charge-demo-production.up.railway.app/mpp/service`

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

Public proof reference:
- [`PUBLIC_PROOF.md`](PUBLIC_PROOF.md)
