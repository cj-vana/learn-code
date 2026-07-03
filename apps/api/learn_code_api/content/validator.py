from __future__ import annotations

from pathlib import Path

from learn_code_api.content.loader import ContentLoadError, load_catalog
from learn_code_api.content.models import (
    ContentCatalog,
    ExerciseContent,
    LessonContent,
    PathContent,
    QuizContent,
    ValidationIssue,
    ValidationReport,
)
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

# The full V1 content-library taxonomy: the controlled concept vocabulary the
# generated bank draws from. It is a superset of the seed concepts, so seed
# content also validates under the "library" profile. Enforced (like "seed") so
# every exercise's concepts and prerequisites reference a known concept.
LIBRARY_KNOWN_CONCEPTS = SEED_PROFILE_KNOWN_CONCEPTS | {
    # Python fundamentals
    "python.variables",
    "python.types",
    "python.operators",
    "python.tuples",
    "python.sets",
    "python.sorting",
    "python.comprehensions",
    "python.slicing",
    "python.debugging",
    # Complexity / general problem-solving
    "concepts.big_o",
    "patterns.brute_force",
    "patterns.set_membership",
    # Interview pattern families
    "patterns.two_pointers",
    "patterns.sliding_window",
    "patterns.prefix_sums",
    "patterns.stack",
    "patterns.queue_bfs",
    "patterns.binary_search",
    "patterns.recursion",
    "patterns.backtracking",
    # Wave-3 expansion: professional Python
    "python.classes",
    "python.dataclasses_dunder",
    "python.iterators_generators",
    "python.closures_decorators",
    "python.exceptions",
    "python.collections_module",
    "python.itertools_module",
    "python.regex",
    "python.string_formatting",
    "python.heapq_bisect",
    "python.trees_as_data",
    # Wave-3 expansion: advanced interview pattern families
    "patterns.linked_list",
    "patterns.tree_traversal",
    "patterns.graph_traversal",
    "patterns.dfs",
    "patterns.heap_topk",
    "patterns.intervals",
    "patterns.greedy",
    "patterns.dynamic_programming",
    "patterns.grid_traversal",
    "patterns.simulation",
    "patterns.state_machine",
    "patterns.bit_manipulation",
    # Wave-3 expansion: cross-cutting concepts
    "concepts.memoization",
    "concepts.grouping_aggregation",
    "concepts.number_theory",
    "concepts.space_complexity",
    # Wave-4 expansion: practical Python
    "python.json_csv",
    "python.datetime_module",
    "python.type_hints",
    "concepts.testing",
    # Wave-5 expansion: AI & ML from scratch
    "ai.gradients_autodiff",
    "ai.language_models",
    "ai.tokenization",
    "ai.classic_ml",
    "ai.embeddings_retrieval",
    "ai.attention_transformers",
    "ai.model_evaluation",
    "concepts.probability",
    # Wave-6 expansion: niche/advanced internals
    "python.descriptors_mro",
    "python.memory_model",
    "python.concurrency_model",
    "python.modern_syntax",
    "python.functools_operator",
    "python.binary_data",
    "python.numeric_precision",
    "python.introspection",
    # Wave-6 expansion: applied Python
    "python.pathlib_os",
    "python.cli_args",
    "python.http_model",
    "python.sqlite_sql",
    "python.logging_diagnostics",
    "python.config_parsing",
    "python.functional_style",
    "python.secure_coding",
    "concepts.performance",
    "concepts.dataframe_thinking",
}

_PROFILE_CONCEPTS = {
    "seed": SEED_PROFILE_KNOWN_CONCEPTS,
    "library": LIBRARY_KNOWN_CONCEPTS,
}

