class SanadNotAllowed(Exception):
    """Sanad is limited to instance staff while it is being introduced."""


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
