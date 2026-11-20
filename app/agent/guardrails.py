import re
from typing import Optional, Tuple

# Patterns that violate Northstar Checkout engineering safety policies
PROHIBITED_PATTERNS = [
    # External public broadcast / social media postings
    (
        r"(?i)\b(tweet|twitter|x\.com|post to twitter|post to social media|linkedin)\b",
        "Policy Refusal: PulseOps is strictly prohibited from publishing incident updates or root cause analyses to external social media channels (e.g., Twitter/X). According to the Northstar Incident Response Guide (`data/docs/incident_response_guide.md`), external communications are governed exclusively by the PR & Communications Team via status.northstar.com."
    ),
    # Destructive database or infrastructure operations
    (
        r"(?i)\b(drop\b.*?\btable|delete\s+from|rm\s+-rf|destroy\s+cluster|truncate\b.*?\btable)\b",
        "Policy Refusal: PulseOps enforces least-privilege safety boundaries. Destructive database and infrastructure mutations (such as dropping tables or manual data deletion) are forbidden. All schema and data modifications must follow the approved deployment and migration protocols (`data/docs/deployment_checklist.md`)."
    ),
    # Bypassing security reviews / unauthorized key extraction
    (
        r"(?i)\b(bypass\s+security|exfiltrate|leak\s+keys|disable\s+audit)\b",
        "Policy Refusal: Security policy bypass requests are strictly declined. Northstar Checkout operates under PCI-DSS compliance boundaries (`data/docs/fraud_detection_policies.md`)."
    )
]


def check_policy_violations(user_input: str) -> Tuple[bool, Optional[str]]:
    """
    Evaluates incoming user prompts against deterministic safety guardrails.
    Returns (is_violating, refusal_message).
    """
    for pattern, explanation in PROHIBITED_PATTERNS:
        if re.search(pattern, user_input):
            return True, explanation
    return False, None
