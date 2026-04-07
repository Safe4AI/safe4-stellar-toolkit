from __future__ import annotations

import argparse
import base64
import json

import httpx


def encode_signature(payload: dict[str, object]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def main() -> int:
    parser = argparse.ArgumentParser(description="Exercise Safe4 x402 facilitator preview end to end.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8080", help="Safe4 toolkit base URL")
    parser.add_argument("--payer", default="GX402DEMOCLIENTXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX", help="Demo payer identifier")
    args = parser.parse_args()

    payload = {
        "client_id": "demo-agent",
        "text": "Safe4 should verify an x402-style payment payload before executing the tool.",
        "max_sentences": 1,
        "risk_flag": "low",
    }

    with httpx.Client(timeout=20.0) as client:
        challenge = client.post(f"{args.base_url.rstrip('/')}/tools/summarise", json=payload)
        if challenge.status_code != 402:
            raise SystemExit(f"Expected 402 challenge, got {challenge.status_code}: {challenge.text}")

        challenge_body = challenge.json()
        request_id = challenge_body["request_id"]
        signature_payload = {
            "x402Version": 2,
            "scheme": "exact",
            "network": "stellar:testnet",
            "payload": {
                "payer": args.payer,
                "requestId": request_id,
            },
        }
        payment_signature = encode_signature(signature_payload)

        authorized = client.post(
            f"{args.base_url.rstrip('/')}/tools/summarise",
            json=payload,
            headers={
                "PAYMENT-SIGNATURE": payment_signature,
                "X-Request-Id": request_id,
            },
        )
        if authorized.status_code != 200:
            raise SystemExit(f"Expected 200 authorized response, got {authorized.status_code}: {authorized.text}")

        print(json.dumps(
            {
                "challenge_status": challenge.status_code,
                "request_id": request_id,
                "authorized_status": authorized.json()["status"],
                "payment_reference": authorized.json()["payment"]["payment_reference"],
                "payment_mode": authorized.json()["receipt"]["payment_mode"],
            },
            indent=2,
            sort_keys=True,
        ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
