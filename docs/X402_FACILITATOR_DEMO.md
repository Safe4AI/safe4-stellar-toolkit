# x402 Facilitator Demo

This repo now contains a local x402 facilitator demo server that matches the
toolkit’s expected endpoint shape:

- `GET /supported`
- `POST /verify`
- `POST /settle`

Files:
- `apps/x402_facilitator_demo/server.mjs`
- `.env.x402.example`
- `scripts/run_x402_facilitator_demo.py`

## What It Is

This is a local compatibility sidecar for the hackathon demo.

It is not presented as the OpenZeppelin Relayer plugin itself. It exists to make
the `x402_facilitator_preview` path runnable under our control.

## Quickstart

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

## Why It Exists

This gives the submission a real end-to-end x402 preview path today, while still
leaving room for:
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
