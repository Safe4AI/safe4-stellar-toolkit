from __future__ import annotations

import argparse
import json

import httpx
from stellar_sdk import Keypair


FRIENDBOT_URL = "https://friendbot.stellar.org"


def main() -> None:
    parser = argparse.ArgumentParser(description="Create and optionally fund a Stellar testnet account.")
    parser.add_argument("--public-key", help="Fund an existing public key instead of creating a new one.")
    parser.add_argument("--skip-fund", action="store_true", help="Create a keypair without calling Friendbot.")
    args = parser.parse_args()

    if args.public_key:
        keypair = None
        public_key = args.public_key
    else:
        keypair = Keypair.random()
        public_key = keypair.public_key

    friendbot_payload = None
    if not args.skip_fund:
        response = httpx.get(FRIENDBOT_URL, params={"addr": public_key}, timeout=20.0)
        response.raise_for_status()
        friendbot_payload = response.json()

    body = {
        "public_key": public_key,
        "secret_key": None if keypair is None else keypair.secret,
        "funded": not args.skip_fund,
        "friendbot_transaction_hash": None if friendbot_payload is None else friendbot_payload.get("hash"),
    }
    print(json.dumps(body, indent=2))


if __name__ == "__main__":
    main()

