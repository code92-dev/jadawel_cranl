from django.urls import re_path

from jadawel.contrib.automation.api.history.views import (
    CancelAutomationWorkflowHistoryView,
)

app_name = "jadawel.contrib.automation.api.history"

urlpatterns = [
    re_path(
        r"workflow_histories/(?P<workflow_history_id>[0-9]+)/cancel/$",
        CancelAutomationWorkflowHistoryView.as_view(),
        name="cancel_workflow_history",
    ),
]
