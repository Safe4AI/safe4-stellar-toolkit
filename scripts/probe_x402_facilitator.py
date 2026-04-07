from __future__ import annotations

import argparse
import json

import httpx


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe an x402 facilitator /supported endpoint.")
    parser.add_argument("--base-url", required=True, help="Facilitator base URL, e.g. http://localhost:8080/api/v1/plugins/x402-facilitator/call")
    parser.add_argument("--api-key", default="", help="Optional bearer token for the facilitator endpoint.")
    args = parser.parse_args()

    headers: dict[str, str] = {}
    if args.api_key.strip():
        headers["Authorization"] = f"Bearer {args.api_key.strip()}"

    with httpx.Client(timeout=15.0) as client:
        response = client.get(f"{args.base_url.rstrip('/')}/supported", headers=headers)
        response.raise_for_status()
        print(json.dumps(response.json(), indent=2, sort_keys=True))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
