from jadawel.core.exceptions import FeatureDisabledException


class FeatureNotGranted(FeatureDisabledException):
    """The feature is neither open to every user nor granted to this one.

    A ``FeatureDisabledException``, so every API view maps it to
    ``ERROR_FEATURE_DISABLED`` (403) without listing it.
    """

    def __init__(self, feature: str):
        self.feature = feature
        super().__init__(f"The {feature} feature is not available to this user.")


class UnknownFeature(Exception):
    """No gated feature has this name."""


class FeatureAccessGrantDoesNotExist(Exception):
    """The grant does not exist or belongs to another feature."""
