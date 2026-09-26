"""Arabase — the Jadawel (جداول) fork's own backend code.

All Arabic-first and enterprise-equivalent functionality that we add on top of the
upstream-derived core lives under this package, kept separate from ``jadawel.*`` so
that provenance stays legible: ``jadawel.*`` is inherited, ``arabase.*`` is ours.
Nothing proprietary from Jadawel's ``premium``/``enterprise`` plugins may ever be
copied in here (see PATCHES.md).

Planned sub-apps are created as their phase begins: ``arabase.fields`` (Hijri date
field) and ``arabase.search`` (Arabic search normalization) in Phase 2, then
``arabase.sso`` (OIDC), ``arabase.audit`` (append-only audit log) and
``arabase.rbac`` (role-based access control) in Phase 3.
"""
