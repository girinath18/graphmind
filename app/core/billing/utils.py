"""
Billing utilities - Feature flag for per-tenant cost tracking.

Centralizes billing feature toggle to keep code clean and maintainable.
Enables easy enable/disable without scattered if-statements.

DESIGN:
- Single source of truth: is_billing_enabled()
- No billing logic scattered across codebase
- Easy to maintain and test
- Future-proof for different billing backends
"""

from ..config import get_settings

logger_placeholder = None  # Not importing logger to avoid circular imports


def is_billing_enabled() -> bool:
    """
    Check if billing system is enabled.

    Returns True if billing is active, False otherwise.
    Centralizes the feature toggle check.

    Returns:
        bool: True if billing enabled, False if disabled

    Usage:
        from app.core.billing.utils import is_billing_enabled

        if is_billing_enabled():
            # Track costs, per-tenant usage, etc.
            track_cost(tenant_id, cost)
    """
    settings = get_settings()
    return settings.enable_billing
