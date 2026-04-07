# x402 Facilitator Setup

The toolkit now treats x402 facilitator access as an endpoint availability
question, not a Defender-only dependency.

There are two realistic ways to run the x402 preview path:

## 1. Hosted OpenZeppelin Channels facilitator

Use:

```text
SAFE4_X402_FACILITATOR_URL=https://channels.openzeppelin.com/x402/testnet
SAFE4_X402_FACILITATOR_API_KEY=<YOUR_TESTNET_API_KEY>
```

Use this when:
- you want the fastest path to a live facilitator endpoint
- you already have access to the hosted service

## 2. Self-hosted OpenZeppelin Relayer plugin

Use the OpenZeppelin Relayer x402 facilitator plugin and point Safe4 at its
plugin call router:

```text
SAFE4_X402_FACILITATOR_URL=http://localhost:8080/api/v1/plugins/x402-facilitator/call
SAFE4_X402_FACILITATOR_API_KEY=
```

This works because the toolkit appends:
- `/supported`
- `/verify`
- `/settle`

to the configured base URL.

Use this when:
- you want to avoid depending on the hosted OpenZeppelin Channels endpoint
- you want your own testnet or mainnet facilitator deployment

## Important nuance

“No Defender dependency” does not mean “no auth or ops at all.”

It means:
- you do not need the hosted OpenZeppelin Channels service specifically
- you can run the facilitator yourself via the Relayer plugin
- your own Relayer deployment may still have its own auth and operational setup

## Toolkit mode

Enable the preview path with:

```text
SAFE4_STELLAR_VERIFICATION_MODE=x402_facilitator_preview
```

Then inspect:
- `GET /protocols/x402/facilitator`
- `GET /payments/x402/guide`

The strongest live proof path in the deployed toolkit is still `transaction_hash`
unless you actively switch the service into `x402_facilitator_preview`.
