# Architecture

## System Shape

- `apps/api/main.py`
  - FastAPI composition root and HTTP surface
- `packages/middleware/firewall.py`
  - request binding, `402` issuance, payment verification handoff, receipts, audit
- `packages/stellar/adapter.py`
  - Stellar payment requirement generation and proof verification
- `packages/protocols/x402.py`
  - preview x402 header generation and optional facilitator client
- `packages/policies/engine.py`
  - explicit policy checks and rate limiting

## End-to-End Flow

1. Client calls a paid tool endpoint.
2. If no payment proof is present, Safe4 returns `402` and a request-bound
   Stellar payment requirement.
3. Client settles the payment on Stellar testnet or uses the mock settlement path.
4. Client retries the same request with payment proof bound to the request ID.
5. Safe4 verifies the proof, enforces policy, and only then executes the tool.
6. Safe4 returns tool output with receipt and audit records.

## Trust Boundary

- payment proof is necessary but not sufficient
- policy sits between verified payment and tool execution
- tool handlers are only called after both checks pass

## Current Limits

- default payment verification mode is mock for demo reliability
- real transaction-hash verification is implemented, but the repo still relies on an external wallet or manual client to submit the Stellar payment
- audit is append-only but lightweight, not a full forensic subsystem
- policy is intentionally small and visible
- x402 support is currently a preview wire surface, not a full facilitator integration
- the repo now includes an optional facilitator-aware x402 preview seam, but not a complete wallet flow
- MPP is not implemented yet

## What Makes The Demo Easy To Evaluate

- only three paid tools
- one visible policy layer
- one receipt path
- one simple audit trail
- two proof modes, clearly labeled
