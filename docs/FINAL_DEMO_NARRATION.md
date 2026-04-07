# Final Demo Narration

This is the shortest strong judge-facing narration. Keep it under 90 seconds.

## 30 Second Version

Safe4 Stellar Toolkit is safety middleware for paid AI tools on Stellar. A paid
tool call does not execute on payment alone. Safe4 returns a payment challenge,
verifies that payment against the original request, applies policy, and then
returns the tool result with a receipt. In this build, the strongest live path
is real Stellar testnet transaction-hash verification, with public x402 and MPP
proof surfaces alongside it.

## 90 Second Version

Agents are moving from suggesting actions to executing paid tool calls. The
problem is that payment success alone is not enough to make those executions
safe.

Safe4 is the control layer between an agent's payment decision and actual tool
execution. Here, I call a paid tool and Safe4 returns a `402` payment
requirement instead of executing immediately.

In the strongest live path, the client makes a real Stellar testnet payment and
submits proof back to Safe4. Safe4 checks that the payment matches the original
request, verifies the destination, amount, memo, payer, and expiry window, then
applies policy checks like spend limits and risk flags.

Only after that does the tool execute, and the response includes a receipt and
an audit record.

Beyond that core path, this repo also exposes two public protocol proof
surfaces. First, a public x402 facilitator sidecar and inspection endpoint.
Second, a public MPP Charge sidecar using the official Stellar SDK path, which
returns a real `402` challenge.

The point is simple: Safe4 makes paid AI tools on Stellar payment-aware,
policy-aware, and receipt-backed.

## Judge Emphasis

If time is short, emphasize these three points:

1. real testnet payment verification exists
2. policy still decides execution after payment
3. x402 and MPP are visible protocol paths, not hand-wavy roadmap claims
