# MPP Charge Demo

This repo now contains a small Node sidecar that follows the official Stellar
MPP Charge model more directly than the Python API can.

Files:
- `apps/mpp_demo/server.mjs`
- `apps/mpp_demo/client.mjs`
- `.env.mpp.example`

## What It Is

- a narrow MPP Charge demo server using:
  - `express`
  - `mppx/server`
  - `@stellar/mpp/charge/server`
- a matching client using:
  - `mppx/client`
  - `@stellar/mpp/charge/client`

This is intentionally separate from the main Python API. The Python app remains
the primary hackathon submission surface and the live Railway deploy. The Node
sidecar exists to show a real MPP path using the official Stellar SDKs.

## Why It Exists

The official Stellar MPP Charge guide is Node-first. A Python-only reimplementation
would be weaker and easier to challenge in review. This sidecar keeps the claim
honest:

- Safe4’s main demo is Python and payment-firewall oriented
- the repo also includes a real MPP Charge path using the official SDKs

## Quickstart

Install dependencies:

```powershell
npm install
```

Copy the example env file:

```powershell
Copy-Item .env.mpp.example .env.mpp
```

You need:
- `STELLAR_RECIPIENT`
- `MPP_SECRET_KEY`
- a funded testnet wallet with testnet USDC for the client:
  - `STELLAR_SECRET`

Start the demo server:

```powershell
npm run mpp:server
```

In another terminal, run the client:

```powershell
npm run mpp:client
```

## Current Limits

- local/demo oriented
- not deployed on Railway today
- defaults to testnet USDC SAC
- intended to strengthen the submission technically, not replace the primary app
