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

GENERATED_AT = "2026-07-03T16:00:00Z"

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
    # Wave-6 expansion: niche/advanced internals
    "oop_internals": "OOP Internals: Descriptors & MRO",
    "memory_lifetime": "Memory Model & Object Lifetime",
    "concurrency_foundations": "Concurrency Foundations",
    "modern_syntax": "Modern Python Syntax",
    "functools_operator": "functools, operator & itertools",
    "binary_data_struct": "Bytes, Buffers & struct",
    "numeric_precision": "Numeric Precision",
    "introspection_metaprogramming": "Introspection & Metaprogramming",
    "typing_runtime": "Typing at the Runtime Boundary",
    # Wave-6 expansion: applied Python
    "scripting_automation": "Scripting & Automation",
    "pathlib_patterns": "pathlib & Path Logic",
    "cli_parsing": "CLI Argument Parsing",
    "http_shapes": "HTTP Request Shapes",
    "sqlite_patterns": "SQLite Patterns",
    "logging_diagnostics": "Logging & Diagnostics",
    "config_parsing": "Config Parsing & Precedence",
    "functional_style": "Functional-Style Python",
    "caching_performance": "Caching & Performance",
    "secure_coding": "Secure Coding",
    "dataframe_thinking": "DataFrame Thinking",
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
# Heaps come before graphs: the graphs unit's shortest-path lesson uses heapq.
CAREER_UNIT_ORDER = [
    *_ORIGINAL_AREAS,
    "linked_lists_patterns",
    "trees_lite",
    "heaps_topk",
    "graphs_lite",
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
            ("heaps_topk", 1),
            ("graphs_lite", 1),
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
        # language_models comes before eval_metrics and tokenization: both the
        # BLEU/perplexity lessons and the BPE lessons build on n-gram models.
        "areas": [
            ("python_refresh", 1),
            ("loops_lists_strings", 1),
            ("dicts_sets_tuples", 1),
            ("collections_itertools", 1),
            ("classic_ml_from_scratch", 1),
            ("autodiff_scalar_engine", 1),
            ("language_models_from_scratch", 1),
            ("eval_metrics_for_models", 1),
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
        "description": "What actually happens inside a language model: n-gram probabilities, tokenization, embeddings and retrieval, and the attention mechanism — all built by hand.",
        "outcomes": [
            "Train BPE merges and tokenize unseen text with them",
            "Compute sequence probabilities, perplexity, and temperature scaling",
            "Implement cosine retrieval, BM25, and single-head attention",
        ],
        # language_models first: the BPE tokenization lessons assume n-gram
        # language models, not the other way around.
        "areas": [
            ("language_models_from_scratch", 1),
            ("tokenization_bpe", 1),
            ("embeddings_similarity_search", 1),
            ("attention_mechanics", 1),
        ],
    },
    {
        "id": "path.career.python_software_engineer",
        "path_type": "career",
        "title": "Python Software Engineer",
        "slug": "python-software-engineer",
        "description": (
            "The deep-internals arc that separates a Python user from a Python "
            "engineer: the object model and descriptors, the memory system, "
            "concurrency, modern syntax, the functools/itertools toolbox, binary "
            "data, numeric precision, introspection, and runtime typing — the "
            "knowledge you reach for when other people's code misbehaves."
        ),
        "outcomes": [
            "Reason about descriptors, the MRO, and __slots__ from first principles",
            "Explain reference counting, cycles, and the GIL under pressure",
            "Choose threads, processes, or asyncio by workload with confidence",
            "Wield modern syntax, functools, struct, Decimal, and inspect fluently",
            "Understand where type hints act at runtime and where they don't",
        ],
        "areas": [
            ("python_refresh", 1),
            ("oop_classes", 1),
            ("modern_syntax", 1),
            ("oop_internals", 1),
            ("functools_operator", 1),
            ("typing_runtime", 1),
            ("numeric_precision", 1),
            ("binary_data_struct", 1),
            ("memory_lifetime", 1),
            ("introspection_metaprogramming", 1),
            ("concurrency_foundations", 1),
            ("mixed_capstones", 1),
        ],
    },
    {
        "id": "path.career.python_automation_engineer",
        "path_type": "career",
        "title": "Python Automation & Backend Engineer",
        "slug": "python-automation-and-backend",
        "description": (
            "The working-developer arc: build robust scripts and services from "
            "files, dates, and CLIs through HTTP clients, SQLite, logging, config, "
            "and secure coding — the practical Python that ships tools, glues "
            "systems, and stays up at 3 a.m."
        ),
        "outcomes": [
            "Architect automation as testable plan-then-act pipelines",
            "Parse files, paths, CLIs, and config with precedence correctly",
            "Model HTTP clients and SQLite access with retry and safety",
            "Log for incidents and write code that resists injection",
        ],
        "areas": [
            ("python_refresh", 1),
            ("error_handling", 1),
            ("files_formats", 1),
            ("datetime_handling", 1),
            ("scripting_automation", 1),
            ("pathlib_patterns", 1),
            ("cli_parsing", 1),
            ("config_parsing", 1),
            ("logging_diagnostics", 1),
            ("http_shapes", 1),
            ("sqlite_patterns", 1),
            ("secure_coding", 1),
            ("mixed_capstones", 1),
        ],
    },
    {
        "id": "path.skill.python_internals",
        "path_type": "skill",
        "title": "Python Internals",
        "slug": "python-internals",
        "description": "The object model up close: descriptors and the MRO, the memory system and the GIL, and reading a program with inspect and dis.",
        "outcomes": [
            "Explain descriptors, C3 linearization, and __slots__",
            "Reason about refcounting, cycles, weakrefs, and the GIL",
            "Introspect signatures, closures, and bytecode",
        ],
        "areas": [
            ("oop_internals", 1),
            ("memory_lifetime", 1),
            ("introspection_metaprogramming", 1),
        ],
    },
    {
        "id": "path.skill.modern_python",
        "path_type": "skill",
        "title": "Modern Python",
        "slug": "modern-python",
        "description": "The idioms of contemporary Python: structural pattern matching, exception groups, the walrus, the functools/itertools deep cuts, and runtime typing.",
        "outcomes": [
            "Use match/case, except*, and modern parameter syntax well",
            "Reach for singledispatch, partial, and itertools deep cuts",
            "Handle type hints at the runtime boundary",
        ],
        "areas": [
            ("modern_syntax", 1),
            ("functools_operator", 1),
            ("typing_runtime", 1),
        ],
    },
    {
        "id": "path.skill.bytes_and_numbers",
        "path_type": "skill",
        "title": "Bytes & Numbers",
        "slug": "bytes-and-numbers",
        "description": "The low-level data layers: bytes, struct, memoryview and buffers, plus float pitfalls, Decimal, and Fraction for numbers that must be exact.",
        "outcomes": [
            "Pack, unpack, and view binary data without copying",
            "Choose float, Decimal, or Fraction by domain and avoid the traps",
        ],
        "areas": [("binary_data_struct", 1), ("numeric_precision", 1)],
    },
    {
        "id": "path.skill.automation_toolkit",
        "path_type": "skill",
        "title": "Automation Toolkit",
        "slug": "automation-toolkit",
        "description": "Everything a robust script needs: plan-then-act architecture, path logic, CLI parsing, and layered configuration.",
        "outcomes": [
            "Build automation as testable plans separated from actions",
            "Handle paths, CLI arguments, and config precedence correctly",
        ],
        "areas": [
            ("scripting_automation", 1),
            ("pathlib_patterns", 1),
            ("cli_parsing", 1),
            ("config_parsing", 1),
        ],
    },
    {
        "id": "path.skill.backend_services",
        "path_type": "skill",
        "title": "Backend & Web Services",
        "slug": "backend-and-web-services",
        "description": "The service developer's core: HTTP request/response shapes and retry logic, SQLite access, and diagnostics-grade logging.",
        "outcomes": [
            "Model HTTP clients with status handling and backoff",
            "Query SQLite safely with parameters, joins, and transactions",
            "Instrument code with leveled, structured logging",
        ],
        "areas": [
            ("http_shapes", 1),
            ("sqlite_patterns", 1),
            ("logging_diagnostics", 1),
        ],
    },
    {
        "id": "path.skill.robust_and_fast",
        "path_type": "skill",
        "title": "Robust & Fast Python",
        "slug": "robust-and-fast-python",
        "description": "Write code that is both safe and quick: functional-style composition, caching and Big-O in practice, and secure coding against injection and secret leaks.",
        "outcomes": [
            "Compose transformations and know when a loop is clearer",
            "Cache correctly and spot accidental quadratics",
            "Validate at the boundary and defeat injection structurally",
        ],
        "areas": [
            ("functional_style", 1),
            ("caching_performance", 1),
            ("secure_coding", 1),
        ],
    },
    {
        "id": "path.skill.data_without_libraries",
        "path_type": "skill",
        "title": "Data Analysis Without the Libraries",
        "slug": "data-without-libraries",
        "description": "The dataframe mindset in pure Python: columnar layout, boolean masking, and split-apply-combine — so pandas is never magic and never mandatory.",
        "outcomes": [
            "Think in columns and vectorized operations",
            "Filter with masks and summarize with split-apply-combine",
        ],
        "areas": [("dataframe_thinking", 1)],
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
        "eval_metrics_for_models": "Classic ML, autodiff, language models, and evaluation — the ML core",
        "tokenization_bpe": "You build and tokenize language models by hand",
        "attention_mechanics": "AI engineer: attention itself, implemented from scratch",
    },
    "path.career.python_software_engineer": {
        "oop_classes": "Object-oriented foundations set",
        "typing_runtime": "Modern syntax, functools, and typing mastered",
        "binary_data_struct": "Down to bytes and exact numbers",
        "concurrency_foundations": "Internals, memory, and concurrency conquered",
        "mixed_capstones": "Engineer: you reason about Python from the inside out",
    },
    "path.career.python_automation_engineer": {
        "datetime_handling": "Files, dates, and robust I/O handled",
        "config_parsing": "Scripting, CLIs, and config precedence down",
        "logging_diagnostics": "Diagnostics-grade instrumentation in place",
        "secure_coding": "Backend, database, and secure-coding skills complete",
        "mixed_capstones": "Automation engineer: you ship tools that stay up",
    },
}


