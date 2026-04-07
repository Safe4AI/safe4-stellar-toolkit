import express from "express";
import { createHash } from "node:crypto";

const PORT = Number.parseInt(process.env.X402_FACILITATOR_PORT || "3200", 10);
const NETWORK = (process.env.X402_FACILITATOR_NETWORK || "stellar:testnet").trim();
const REQUIRE_BEARER = (process.env.X402_FACILITATOR_API_KEY || "").trim();

const app = express();
app.use(express.json({ limit: "256kb" }));

function bearerOk(req) {
  if (!REQUIRE_BEARER) return true;
  const header = req.headers.authorization || "";
  return header === `Bearer ${REQUIRE_BEARER}`;
}

function canonical(value) {
  return JSON.stringify(value, Object.keys(value).sort());
}

function buildReference(paymentPayload, paymentRequirements) {
  return createHash("sha256")
    .update(canonical(paymentPayload))
    .update(canonical(paymentRequirements))
    .digest("hex");
}

app.use((req, res, next) => {
  if (!bearerOk(req)) {
    return res.status(401).json({
      status: "unauthorized",
      detail: "Bearer token required for this facilitator demo.",
    });
  }
  return next();
});

app.get("/supported", (_req, res) => {
  res.json({
    status: "ok",
    network: NETWORK,
    modes: ["exact"],
    supportedMethods: ["verify", "settle"],
    note: "Local Safe4 demo facilitator. Use OpenZeppelin Relayer for the production-grade path.",
  });
});

app.post("/verify", (req, res) => {
  const paymentPayload = req.body?.paymentPayload;
  const paymentRequirements = req.body?.paymentRequirements;

  if (!paymentPayload || !paymentRequirements) {
    return res.status(400).json({
      isValid: false,
      error: "paymentPayload and paymentRequirements are required",
    });
  }

  const payer =
    paymentPayload?.payload?.payer ||
    paymentPayload?.payload?.from ||
    paymentPayload?.payer ||
    paymentPayload?.from;

  if (!payer || typeof payer !== "string") {
    return res.status(400).json({
      isValid: false,
      error: "paymentPayload must include a payer identity",
    });
  }

  if (paymentRequirements.network !== NETWORK) {
    return res.status(400).json({
      isValid: false,
      error: `network mismatch: expected ${NETWORK}`,
    });
  }

  if (!paymentRequirements.payTo || !paymentRequirements.maxAmountRequired) {
    return res.status(400).json({
      isValid: false,
      error: "paymentRequirements must include payTo and maxAmountRequired",
    });
  }

  return res.json({
    isValid: true,
    payer,
    network: NETWORK,
    paymentReference: `x402_demo_${buildReference(paymentPayload, paymentRequirements).slice(0, 16)}`,
  });
});

app.post("/settle", (req, res) => {
  const paymentPayload = req.body?.paymentPayload;
  const paymentRequirements = req.body?.paymentRequirements;

  if (!paymentPayload || !paymentRequirements) {
    return res.status(400).json({
      success: false,
      error: "paymentPayload and paymentRequirements are required",
    });
  }

  const transactionHash = buildReference(paymentPayload, paymentRequirements);
  return res.json({
    success: true,
    transactionHash,
    network: NETWORK,
    settledAt: new Date().toISOString(),
  });
});

app.use((error, _req, res, _next) => {
  res.status(500).json({
    status: "error",
    detail: error instanceof Error ? error.message : String(error),
  });
});

app.listen(PORT, () => {
  console.log(`Safe4 x402 facilitator demo listening on http://localhost:${PORT}`);
});
