from __future__ import annotations

import argparse
import json
from decimal import Decimal

import httpx
from stellar_sdk import Asset, Keypair, Network, Server, TransactionBuilder


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the real Safe4 Stellar testnet paid-tool demo.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8080", help="Safe4 Stellar Toolkit base URL")
    parser.add_argument("--source-secret", required=True, help="Funded Stellar testnet secret key for the paying account")
    parser.add_argument("--horizon-url", default="https://horizon-testnet.stellar.org", help="Horizon endpoint to submit and verify the testnet payment")
    parser.add_argument(
        "--payload-json",
        default=json.dumps(
            {
                "client_id": "demo-agent",
                "text": "Safe4 stands between agent intent and payment execution. It verifies payment, enforces policy, and returns a receipt.",
                "max_sentences": 1,
                "risk_flag": "low",
            }
        ),
        help="JSON payload for POST /tools/summarise",
    )
    return parser.parse_args()


def build_asset(requirement: dict[str, str]) -> Asset:
    asset_code = str(requirement["asset_code"]).upper()
    if asset_code == "XLM":
        return Asset.native()
    issuer = str(requirement.get("asset_issuer") or "").strip()
    if not issuer:
        raise ValueError("Non-native asset payments require asset_issuer in the Safe4 challenge.")
    return Asset(code=asset_code, issuer=issuer)


def network_passphrase(network: str) -> str:
    normalized = network.strip().lower()
    if normalized in {"stellar-testnet", "testnet"}:
        return Network.TESTNET_NETWORK_PASSPHRASE
    if normalized in {"stellar-mainnet", "mainnet", "pubnet"}:
        return Network.PUBLIC_NETWORK_PASSPHRASE
    raise ValueError(f"Unsupported Stellar network label: {network}")


def submit_stellar_payment(*, horizon_url: str, source_secret: str, requirement: dict[str, str]) -> dict[str, str]:
    keypair = Keypair.from_secret(source_secret)
    server = Server(horizon_url=horizon_url)
    account = server.load_account(keypair.public_key)
    base_fee = server.fetch_base_fee()
    tx = (
        TransactionBuilder(
            source_account=account,
            network_passphrase=network_passphrase(requirement["network"]),
            base_fee=base_fee,
        )
        .add_text_memo(requirement["memo"])
        .append_payment_op(
            destination=requirement["destination"],
            amount=str(Decimal(requirement["amount"])),
            asset=build_asset(requirement),
        )
        .set_timeout(60)
        .build()
    )
    tx.sign(keypair)
    response = server.submit_transaction(tx)
    return {
        "public_key": keypair.public_key,
        "tx_hash": response["hash"],
    }


def main() -> None:
    args = parse_args()
    base_url = args.base_url.rstrip("/")
    payload = json.loads(args.payload_json)

    with httpx.Client(timeout=20.0) as client:
        first = client.post(f"{base_url}/tools/summarise", json=payload)
        if first.status_code != 402:
            raise RuntimeError(f"Expected 402 from /tools/summarise, got {first.status_code}: {first.text}")

        challenge = first.json()
        requirement = challenge["payment_requirement"]
        if requirement["verification_mode"] != "transaction_hash":
            raise RuntimeError(
                "Safe4 is not configured for the real testnet path. Set SAFE4_STELLAR_VERIFICATION_MODE=transaction_hash."
            )

        payment = submit_stellar_payment(
            horizon_url=args.horizon_url,
            source_secret=args.source_secret,
            requirement=requirement,
        )

        proof = client.post(
            f"{base_url}/payments/transaction-hash-proof",
            json={
                "request_id": challenge["request_id"],
                "payer": payment["public_key"],
                "tx_hash": payment["tx_hash"],
            },
        )
        proof.raise_for_status()
        payment_token = proof.json()["payment_token"]

        final = client.post(
            f"{base_url}/tools/summarise",
            json=payload,
            headers={
                "Authorization": f"Payment {payment_token}",
                "X-Request-Id": challenge["request_id"],
            },
        )
        final.raise_for_status()

    body = {
        "challenge": challenge,
        "submitted_payment": payment,
        "proof": proof.json(),
        "authorized_response": final.json(),
    }
    print(json.dumps(body, indent=2))


if __name__ == "__main__":
    main()
