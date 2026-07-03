"""Human-readable labels for the concept taxonomy.

Concept ids (``python.loops``) are for machines; anything shown to a learner
goes through ``concept_label``. A test keeps this map in lockstep with the
validator's ``LIBRARY_KNOWN_CONCEPTS`` so no concept ever renders as a raw id.
"""

from __future__ import annotations

CONCEPT_TITLES: dict[str, str] = {
    # Python fundamentals
    "python.variables": "Variables",
    "python.types": "Basic types",
    "python.operators": "Operators",
    "python.conditionals": "Conditionals",
    "python.loops": "Loops",
    "python.functions": "Functions",
    "python.strings": "Strings",
    "python.lists": "Lists",
    "python.dictionaries": "Dictionaries",
    "python.tuples": "Tuples",
    "python.sets": "Sets",
    "python.sorting": "Sorting",
    "python.comprehensions": "Comprehensions",
    "python.slicing": "Slicing",
    "python.debugging": "Debugging",
    # Complexity / general problem-solving
    "concepts.big_o": "Big-O notation",
    "patterns.brute_force": "Brute-force search",
    "patterns.filtering": "Filtering",
    "patterns.running_total": "Running totals",
    "patterns.hash_map_counting": "Counting with hash maps",
    "patterns.set_membership": "Set membership",
    # Interview pattern families
    "patterns.two_pointers": "Two pointers",
    "patterns.sliding_window": "Sliding window",
    "patterns.prefix_sums": "Prefix sums",
    "patterns.stack": "Stacks",
    "patterns.queue_bfs": "Queues & BFS",
    "patterns.binary_search": "Binary search",
    "patterns.recursion": "Recursion",
    "patterns.backtracking": "Backtracking",
    "patterns.linked_list": "Linked lists",
    "patterns.tree_traversal": "Tree traversal",
    "patterns.graph_traversal": "Graph traversal",
    "patterns.dfs": "Depth-first search",
    "patterns.heap_topk": "Heaps & top-k",
    "patterns.intervals": "Intervals",
    "patterns.greedy": "Greedy algorithms",
    "patterns.dynamic_programming": "Dynamic programming",
    "patterns.grid_traversal": "Grid traversal",
    "patterns.simulation": "Simulation",
    "patterns.state_machine": "State machines",
    "patterns.bit_manipulation": "Bit manipulation",
    # Cross-cutting concepts
    "concepts.memoization": "Memoization",
    "concepts.grouping_aggregation": "Grouping & aggregation",
    "concepts.number_theory": "Number theory",
    "concepts.space_complexity": "Space complexity",
    "concepts.testing": "Testing",
    "concepts.probability": "Probability basics",
    "concepts.performance": "Performance",
    "concepts.dataframe_thinking": "DataFrame thinking",
    # Professional Python
    "python.classes": "Classes",
    "python.dataclasses_dunder": "Dataclasses & dunder methods",
    "python.iterators_generators": "Iterators & generators",
    "python.closures_decorators": "Closures & decorators",
    "python.exceptions": "Exceptions",
    "python.collections_module": "The collections module",
    "python.itertools_module": "The itertools module",
    "python.regex": "Regular expressions",
    "python.string_formatting": "String formatting",
    "python.heapq_bisect": "heapq & bisect",
    "python.trees_as_data": "Trees as data",
    "python.json_csv": "JSON & CSV",
    "python.datetime_module": "The datetime module",
    "python.type_hints": "Type hints",
    # AI & ML from scratch
    "ai.gradients_autodiff": "Gradients & autodiff",
    "ai.language_models": "Language models",
    "ai.tokenization": "Tokenization",
    "ai.classic_ml": "Classic machine learning",
    "ai.embeddings_retrieval": "Embeddings & retrieval",
    "ai.attention_transformers": "Attention & transformers",
    "ai.model_evaluation": "Model evaluation",
    # Internals & applied Python
    "python.descriptors_mro": "Descriptors & the MRO",
    "python.memory_model": "The memory model",
    "python.concurrency_model": "Concurrency",
    "python.modern_syntax": "Modern syntax",
    "python.functools_operator": "functools & operator",
    "python.binary_data": "Binary data",
    "python.numeric_precision": "Numeric precision",
    "python.introspection": "Introspection",
    "python.pathlib_os": "pathlib & the filesystem",
    "python.cli_args": "CLI arguments",
    "python.http_model": "HTTP fundamentals",
    "python.sqlite_sql": "SQLite & SQL",
    "python.logging_diagnostics": "Logging",
    "python.config_parsing": "Config parsing",
    "python.functional_style": "Functional style",
    "python.secure_coding": "Secure coding",
}


def concept_label(concept_id: str) -> str:
    """Readable label for a concept id; falls back to a cleaned-up id."""
    label = CONCEPT_TITLES.get(concept_id)
    if label is not None:
        return label
    return concept_id.split(".", 1)[-1].replace("_", " ").title()
