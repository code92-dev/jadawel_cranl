from django.urls import path

from .views import (
    AcceptInvitationView,
    AdminOrganizationCreateView,
    AdminOrganizationListView,
    AuditView,
    InvitationListCreateView,
    InvitationDetailView,
    LifecycleView,
    MemberDetailView,
    MemberListView,
    OrganizationDetailView,
    OrganizationListView,
    StartTeamView,
    WorkspaceBindView,
    WorkspaceBindingDetailView,
    WorkspaceMemberAssignmentView,
    WorkspaceListView,
    TransitionToPersonalView,
)

app_name = "jadawel_organizations"
urlpatterns = [
    path("", OrganizationListView.as_view(), name="list"),
    path(
        "invitations/accept/", AcceptInvitationView.as_view(), name="accept_invitation"
    ),
    path("admin/", AdminOrganizationListView.as_view(), name="admin_list"),
    path("admin/create/", AdminOrganizationCreateView.as_view(), name="admin_create"),
    path("start-team/", StartTeamView.as_view(), name="start_team"),
    path("<uuid:organization_id>/", OrganizationDetailView.as_view(), name="detail"),
    path("<uuid:organization_id>/members/", MemberListView.as_view(), name="members"),
    path(
        "<uuid:organization_id>/members/<int:membership_id>/",
        MemberDetailView.as_view(),
        name="member",
    ),
    path(
        "<uuid:organization_id>/invitations/",
        InvitationListCreateView.as_view(),
        name="invitations",
    ),
    path(
        "<uuid:organization_id>/invitations/<int:invitation_id>/",
        InvitationDetailView.as_view(),
        name="invitation_detail",
    ),
    path(
        "<uuid:organization_id>/workspaces/",
        WorkspaceListView.as_view(),
        name="workspaces",
    ),
    path(
        "<uuid:organization_id>/workspaces/bind/",
        WorkspaceBindView.as_view(),
        name="bind_workspace",
    ),
    path(
        "<uuid:organization_id>/workspaces/<int:binding_id>/",
        WorkspaceBindingDetailView.as_view(),
        name="workspace_binding",
    ),
    path(
        "<uuid:organization_id>/workspaces/<int:binding_id>/members/<int:membership_id>/",
        WorkspaceMemberAssignmentView.as_view(),
        name="workspace_member",
    ),
    path(
        "<uuid:organization_id>/lifecycle/", LifecycleView.as_view(), name="lifecycle"
    ),
    path(
        "<uuid:organization_id>/transition-to-personal/",
        TransitionToPersonalView.as_view(),
        name="transition_to_personal",
    ),
    path("<uuid:organization_id>/audit/", AuditView.as_view(), name="audit"),
]
