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
    # Wave-3 expansion
    "oop_classes": "Object-Oriented Python",
    "iterators_generators": "Iterators & Generators",
    "decorators_closures": "Closures & Decorators",
    "error_handling": "Errors & Exceptions",
    "collections_itertools": "Collections & Itertools",
    "regex_text_processing": "Regex & Text Processing",
    "linked_lists_patterns": "Linked Lists",
    "trees_lite": "Trees",
    "graphs_lite": "Graphs",
    "heaps_topk": "Heaps & Top-K",
    "intervals_greedy": "Intervals & Greedy",
    "dp_recognition": "Dynamic Programming",
    "data_wrangling_python": "Pure-Python Data Wrangling",
    "grid_simulation": "Grids & Simulation",
    "bit_number_theory": "Bits & Number Theory",
    # Wave-4 expansion: practical Python + capstones
    "files_formats": "Files & Data Formats",
    "datetime_handling": "Dates & Times",
    "testing_concepts": "Testing & Invariants",
    "type_hints": "Type Hints & Contracts",
    "capstone_ledger": "Capstone: The Market Ledger",
    "capstone_observatory": "Capstone: The Observatory Night Logs",
    "capstone_dispatch": "Capstone: The Courier Dispatch Board",
    # Wave-5 expansion: AI & ML from scratch
    "classic_ml_from_scratch": "Classic ML from Scratch",
    "autodiff_scalar_engine": "Autodiff from Scratch",
    "eval_metrics_for_models": "Evaluating Models",
    "language_models_from_scratch": "Language Models from Scratch",
    "tokenization_bpe": "Tokenization & BPE",
    "embeddings_similarity_search": "Embeddings & Retrieval",
    "attention_mechanics": "Attention Mechanics",
}

_ORIGINAL_AREAS = [
    "python_refresh",
    "loops_lists_strings",
    "dicts_sets_tuples",
    "debugging",
    "brute_force_bigo",
    "hashmap_set",
    "two_pointers",
    "sliding_window",
    "prefix_sums",
    "stack_queue_bfs",
    "binary_search",
    "recursion_backtracking",
]

