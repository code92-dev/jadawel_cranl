class SanadNotAllowed(Exception):
    """Sanad is not available to this user (arabase.feature_access)."""


class SanadChatDoesNotExist(Exception):
    """The chat does not exist or belongs to another user."""


class SanadNoModelAvailable(Exception):
    """No generative AI provider is configured on this instance."""


class SanadModelNotAvailable(Exception):
    """The requested model is not one of the instance's enabled models."""


class SanadChatBusy(Exception):
    """A turn is still running, or waiting for an approval decision."""


class SanadNothingToApprove(Exception):
    """The chat has no tool call waiting for a decision."""


class SanadTurnTooLong(Exception):
    """The turn ran past ``agent.TURN_TIME_LIMIT``."""


class SanadBudgetExceeded(Exception):
    """The workspace has used up this month's Sanad turns or tokens."""
