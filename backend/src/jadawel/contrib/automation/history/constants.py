from django.db import models


class HistoryStatusChoices(models.TextChoices):
    SUCCESS = "success"
    ERROR = "error"
    DISABLED = "disabled"
    STARTED = "started"
    # The run was stopped on request before all of its nodes were dispatched.
    CANCELLED = "cancelled"
