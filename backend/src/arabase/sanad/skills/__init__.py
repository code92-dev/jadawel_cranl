"""Sanad's skills: expert guidance for one area of work, loaded on demand.

A skill is ``skills/<name>/SKILL.md``: a front matter block with ``name``,
``title`` and ``description`` (what it covers and when to load it), then plain
Markdown instructions. The system prompt lists only the descriptions; the model
calls ``load_skill`` when it is about to work in that area, and the instructions
stay in the conversation from then on. Tools that are only safe to use with a
skill's guidance are hidden until that skill is loaded (``SanadTool.skill``).

Skills are plain text that any model reads the same way: no provider-specific
features, and every tool name and argument they mention exists.
"""

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterable

from django.core.exceptions import ImproperlyConfigured

SKILLS_DIR = Path(__file__).parent

LOAD_SKILL_TOOL = "load_skill"


@dataclass(frozen=True)
class Skill:
    name: str
    title: str
    description: str
    instructions: str


def _parse(path: Path) -> Skill:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n") or "\n---\n" not in text[4:]:
        raise ImproperlyConfigured(f"{path} must start with a front matter block.")
    header, body = text[4:].split("\n---\n", 1)
    meta = {}
    for line in header.splitlines():
        key, _, value = line.partition(":")
        if key.strip():
            meta[key.strip()] = value.strip()
    missing = {"name", "title", "description"} - meta.keys()
    if missing:
        raise ImproperlyConfigured(f"{path} front matter lacks {sorted(missing)}.")
    if meta["name"] != path.parent.name:
        raise ImproperlyConfigured(f"{path} is named {meta['name']!r}.")
    return Skill(
        name=meta["name"],
        title=meta["title"],
        description=meta["description"],
        instructions=body.strip(),
    )


@lru_cache(maxsize=1)
def get_skills() -> dict[str, Skill]:
    """Every skill, by name, in a stable order."""

    return {
        skill.name: skill
        for skill in (_parse(path) for path in sorted(SKILLS_DIR.glob("*/SKILL.md")))
    }


def skills_index() -> str:
    """The lines the system prompt lists, one per skill."""

    return "\n".join(
        f"- {skill.name}: {skill.description}" for skill in get_skills().values()
    )


def loaded_skills(messages: Iterable) -> set[str]:
    """The skills a ``load_skill`` call has returned in ``messages``.

    Read from the conversation itself, so a skill loaded in an earlier turn
    still counts: its instructions are still in the history the model sees.
    """

    from pydantic_ai.messages import ModelRequest, ToolReturnPart

    names = set()
    for message in messages:
        if not isinstance(message, ModelRequest):
            continue
        for part in message.parts:
            if (
                isinstance(part, ToolReturnPart)
                and part.tool_name == LOAD_SKILL_TOOL
                and isinstance(part.content, dict)
                and part.content.get("skill") in get_skills()
            ):
                names.add(part.content["skill"])
    return names
