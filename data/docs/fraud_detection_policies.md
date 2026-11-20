# Northstar Fraud Detection & Risk Scoring Policies

## 1. Risk Tiering & Scoring Model
The `fraud-detector` service evaluates incoming checkout sessions and produces an integer risk score ranging from **0 (Lowest Risk)** to **100 (Highest Risk)**:

- **Score 0 – 35 (Green / Low Risk)**: Automated pass. Checkout proceeds straight to payment gateway authorization.
- **Score 36 – 65 (Yellow / Medium Risk)**: Step-up authentication required. Triggers mandatory 3D-Secure SMS/app verification.
- **Score 66 – 85 (Orange / High Risk)**: Transaction auto-held for manual review queue. Customer sees delayed confirmation notice.
- **Score 86 – 100 (Red / Critical Threat)**: Immediate decline with security alert. IP address added to dynamic temporary blocklist.

## 2. Evaluation Factors
1. **IP Velocity**: > 3 checkout attempts in 60 seconds from same /24 subnet.
2. **Device Fingerprint Mismatch**: Browser canvas hash mismatch across active sessions.
3. **Card Bin Country vs Shipping Address**: Geo-distance discrepancy greater than 2,000 miles without travel flag.
4. **Proxy / Tor Exit Detection**: IP reputation match against commercial threat intelligence feed.

## 3. Fallback & Fail-Safe Policy
If the fraud detector service times out (> 250ms), the checkout pipeline **fails open** for authenticated users with > 2 previous successful orders, and **fails closed** for first-time anonymous guest checkouts.
