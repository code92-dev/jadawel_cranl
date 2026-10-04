from arabase.feature_access.handler import USER_DATA_KEY, get_user_features
from jadawel.api.user.registries import UserDataType


class FeatureAccessUserDataType(UserDataType):
    """Which gated features the user may use, in the login and token-refresh
    responses. The frontend shows or hides each feature's entry points from it."""

    type = USER_DATA_KEY

    def get_user_data(self, user, request) -> dict:
        return get_user_features(user)
