# Pitch

## 30 Second Pitch

Safe4 Stellar Toolkit is Stripe-like safety middleware for paid AI tools on
Stellar. Instead of letting payment alone unlock execution, Safe4 verifies the
payment context, enforces policy, and returns receipts for every tool call.

## 90 Second Pitch

Agents are moving from suggesting actions to executing them, including paid API
calls and financial workflows. The missing layer is safety middleware between an
agent's payment decision and tool execution. Safe4 provides that layer.

In this hackathon build, a developer wraps a paid tool with Safe4. The first
request returns a `402` Stellar payment requirement. The client pays and retries
with payment proof. Safe4 then checks that the payment is bound to the right
request, enforces explicit policy such as max spend and risk flags, and returns
the tool result with a receipt and audit record.

The result is a simple but powerful model: paid AI tools on Stellar, with
runtime safety controls built in.

## Judge Hooks

- paid AI tools should be policy-aware, not just payment-aware
- Safe4 makes Stellar payments usable for agent workflows in a developer-native way
- the demo shows both monetization and safety in the same request flow
- the architecture is thin, reusable middleware rather than a one-off app
