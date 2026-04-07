from __future__ import annotations

import base64
import json
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
        self.assertIn("PAYMENT-REQUIRED", first.headers)
        self.assertEqual(first.headers["X-Payment-Protocol"], "x402-stellar-preview")
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
        self.assertIn("PAYMENT-RESPONSE", authorized.headers)
        body = authorized.json()
        self.assertEqual(body["status"], "AUTHORIZED")
        self.assertEqual(body["tool"], "summarise")
        self.assertEqual(body["policy"]["decision"], "allow")
        self.assertIn("payment_reference", body["payment"])

    def test_preview_payment_signature_header_also_authorizes(self) -> None:
        payload = {
            "client_id": "demo-agent",
            "text": "A preview x402 retry header should be accepted for the same paid tool request.",
            "max_sentences": 1,
            "risk_flag": "low",
        }
        first = self.client.post("/tools/summarise", json=payload)
        challenge = first.json()

        settle = self.client.post(
            "/payments/mock/settle",
            json={"request_id": challenge["request_id"], "payer": "GDEMO_PAYER_ACCOUNT"},
        )
        token = settle.json()["payment_token"]

        authorized = self.client.post(
            "/tools/summarise",
            json=payload,
            headers={
                "PAYMENT-SIGNATURE": token,
                "X-Request-Id": challenge["request_id"],
            },
        )
        self.assertEqual(authorized.status_code, 200)
        self.assertEqual(authorized.json()["status"], "AUTHORIZED")

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
        protocols = self.client.get("/protocols/status")
        self.assertEqual(protocols.status_code, 200)
        self.assertEqual(protocols.json()["primary_demo_target"], "x402")

    def test_x402_facilitator_status_reports_not_configured_by_default(self) -> None:
        response = self.client.get("/protocols/x402/facilitator")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertFalse(body["configured"])
        self.assertEqual(body["supported"]["status"], "not_configured")

    def test_x402_guide_reports_preview_state(self) -> None:
        response = self.client.get("/payments/x402/guide")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "preview")
        self.assertFalse(body["facilitator"]["configured"])
        self.assertIn("PAYMENT-SIGNATURE", body["client_retry_headers"])
        self.assertIn("hosted_channels", body["deployment_options"])
        self.assertIn("self_hosted_relayer_plugin", body["deployment_options"])
        self.assertTrue(body["deployment_options"]["self_hosted_relayer_plugin"]["may_require_relayer_api_key"])

    def test_mpp_charge_and_session_endpoints_exist(self) -> None:
        charge = self.client.get("/protocols/mpp/charge")
        self.assertEqual(charge.status_code, 200)
        self.assertEqual(charge.json()["status"], "preview")
        self.assertEqual(charge.json()["sdk"], "@stellar/mpp")
        self.assertFalse(charge.json()["service"]["configured"])

        session = self.client.get("/protocols/mpp/session")
        self.assertEqual(session.status_code, 200)
        self.assertEqual(session.json()["status"], "planned")

        guide = self.client.get("/payments/mpp/charge/guide")
        self.assertEqual(guide.status_code, 200)
        self.assertEqual(guide.json()["status"], "preview")
        self.assertEqual(guide.json()["protocol"], "mpp-charge-preview")
        self.assertFalse(guide.json()["service"]["configured"])

        service = self.client.get("/protocols/mpp/charge/service")
        self.assertEqual(service.status_code, 200)
        self.assertFalse(service.json()["configured"])

    def test_transaction_hash_verification_authorizes_with_matching_horizon_data(self) -> None:
        payload = {
            "client_id": "demo-agent",
            "text": "Safe4 verifies a real Stellar testnet payment before executing the tool.",
            "max_sentences": 1,
            "risk_flag": "low",
        }
        with patch.dict(
            os.environ,
            {
                "SAFE4_STELLAR_VERIFICATION_MODE": "transaction_hash",
                "SAFE4_STELLAR_ASSET_CODE": "XLM",
                "SAFE4_STELLAR_ASSET_ISSUER": "",
            },
            clear=False,
        ):
            client = TestClient(build_app())
            first = client.post("/tools/summarise", json=payload)
            self.assertEqual(first.status_code, 402)
            challenge = first.json()
            self.assertEqual(challenge["payment_requirement"]["verification_mode"], "transaction_hash")
            self.assertEqual(challenge["payment_requirement"]["asset_issuer"], "")
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
                            "asset_type": "native",
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

    def test_mock_settlement_is_disabled_outside_mock_mode(self) -> None:
        payload = {
            "client_id": "demo-agent",
            "text": "Transaction hash mode should not accept mock settlement.",
            "max_sentences": 1,
            "risk_flag": "low",
        }
        with patch.dict(
            os.environ,
            {
                "SAFE4_STELLAR_VERIFICATION_MODE": "transaction_hash",
                "SAFE4_STELLAR_ASSET_CODE": "XLM",
                "SAFE4_STELLAR_ASSET_ISSUER": "",
            },
            clear=False,
        ):
            client = TestClient(build_app())
            first = client.post("/tools/summarise", json=payload)
            self.assertEqual(first.status_code, 402)
            challenge = first.json()

            settle = client.post(
                "/payments/mock/settle",
                json={"request_id": challenge["request_id"], "payer": "GDEMO_PAYER_ACCOUNT"},
            )
            self.assertEqual(settle.status_code, 409)
            self.assertIn("disabled", settle.json()["detail"])

    def test_transaction_hash_verification_rejects_wrong_destination(self) -> None:
        payload = {
            "client_id": "demo-agent",
            "text": "Safe4 should deny a proof when the onchain payment misses the expected destination.",
            "max_sentences": 1,
            "risk_flag": "low",
        }
        with patch.dict(
            os.environ,
            {
                "SAFE4_STELLAR_VERIFICATION_MODE": "transaction_hash",
                "SAFE4_STELLAR_ASSET_CODE": "XLM",
                "SAFE4_STELLAR_ASSET_ISSUER": "",
            },
            clear=False,
        ):
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
                            "asset_type": "native",
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

    def test_x402_facilitator_preview_verifies_and_settles_payment_signature(self) -> None:
        payload = {
            "client_id": "demo-agent",
            "text": "Safe4 can call a facilitator to verify and settle an x402 payment payload.",
            "max_sentences": 1,
            "risk_flag": "low",
        }
        fake_payment_payload = {
            "x402Version": 2,
            "scheme": "exact",
            "network": "stellar:testnet",
            "payload": {"payer": "GREALX402PAYERXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"},
        }
        payment_signature = base64.urlsafe_b64encode(
            json.dumps(fake_payment_payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
        ).decode("utf-8").rstrip("=")

        verify_response = FakeHttpResponse({"isValid": True})
        settle_response = FakeHttpResponse({"transactionHash": "stellar_x402_hash_123"})
        supported_response = FakeHttpResponse({"networks": ["stellar:testnet"]})

        with patch.dict(
            os.environ,
            {
                "SAFE4_STELLAR_VERIFICATION_MODE": "x402_facilitator_preview",
                "SAFE4_X402_FACILITATOR_URL": "https://facilitator.example/x402",
                "SAFE4_X402_FACILITATOR_API_KEY": "demo-key",
                "SAFE4_STELLAR_ASSET_CODE": "XLM",
                "SAFE4_STELLAR_ASSET_ISSUER": "",
            },
            clear=False,
        ):
            client = TestClient(build_app())
            first = client.post("/tools/summarise", json=payload)
            self.assertEqual(first.status_code, 402)
            challenge = first.json()
            self.assertEqual(challenge["payment_requirement"]["verification_mode"], "x402_facilitator_preview")

            with patch(
                "packages.protocols.x402.httpx.post",
                side_effect=[verify_response, settle_response],
            ):
                authorized = client.post(
                    "/tools/summarise",
                    json=payload,
                    headers={
                        "PAYMENT-SIGNATURE": payment_signature,
                        "X-Request-Id": challenge["request_id"],
                    },
                )
            self.assertEqual(authorized.status_code, 200)
            self.assertEqual(authorized.json()["status"], "AUTHORIZED")
            self.assertEqual(authorized.json()["receipt"]["payment_mode"], "x402_facilitator")
            self.assertEqual(authorized.json()["payment"]["payment_reference"], "stellar_x402_hash_123")

            with patch("packages.protocols.x402.httpx.get", return_value=supported_response):
                facilitator_status = client.get("/protocols/x402/facilitator")
            self.assertEqual(facilitator_status.status_code, 200)
            self.assertTrue(facilitator_status.json()["configured"])

    def test_mpp_charge_preview_changes_challenge_framing(self) -> None:
        payload = {
            "client_id": "demo-agent",
            "text": "Safe4 should expose an MPP Charge preview challenge without overclaiming settlement.",
            "max_sentences": 1,
            "risk_flag": "low",
        }
        with patch.dict(
            os.environ,
            {
                "SAFE4_STELLAR_VERIFICATION_MODE": "mpp_charge_preview",
                "SAFE4_STELLAR_ASSET_CODE": "XLM",
                "SAFE4_STELLAR_ASSET_ISSUER": "",
            },
            clear=False,
        ):
            client = TestClient(build_app())
            first = client.post("/tools/summarise", json=payload)
            self.assertEqual(first.status_code, 402)
            self.assertEqual(first.headers["X-Payment-Protocol"], "mpp-charge-preview")
            self.assertIn("MPP-CHARGE-REQUIRED", first.headers)
            self.assertNotIn("PAYMENT-REQUIRED", first.headers)
            challenge = first.json()
            self.assertEqual(challenge["payment_requirement"]["verification_mode"], "mpp_charge_preview")
            self.assertTrue(challenge["payment_requirement"]["settle_endpoint"].endswith("/payments/mpp/charge/guide"))

            guide = client.get(f"/payments/mpp/charge/guide?request_id={challenge['request_id']}")
            self.assertEqual(guide.status_code, 200)
            guide_body = guide.json()
            self.assertEqual(guide_body["protocol"], "mpp-charge-preview")
            self.assertEqual(guide_body["request"]["charge"]["memo"], challenge["payment_requirement"]["memo"])

            protocols = client.get("/protocols/status")
            self.assertEqual(protocols.status_code, 200)
            self.assertEqual(protocols.json()["mpp_charge"]["status"], "preview")
            self.assertEqual(protocols.json()["primary_demo_target"], "mpp_charge")

    def test_mpp_charge_service_status_reports_live_sidecar_when_configured(self) -> None:
        service_payload = {
            "status": "ok",
            "protocol": "mpp-charge-demo",
            "network": "stellar:testnet",
            "recipient": "GRECIPIENTXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
            "sponsoredFees": False,
            "currency": "USDC_SAC_TESTNET",
        }
        with patch.dict(
            os.environ,
            {
                "SAFE4_MPP_CHARGE_SERVICE_URL": "https://mpp-charge-demo.example",
            },
            clear=False,
        ):
            with patch("packages.protocols.mpp.httpx.get", return_value=FakeHttpResponse(service_payload)):
                client = TestClient(build_app())
                charge = client.get("/protocols/mpp/charge")
                self.assertEqual(charge.status_code, 200)
                self.assertTrue(charge.json()["service"]["configured"])
                self.assertEqual(charge.json()["service"]["protocol"], "mpp-charge-demo")

                service = client.get("/protocols/mpp/charge/service")
                self.assertEqual(service.status_code, 200)
                self.assertEqual(service.json()["url"], "https://mpp-charge-demo.example")
                self.assertTrue(service.json()["health"]["configured"])
