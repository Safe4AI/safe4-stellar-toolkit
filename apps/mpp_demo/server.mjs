import express from "express";
import { Mppx } from "mppx/server";
import { USDC_SAC_TESTNET } from "@stellar/mpp";
import { stellar } from "@stellar/mpp/charge/server";
import { Keypair } from "@stellar/stellar-sdk";

const PORT = Number.parseInt(process.env.PORT || process.env.MPP_DEMO_PORT || "3001", 10);
const RECIPIENT = (process.env.STELLAR_RECIPIENT || "").trim();
const MPP_SECRET_KEY = (process.env.MPP_SECRET_KEY || "").trim();
const NETWORK = (process.env.MPP_NETWORK || "stellar:testnet").trim();
const ASSET = (process.env.MPP_CURRENCY || "USDC_SAC_TESTNET").trim();
const FEE_PAYER_SECRET = (process.env.FEE_PAYER_SECRET || "").trim();

if (!RECIPIENT) {
  console.error("Set STELLAR_RECIPIENT to a Stellar public key (G...).");
  process.exit(1);
}

if (!MPP_SECRET_KEY) {
  console.error("Set MPP_SECRET_KEY to a strong shared secret for MPP credential verification.");
  process.exit(1);
}

const currency = ASSET === "USDC_SAC_TESTNET" ? USDC_SAC_TESTNET : USDC_SAC_TESTNET;
const feePayer = FEE_PAYER_SECRET
  ? {
      envelopeSigner: Keypair.fromSecret(FEE_PAYER_SECRET),
    }
  : undefined;

const mppx = Mppx.create({
  secretKey: MPP_SECRET_KEY,
  methods: [
    stellar.charge({
      recipient: RECIPIENT,
      currency,
      network: NETWORK,
      feePayer,
    }),
  ],
});

const app = express();

app.get("/", (_req, res) => {
  res.json({
    name: "safe4-mpp-charge-demo",
    status: "ok",
    protocol: "mpp-charge-demo",
    network: NETWORK,
    endpoints: ["/health", "/mpp/service"],
  });
});

function toWebRequest(req) {
  const headers = new Headers();
  for (const [key, value] of Object.entries(req.headers)) {
    if (value == null) continue;
    if (Array.isArray(value)) {
      for (const entry of value) {
        headers.append(key, entry);
      }
    } else {
      headers.set(key, value);
    }
  }
  const host = req.headers.host || `localhost:${PORT}`;
  const url = new URL(req.originalUrl || req.url, `http://${host}`);
  return new Request(url, {
    method: req.method,
    headers,
  });
}

function copyResponseHeaders(from, to) {
  from.headers.forEach((value, key) => to.setHeader(key, value));
}

app.get("/health", (_req, res) => {
  res.json({
    status: "ok",
    protocol: "mpp-charge-demo",
    network: NETWORK,
    recipient: RECIPIENT,
    sponsoredFees: Boolean(feePayer),
    currency: ASSET,
  });
});

app.get("/mpp/service", async (req, res, next) => {
  try {
    const webReq = toWebRequest(req);
    const result = await mppx.charge({
      amount: "0.01",
      description: "Safe4 premium risk-gated Stellar tool",
    })(webReq);

    if (result.status === 402) {
      const challenge = result.challenge;
      copyResponseHeaders(challenge, res);
      return res.status(402).send(await challenge.text());
    }

    const response = result.withReceipt(
      Response.json({
        status: "AUTHORIZED",
        tool: "mpp-demo",
        result: {
          summary:
            "This response shows how Safe4 can pair policy-aware AI tooling with a real Stellar MPP Charge flow.",
        },
      }),
    );
    copyResponseHeaders(response, res);
    return res.status(response.status).send(await response.text());
  } catch (error) {
    return next(error);
  }
});

app.use((error, _req, res, _next) => {
  res.status(500).json({
    status: "error",
    detail: error instanceof Error ? error.message : String(error),
  });
});

app.listen(PORT, () => {
  console.log(`Safe4 MPP charge demo listening on http://localhost:${PORT}/mpp/service`);
});