def area_key(area: str, wave: int) -> str:
    return area if wave == 1 else f"{area}_w2"


def order_lessons(lessons: list[str], concepts: dict[str, set], prereqs: dict[str, set]) -> list[str]:
    """Stable topological sort: a lesson whose prerequisites are taught by a
    sibling lesson in the same unit comes after that sibling. Ties keep id
    order; a cycle falls back to id order for the remainder."""
    remaining = list(lessons)
    taught: set = set()
    ordered: list[str] = []
    while remaining:
        taught_by_remaining = set().union(*(concepts[l] for l in remaining))
        pick = None
        for lesson in remaining:
            unmet_here = prereqs[lesson] - taught
            if not (unmet_here & (taught_by_remaining - concepts[lesson])):
                pick = lesson
                break
        if pick is None:  # dependency cycle; keep deterministic id order
            ordered.extend(remaining)
            break
        remaining.remove(pick)
        ordered.append(pick)
        taught |= concepts[pick]
    return ordered


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
    concepts: dict[str, set] = {}
    prereqs: dict[str, set] = {}
    lesson_ids: set[str] = set()
    for pool, kind in ((catalog.lessons, "lesson"), (catalog.exercises, "exercise"), (catalog.quizzes, "quiz")):
        for item in pool:
            concepts[item.id] = set(item.concepts)
            prereqs[item.id] = set(item.prerequisites)
            if kind == "lesson":
                lesson_ids.add(item.id)
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
                order_lessons(sorted(kinds.get("lesson", [])), concepts, prereqs),
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

        # Prior knowledge the path presumes: prerequisites of items that no
        # LESSON at an earlier position in the path teaches. Exercises and
        # quizzes tag concepts they practice, but only lessons teach, so
        # assumed_concepts stays honest ("do this path knowing X") instead of
        # crediting a late drill with teaching a fundamental.
        assumed: set = set()
        taught: set = set()
        for unit in units:
            for item_id in unit["items"]:
                assumed |= prereqs[item_id] - taught - assumed
                if item_id in lesson_ids:
                    taught |= concepts[item_id]

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
            "assumed_concepts": sorted(assumed),
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
