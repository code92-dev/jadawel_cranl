"""Fork-hygiene guardrails.

These tests fail loudly if Baserow's proprietary premium/enterprise code ever leaks
back into the build (e.g. via an upstream merge), confirm our additive ``arabase``
app is wired in, and hold the attribution the MIT and Apache licences require.
Keep them fast and DB-free.
"""

import importlib
import re
from pathlib import Path

from django.conf import settings

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]

# Renaming the fork must never rewrite an upstream author's name. MIT terminates the
# grant if the notice is dropped, and Apache-2.0 section 4 requires notices be kept.
# Two separate rename passes have flipped one of these to "Jadawel B.V." already, so
# they are asserted rather than trusted.
REQUIRED_ATTRIBUTION = [
    ("LICENSE", "Copyright (c) 2019-present Baserow B.V."),
    ("deploy/helm/jadawel/values.yaml", "Copyright Baserow B.V. All Rights Reserved."),
    (
        "backend/src/jadawel/contrib/database/fields/dependencies/"
        "circular_reference_checker.py",
        "Copyright 2020, Jack Linke",
    ),
    (
        "backend/src/jadawel/contrib/database/fields/dependencies/"
        "circular_reference_checker.py",
        "Copyright (c) 2019-present Baserow B.V.",
    ),
    ("formula/JadawelFormulaLexer.g4", "Copyright 2018 Tal Shprecher"),
]


def test_arabase_app_is_installed():
    assert "arabase" in settings.INSTALLED_APPS


def test_oss_only_and_no_builtin_plugins():
    assert settings.JADAWEL_OSS_ONLY is True
    assert settings.JADAWEL_BUILT_IN_PLUGINS == []


@pytest.mark.parametrize("module_name", ["baserow_premium", "baserow_enterprise"])
def test_proprietary_plugins_are_not_importable(module_name):
    # The premium/ and enterprise/ directories are deleted; importing them must fail.
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module(module_name)


@pytest.mark.parametrize("app_label", ["baserow_premium", "baserow_enterprise"])
def test_proprietary_apps_not_in_installed_apps(app_label):
    assert app_label not in settings.INSTALLED_APPS


@pytest.mark.parametrize("relative_path,notice", REQUIRED_ATTRIBUTION)
def test_upstream_attribution_is_intact(relative_path, notice):
    path = REPO_ROOT / relative_path
    assert path.is_file(), f"{relative_path} is missing"
    assert notice in path.read_text(encoding="utf-8"), (
        f"{relative_path} no longer carries {notice!r}. A rename pass must never "
        f"rewrite an upstream author's name — restore it."
    )


FOUR_DOCUMENTED_BASEROW_EXCEPTION_PATHS = (
    # 1. Licence notices (asserted above) live in LICENSE and the two notice
    #    files; upstream Docker image/issue URLs and provenance live under
    #    deploy/ and .github/.
    "LICENSE",
    "docs/",
    "deploy/",
    ".github/",
    # 2. Historical migration identifiers that RenameModel operations refer to.
    "migrations/",
)

_SOURCE_SUFFIXES = (".py", ".js", ".vue", ".ts", ".scss")


def _iter_tracked_source_files():
    import shutil
    import subprocess

    git = shutil.which("git") or "git"
    # Fixed argv, no user input; upstream source uses noqa: S603 likewise.
    listing = subprocess.run(  # noqa: S603
        [git, "ls-files", "backend/src", "web-frontend/modules"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    for relative in listing:
        path = REPO_ROOT / relative
        if not path.is_file():
            continue
        if any(part in relative for part in FOUR_DOCUMENTED_BASEROW_EXCEPTION_PATHS):
            continue
        if not relative.endswith(_SOURCE_SUFFIXES):
            continue
        yield path


def test_no_new_baserow_namespace_identifiers():
    """
    New source identifiers must use the ``jadawel`` namespace, not ``baserow``.

    Four things still read ``baserow`` on purpose (see AGENTS.md): licence
    notices, upstream URLs/provenance, the premium/enterprise package names,
    and historical migration names. Outside the paths carrying those, a
    ``baserow``-prefixed identifier in code is rename drift.
    """
    offenders = []
    for path in _iter_tracked_source_files():
        for line_number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            # `baseRow`-style identifiers merely contain the substring; only
            # the `baserow` word (or a prefixed identifier like `baserowFoo`)
            # is namespace drift.
            if not re.search(r"\bbaserow", line, re.IGNORECASE):
                continue
            if "DatabaseRow" in line:
                continue
            stripped = line.strip()
            # Comments and docstrings may legitimately mention upstream.
            if stripped.startswith(("#", "*", "//", "/*", "<!--", '"""', "'''")):
                continue
            # The premium/enterprise guardrails and the legacy env-var
            # acceptance shim read `baserow` on purpose (see AGENTS.md).
            if re.search(r"baserow_(premium|enterprise)", line):
                continue
            if "BASEROW_" in line or "baserow/baserow" in line:
                continue
            # Historical upstream naming inside the Airtable legacy mapping.
            if "AIRTABLE_BASEROW_COLOR_MAPPING" in line:
                continue
            offenders.append(
                f"{path.relative_to(REPO_ROOT)}:{line_number}: {stripped[:100]}"
            )

    assert not offenders, (
        "New `baserow`-namespace source identifiers found (the fork is named "
        "`jadawel`; see AGENTS.md for the four documented exceptions):\n"
        + "\n".join(offenders[:20])
    )
