# Northstar Payment Gateway API Specification (v2)

## 1. Overview
The Payment Gateway (`svc-payment-gw`) acts as the single PCI-compliant gateway for credit card authorizations, 3D-Secure handoffs, and refund captures.

## 2. Mandatory Idempotency Header
To prevent duplicate financial charges during transient network retries, all mutating endpoints (`POST /v2/payments/authorize`, `POST /v2/payments/capture`) **MUST** supply the idempotency key header:

```http
X-Idempotency-Key: <UUIDv4>
```

- **TTL**: Idempotency keys are cached in Redis with a 24-hour expiration window.
- **Replay Behavior**: If a request with an existing `X-Idempotency-Key` arrives within the 24-hour window:
  - If original request succeeded: Returns cached HTTP 200/201 response payload immediately without charging the payment card again.
  - If original request is still in-flight: Returns `HTTP 409 Conflict` with error code `PAYMENT_AUTHORIZATION_IN_PROGRESS`.

## 3. Core Endpoints
- `POST /v2/payments/authorize`: Authorizes customer payment token. Payload requires `amount_cents`, `currency`, `cart_id`, `token`.
- `POST /v2/payments/refund`: Submits full or partial refund to card issuer. Requires P1 approval if `amount > $1,000`.
- `GET /v2/payments/{payment_id}/status`: Fetches settlement status.
