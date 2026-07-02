"""The ``validate-content`` action: the CLI's one allowed local computation.

This validates repo content, not learner code, so it does not violate the
HTTP-only-for-learner-actions rule. It reuses the API's own validator
(``learn_code_api.content.validator``) rather than re-implementing it. The
import is deferred to call time so the rest of the CLI (pure HTTP) does not
depend on the API package being importable.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def validate(
    content_root: Path,
    *,
    profile: str = "seed",
    include_drafts: bool = False,
    run_solutions: bool = True,
) -> Any:
    """Return the validator's ``ValidationReport`` for ``content_root``."""
    from learn_code_api.content.validator import validate_content_tree

    return validate_content_tree(
        content_root,
        profile=profile,
        include_drafts=include_drafts,
        run_solutions=run_solutions,
    )


def render_report(report: Any) -> str:
    """Terse pass/fail summary of a ``ValidationReport``."""
    if report.ok:
        count = len(report.catalog.exercises) if report.catalog else 0
        return f"content OK: {count} exercise(s) validated"
    lines = [f"content INVALID: {len(report.issues)} issue(s)"]
    for issue in report.issues:
        lines.append(f"- {issue.path}: {issue.message}")
    return "\n".join(lines)
