from __future__ import annotations

import sys
import unittest
from pathlib import Path

from fastapi.testclient import TestClient


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from apps.api.main import build_app  # noqa: E402


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