SUSPICIOUS_PLATFORM_NAMES = (
    "leetcode",
    "hacker rank",
    "hackerrank",
    "codesignal",
    "code signal",
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

    known_concepts = set(_PROFILE_CONCEPTS.get(profile, set()))
    enforce_known_concepts = profile in _PROFILE_CONCEPTS
    for exercise in catalog.exercises:
        _validate_exercise(
            exercise,
            issues,
            known_concepts,
            enforce_known_concepts,
            run_solutions,
        )
    for lesson in catalog.lessons:
        _validate_lesson(lesson, issues, known_concepts, enforce_known_concepts)
    for quiz in catalog.quizzes:
        _validate_quiz(quiz, issues, known_concepts, enforce_known_concepts)
    for path_item in catalog.paths:
        _validate_path(path_item, catalog, issues)

    ok = not any(issue.severity == "error" for issue in issues)
    return ValidationReport(ok=ok, issues=issues, catalog=catalog)


def _validate_exercise(
    exercise: ExerciseContent,
    issues: list[ValidationIssue],
    known_concepts: set[str],
    enforce_known_concepts: bool,
    run_solutions: bool,
) -> None:
    if enforce_known_concepts:
        for concept in exercise.concepts:
            if concept not in known_concepts:
                issues.append(
                    ValidationIssue(
                        path=exercise.id,
                        message=f"unknown exercise concept: {concept}",
                    )
                )
    else:
        known_concepts.update(exercise.concepts)

    for prerequisite in exercise.prerequisites:
        if prerequisite not in known_concepts:
            issues.append(
                ValidationIssue(
                    path=exercise.id,
                    message=f"unknown prerequisite concept: {prerequisite}",
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


def _check_item_concepts(
    item_id: str,
    kind_label: str,
    concepts: list[str],
    prerequisites: list[str],
    issues: list[ValidationIssue],
    known_concepts: set[str],
    enforce_known_concepts: bool,
) -> None:
    if enforce_known_concepts:
        for concept in concepts:
            if concept not in known_concepts:
                issues.append(
                    ValidationIssue(
                        path=item_id, message=f"unknown {kind_label} concept: {concept}"
                    )
                )
    else:
        known_concepts.update(concepts)

    for prerequisite in prerequisites:
        if prerequisite not in known_concepts:
            issues.append(
                ValidationIssue(
                    path=item_id, message=f"unknown prerequisite concept: {prerequisite}"
                )
            )


def _validate_lesson(
    lesson: LessonContent,
    issues: list[ValidationIssue],
    known_concepts: set[str],
    enforce_known_concepts: bool,
) -> None:
    _check_item_concepts(
        lesson.id,
        "lesson",
        lesson.concepts,
        lesson.prerequisites,
        issues,
        known_concepts,
        enforce_known_concepts,
    )


def _validate_quiz(
    quiz: QuizContent,
    issues: list[ValidationIssue],
    known_concepts: set[str],
    enforce_known_concepts: bool,
) -> None:
    _check_item_concepts(
        quiz.id,
        "quiz",
        quiz.concepts,
        quiz.prerequisites,
        issues,
        known_concepts,
        enforce_known_concepts,
    )
    for question in quiz.questions:
        if question.correct_choice not in question.choices:
            issues.append(
                ValidationIssue(
                    path=quiz.id,
                    message=f"quiz question {question.id}: correct_choice is not one of choices",
                )
            )
        if enforce_known_concepts:
            for concept in question.concepts:
                if concept not in known_concepts:
                    issues.append(
                        ValidationIssue(
                            path=quiz.id,
                            message=f"unknown quiz question concept: {concept}",
                        )
                    )


def _validate_path(
    path_content: PathContent,
    catalog: ContentCatalog,
    issues: list[ValidationIssue],
) -> None:
    """Path items must reference published catalog content; ordering that
    puts an item before its prerequisite concepts is a warning, not an error."""
    items_by_id: dict[str, ExerciseContent | LessonContent | QuizContent] = {
        item.id: item
        for pool in (catalog.exercises, catalog.lessons, catalog.quizzes)
        for item in pool
    }

    concepts_seen: set[str] = set()
    for unit in path_content.units:
        for item_id in unit.items:
            item = items_by_id.get(item_id)
            if item is None:
                issues.append(
                    ValidationIssue(
                        path=path_content.id,
                        message=f"unknown path item: {item_id}",
                    )
                )
                continue
            missing = [
                prerequisite
                for prerequisite in item.prerequisites
                if prerequisite not in concepts_seen
            ]
            if missing:
                issues.append(
                    ValidationIssue(
                        path=path_content.id,
                        message=(
                            f"path item {item_id} appears before its prerequisite "
                            f"concepts are taught: {', '.join(sorted(missing))}"
                        ),
                        severity="warning",
                    )
                )
            concepts_seen.update(item.concepts)


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
