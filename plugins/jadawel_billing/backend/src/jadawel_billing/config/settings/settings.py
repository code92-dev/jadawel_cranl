import os
from typing import Any


def setup(settings: dict[str, Any]) -> None:
    """Provider configuration belongs to the standalone plugin, not core."""
    for name in (
        "JADAWEL_MOYASAR_SECRET_KEY",
        "JADAWEL_MOYASAR_PUBLISHABLE_KEY",
        "JADAWEL_MOYASAR_WEBHOOK_SECRET",
    ):
        settings[name] = os.getenv(name, "")
    settings["JADAWEL_BILLING_MODE"] = os.getenv("JADAWEL_BILLING_MODE", "test")
    settings["JADAWEL_BILLING_LIVE_ENABLED"] = (
        os.getenv("JADAWEL_BILLING_LIVE_ENABLED", "false").lower() == "true"
    )
    settings["JADAWEL_BILLING_GRACE_DAYS"] = int(
        os.getenv("JADAWEL_BILLING_GRACE_DAYS", "7")
    )
    schedule = dict(settings.get("CELERY_BEAT_SCHEDULE") or {})
    schedule["billing-reconcile"] = {
        "task": "jadawel_billing.reconcile_payments",
        "schedule": 60.0,
    }
    schedule["billing-renewals"] = {
        "task": "jadawel_billing.renew_subscriptions",
        "schedule": 3600.0,
    }
    settings["CELERY_BEAT_SCHEDULE"] = schedule
