# Deployment

## Recommended Demo Host

Railway is a good fit for the hackathon build because the repo is small, the
app is stateless apart from the append-only audit log, and the public demo only
needs one Python web process.

## What The Container Runs

The Docker image starts:

```text
python -m uvicorn apps.api.main:app --host 0.0.0.0 --port ${PORT}
```

## Required Environment Variables

Minimum safe defaults:

- `SAFE4_STELLAR_VERIFICATION_MODE`
  - `mock` for the fastest public demo
  - `transaction_hash` for the stronger real testnet demo
- `SAFE4_STELLAR_NETWORK`
  - usually `stellar-testnet`
- `SAFE4_STELLAR_ASSET_CODE`
  - `XLM` for the easiest real testnet setup
- `SAFE4_STELLAR_ASSET_ISSUER`
  - blank for native `XLM`
- `SAFE4_STELLAR_DESTINATION`
  - funded receiving testnet account
- `SAFE4_STELLAR_HORIZON_URL`
  - default testnet Horizon endpoint is already wired
- `SAFE4_STELLAR_PROOF_SECRET`
  - required if mock proof mode is enabled
- `SAFE4_X402_FACILITATOR_URL`
  - optional for x402 preview mode
- `SAFE4_X402_FACILITATOR_API_KEY`
  - optional unless your facilitator requires it

## Recommended Demo Config

### Strongest hackathon path

```text
SAFE4_STELLAR_VERIFICATION_MODE=transaction_hash
SAFE4_STELLAR_NETWORK=stellar-testnet
SAFE4_STELLAR_ASSET_CODE=XLM
SAFE4_STELLAR_ASSET_ISSUER=
SAFE4_STELLAR_DESTINATION=<FUNDED_TESTNET_RECEIVER>
```

### Optional x402 preview config

```text
SAFE4_STELLAR_VERIFICATION_MODE=x402_facilitator_preview
SAFE4_STELLAR_NETWORK=stellar-testnet
SAFE4_STELLAR_ASSET_CODE=XLM
SAFE4_STELLAR_ASSET_ISSUER=
SAFE4_STELLAR_DESTINATION=<FUNDED_TESTNET_RECEIVER>
SAFE4_X402_FACILITATOR_URL=https://channels.openzeppelin.com/x402/testnet
SAFE4_X402_FACILITATOR_API_KEY=<OPTIONAL_TESTNET_API_KEY>
```

### Optional MPP Charge preview config

```text
SAFE4_STELLAR_VERIFICATION_MODE=mpp_charge_preview
SAFE4_STELLAR_NETWORK=stellar-testnet
SAFE4_STELLAR_ASSET_CODE=XLM
SAFE4_STELLAR_ASSET_ISSUER=
SAFE4_STELLAR_DESTINATION=<FUNDED_TESTNET_RECEIVER>
```

### Reliable fallback path

```text
SAFE4_STELLAR_VERIFICATION_MODE=mock
SAFE4_STELLAR_ASSET_CODE=XLM
SAFE4_STELLAR_ASSET_ISSUER=
SAFE4_STELLAR_DESTINATION=<ANY_PLACEHOLDER_OR_TEST_ACCOUNT>
SAFE4_STELLAR_PROOF_SECRET=<LONG_RANDOM_SECRET>
```

Do not expect `transaction_hash` mode to accept mock proof tokens. The service
now enforces that mode boundary explicitly.

## Smoke Checks

After deploy:

1. `GET /health`
2. `GET /protocols/status`
3. `GET /protocols/x402/facilitator`
4. `GET /payments/x402/guide`
5. `GET /protocols/mpp/charge`
6. `GET /payments/mpp/charge/guide`
7. `GET /tools`
8. `POST /tools/summarise` and confirm:
   - `402`
   - either `PAYMENT-REQUIRED` or `MPP-CHARGE-REQUIRED`, depending on verification mode
   - `WWW-Authenticate`
9. complete either the mock or real testnet proof path
10. confirm `PAYMENT-RESPONSE` on the successful retry

## Important Safety Note

Do not deploy this toolkit over the existing Safe4 production service. It should
run as a separate demo service or separate Railway project.
