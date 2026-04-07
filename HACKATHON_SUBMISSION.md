# Hackathon Submission

## Problem

AI agents can already call tools and trigger payments, but payment success alone
is not a sufficient safety model. Paid tool calls also need policy controls,
request binding, and receipts so developers can understand what was executed and
why.

## Solution

Safe4 Stellar Toolkit is Stripe-like safety middleware for paid AI tools on
Stellar. A tool call without payment receives a `402` payment requirement. After
payment proof is supplied, the server verifies the payment context, enforces
policy, and returns a receipt-backed tool response.

## Why Agent Payments Need Safety

- agents can overspend or call tools too quickly
- payment success does not prove the request is safe or intended
- developers need receipts and audit records for every monetized tool call

## Why Stellar

- Stellar is pushing agentic payment rails such as x402 and MPP
- the ecosystem is focused on fast, programmable, HTTP-native payment flows
- Stellar testnet makes it practical to demo paid API workflows quickly

## What Is Live

- paid tool middleware
- visible policy enforcement
- receipt + audit output
- mock settlement flow for fast demos
- real transaction-hash verification against Stellar Horizon data
- preview x402 wire/header surface
- optional facilitator-aware x402 preview seam
- MPP Charge preview guide and challenge surface
- local Node sidecar using the official `@stellar/mpp` SDK path
- client-side testnet helper scripts to create/fund accounts and execute the real demo flow
- thin Stellar adapter with request-bound payment requirements
- validated locally against a real Stellar testnet XLM payment path

## What Is Deliberately Out Of Scope

- MCP governance
- AP2
- HITL approvals
- anomaly scoring
- enterprise operational scaffolding

## Demo Positioning

The repo supports two proof paths:

- `mock`
  - fastest and most reliable for a live hackathon demo
- `transaction_hash`
  - stronger submission claim because the verifier checks a real Stellar testnet transaction against the request requirements

These modes are now enforced separately. Running in `transaction_hash` mode does
not allow mock settlement as a silent fallback.

Protocol status:
- real proof path today: `transaction_hash`
- x402: `preview`
- MPP Charge: `preview`
- MPP Session: `planned`

The x402 preview currently includes:
- `PAYMENT-REQUIRED`
- `PAYMENT-SIGNATURE`
- `PAYMENT-RESPONSE`
- facilitator status and guide endpoints for judge inspection
- support for either a hosted facilitator or a self-hosted OpenZeppelin Relayer plugin base URL
- local x402 facilitator demo sidecar for a controlled end-to-end preview flow
- locally verified end-to-end facilitator authorize flow
- public facilitator sidecar deployment under our control
- public toolkit inspection endpoint that resolves against that sidecar
- public MPP Charge sidecar using the official Stellar SDK path
- public toolkit inspection endpoint that resolves against that sidecar

## Evidence

- browser screenshots:
  - `docs/assets/demo-home.png`
  - `docs/assets/demo-payment-required.png`
  - `docs/assets/demo-authorized.png`
- public proof screenshots:
  - `docs/assets/public-demo-home.png`
  - `docs/assets/public-x402-status.png`
  - `docs/assets/public-x402-sidecar.png`
  - `docs/assets/public-mpp-status.png`
  - `docs/assets/public-mpp-sidecar-402.png`
- verified testnet note:
  - [`docs/TESTNET_VERIFICATION.md`](docs/TESTNET_VERIFICATION.md)
- public proof index:
  - [`docs/PUBLIC_PROOF.md`](docs/PUBLIC_PROOF.md)
- submission copy:
  - [`docs/DORAHACKS_SUBMISSION_COPY.md`](docs/DORAHACKS_SUBMISSION_COPY.md)
- final narration:
  - [`docs/FINAL_DEMO_NARRATION.md`](docs/FINAL_DEMO_NARRATION.md)
- public x402 facilitator inspection:
  - `https://toolkit-api-production-a04c.up.railway.app/protocols/x402/facilitator`
- public MPP Charge inspection:
  - `https://toolkit-api-production-a04c.up.railway.app/protocols/mpp/charge`
