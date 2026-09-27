"""Tools every conversation needs, whatever the domain: skills and applications."""

from typing import Optional

from pydantic import BaseModel, Field

from arabase.sanad.tools.base import SanadEndpoint, SanadTool, application_type


class LoadSkillInput(BaseModel):
    name: str = Field(..., description="The skill's name, from the list of skills.")


def load_skill(endpoint: SanadEndpoint, args: LoadSkillInput) -> dict:
    from arabase.sanad.skills import get_skills

    skill = get_skills().get(args.name)
    if skill is None:
        raise ValueError(
            f"There is no skill {args.name!r}. Skills: {', '.join(get_skills())}."
        )
    return {
        "skill": skill.name,
        "title": skill.title,
        "instructions": skill.instructions,
        "note": "Follow these instructions for the rest of this conversation. "
        "They stay available here; do not load this skill again.",
    }


class ListApplicationsInput(BaseModel):
    type: Optional[str] = Field(
        None,
        description="Only list this type: database, builder, automation or dashboard.",
    )


def list_applications(endpoint: SanadEndpoint, args: ListApplicationsInput):
    from jadawel.core.handler import CoreHandler
    from jadawel.core.models import Application
    from jadawel.core.operations import ListApplicationsWorkspaceOperationType

    queryset = CoreHandler().filter_queryset(
        endpoint.user,
        ListApplicationsWorkspaceOperationType.type,
        Application.objects.filter(
            workspace=endpoint.workspace, trashed=False
        ).order_by("order", "id"),
        workspace=endpoint.workspace,
    )
    applications = [
        {"id": app.id, "name": app.name, "type": application_type(app)}
        for app in queryset.select_related("content_type")
    ]
    if args.type:
        applications = [app for app in applications if app["type"] == args.type]
    return applications


def get_tools() -> list[SanadTool]:
    return [
        SanadTool(
            "load_skill",
            "Load a skill: expert instructions for one kind of work. Call it "
            "before you start that work, once per conversation.",
            LoadSkillInput,
            load_skill,
        ),
        SanadTool(
            "list_applications",
            "List the workspace's applications (databases, builder apps, "
            "automations, dashboards) with their IDs.",
            ListApplicationsInput,
            list_applications,
        ),
    ]
