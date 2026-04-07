# x402 Facilitator Demo

This repo contains a small x402 facilitator demo server that matches the
toolkit's expected endpoint shape:

- `GET /supported`
- `POST /verify`
- `POST /settle`

Files:
- `apps/x402_facilitator_demo/server.mjs`
- `apps/x402_facilitator_demo/package.json`
- `apps/x402_facilitator_demo/Dockerfile`
- `.env.x402.example`
- `scripts/run_x402_facilitator_demo.py`

## What It Is

This is a controlled compatibility sidecar for the hackathon demo.

It is not presented as the OpenZeppelin Relayer plugin itself. It exists to
make the `x402_facilitator_preview` path runnable under our control, while
keeping the public toolkit app honest about what is preview-only.

## Local Quickstart

Copy:

```powershell
Copy-Item .env.x402.example .env.x402
```

Start the facilitator sidecar:

```powershell
npm run x402:facilitator
```

Start the toolkit API in facilitator preview mode:

```powershell
$env:SAFE4_STELLAR_VERIFICATION_MODE="x402_facilitator_preview"
$env:SAFE4_X402_FACILITATOR_URL="http://127.0.0.1:3200"
python -m uvicorn apps.api.main:app --host 0.0.0.0 --port 8080
```

Run the demo:

```powershell
python scripts/run_x402_facilitator_demo.py
```

## Public Sidecar

The same sidecar is also deployable as a standalone service:

- `https://x402-facilitator-demo-production.up.railway.app/health`
- `https://x402-facilitator-demo-production.up.railway.app/supported`

## Why It Exists

This gives the submission a real end-to-end x402 preview path today, while
still leaving room for:

- hosted OpenZeppelin Channels
- self-hosted OpenZeppelin Relayer plugin

Those remain the production-facing next steps. This sidecar is the controlled
demo implementation.

## Verified Locally

The local demo path has been exercised successfully with:

- local facilitator sidecar on `http://127.0.0.1:3200`
- toolkit API on `http://127.0.0.1:8091`
- `SAFE4_STELLAR_VERIFICATION_MODE=x402_facilitator_preview`

Observed result:

- `402` challenge returned
- facilitator-backed retry returned `AUTHORIZED`
- receipt `payment_mode` was `x402_facilitator`

## Public Inspection Path

The public toolkit deploy still uses `transaction_hash` as its primary proof
mode, but its x402 inspection endpoints now resolve against the public
facilitator sidecar:

- `https://toolkit-api-production-a04c.up.railway.app/protocols/x402/facilitator`
- `https://toolkit-api-production-a04c.up.railway.app/payments/x402/guide`