# Interview prep now runs through the advanced pattern families before capstones.
CAREER_UNIT_ORDER = [
    *_ORIGINAL_AREAS,
    "linked_lists_patterns",
    "trees_lite",
    "graphs_lite",
    "heaps_topk",
    "intervals_greedy",
    "dp_recognition",
    "mixed_capstones",
]

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
        "description": "Dictionaries, sets, tuples, and sorting — then the structures they build: objects, linked lists, and trees.",
        "outcomes": [
            "Pick the right container for the job",
            "Sort with keys and reason about lookup costs",
            "Model data with classes and traverse linked and tree-shaped structures",
        ],
        "areas": [
            ("dicts_sets_tuples", 1),
            ("dicts_sets_tuples", 2),
            ("oop_classes", 1),
            ("linked_lists_patterns", 1),
            ("trees_lite", 1),
        ],
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
        "description": "Prefix sums, stacks and queues, binary search, recursion, heaps, intervals, and mixed capstones.",
        "outcomes": [
            "Apply prefix sums, stacks, and binary search to fresh problems",
            "Reach for heaps and greedy interval sweeps when they fit",
            "Hold your own on mixed problems that hide which pattern applies",
        ],
        "areas": [
            ("prefix_sums", 1),
            ("stack_queue_bfs", 1),
            ("binary_search", 1),
            ("recursion_backtracking", 1),
            ("heaps_topk", 1),
            ("intervals_greedy", 1),
            ("mixed_capstones", 1),
        ],
    },
    {
        "id": "path.career.python_developer_mastery",
        "path_type": "career",
        "title": "Python Developer Mastery",
        "slug": "python-developer-mastery",
        "description": (
            "The full beginner-to-advanced language arc: syntax fluency and core data "
            "structures, then every professional Python skill — OOP, iterators and "
            "generators, decorators, error handling, collections and itertools, regex, "
            "and pure-Python data wrangling — capped by mixed capstones."
        ),
        "outcomes": [
            "Write idiomatic Python from fundamentals through advanced idioms",
            "Model programs with classes, generators, and decorators",
            "Handle errors deliberately and process real-world text and records",
            "Finish with capstones that mix everything without hints",
        ],
        "areas": [
            ("python_refresh", 1),
            ("loops_lists_strings", 1),
            ("dicts_sets_tuples", 1),
            ("debugging", 1),
            ("error_handling", 1),
            ("oop_classes", 1),
            ("iterators_generators", 1),
            ("decorators_closures", 1),
            ("collections_itertools", 1),
            ("regex_text_processing", 1),
            ("files_formats", 1),
            ("datetime_handling", 1),
            ("data_wrangling_python", 1),
            ("testing_concepts", 1),
            ("type_hints", 1),
            ("mixed_capstones", 1),
            ("capstone_ledger", 1),
        ],
    },
    {
        "id": "path.career.algorithms_specialist",
        "path_type": "career",
        "title": "Algorithms Specialist",
        "slug": "algorithms-specialist",
        "description": (
            "A deep, pattern-by-pattern algorithms arc from Big-O and hashing through "
            "every classic interview family: linked lists, trees, graphs, heaps, "
            "intervals and greedy, dynamic programming, and bit-level puzzles."
        ),
        "outcomes": [
            "Name the pattern before you write a line of code",
            "Traverse linked, tree, and graph structures from memory",
            "Recognize DP structure and apply memoization or tabulation",
            "Handle bitwise and number-theory problems without flinching",
        ],
        "areas": [
            ("brute_force_bigo", 1),
            ("hashmap_set", 1),
            ("two_pointers", 1),
            ("sliding_window", 1),
            ("prefix_sums", 1),
            ("stack_queue_bfs", 1),
            ("binary_search", 1),
            ("recursion_backtracking", 1),
            ("linked_lists_patterns", 1),
            ("trees_lite", 1),
            ("graphs_lite", 1),
            ("heaps_topk", 1),
            ("intervals_greedy", 1),
            ("dp_recognition", 1),
            ("bit_number_theory", 1),
            ("mixed_capstones", 1),
            ("capstone_dispatch", 1),
        ],
    },
    {
        "id": "path.career.python_data_automation",
        "path_type": "career",
        "title": "Python Data & Automation Specialist",
        "slug": "python-data-and-automation",
        "description": (
            "A data-and-scripting arc: robust code with OOP and error handling, then "
            "collections and itertools, regex and text processing, pure-Python data "
            "wrangling, and grid/simulation puzzles, finishing with mixed capstones."
        ),
        "outcomes": [
            "Build robust, well-structured data-processing functions",
            "Group, join, pivot, and dedupe records with the standard library alone",
            "Parse and transform messy text with regex confidently",
        ],
        "areas": [
            ("oop_classes", 1),
            ("error_handling", 1),
            ("collections_itertools", 1),
            ("regex_text_processing", 1),
            ("files_formats", 1),
            ("datetime_handling", 1),
            ("data_wrangling_python", 1),
            ("grid_simulation", 1),
            ("capstone_observatory", 1),
        ],
    },
    {
        "id": "path.skill.oop_error_handling",
        "path_type": "skill",
        "title": "OOP & Error Handling",
        "slug": "oop-and-error-handling",
        "description": "Model data with classes and dunder methods, then make code resilient with structured exception handling.",
        "outcomes": [
            "Design small class hierarchies with clean interfaces",
            "Raise, catch, and define exceptions deliberately",
        ],
        "areas": [("oop_classes", 1), ("error_handling", 1)],
    },
    {
        "id": "path.skill.generators_decorators",
        "path_type": "skill",
        "title": "Generators & Decorators",
        "slug": "generators-and-decorators",
        "description": "Master lazy iteration with generators and higher-order composition with closures and decorators — the two most senior-signaling Python idioms.",
        "outcomes": [
            "Write and chain generator pipelines",
            "Build decorators, including parameterized and stacked ones",
        ],
        "areas": [("iterators_generators", 1), ("decorators_closures", 1)],
    },
    {
        "id": "path.skill.advanced_interview_patterns",
        "path_type": "skill",
        "title": "Advanced Interview Patterns",
        "slug": "advanced-interview-patterns",
        "description": "The four classic families most prep skips: linked lists, trees, graphs, and heaps/top-k, simulated with plain data structures.",
        "outcomes": [
            "Reverse, merge, and cycle-check linked structures",
            "Traverse trees and graphs in every standard order",
            "Solve top-k and k-way-merge problems with heaps",
        ],
        "areas": [
            ("linked_lists_patterns", 1),
            ("trees_lite", 1),
            ("graphs_lite", 1),
            ("heaps_topk", 1),
        ],
    },
    {
        "id": "path.skill.greedy_intervals_dp",
        "path_type": "skill",
        "title": "Greedy, Intervals & Dynamic Programming",
        "slug": "greedy-intervals-and-dp",
        "description": "From greedy interval-sweep reasoning to recognizing and solving overlapping-subproblem DP.",
        "outcomes": [
            "Merge, sweep, and schedule intervals greedily",
            "Spot overlapping subproblems and memoize them away",
        ],
        "areas": [("intervals_greedy", 1), ("dp_recognition", 1)],
    },
    {
        "id": "path.skill.text_data_collections",
        "path_type": "skill",
        "title": "Text, Data & Collections",
        "slug": "text-data-and-collections",
        "description": "Regex-powered text processing, the collections/itertools toolbox, and pandas-style wrangling in pure Python.",
        "outcomes": [
            "Extract and rewrite structured text with regex",
            "Group, join, and pivot records with stdlib tools",
        ],
        "areas": [
            ("regex_text_processing", 1),
            ("collections_itertools", 1),
            ("data_wrangling_python", 1),
        ],
    },
    {
        "id": "path.skill.grid_puzzles_bits",
        "path_type": "skill",
        "title": "Grid Puzzles & Bits",
        "slug": "grid-puzzles-and-bits",
        "description": "Spatial reasoning on 2D grids and simulations, plus bitwise tricks and number theory for the math-minded.",
        "outcomes": [
            "Flood-fill, rotate, and simulate on 2D grids",
            "Use bitmasks, GCD, and modular arithmetic fluently",
        ],
        "areas": [("grid_simulation", 1), ("bit_number_theory", 1)],
    },
    {
        "id": "path.career.ai_engineer_python",
        "path_type": "career",
        "title": "AI Engineer Python",
        "slug": "ai-engineer-python",
        "description": (
            "Build the machinery behind modern AI with nothing but Python: "
            "classic ML algorithms, a scalar autodiff engine, counting language "
            "models, byte-pair tokenization, embeddings and retrieval scoring, "
            "and scaled dot-product attention — every formula implemented and "
            "tested by hand, no numpy, no torch."
        ),
        "outcomes": [
            "Implement k-NN, k-means, and gradient descent from scratch",
            "Build and verify a micrograd-style backward pass",
            "Train a bigram language model and measure its perplexity",
            "Write BPE tokenization, cosine retrieval, and attention by hand",
            "Evaluate models with precision/recall, BLEU-style overlap, and calibration",
        ],
        "areas": [
            ("python_refresh", 1),
            ("loops_lists_strings", 1),
            ("dicts_sets_tuples", 1),
            ("collections_itertools", 1),
            ("classic_ml_from_scratch", 1),
            ("autodiff_scalar_engine", 1),
            ("eval_metrics_for_models", 1),
            ("language_models_from_scratch", 1),
            ("tokenization_bpe", 1),
            ("embeddings_similarity_search", 1),
            ("attention_mechanics", 1),
        ],
    },
    {
        "id": "path.skill.practical_python",
        "path_type": "skill",
        "title": "Practical Python: Files, Formats & Dates",
        "slug": "practical-python-files-and-dates",
        "description": "The working developer's daily bread: parsing text, JSON, and CSV safely, and doing calendar math without off-by-one regrets.",
        "outcomes": [
            "Parse config files, JSON payloads, and quoted CSV correctly",
            "Do date arithmetic, recurrence, and timestamp parsing with datetime",
        ],
        "areas": [("files_formats", 1), ("datetime_handling", 1)],
    },
    {
        "id": "path.skill.testing_types",
        "path_type": "skill",
        "title": "Testing & Type Hints",
        "slug": "testing-and-type-hints",
        "description": "Write code you can trust: assertions, edge cases, and property-based thinking, plus type hints that turn signatures into contracts.",
        "outcomes": [
            "Design test cases with boundary analysis and property oracles",
            "Read and write typed signatures, unions, and structural contracts",
        ],
        "areas": [("testing_concepts", 1), ("type_hints", 1)],
    },
    {
        "id": "path.skill.ml_from_scratch",
        "path_type": "skill",
        "title": "Machine Learning from Scratch",
        "slug": "machine-learning-from-scratch",
        "description": "The algorithms under every ML library, implemented in pure Python: distances, clustering, gradient descent, backprop, and the metrics that judge them.",
        "outcomes": [
            "Implement k-NN, k-means, and perceptron updates by hand",
            "Build and numerically verify a scalar autodiff backward pass",
            "Score models with confusion matrices, F1, and calibration error",
        ],
        "areas": [
            ("classic_ml_from_scratch", 1),
            ("autodiff_scalar_engine", 1),
            ("eval_metrics_for_models", 1),
        ],
    },
    {
        "id": "path.skill.llm_internals",
        "path_type": "skill",
        "title": "LLM Internals",
        "slug": "llm-internals",
        "description": "What actually happens inside a language model: tokenization, n-gram probabilities, embeddings and retrieval, and the attention mechanism — all built by hand.",
        "outcomes": [
            "Train BPE merges and tokenize unseen text with them",
            "Compute sequence probabilities, perplexity, and temperature scaling",
            "Implement cosine retrieval, BM25, and single-head attention",
        ],
        "areas": [
            ("tokenization_bpe", 1),
            ("language_models_from_scratch", 1),
            ("embeddings_similarity_search", 1),
            ("attention_mechanics", 1),
        ],
    },
]


