# DoraHacks Submission Copy

Use this as the copy-paste source for the hackathon submission form. Edit only
for field length constraints.

## Project Name

`Safe4 Stellar Toolkit`

## Tagline

`Stripe-like safety middleware for paid AI tools on Stellar`

## One-Sentence Summary

Safe4 makes paid AI tools on Stellar payment-aware, policy-aware, and
receipt-backed.

## Short Description

Safe4 Stellar Toolkit is middleware for agentic commerce. A paid tool call does
not execute just because payment exists. The server first returns a `402`
payment requirement, then checks payment proof against the original request,
applies policy, and only then returns the tool result with a receipt and audit
record.

## Problem

AI agents can already call tools and trigger payments, but payment success
alone is not a safe execution model. Paid tool calls also need request binding,
policy checks, and auditability so developers can understand what was executed
and why.

## Solution

Safe4 sits between a tool call and execution. It issues a Stellar payment
challenge, verifies payment context, enforces policy, and returns receipts.
This turns paid AI tools into controlled middleware instead of raw paywalls.

## Why This Matters

- agents should not unlock tools on payment alone
- payment needs to be tied to the original request
- developers need receipts and audit records for monetized agent workflows
- Stellar is a strong fit for low-friction internet-native payment flows

## What Is Live

- real Stellar testnet transaction-hash verification
- public x402 facilitator inspection path and sidecar
- public MPP Charge sidecar using the official Stellar SDK path
- explicit policy controls:
  - max spend per request
  - deny on high risk flag
  - simple rate limiting
- receipts and append-only audit output

## What Makes It Different

- the product focuses on the safety layer, not only the payment rail
- payment proof is bound to a specific request before execution
- policy still has veto power after payment
- the repo demonstrates one core live path plus public x402 and MPP proof surfaces

## Protocol Positioning

- strongest live paid execution proof:
  - Stellar testnet `transaction_hash`
- x402:
  - public facilitator inspection and locally verified preview flow
- MPP Charge:
  - public official-SDK sidecar returning a real `402` challenge
- MPP Session:
  - planned, not claimed

## GitHub Repo

`https://github.com/Safe4AI/safe4-stellar-toolkit`

## Live Demo URLs

- main toolkit API:
  - `https://toolkit-api-production-a04c.up.railway.app`
- x402 facilitator sidecar:
  - `https://x402-facilitator-demo-production.up.railway.app`
- MPP Charge sidecar:
  - `https://mpp-charge-demo-production.up.railway.app`

## Best Proof URLs

- `https://toolkit-api-production-a04c.up.railway.app/protocols/x402/facilitator`
- `https://toolkit-api-production-a04c.up.railway.app/protocols/mpp/charge`
- `https://mpp-charge-demo-production.up.railway.app/mpp/service`

## Demo Video Framing

The best demo framing is:

1. show a real testnet-backed paid tool flow
2. show the public x402 sidecar under our control
3. show the public MPP sidecar returning a real `402` challenge
4. close on the idea that Safe4 is the safety layer between agent decisions and payment execution
