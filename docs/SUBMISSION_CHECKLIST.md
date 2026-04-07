# Submission Checklist

Use this before submitting or recording the final demo.

## Repo

- GitHub repo is public and current
- `README.md` matches the live deployment
- `HACKATHON_SUBMISSION.md` is current
- `docs/PUBLIC_PROOF.md` is current
- public screenshots are committed

## Live URLs

- main toolkit API responds:
  - `https://toolkit-api-production-a04c.up.railway.app/health`
- x402 sidecar responds:
  - `https://x402-facilitator-demo-production.up.railway.app/health`
- MPP Charge sidecar responds:
  - `https://mpp-charge-demo-production.up.railway.app/health`

## Proof Surfaces

- real transaction-hash proof path still documented in:
  - `docs/TESTNET_VERIFICATION.md`
- x402 inspection endpoint responds:
  - `https://toolkit-api-production-a04c.up.railway.app/protocols/x402/facilitator`
- MPP inspection endpoint responds:
  - `https://toolkit-api-production-a04c.up.railway.app/protocols/mpp/charge`
- MPP sidecar challenge responds:
  - `https://mpp-charge-demo-production.up.railway.app/mpp/service`

## Local Verification

- `python -m unittest discover -s tests -q`
- `npm run capture:public-proof`

## Submission Copy

- use `docs/DORAHACKS_SUBMISSION_COPY.md`
- use `docs/FINAL_DEMO_NARRATION.md` for the video/demo script
- keep claims narrow:
  - strongest live paid execution path is `transaction_hash`
  - x402 is preview plus public facilitator inspection
  - MPP Charge is preview plus public official-SDK sidecar

## Do Not Overclaim

- do not claim full wallet-integrated x402 settlement
- do not claim full MPP paid retry execution
- do not claim MPP Session is implemented
- do not present preview surfaces as production-complete