# Milestone labels shown when the learner finishes these units — waypoints
# that break long career paths into celebrated sections.
MILESTONES = {
    "path.career.python_interview_prep": {
        "debugging": "Fundamentals complete — you write working Python",
        "sliding_window": "Core patterns down — half the interview toolkit is yours",
        "recursion_backtracking": "Every classic pattern family covered",
        "dp_recognition": "Advanced families done — capstones ahead",
        "mixed_capstones": "Interview-ready: the full arc is complete",
    },
    "path.career.python_developer_mastery": {
        "debugging": "Fundamentals complete — you write working Python",
        "decorators_closures": "The senior idioms — OOP, generators, decorators — are yours",
        "regex_text_processing": "Text and data tooling mastered",
        "type_hints": "You test and type like a professional",
        "capstone_ledger": "Mastery: you built a complete system from scratch",
    },
    "path.career.algorithms_specialist": {
        "sliding_window": "Array patterns mastered",
        "recursion_backtracking": "Search and recursion under your belt",
        "heaps_topk": "Linked, tree, graph, and heap structures conquered",
        "bit_number_theory": "The whole pattern catalog — including DP and bits",
        "capstone_dispatch": "Specialist: you composed every pattern into one system",
    },
    "path.career.python_data_automation": {
        "error_handling": "Robust code foundations set",
        "regex_text_processing": "Text processing toolkit complete",
        "data_wrangling_python": "You wrangle data with the stdlib alone",
        "capstone_observatory": "Automation pro: a real pipeline, built end to end",
    },
    "path.career.ai_engineer_python": {
        "collections_itertools": "Python foundations locked in",
        "eval_metrics_for_models": "Classic ML, autodiff, and evaluation — the ML core",
        "tokenization_bpe": "You build and tokenize language models by hand",
        "attention_mechanics": "AI engineer: attention itself, implemented from scratch",
    },
}


