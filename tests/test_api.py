from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from apps.api.main import build_app  # noqa: E402


class FakeHttpResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self):
        return self._payload


class Safe4StellarToolkitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(build_app())

    def test_paid_tool_flow_returns_402_then_authorizes(self) -> None:
        payload = {
            "client_id": "demo-agent",
            "text": "Safe4 stands between agent intent and payment execution. It enforces policy and returns receipts.",
            "max_sentences": 1,
            "risk_flag": "low",
        }
        first = self.client.post("/tools/summarise", json=payload)
        self.assertEqual(first.status_code, 402)
        challenge = first.json()
        self.assertEqual(challenge["status"], "payment_required")

        settle = self.client.post(
            "/payments/mock/settle",
            json={"request_id": challenge["request_id"], "payer": "GDEMO_PAYER_ACCOUNT"},
        )
        self.assertEqual(settle.status_code, 200)
        token = settle.json()["payment_token"]

        authorized = self.client.post(
            "/tools/summarise",
            json=payload,
            headers={
                "Authorization": f"Payment {token}",
                "X-Request-Id": challenge["request_id"],
            },
        )
        self.assertEqual(authorized.status_code, 200)
        body = authorized.json()
        self.assertEqual(body["status"], "AUTHORIZED")
        self.assertEqual(body["tool"], "summarise")
        self.assertEqual(body["policy"]["decision"], "allow")
        self.assertIn("payment_reference", body["payment"])

    def test_policy_can_deny_after_payment(self) -> None:
        payload = {
            "client_id": "demo-agent",
            "text": "This text should still require payment before a policy denial is returned.",
            "max_sentences": 1,
            "risk_flag": "high",
        }
        first = self.client.post("/tools/summarise", json=payload)
        request_id = first.json()["request_id"]
        settle = self.client.post(
            "/payments/mock/settle",
            json={"request_id": request_id, "payer": "GDEMO_PAYER_ACCOUNT"},
        )
        token = settle.json()["payment_token"]
        denied = self.client.post(
            "/tools/summarise",
            json=payload,
            headers={"Authorization": f"Payment {token}", "X-Request-Id": request_id},
        )
        self.assertEqual(denied.status_code, 403)
        self.assertEqual(denied.json()["policy"]["decision"], "deny")
        self.assertIn("risk_flag_high", denied.json()["policy"]["reasons"])

    def test_demo_page_and_audit_endpoint_exist(self) -> None:
        demo = self.client.get("/demo")
        self.assertEqual(demo.status_code, 200)
        audit = self.client.get("/audit/entries")
        self.assertEqual(audit.status_code, 200)
        self.assertIn("entries", audit.json())

    def test_transaction_hash_verification_authorizes_with_matching_horizon_data(self) -> None:
        payload = {
            "client_id": "demo-agent",
            "text": "Safe4 verifies a real Stellar testnet payment before executing the tool.",
            "max_sentences": 1,
            "risk_flag": "low",
        }
        with patch.dict(os.environ, {"SAFE4_STELLAR_VERIFICATION_MODE": "transaction_hash"}, clear=False):
            client = TestClient(build_app())
            first = client.post("/tools/summarise", json=payload)
            self.assertEqual(first.status_code, 402)
            challenge = first.json()
            self.assertEqual(challenge["payment_requirement"]["verification_mode"], "transaction_hash")
            self.assertTrue(challenge["payment_requirement"]["settle_endpoint"].endswith("/payments/transaction-hash-proof"))

            proof = client.post(
                "/payments/transaction-hash-proof",
                json={
                    "request_id": challenge["request_id"],
                    "payer": "GREALPAYERXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
                    "tx_hash": "tx_1234567890abcdef",
                },
            )
            self.assertEqual(proof.status_code, 200)
            token = proof.json()["payment_token"]

            transaction_payload = {
                "successful": True,
                "memo": challenge["payment_requirement"]["memo"],
                "created_at": "2026-04-06T18:00:00Z",
            }
            operations_payload = {
                "_embedded": {
                    "records": [
                        {
                            "type": "payment",
                            "from": "GREALPAYERXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
                            "to": challenge["payment_requirement"]["destination"],
                            "amount": challenge["payment_requirement"]["amount"],
                            "asset_code": challenge["payment_requirement"]["asset_code"],
                            "asset_issuer": challenge["payment_requirement"]["asset_issuer"],
                        }
                    ]
                }
            }
            with patch(
                "packages.stellar.adapter.httpx.get",
                side_effect=[FakeHttpResponse(transaction_payload), FakeHttpResponse(operations_payload)],
            ):
                authorized = client.post(
                    "/tools/summarise",
                    json=payload,
                    headers={
                        "Authorization": f"Payment {token}",
                        "X-Request-Id": challenge["request_id"],
                    },
                )
            self.assertEqual(authorized.status_code, 200)
            self.assertEqual(authorized.json()["status"], "AUTHORIZED")
            self.assertEqual(authorized.json()["payment"]["payment_reference"], "tx_1234567890abcdef")

    def test_transaction_hash_verification_rejects_wrong_destination(self) -> None:
        payload = {
            "client_id": "demo-agent",
            "text": "Safe4 should deny a proof when the onchain payment misses the expected destination.",
            "max_sentences": 1,
            "risk_flag": "low",
        }
        with patch.dict(os.environ, {"SAFE4_STELLAR_VERIFICATION_MODE": "transaction_hash"}, clear=False):
            client = TestClient(build_app())
            first = client.post("/tools/summarise", json=payload)
            challenge = first.json()
            proof = client.post(
                "/payments/transaction-hash-proof",
                json={
                    "request_id": challenge["request_id"],
                    "payer": "GREALPAYERXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
                    "tx_hash": "tx_wrong_destination",
                },
            )
            token = proof.json()["payment_token"]

            transaction_payload = {
                "successful": True,
                "memo": challenge["payment_requirement"]["memo"],
                "created_at": "2026-04-06T18:00:00Z",
            }
            operations_payload = {
                "_embedded": {
                    "records": [
                        {
                            "type": "payment",
                            "from": "GREALPAYERXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
                            "to": "GBADDESTINATIONXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
                            "amount": challenge["payment_requirement"]["amount"],
                            "asset_code": challenge["payment_requirement"]["asset_code"],
                            "asset_issuer": challenge["payment_requirement"]["asset_issuer"],
                        }
                    ]
                }
            }
            with patch(
                "packages.stellar.adapter.httpx.get",
                side_effect=[FakeHttpResponse(transaction_payload), FakeHttpResponse(operations_payload)],
            ):
                denied = client.post(
                    "/tools/summarise",
                    json=payload,
                    headers={
                        "Authorization": f"Payment {token}",
                        "X-Request-Id": challenge["request_id"],
                    },
                )
            self.assertEqual(denied.status_code, 402)
            self.assertEqual(denied.json()["status"], "payment_invalid")
            self.assertIn("No Stellar payment operation matched", denied.json()["detail"])
