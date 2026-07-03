"""Terse, encouraging formatting for CLI output (spec lines 825-850).

Pure functions from response dicts to strings so they are unit-testable without
Typer. Keep it short: prompt/plan summary, concepts, test result summary, next
action, and the Ollama review summary when requested.
"""

from __future__ import annotations

from typing import Any

from learn_code_cli.docker_compose import COMPOSE_HINT
from learn_code_cli.http_client import ApiError

_FRIENDLY_ERRORS = {
    "content_not_found": "No such exercise.",
    "runner_unavailable": "The code runner isn't available right now. Try again once the stack is up.",
    "ollama_unavailable": "Ollama isn't available; tests still decide pass/fail.",
}


def friendly_error(error: ApiError) -> str:
    """Map an API error envelope to a terse, human message."""
    return _FRIENDLY_ERRORS.get(error.code, error.message)


def unreachable(api_url: str) -> str:
    return (
        f"Can't reach the API at {api_url}.\n"
        f"Start the stack from the repo root:\n  {COMPOSE_HINT}"
    )


def render_status(api_url: str) -> str:
    return f"API status: ok ({api_url})"


def render_plan(items: list[dict[str, Any]]) -> str:
    if not items:
        return "Nothing queued for today. You're caught up."
    lines = ["Today's plan:"]
    for item in items:
        concepts = ", ".join(item.get("concepts", [])) or "-"
        lines.append(
            f"- {item['title']} [{item['kind']}] "
            f"~{item['estimated_time_minutes']}m (priority {item['priority']:.2f})"
        )
        lines.append(f"    concepts: {concepts}")
        rationale = item.get("rationale") or {}
        if rationale.get("reason"):
            lines.append(f"    why: {rationale['reason']}")
    return "\n".join(lines)


def render_run(run: dict[str, Any]) -> str:
    lines = [_run_summary(run)]
    lines.extend(_failing_tests(run))
    if run.get("stderr"):
        lines.append(f"stderr: {run['stderr'].strip()}")
    return "\n".join(lines)


def render_submission(response: dict[str, Any]) -> str:
    run = response.get("run", {})
    delta = response.get("progress_delta", {})
    lines = [_run_summary(run)]
    lines.extend(_failing_tests(run))
    changed = ", ".join(delta.get("concepts_changed", [])) or "-"
    lines.append(
        f"mastery: {delta.get('mastery_before')} -> {delta.get('mastery_after')} "
        f"(concepts: {changed})"
    )
    if delta.get("review_due_at"):
        lines.append(f"next review: {delta['review_due_at']}")
    for action in response.get("next_actions", []):
        lines.append(f"next: {action}")
    return "\n".join(lines)


def render_lesson(detail: dict[str, Any]) -> str:
    lines = [
        f"{detail['title']}  ({detail.get('difficulty', '?')} · "
        f"{detail.get('estimated_time_minutes', '?')} min)",
        "",
        detail["body_markdown"],
    ]
    checkpoints = detail.get("checkpoints", [])
    if checkpoints:
        lines.extend(["", "Checkpoints:"])
        for number, checkpoint in enumerate(checkpoints, start=1):
            lines.append(f"  {number}. {checkpoint['question']}")
            lines.append(f"     -> {checkpoint['answer']} ({checkpoint['explanation']})")
    lines.extend(["", f"Mark it done in the browser: /lesson/{detail['id']}"])
    return "\n".join(lines)


def render_paths(items: list[dict[str, Any]]) -> str:
    if not items:
        return "No paths published yet."
    lines = []
    for item in items:
        marker = "enrolled" if item.get("enrolled") else "       -"
        level = item.get("level", "")
        level_part = f"{level}, " if level else ""
        lines.append(
            f"[{marker}] {item['percent_complete']:>3}%  {item['id']}  "
            f"({item['path_type']}, {level_part}{item['units']} units, ~{item['estimated_hours']}h)  "
            f"{item['title']}"
        )
    return "\n".join(lines)


def render_path_detail(detail: dict[str, Any]) -> str:
    lines = [
        f"{detail['title']}  ({detail['path_type']} path · ~{detail['estimated_hours']}h · "
        f"{detail['percent_complete']}% complete)",
        detail["description"],
    ]
    if detail.get("assumed_concepts"):
        lines.append(f"before you start: {', '.join(detail['assumed_concepts'])}")
    for unit in detail.get("units", []):
        lines.append("")
        unit_status = unit.get("status", "available")
        lock = " (locked until previous unit hits 70%)" if unit_status == "locked" else ""
        lines.append(f"{unit['title']}  [{unit['percent_complete']}%]{lock}")
        for item in unit.get("items", []):
            mark = "x" if item["status"] == "complete" else " "
            lines.append(
                f"  [{mark}] {item['kind']:<8} {item['title']}  ({item['id']})"
            )
        if unit.get("milestone") and unit_status == "complete":
            lines.append(f"  ** milestone: {unit['milestone']}")
    if detail.get("next_item_id"):
        lines.append("")
        lines.append(f"next: {detail['next_item_id']}")
    return "\n".join(lines)


def render_progress(summary: dict[str, Any]) -> str:
    lines = [
        f"streak: {summary.get('streak_days', 0)} days | "
        f"time: {summary.get('total_time_minutes', 0)}m",
    ]
    concepts = summary.get("concepts", [])
    if concepts:
        lines.append("concepts:")
        for concept in concepts:
            lines.append(
                f"- {concept['id']}: {concept['mastery']} ({concept['label']})"
            )
    else:
        lines.append("concepts: none yet")
    mistakes = summary.get("recent_mistakes", [])
    if mistakes:
        lines.append("recent mistakes: " + "; ".join(mistakes))
    if summary.get("next_recommended_action"):
        lines.append(f"next: {summary['next_recommended_action']}")
    return "\n".join(lines)


def render_review(review: dict[str, Any]) -> str:
    lines = [f"Ollama review ({review.get('status')}): {review.get('summary')}"]
    for label, key in (
        ("correctness", "correctness_notes"),
        ("readability", "readability_notes"),
        ("simplify", "python_simplifications"),
    ):
        for note in review.get(key, []) or []:
            lines.append(f"- {label}: {note}")
    if review.get("big_o_notes"):
        lines.append(f"- big-O: {review['big_o_notes']}")
    if review.get("next_improvement"):
        lines.append(f"next: {review['next_improvement']}")
    if review.get("encouragement"):
        lines.append(review["encouragement"])
    return "\n".join(lines)


def _run_summary(run: dict[str, Any]) -> str:
    status = run.get("status", "unknown")
    return (
        f"{status}: {run.get('passed', 0)} passed, {run.get('failed', 0)} failed "
        f"({run.get('duration_ms', 0)}ms)"
    )


def _failing_tests(run: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for entry in run.get("test_summary", []):
        if not entry.get("passed", True):
            message = entry.get("message") or "failed"
            lines.append(f"  x {entry.get('name')}: {message}")
    return lines
