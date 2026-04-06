# Hackathon Submission

## Problem

AI agents can already call tools and trigger payments, but payment success alone
is not a sufficient safety model. Paid tool calls also need policy controls,
request binding, and receipts so developers can understand what was executed and
why.

## Solution

Safe4 Stellar Toolkit is Stripe-like safety middleware for paid AI tools on
Stellar. A tool call without payment receives a `402` payment requirement. After
payment proof is supplied, Safe4 verifies the payment context, enforces policy,
and returns a receipt-backed tool response.

## Why Agent Payments Need Safety

- agents can overspend or call tools too quickly
- payment success does not prove the request is safe or intended
- developers need receipts and audit records for every monetized tool call

## Why Stellar

- Stellar is pushing agentic payment rails such as x402 and MPP
- the ecosystem is focused on fast, programmable, HTTP-native payment flows
- Stellar testnet makes it practical to demo paid API workflows quickly

## What Is Live vs Adapted

### Live in this repo

- paid tool middleware
- visible policy enforcement
- receipt + audit output
- mock settlement flow for fast demos
- real transaction-hash verification against Stellar Horizon data
- client-side testnet helper scripts to create/fund accounts and execute the real demo flow
- thin Stellar adapter with request-bound payment requirements
- validated locally against a real Stellar testnet XLM payment path

### Adapted from Safe4

- the core `402 -> verify -> policy -> execute -> receipt` pattern
- the idea that payment proof is necessary but not sufficient
- explicit policy gating and auditability as first-class concerns

### Not Ported

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
  - stronger submission claim because Safe4 validates a real Stellar testnet transaction against the request requirements
