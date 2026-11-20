# Northstar Checkout — Architecture Overview

## 1. System Topology
Northstar Checkout is an asynchronous, event-driven e-commerce transaction platform designed for high availability and strict financial consistency.

The system is partitioned into the following tier architecture:
- **Presentation & Ingestion Tier**: `checkout-api` (Port 8000) acts as the public-facing HTTP reverse gateway. It ingests cart checkout payloads, validates session tokens, and orchestrates downstream calls.
- **Computation & Risk Tier**:
  - `pricing-engine`: Calculates cart totals, applies promotional discount vouchers, and checks regional VAT/sales taxes.
  - `fraud-detector`: Performs sub-50ms heuristic analysis, IP geolocation lookups, and velocity fraud scoring.
- **Execution & Settlement Tier**:
  - `payment-gateway`: Communicates with external payment processors (e.g. Stripe, Adyen). Uses mutual TLS and client idempotency tokens.
  - `ledger-db`: Append-only, double-entry transactional ledger storing financial journals.

## 2. Request Flow
1. Client POSTs `/v2/checkout/orders` with cart ID and payment token.
2. `checkout-api` initiates parallel calls to `pricing-engine` (for price lock) and `fraud-detector` (for fraud score).
3. If fraud score < 65, `checkout-api` submits payment authorization to `payment-gateway`.
4. Upon successful authorization, an immutable journal entry is written to `ledger-db`.
5. Order confirmation is returned with HTTP 201 Created and transaction receipt ID.

## 3. Communication Protocols
- Internal RPCs use gRPC over HTTP/2 with mutual TLS (mTLS).
- External webhooks and client APIs use HTTPS JSON REST with mandatory `X-Idempotency-Key` headers.
- Async audit events are broadcast over Apache Kafka topic `events.checkout.completed`.
