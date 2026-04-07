# Public Proof Surface

This document records the public URLs and screenshot assets that back the
current hackathon submission state.

## Live Public URLs

Main toolkit API:

- `https://toolkit-api-production-a04c.up.railway.app`

x402 facilitator sidecar:

- `https://x402-facilitator-demo-production.up.railway.app/health`
- `https://x402-facilitator-demo-production.up.railway.app/supported`

MPP Charge sidecar:

- `https://mpp-charge-demo-production.up.railway.app/health`
- `https://mpp-charge-demo-production.up.railway.app/mpp/service`

Toolkit protocol inspection:

- `https://toolkit-api-production-a04c.up.railway.app/protocols/x402/facilitator`
- `https://toolkit-api-production-a04c.up.railway.app/payments/x402/guide`
- `https://toolkit-api-production-a04c.up.railway.app/protocols/mpp/charge`
- `https://toolkit-api-production-a04c.up.railway.app/protocols/mpp/charge/service`
- `https://toolkit-api-production-a04c.up.railway.app/payments/mpp/charge/guide`

## Captured Screenshots

- `docs/assets/public-demo-home.png`
  - public toolkit demo landing page
- `docs/assets/public-x402-status.png`
  - toolkit x402 facilitator inspection response
- `docs/assets/public-x402-sidecar.png`
  - x402 sidecar `/supported` response
- `docs/assets/public-mpp-status.png`
  - toolkit MPP Charge inspection response
- `docs/assets/public-mpp-sidecar-402.png`
  - public MPP sidecar `402` challenge with live `WWW-Authenticate` header

## What These Assets Prove

- the toolkit API is publicly reachable
- the submission still has a real Stellar testnet transaction-hash proof path
- x402 has a public facilitator inspection surface under our control
- MPP Charge has a public official-SDK sidecar returning a real `402` challenge

## Honest Limits

- the strongest live paid execution proof remains the `transaction_hash` flow
- x402 is still a preview flow, not a complete wallet-integrated settlement path
- MPP Charge is still a preview/proof surface rather than a full paid retry flow
