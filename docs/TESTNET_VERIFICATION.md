# Testnet Verification

This repo has been exercised against a real Stellar testnet XLM payment path,
not only the mock flow.

## Verified Run

Date:
- 2026-04-06

Mode:
- `transaction_hash`

Network:
- `stellar-testnet`

Asset:
- `XLM`

Receiver account:
- `GB3G3UMQRADJ3M2GZH52PETKM44ZF6XL2NYXKT3IKTQBKHHOHBNT7PWX`

Payer account:
- `GDIIDYKW4S3JHT5GQH2CZMJOA2WJKMPDHAORMDVBJVDFDGNTA35AJNS6`

Safe4 request ID:
- `d38a9431b61c4835bc00eefa67360afd`

Verified testnet transaction hash:
- `ef0bcfd7c46f1f47d7c3769f60a0a9b12886bb96a67ef6b51f994acb4d2c3b83`

Safe4 outcome:
- `AUTHORIZED`

## What Was Verified

Safe4 accepted the paid tool call only after checking:

- successful Stellar transaction
- memo binding to the Safe4 challenge
- challenge expiry window
- destination account
- native XLM asset handling
- amount paid
- payer binding

## Reproduce Locally

1. Configure the server:

```powershell
$env:SAFE4_STELLAR_VERIFICATION_MODE="transaction_hash"
$env:SAFE4_STELLAR_ASSET_CODE="XLM"
$env:SAFE4_STELLAR_ASSET_ISSUER=""
$env:SAFE4_STELLAR_DESTINATION="<FUNDED_TESTNET_RECEIVER>"
```

2. Start the API:

```powershell
python -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8080
```

3. Create a funded payer account if needed:

```powershell
python scripts/create_testnet_account.py
```

4. Run the real demo:

```powershell
python scripts/run_testnet_payment_demo.py --source-secret <FUNDED_TESTNET_SECRET>
```

The script prints:
- the original Safe4 challenge
- the submitted Stellar tx hash
- the generated Safe4 proof
- the final authorized response
