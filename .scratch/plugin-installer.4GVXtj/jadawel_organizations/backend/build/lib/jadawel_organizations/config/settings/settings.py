from typing import Any


def setup(settings: dict[str, Any]) -> None:
    """Organization settings are intentionally small and provider-independent."""
    settings.setdefault("JADAWEL_ORGANIZATION_INVITATION_DAYS", 7)
    managers = list(settings.get("PERMISSION_MANAGERS") or [])
    if "organization" not in managers:
        managers.insert(0, "organization")
    settings["PERMISSION_MANAGERS"] = managers
