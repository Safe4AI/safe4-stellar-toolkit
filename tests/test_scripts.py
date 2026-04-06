from __future__ import annotations

import sys
import unittest
from pathlib import Path

from stellar_sdk import Keypair

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.run_testnet_payment_demo import build_asset, network_passphrase  # noqa: E402


class StellarDemoScriptTests(unittest.TestCase):
    def test_network_passphrase_maps_testnet_and_mainnet(self) -> None:
        self.assertIn("Test SDF Network", network_passphrase("stellar-testnet"))
        self.assertIn("Public Global Stellar Network", network_passphrase("mainnet"))

    def test_build_asset_supports_native_and_issued_assets(self) -> None:
        native = build_asset({"asset_code": "XLM", "asset_issuer": ""})
        self.assertEqual(native.type, "native")

        issuer = Keypair.random().public_key
        issued = build_asset({"asset_code": "USDC", "asset_issuer": issuer})
        self.assertEqual(issued.code, "USDC")
        self.assertEqual(issued.issuer, issuer)

    def test_build_asset_requires_issuer_for_non_native_assets(self) -> None:
        with self.assertRaises(ValueError):
            build_asset({"asset_code": "USDC", "asset_issuer": ""})
