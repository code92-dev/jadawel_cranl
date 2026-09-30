class SavedDashboardDoesNotExist(Exception):
    """No such saved dashboard, or it belongs to someone else."""


class InvalidDashboardLink(Exception):
    """Not the public link of a Jadawel dashboard."""


class SavedDashboardPasswordRequired(Exception):
    """The link is password protected and the user has not been let in, or the
    owner changed the password since."""


class SavedDashboardPasswordIncorrect(Exception):
    """The password the user entered is not the link's."""


class SavedDashboardUnavailable(Exception):
    """The dashboard can no longer be read: the link was revoked or replaced,
    the dashboard deleted, or the user lost access to its workspace."""


class SavedDashboardUnreachable(Exception):
    """The other server did not answer, or answered with something that is not
    a Jadawel dashboard."""


class SavedDashboardHasNoPassword(Exception):
    """A dashboard from the user's own workspace takes no password."""


class RemoteDispatchFailed(Exception):
    """The other server could not load one data source; the rest may be fine."""
