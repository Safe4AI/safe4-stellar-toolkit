# x402 Relayer Demo

This repo now includes a small scaffold for a self-hosted OpenZeppelin Relayer
x402 facilitator path.

Files:
- `apps/x402_relayer_demo/config/plugin.example.json`
- `apps/x402_relayer_demo/plugins/x402-facilitator/index.ts.example`
- `scripts/probe_x402_facilitator.py`

## What It Is

This is not a full Relayer distribution inside the toolkit repo.

It is:
- a concrete plugin wrapper example
- a minimal plugin config example
- a probe script for `/supported`

The goal is to make the self-hosted facilitator route operationally clear for
reviewers and for local testnet setup.

## Expected Relayer Base URL

Point the toolkit at:

```text
http://localhost:8080/api/v1/plugins/x402-facilitator/call
```

The toolkit appends:
- `/supported`
- `/verify`
- `/settle`

to that base URL.

## Toolkit Environment

```text
SAFE4_STELLAR_VERIFICATION_MODE=x402_facilitator_preview
SAFE4_X402_FACILITATOR_URL=http://localhost:8080/api/v1/plugins/x402-facilitator/call
SAFE4_X402_FACILITATOR_API_KEY=<OPTIONAL_RELAYER_API_KEY>
```

If your self-hosted Relayer protects plugin routes with bearer auth, set
`SAFE4_X402_FACILITATOR_API_KEY` to the Relayer API key. If your local setup
does not require auth, leave it blank.

## Probe The Facilitator

```powershell
python scripts/probe_x402_facilitator.py `
  --base-url http://localhost:8080/api/v1/plugins/x402-facilitator/call `
  --api-key <OPTIONAL_RELAYER_API_KEY>
```

## Why This Matters

This removes the false implication that Safe4’s x402 path depends on the hosted
OpenZeppelin Channels service specifically.

The real dependency is simpler:
- an x402-capable client or wallet
- a facilitator endpoint
- optionally auth for that endpoint
