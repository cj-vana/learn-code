from __future__ import annotations

from pathlib import Path

from learn_code_api.content.loader import ContentLoadError, load_catalog
from learn_code_api.content.models import ContentCatalog, ExerciseContent, ValidationIssue, ValidationReport
from learn_code_api.content.sample_solution_runner import run_sample_solution

SEED_PROFILE_KNOWN_CONCEPTS = {
    "python.conditionals",
    "python.dictionaries",
    "python.functions",
    "python.lists",
    "python.loops",
    "python.strings",
    "patterns.filtering",
    "patterns.hash_map_counting",
    "patterns.running_total",
}

SUSPICIOUS_PLATFORM_NAMES = (
    "leetcode",
    "hacker rank",
    "hackerrank",
    "codewars",
    "codeforces",
    "project euler",
)


def validate_content_tree(
    content_root: Path,
    profile: str = "seed",
    include_drafts: bool = False,
    run_solutions: bool = True,
) -> ValidationReport:
    """Validate a content tree and optionally execute trusted sample solutions."""
    issues: list[ValidationIssue] = []

    try:
        catalog = load_catalog(content_root, include_drafts=include_drafts)
    except ContentLoadError as exc:
        return ValidationReport(
            ok=False,
            issues=[ValidationIssue(path=str(content_root), message=str(exc))],
            catalog=None,
        )

    known_concepts = set(SEED_PROFILE_KNOWN_CONCEPTS if profile == "seed" else [])
    for exercise in catalog.exercises:
        _validate_exercise(exercise, issues, known_concepts, run_solutions)

    return ValidationReport(ok=not issues, issues=issues, catalog=catalog)


def _validate_exercise(
    exercise: ExerciseContent,
    issues: list[ValidationIssue],
    known_concepts: set[str],
    run_solutions: bool,
) -> None:
    for concept in exercise.concepts:
        known_concepts.add(concept)

    for prerequisite in exercise.prerequisites:
        if prerequisite not in known_concepts:
            issues.append(
                ValidationIssue(
                    path=exercise.id,
                    message=f"missing prerequisite concept: {prerequisite}",
                )
            )

    if len(exercise.tests.public) < 3:
        issues.append(
            ValidationIssue(path=exercise.id, message="exercise must include at least 3 public tests")
        )
    if len(exercise.tests.validation) < 3:
        issues.append(
            ValidationIssue(path=exercise.id, message="exercise must include at least 3 validation tests")
        )

    _check_suspicious_metadata(exercise, issues)

    if run_solutions:
        result = run_sample_solution(exercise)
        if not result.ok:
            details = "; ".join(result.failures)
            issues.append(
                ValidationIssue(path=exercise.id, message=f"sample solution failed: {details}")
            )


def _check_suspicious_metadata(exercise: ExerciseContent, issues: list[ValidationIssue]) -> None:
    searchable_parts = [
        exercise.provenance.originality_notes,
        *exercise.provenance.inspiration_sources,
    ]
    searchable = "\n".join(searchable_parts).lower()
    for platform_name in SUSPICIOUS_PLATFORM_NAMES:
        if platform_name in searchable:
            issues.append(
                ValidationIssue(
                    path=exercise.id,
                    message=f"suspicious platform name in originality metadata: {platform_name}",
                )
            )
