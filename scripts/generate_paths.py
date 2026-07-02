"""Generate the seed learning paths from the existing content catalog.

Deterministic: unit items are the area's lessons, then exercises, then quizzes,
each sorted by id, so re-running against the same catalog reproduces the same
files. Run from the repo root:

    .venv/bin/python scripts/generate_paths.py
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps" / "api"))

from learn_code_api.content.loader import load_catalog  # noqa: E402

CONTENT_ROOT = REPO_ROOT / "content" / "python"
PATHS_DIR = CONTENT_ROOT / "paths"

GENERATED_AT = "2026-07-02T18:00:00Z"

AREA_TITLES = {
    "python_refresh": "Python Refresh",
    "loops_lists_strings": "Loops, Lists & Strings",
    "dicts_sets_tuples": "Dicts, Sets & Tuples",
    "debugging": "Debugging",
    "brute_force_bigo": "Brute Force & Big-O",
    "hashmap_set": "Hash Maps & Sets",
    "two_pointers": "Two Pointers",
    "sliding_window": "Sliding Window",
    "prefix_sums": "Prefix Sums",
    "stack_queue_bfs": "Stacks, Queues & BFS",
    "binary_search": "Binary Search",
    "recursion_backtracking": "Recursion & Backtracking",
    "mixed_capstones": "Mixed Capstones",
}

CAREER_UNIT_ORDER = list(AREA_TITLES)

PATHS = [
    {
        "id": "path.career.python_interview_prep",
        "path_type": "career",
        "title": "Python Interview Prep",
        "slug": "python-interview-prep",
        "description": (
            "The full arc from Python fundamentals to timed-style mixed practice: "
            "refresh the language, master the core data structures, then drill "
            "every high-yield interview pattern with original problems."
        ),
        "outcomes": [
            "Write fluent, idiomatic Python under interview conditions",
            "Recognize the right algorithm pattern before you start coding",
            "Solve original easy and easy-medium problems across all core patterns",
            "Explain your solution and its Big-O out loud",
        ],
        "areas": [(area, 1) for area in CAREER_UNIT_ORDER],
    },
    {
        "id": "path.skill.python_foundations",
        "path_type": "skill",
        "title": "Python Foundations",
        "slug": "python-foundations",
        "description": "Variables, types, conditionals, and functions — the ground floor, twice over for retention.",
        "outcomes": [
            "Use variables, types, and conditionals without second-guessing",
            "Write and call functions with confidence",
        ],
        "areas": [("python_refresh", 1), ("python_refresh", 2)],
    },
    {
        "id": "path.skill.loops_lists_strings",
        "path_type": "skill",
        "title": "Loops, Lists & Strings",
        "slug": "loops-lists-strings",
        "description": "Iteration and the two workhorse sequence types, learned then reinforced.",
        "outcomes": [
            "Iterate cleanly with loops, enumerate, and slicing",
            "Manipulate lists and strings idiomatically",
        ],
        "areas": [("loops_lists_strings", 1), ("loops_lists_strings", 2)],
    },
    {
        "id": "path.skill.data_structures",
        "path_type": "skill",
        "title": "Data Structures in Python",
        "slug": "data-structures-in-python",
        "description": "Dictionaries, sets, tuples, and sorting — the containers interviews lean on.",
        "outcomes": [
            "Pick the right container for the job",
            "Sort with keys and reason about lookup costs",
        ],
        "areas": [("dicts_sets_tuples", 1), ("dicts_sets_tuples", 2)],
    },
    {
        "id": "path.skill.debugging",
        "path_type": "skill",
        "title": "Debugging & Pythonic Habits",
        "slug": "debugging-pythonic-habits",
        "description": "Read tracebacks, fix classic beginner mistakes, and build habits that prevent them.",
        "outcomes": [
            "Diagnose the most common Python errors from the traceback alone",
            "Spot and fix assignment-versus-comparison and scope mistakes",
        ],
        "areas": [("debugging", 1), ("debugging", 2)],
    },
    {
        "id": "path.skill.algorithm_patterns_1",
        "path_type": "skill",
        "title": "Algorithm Patterns I",
        "slug": "algorithm-patterns-1",
        "description": "Big-O, brute force, hashing, two pointers, and sliding window — the first pattern family.",
        "outcomes": [
            "Estimate Big-O before writing code",
            "Recognize hashing, two-pointer, and sliding-window shaped problems",
        ],
        "areas": [
            ("brute_force_bigo", 1),
            ("hashmap_set", 1),
            ("two_pointers", 1),
            ("sliding_window", 1),
        ],
    },
    {
        "id": "path.skill.algorithm_patterns_2",
        "path_type": "skill",
        "title": "Algorithm Patterns II",
        "slug": "algorithm-patterns-2",
        "description": "Prefix sums, stacks and queues, binary search, recursion, and mixed capstones.",
        "outcomes": [
            "Apply prefix sums, stacks, and binary search to fresh problems",
            "Hold your own on mixed problems that hide which pattern applies",
        ],
        "areas": [
            ("prefix_sums", 1),
            ("stack_queue_bfs", 1),
            ("binary_search", 1),
            ("recursion_backtracking", 1),
            ("mixed_capstones", 1),
        ],
    },
]


def area_key(area: str, wave: int) -> str:
    return area if wave == 1 else f"{area}_w2"


def unit_title(area: str, wave: int) -> str:
    base = AREA_TITLES[area]
    return base if wave == 1 else f"{base}: Round Two"


def main() -> None:
    catalog = load_catalog(CONTENT_ROOT)
    by_area: dict[str, dict[str, list]] = {}
    minutes: dict[str, int] = {}
    for pool, kind in ((catalog.lessons, "lesson"), (catalog.exercises, "exercise"), (catalog.quizzes, "quiz")):
        for item in pool:
            parts = item.id.split(".")
            if parts[1] != "library":
                continue
            by_area.setdefault(parts[2], {}).setdefault(kind, []).append(item.id)
            minutes[item.id] = item.estimated_time_minutes

    PATHS_DIR.mkdir(parents=True, exist_ok=True)
    for spec in PATHS:
        units = []
        total_minutes = 0
        for area, wave in spec["areas"]:
            key = area_key(area, wave)
            kinds = by_area.get(key)
            if kinds is None:
                raise SystemExit(f"no content found for area {key}")
            items = [
                *sorted(kinds.get("lesson", [])),
                *sorted(kinds.get("exercise", [])),
                *sorted(kinds.get("quiz", [])),
            ]
            total_minutes += sum(minutes[item_id] for item_id in items)
            units.append(
                {
                    "id": f"unit.{key}",
                    "title": unit_title(area, wave),
                    "description": f"Lessons, drills, and quizzes for {AREA_TITLES[area].lower()}.",
                    "items": items,
                }
            )
        doc = {
            "id": spec["id"],
            "kind": "path",
            "path_type": spec["path_type"],
            "version": 1,
            "language": "python",
            "title": spec["title"],
            "slug": spec["slug"],
            "description": spec["description"],
            "outcomes": spec["outcomes"],
            "estimated_hours": max(1, math.ceil(total_minutes / 60)),
            "review_status": "published",
            "source_status": "original",
            "provenance": {
                "brief_id": "brief.paths.v1",
                "author": "agent",
                "generated_at": GENERATED_AT,
                "inspiration_sources": [],
                "originality_notes": (
                    "Curated ordering over the repository's original content bank; "
                    "no external syllabus copied."
                ),
            },
            "units": units,
        }
        out = PATHS_DIR / f"{spec['slug']}.yml"
        out.write_text(yaml.safe_dump(doc, sort_keys=False, width=100), encoding="utf-8")
        print(f"wrote {out.relative_to(REPO_ROOT)} ({len(units)} units, ~{doc['estimated_hours']}h)")


if __name__ == "__main__":
    main()