def area_key(area: str, wave: int) -> str:
    return area if wave == 1 else f"{area}_w2"


def interleave_items(lessons: list[str], exercises: list[str], quizzes: list[str]) -> list[str]:
    """Lessons teach first; quizzes then interleave between exercise blocks so
    assessment lands mid-unit instead of stacking at the end."""
    if not quizzes or not exercises:
        return [*lessons, *exercises, *quizzes]
    blocks = len(quizzes) + 1
    per_block = math.ceil(len(exercises) / blocks)
    items = list(lessons)
    remaining = list(exercises)
    for quiz in quizzes:
        items.extend(remaining[:per_block])
        remaining = remaining[per_block:]
        items.append(quiz)
    items.extend(remaining)
    return items


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
            items = interleave_items(
                sorted(kinds.get("lesson", [])),
                sorted(kinds.get("exercise", [])),
                sorted(kinds.get("quiz", [])),
            )
            total_minutes += sum(minutes[item_id] for item_id in items)
            unit = {
                "id": f"unit.{key}",
                "title": unit_title(area, wave),
                "description": f"Lessons, drills, and quizzes for {AREA_TITLES[area].lower()}.",
                "items": items,
            }
            milestone = MILESTONES.get(spec["id"], {}).get(key)
            if milestone:
                unit["milestone"] = milestone
            units.append(unit)
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
