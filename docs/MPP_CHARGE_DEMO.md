# MPP Charge Demo

This repo contains a small Node sidecar that follows the official Stellar MPP
Charge model more directly than the Python API can.

Files:

- `apps/mpp_demo/server.mjs`
- `apps/mpp_demo/client.mjs`
- `apps/mpp_demo/package.json`
- `apps/mpp_demo/Dockerfile`
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

The official Stellar MPP Charge guide is Node-first. A Python-only
reimplementation would be weaker and easier to challenge in review. This sidecar
keeps the claim honest:

- the main Safe4 demo is payment-firewall oriented
- the repo also includes a real MPP Charge path using the official SDKs

## Local Quickstart

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

## Public Sidecar

The same server is now deployed publicly:

- `https://mpp-charge-demo-production.up.railway.app/health`
- `https://mpp-charge-demo-production.up.railway.app/mpp/service`

The `/mpp/service` endpoint returns a real `402` challenge from the official
MPP SDK path.

## Public Inspection Path

The public toolkit deploy still uses `transaction_hash` as its primary proof
mode, but its MPP inspection endpoints now resolve against the public MPP
sidecar:

- `https://toolkit-api-production-a04c.up.railway.app/protocols/mpp/charge`
- `https://toolkit-api-production-a04c.up.railway.app/protocols/mpp/charge/service`

## Current Limits

- preview-oriented
- public sidecar proves the challenge path, not full paid settlement
- defaults to testnet USDC SAC
- intended to strengthen the submission technically, not replace the primary app
