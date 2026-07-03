# Comprehensive Python Topic Map — Next Content Waves

Synthesis of four research reports (AI/ML from scratch, niche/advanced internals, applied Python, curriculum-shape benchmarking) into a concrete blueprint for learn-code's next content waves. Platform constraint restated: autograded exercises run in a sandboxed `python:3.12-slim` container, **stdlib only, no pip/no numpy/no network/no real filesystem**, every exercise a single deterministic pure function graded on input/output values. Lessons (markdown) and quizzes (multiple choice) have no such constraint.

Existing baseline: 28 topic areas / ~750 items, covering fundamentals, debugging, all classic interview algorithm patterns (two pointers → DP → graphs → bits), and professional Python (OOP, iterators/generators, decorators, exceptions, collections/itertools, regex, pure-Python data wrangling). In progress: files/JSON/CSV, datetime, testing concepts, type hints, capstone projects.

Curriculum-shape benchmark (Exercism, Hyperskill, freeCodeCamp CFSD, roadmap.sh, CS50P) says: breadth is not the gap (learn-code's ~750 items already beats Exercism's 140 and rivals freeCodeCamp's 795-unit CFSD). The gap is (a) an explicit prerequisite/dependency structure and long-tailed difficulty distribution rather than a flat list, and (b) a structural mechanism for marking ecosystem/optional content as lesson-only vs core-autograded — which the stdlib-only constraint already gives this platform for free, mirroring roadmap.sh's "core path vs. pick-a-framework" split. Difficulty inside each new area below should cluster ~60-65% at intro/easy tiers with a long tail of advanced/capstone items, not spread evenly.

---

## 1. Proposed New Content Areas, by Wave

Each area: `key` (snake_case, matches `content/python/library/<key>` convention), title, 3-lesson outline, 12-exercise topic list (stdlib-only, single pure function each), 2-quiz focus, difficulty tier, career/skill path.

### Wave A — AI & ML From Scratch

#### `autodiff-scalar-engine`
**Title**: Scalar Autodiff — Build a Micrograd-Style Engine
**Lessons**:
1. What automatic differentiation is and why it powers every neural net (forward pass vs. backward pass, computational graph as DAG).
2. The `Value` node: wrapping a scalar with `data`, local derivatives, and a `_backward` closure per operation.
3. Topological sort + `.backward()`: how the chain rule composes across a whole graph.
**Exercises** (pure functions):
1. `add_forward(a, b)` — forward value of `a + b` node
2. `add_backward(grad_out)` — local gradient distribution for `+`
3. `mul_forward(a, b)` / `mul_backward(a, b, grad_out)` — product rule
4. `pow_forward(a, n)` / `pow_backward(a, n, grad_out)` — power rule
5. `tanh_forward(x)` / `tanh_backward(x, grad_out)` — nonlinearity + derivative
6. `exp_forward(x)` / `exp_backward(x, grad_out)`
7. `topo_sort(node_edges)` — given a DAG as adjacency dict, return valid topological order
8. `build_expression_value(ops)` — evaluate a small fixed expression tree given leaf values, return output
9. `chain_rule_compose(local_grads)` — multiply a list of local gradients into total gradient
10. `neuron_forward(weights, bias, inputs)` — weighted sum + tanh activation, no state
11. `mse_loss(predictions, targets)` — scalar loss pure function
12. `gradient_check(f, x, eps)` — numeric finite-difference gradient estimate vs analytic value (returns bool within tolerance)
**Quizzes**: (1) why closures capture the right local derivative per op; (2) reading a small computation graph and predicting `.grad` values by hand.
**Tier**: Advanced. **Path**: AI Engineer Python.

#### `language-models-from-scratch`
**Title**: Language Models From Scratch — Bigram to N-gram
**Lessons**:
1. Counting-based language models: bigram tables, conditional probability.
2. Smoothing (add-one/Laplace) and why raw counts fail on unseen pairs.
3. Evaluating a language model: perplexity and what it means.
**Exercises**:
1. `bigram_counts(corpus)` — build `{(a,b): count}` from a string/token list
2. `char_vocab(corpus)` — sorted unique-character vocabulary
3. `bigram_probabilities(counts)` — normalize counts into conditional probs
4. `laplace_smooth(counts, vocab_size)` — add-one smoothed probability table
5. `ngram_counts(corpus, n)` — generalize to n-grams
6. `next_token_distribution(context, ngram_table)` — probability dict for next token
7. `sequence_log_probability(tokens, bigram_probs)` — sum of log-probs
8. `perplexity(log_probs)` — `exp(-mean(log_probs))`
9. `most_likely_next(context, table)` — argmax next token (deterministic tie-break)
10. `train_test_split_tokens(tokens, ratio)` — deterministic split by index
11. `unk_token_replace(tokens, vocab)` — replace out-of-vocab tokens with `<unk>`
12. `interpolate_probabilities(p1, p2, lam)` — linear interpolation of two n-gram models
**Quizzes**: (1) greedy decoding vs sampling tradeoffs; (2) why perplexity is sensitive to vocabulary size/smoothing choice.
**Tier**: Advanced. **Path**: AI Engineer Python.

#### `tokenization-bpe`
**Title**: Tokenization — Byte-Pair Encoding From Scratch
**Lessons**:
1. From whitespace splitting to subword tokenization: why BPE exists.
2. The BPE training loop: count pairs, merge most frequent, repeat.
3. Encoding new text with a learned merge list; special tokens.
**Exercises**:
1. `word_to_symbols(word)` — split word into list of characters (+ end marker)
2. `pair_frequencies(corpus_symbols)` — `Counter` of adjacent symbol pairs
3. `most_frequent_pair(freqs)` — argmax pair with deterministic tie-break
4. `merge_pair(symbols, pair)` — merge one pair occurrence-wise in a symbol sequence
5. `merge_pair_in_corpus(corpus_symbols, pair)` — apply merge across whole corpus
6. `train_bpe(corpus, num_merges)` — return ordered list of learned merges
7. `apply_merges(word, merges)` — encode a new word using learned merge order
8. `vocab_from_merges(base_vocab, merges)` — build final vocabulary set
9. `tokenize_text(text, merges)` — full string → token list
10. `detokenize(tokens)` — reverse mapping back to string
11. `token_length_stats(tokens)` — min/max/avg token length (stdlib `statistics`)
12. `compression_ratio(original_chars, token_count)` — simple efficiency metric
**Quizzes**: (1) why BPE sits between char-level and word-level tokenization; (2) tracing one merge step by hand on a toy corpus.
**Tier**: Advanced. **Path**: AI Engineer Python.

#### `classic-ml-from-scratch`
**Title**: Classic ML Algorithms From Scratch (No NumPy)
**Lessons**:
1. Distance-based learning: Euclidean/Manhattan distance, k-NN classification.
2. Clustering: k-means as iterative assign/update.
3. Linear models: gradient descent on MSE/logistic loss, one step at a time.
**Exercises**:
1. `euclidean_distance(a, b)` — pure-tuple distance
2. `manhattan_distance(a, b)`
3. `nearest_centroid(point, centroids)` — index of closest centroid
4. `assign_clusters(points, centroids)` — list of cluster assignments
5. `update_centroids(points, assignments, k)` — recompute centroid means
6. `knn_predict(train_points, train_labels, query, k)` — majority vote
7. `perceptron_update(weights, bias, x, y, lr)` — one SGD step
8. `gradient_descent_step(params, grad, lr)` — generic param update
9. `mse_loss(predictions, targets)` / `mse_gradient(predictions, targets, inputs)`
10. `logistic_sigmoid(x)` — numerically stable sigmoid
11. `binary_cross_entropy(predictions, targets)`
12. `standardize_features(values)` — z-score normalization (mean/std via stdlib `statistics`)
**Quizzes**: (1) k-means convergence behavior and sensitivity to init; (2) when gradient descent diverges (learning rate too high) — reading a trace.
**Tier**: Intermediate/Advanced. **Path**: AI Engineer Python, Data/Algorithms.

#### `embeddings-similarity-search`
**Title**: Embeddings, Similarity, and Retrieval Mechanics
**Lessons**:
1. Vectors as meaning: what an embedding represents, dot product intuition.
2. Cosine similarity vs Euclidean distance for retrieval.
3. Chunking and scoring documents for search (precursor to RAG).
**Exercises**:
1. `dot_product(a, b)`
2. `magnitude(v)`
3. `cosine_similarity(a, b)`
4. `most_similar(query_vec, corpus_vecs)` — index of best match
5. `top_k_similar(query_vec, corpus_vecs, k)` — ranked indices
6. `normalize_vector(v)` — unit-length vector
7. `chunk_text(text, size, overlap)` — sliding window string chunker
8. `term_frequency(doc_tokens)` — dict of term counts
9. `inverse_document_frequency(corpus_token_lists)` — idf per term
10. `bm25_score(query_tokens, doc_tokens, corpus_stats, k1, b)` — BM25 formula
11. `rank_documents(query, docs, scorer)` — sort docs by a scoring function
12. `softmax(scores)` — numerically stable softmax over a list
**Quizzes**: (1) cosine vs Euclidean when vectors aren't normalized; (2) keyword (BM25) vs semantic (embedding) search tradeoffs.
**Tier**: Advanced. **Path**: AI Engineer Python.

#### `attention-mechanics`
**Title**: Attention Mechanics — Toy Scaled Dot-Product Attention
**Lessons**:
1. Queries, keys, values as a lookup-with-weights metaphor.
2. The attention formula step by step: scores → scale → softmax → weighted sum.
3. Why attention replaced recurrence (parallelism, long-range dependencies) — conceptual, ties to transformer capstone.
**Exercises**:
1. `attention_scores(query, keys)` — dot products, fixed small dims
2. `scale_scores(scores, dim_k)` — divide by `sqrt(dim_k)`
3. `softmax_stable(scores)` — max-subtraction softmax
4. `weighted_sum(weights, values)` — attention output vector
5. `single_head_attention(query, keys, values)` — compose the above
6. `causal_mask(scores)` — apply -inf mask above diagonal for a small fixed sequence
7. `multi_query_attention(query, keys_list, values_list)` — attention over multiple KV pairs
8. `positional_encoding_value(pos, dim, i)` — one sinusoidal PE component
9. `layer_norm_1d(vector, eps)` — mean/var normalize a small vector (stdlib only)
10. `residual_add(x, sublayer_out)` — trivial but tests understanding of skip connections
11. `attention_entropy(weights)` — how "peaked" vs "diffuse" attention is (Shannon entropy)
12. `average_attention_over_heads(head_outputs)` — combine fixed small multi-head outputs
**Quizzes**: (1) why we scale by `sqrt(d_k)`; (2) causal masking's role in autoregressive generation.
**Tier**: Advanced/Expert (careful fixed-small-dimension test design required per report 1). **Path**: AI Engineer Python.

#### `eval-metrics-for-models`
**Title**: Evaluation Metrics for ML/LLM Systems
**Lessons**:
1. Classification metrics: confusion matrix, precision/recall/F1, accuracy tradeoffs.
2. Generation metrics: perplexity, BLEU-style n-gram overlap.
3. Building a lightweight eval harness mentally (what production eval code checks).
**Exercises**:
1. `confusion_counts(predictions, labels)` — tp/fp/tn/fn dict
2. `accuracy(tp, tn, fp, fn)`
3. `precision(tp, fp)`
4. `recall(tp, fn)`
5. `f1_score(precision, recall)`
6. `macro_f1(per_class_f1)` — average across classes
7. `perplexity_from_log_probs(log_probs)`
8. `bleu_1gram(candidate_tokens, reference_tokens)` — simplified unigram precision
9. `exact_match(prediction, reference)` — normalized string equality
10. `mean_reciprocal_rank(ranked_lists, correct_answers)`
11. `roc_point(tp, fp, total_pos, total_neg)` — one TPR/FPR point
12. `calibration_bucket_error(confidences, correctness, num_buckets)` — simple ECE-style bucketing
**Quizzes**: (1) precision/recall tradeoff scenarios (spam filter vs medical screen); (2) why perplexity alone doesn't measure factual correctness.
**Tier**: Intermediate/Advanced. **Path**: AI Engineer Python, general Data.

*(Lesson/capstone-only, not autograded, still belongs to this wave — see Section 2: full NN training loops, BatchNorm, GPT assembly, transfer learning, real vector DBs, prompt engineering practice.)*

---

### Wave B — Niche / Advanced Internals

#### `oop-internals-descriptors-mro`
**Title**: OOP Internals — Descriptors, MRO, `__slots__`
**Lessons**:
1. The descriptor protocol (`__get__`/`__set__`/`__set_name__`) and how properties are built from it.
2. Multiple inheritance and C3 linearization — how Python resolves method lookup order.
3. `__slots__`: memory layout, tradeoffs, and interactions with inheritance.
**Exercises**:
1. `build_validated_field(min_val, max_val)` — returns a descriptor class instance behavior via a helper function that exercises get/set
2. `lazy_property_value(compute_fn, instance)` — memoizing descriptor pattern, function returns computed+cached value
3. `mro_order(class_hierarchy)` — given a diamond hierarchy dict, return linearization order
4. `resolve_method(class_hierarchy, method_owners, start_class)` — which ancestor's method wins
5. `has_dict_attr(instance)` — return whether instance has `__dict__` (slots vs not)
6. `slot_assignment_error(cls, attr, value)` — catches and returns whether `AttributeError` raised for non-declared slot
7. `register_subclass(base_registry, subclass_name)` — `__init_subclass__`-style registry update, pure dict operation
8. `virtual_subclass_check(abc_cls, candidate_cls)` — `issubclass` via `register()`
9. `total_ordering_compare(a, b, defined_ops)` — verify `functools.total_ordering` derives correct comparisons
10. `custom_format(value, spec)` — implement/exercise `__format__`-style dispatch
11. `identity_vs_equality(a, b)` — return `(a is b, a == b)` for given constructed values
11(alt). `intern_check(s1, s2)` — using `sys.intern`, return whether interned strings are identical objects
12. `subscriptable_capture(cls_getitem_args)` — what `__class_getitem__` captured, given input args
**Quizzes**: (1) predict MRO output for a given diamond hierarchy; (2) small-int cache / string interning gotchas — predict `is` results.
**Tier**: Advanced. **Path**: Professional Python / Software Engineer.

#### `memory-and-object-lifetime`
**Title**: Memory Model — References, Weak Refs, Object Lifetime
**Lessons**:
1. Reference counting basics and why `sys.getrefcount` is misleading (off-by-one).
2. Cyclic garbage collection: when refcounting alone isn't enough.
3. `weakref`: caches that don't keep objects alive.
**Exercises**:
1. `weak_cache_get_or_set(cache, key, factory)` — using `WeakValueDictionary` semantics simulated via plain dict + explicit invalidation logic
2. `is_evicted_after_del(weak_cache, key)` — deterministic check after forcing removal
3. `build_finalize_log(objects)` — simulate `weakref.finalize` callback ordering as pure function over a list
4. `find_reference_cycle(graph)` — given adjacency dict, detect a cycle (models what GC must find)
5. `topo_or_cycle(graph)` — return topological order or `None` if cyclic
6. `context_var_isolated_values(tasks)` — simulate `contextvars.copy_context()` isolation across "tasks" as pure input/output
7. `small_int_cache_hit(n)` — predict `is` behavior for ints in [-5, 256] vs outside
8. `string_literal_intern_predict(s)` — predict interning behavior for compile-time literal vs runtime-built string
9. `refcount_delta_predict(scenario)` — conceptual MCQ-shaped function stub (or keep as quiz — see note)
10. `gc_referents_of(obj_graph, node)` — return direct referents given adjacency dict
11. `gc_referrers_of(obj_graph, node)` — return direct referrers
12. `object_graph_memory_estimate(objects, sizes)` — sum sizes reachable from roots (models memory footprint reasoning)
**Quizzes**: (1) why `gc.collect()` matters only for cyclic garbage, not general refcounting; (2) GIL — what it protects, when released (lesson/quiz only, no exercise).
**Tier**: Advanced. **Path**: Professional Python / Software Engineer.

#### `concurrency-foundations`
**Title**: Concurrency Foundations — Without the Flakiness
**Lessons**:
1. threading vs multiprocessing vs asyncio: decision framework (I/O-bound vs CPU-bound vs GIL).
2. The event loop model: what `await` actually does (coroutine state machine).
3. `contextvars` and task-local isolation.
**Exercises** (all deterministic — no real timing/sleep/network):
1. `merge_producer_consumer(items, queue_capacity)` — simulate bounded queue logic as pure function
2. `lock_ordering_deadlock_check(acquisition_order)` — detect deadlock potential from a lock-order list
3. `run_coroutines_gather(coro_results)` — given precomputed results, simulate `asyncio.gather` aggregation order
4. `drive_generator_coroutine(gen, sent_values)` — manually `.send()` values through a generator-based coroutine, return yielded sequence
5. `context_var_snapshot(base_value, overrides)` — `copy_context()`-style isolated value resolution
6. `task_priority_schedule(tasks)` — deterministic priority-queue-based scheduling order (no real concurrency)
7. `simulate_interleaving(thread_ops)` — given fixed op sequences per "thread", return one valid deterministic interleave under a stated rule
8. `is_io_bound_or_cpu_bound(task_description)` — classification heuristic function (models decision framework)
9. `retry_with_backoff_schedule(attempt, base_delay)` — pure computation of backoff delay sequence (no real sleep)
10. `chunk_work_for_processes(items, num_workers)` — partition list into balanced work chunks
11. `aggregate_worker_results(partial_results)` — reduce step for multiprocessing-style map/reduce
12. `exception_group_summary(sub_results)` — build `ExceptionGroup`-style summary dict from mixed success/fail results
**Quizzes**: (1) GIL — what it protects and when it's released, free-threading (3.13+) as "what's new"; (2) subinterpreters/PEP 703 concept check.
**Tier**: Advanced/Expert. **Path**: Professional Python / Software Engineer.

#### `modern-syntax-3.10-3.12`
**Title**: Modern Python Syntax — match/case, Exception Groups, Walrus
**Lessons**:
1. Structural pattern matching (`match`/`case`): class patterns, guards, capture.
2. Exception groups and `except*` (3.11+); `Exception.add_note()`.
3. Walrus operator and positional-only/keyword-only parameters as API design tools.
**Exercises**:
1. `classify_shape(shape_obj)` — `match/case` over class patterns
2. `match_with_guard(value)` — pattern + guard clause dispatch
3. `match_sequence_capture(seq)` — `*rest` capture pattern
4. `match_mapping_pattern(d)` — mapping pattern extraction
5. `match_or_pattern(value)` — or-pattern dispatch
6. `run_subtasks_collect_errors(tasks)` — raises `ExceptionGroup`, caller catches via `except*`, returns summary
7. `annotate_and_reraise(exc, note)` — `add_note()` then return `str(exc)`
8. `dedupe_with_walrus(items)` — comprehension using `:=`
9. `chunk_with_walrus(iterable, size)` — while-loop chunker using `:=`
10. `strict_signature_call(func, args, kwargs)` — enforce positional-only/keyword-only contract, return result or `TypeError` marker
11. `format_debug_spec(x)` — `f"{x=}"`-style debug string builder
12. `runtime_checkable_protocol_match(obj, protocol_methods)` — `isinstance` against a `@runtime_checkable Protocol`
**Quizzes**: (1) reading `match`/`case` dispatch trees; (2) `except*` vs `except` semantics with multiple exception types.
**Tier**: Intermediate/Advanced. **Path**: Professional Python.

#### `functools-operator-deep-cuts`
**Title**: `functools`/`operator`/`itertools` Deep Cuts
**Lessons**:
1. `singledispatch`, `partial`/`partialmethod`, `cache`/`lru_cache` internals (`cache_info`).
2. `operator` module for functional pipelines and sort keys.
3. Underused iterator tools: `tee`, `pairwise`, `batched`, `accumulate` with `initial=`.
**Exercises**:
1. `dispatch_by_type(value, handlers)` — `singledispatch`-style behavior over mixed types
2. `partial_pipeline(funcs, initial_args)` — compose `partial`-built function chain
3. `cache_info_after_calls(func, call_args_sequence)` — return `cache_info()` tuple state
4. `reduce_with_initial(items, op, initial)` — `functools.reduce` edge cases
5. `sort_by_itemgetter(records, keys)` — multi-key sort via `operator.itemgetter`
6. `sort_by_methodcaller(objects, method_name)` — `operator.methodcaller` sort key
7. `groupby_requires_sorted(data, key)` — demonstrate the sorted-input precondition (return correct vs "trap" grouping)
8. `pairwise_diffs(sequence)` — `itertools.pairwise`
9. `batched_chunks(iterable, n)` — `itertools.batched` (3.12+)
10. `tee_and_compare(iterable, n)` — `itertools.tee` independent consumption
11. `accumulate_custom(items, func, initial)` — `itertools.accumulate` with custom func
12. `product_with_repeat(items, repeat)` — `itertools.product(repeat=...)`
**Quizzes**: (1) `groupby` unsorted-input gotcha; (2) `lru_cache(maxsize=, typed=)` behavior prediction.
**Tier**: Intermediate/Advanced. **Path**: Professional Python. *(Sequel to existing `collections-itertools` and `decorators-closures`.)*

#### `binary-data-and-struct`
**Title**: Bytes, Buffers, and Binary Protocols
**Lessons**:
1. `bytes` vs `bytearray` mutability; the buffer protocol conceptually.
2. `struct`: pack/unpack format codes, endianness, fixed-width records.
3. `memoryview` and `array`: zero-copy slicing and typed numeric arrays without numpy.
**Exercises**:
1. `pack_record(fields)` — `struct.pack` a fixed-width binary record
2. `unpack_record(data, fmt)` — `struct.unpack` back to a tuple
3. `parse_binary_header(data)` — extract fields from a mock binary protocol header
4. `endian_convert(data, fmt_from, fmt_to)` — swap endianness of packed data
5. `mutate_bytearray_slice(ba, start, end, new_bytes)` — in-place bytearray mutation
6. `memoryview_slice_sum(buf, start, end)` — slice + sum via `memoryview`
7. `zero_copy_mutate(buf, index, value)` — mutate underlying bytearray through a memoryview
8. `typed_array_stats(values, typecode)` — build `array.array`, return min/max/sum
9. `base64_roundtrip(data)` — encode/decode round trip
10. `binascii_hex_roundtrip(data)` — hex encode/decode round trip
11. `bytes_vs_bytearray_check(data)` — return mutability-derived behavior differences
12. `checksum_bytes(data)` — simple pure-Python checksum (e.g., additive or CRC-lite) over bytes
**Quizzes**: (1) when to reach for `struct` vs manual byte slicing; (2) buffer protocol / zero-copy conceptual check.
**Tier**: Advanced. **Path**: Professional Python / Systems-adjacent.

#### `numeric-precision-and-edge-cases`
**Title**: Numeric Precision — Decimals, Fractions, Float Pitfalls
**Lessons**:
1. Why `0.1 + 0.2 != 0.3`: float representation and `math.isclose`.
2. `decimal.Decimal`: context, precision, rounding modes for money math.
3. `fractions.Fraction` for exact rational arithmetic; `math` deep cuts (`fsum`, `prod`, `isqrt`, `comb`/`perm`).
**Exercises**:
1. `is_close_enough(a, b, rel_tol)` — wraps `math.isclose` semantics
2. `float_sum_error_demo(values)` — naive sum vs `math.fsum` divergence, return both
3. `decimal_round(value_str, places, mode)` — `Decimal` with rounding mode
4. `decimal_money_add(amounts_str)` — exact decimal addition avoiding float drift
5. `fraction_reduce(numerator, denominator)` — `Fraction` auto-reduction
6. `fraction_arithmetic(a, b, op)` — exact rational ops
7. `gcd_via_fraction(a, b)` — reduction-based GCD
8. `safe_isqrt(n)` — `math.isqrt` with negative-input handling
9. `combinations_count(n, k)` — `math.comb`
10. `permutations_count(n, k)` — `math.perm`
11. `product_of_list(values)` — `math.prod`
12. `bigint_no_overflow_demo(base, exponent)` — arbitrary-precision int result (conceptual: no overflow)
**Quizzes**: (1) float representation pitfalls in real code (comparing floats for equality); (2) Python ints don't overflow — CPython digit representation conceptual check.
**Tier**: Intermediate. **Path**: Professional Python.

#### `introspection-and-metaprogramming`
**Title**: Introspection — `inspect`, Signatures, Recursion Limits
**Lessons**:
1. `inspect.signature`: reading parameter names, defaults, annotations from a function object.
2. Recursion limits and `RecursionError` — CPython's lack of tail-call optimization.
3. `dis`-level intuition (conceptual, not exact-match): what bytecode disassembly tells you.
**Exercises**:
1. `signature_params(func)` — return param names/defaults dict via `inspect.signature`
2. `signature_annotations(func)` — return annotation dict
3. `is_bound_method(obj)` — `inspect.ismethod` check
4. `get_members_summary(obj)` — filtered `inspect.getmembers` result
5. `call_with_bound_args(func, args, kwargs)` — use `signature.bind` to normalize call
6. `recursion_with_fallback(n, limit)` — catch `RecursionError` at a lowered limit, return fallback value
7. `deepest_safe_recursion(func, limit)` — probe max safe depth deterministically
8. `contains_opcode_name(func, opcode_substr)` — loose check via `dis.dis` string capture (regex presence only, not exact match)
9. `function_source_lines_count(func)` — `inspect.getsource`-based line count
10. `default_args_snapshot(func)` — mutable-default-argument gotcha demonstration
11. `closure_variables(func)` — `func.__closure__`/`__code__.co_freevars` introspection
12. `is_generator_function(func)` — `inspect.isgeneratorfunction` check
**Quizzes**: (1) why Python has no tail-call optimization and what that means for deep recursion; (2) reading `dis.dis` output conceptually (not exact bytecode matching).
**Tier**: Advanced. **Path**: Professional Python.

#### `typing-runtime-boundary`
**Title**: Type Hints at the Runtime Boundary
**Lessons**:
1. Hints are documentation, not enforcement: the gap between `typing` and runtime behavior.
2. `Protocol` + `@runtime_checkable`, `TypedDict`, `Literal` — what actually executes.
3. Generics (`TypeVar`, `Generic[T]`, PEP 695 `class Foo[T]`) as containers you can still grade behaviorally.
**Exercises**:
1. `runtime_checkable_isinstance(obj, protocol)` — `@runtime_checkable Protocol` check
2. `validate_typed_dict_shape(d, required_keys, key_types)` — manual `TypedDict` shape validation
3. `validate_literal_choice(value, allowed)` — `Literal`-style manual enforcement
4. `generic_stack_push_pop(ops)` — behaviorally test a generic container class via push/pop op sequence
5. `generic_pair_swap(pair)` — generic 2-tuple-like container, swap elements
6. `overload_dispatch_result(value)` — behavior matching an `@overload`-documented function's actual runtime branch
7. `newtype_unwrap(value)` — `NewType` is identity at runtime; return raw value to demonstrate
8. `type_hint_ignored_at_runtime(func, wrong_type_arg)` — call with hint-violating arg, show no `TypeError` unless manually checked
9. `manual_type_guard(value, expected_type)` — hand-rolled runtime type check function
10. `covariant_container_read(container)` — behavioral demonstration of variance concept via a getter
11. `generic_max_by(items, key_func)` — generic-typed utility, graded on behavior
12. `signature_matches_protocol(func, protocol_methods)` — structural check via `inspect`
**Quizzes**: (1) `ParamSpec`/`Concatenate`/`TypeVarTuple` — static-only typing tools, no runtime exercise possible (concept check); (2) why `isinstance(x, list[int])` fails / generic erasure at runtime.
**Tier**: Advanced. **Path**: Professional Python.

*(Lesson/quiz-only companions for this wave, not standalone areas: GIL mechanics, free-threading PEP 703, exact `dis` bytecode reading, `sys.settrace`/`sys.setprofile`, Timsort internals — see Section 2.)*

---

### Wave C — Applied Python

#### `scripting-automation-logic`
**Title**: Scripting & Automation Logic
**Lessons**:
1. The shape of an automation script: filter → transform → act, without touching real I/O.
2. Batch operations as pure transforms over record lists (simulated files).
3. When to reach for real `os`/`shutil` vs. keeping logic pure and testable.
**Exercises**:
1. `filter_files_by_extension(records, ext)` — records = list of dicts (name/size/mtime)
2. `group_files_by_extension(records)`
3. `rename_plan(records, pattern)` — compute new names without touching disk
4. `find_duplicates_by_size(records)`
5. `sort_files_by_mtime(records)`
6. `total_size_by_group(records, group_key)`
7. `filter_stale_files(records, cutoff_mtime)`
8. `build_archive_plan(records, max_batch_size)` — partition into batches
9. `detect_naming_collisions(planned_names)`
10. `apply_rename_pattern(name, pattern)` — string template substitution
11. `dedupe_file_list(records, key_fields)`
12. `summarize_directory_stats(records)` — count/total size/extension breakdown dict
**Quizzes**: (1) real `os.walk`/watch-scripts conceptual overview; (2) idempotency in automation scripts (why rerun-safety matters).
**Tier**: Beginner/Intermediate. **Path**: Applied Python / Automation.

#### `pathlib-string-patterns`
**Title**: Path String Patterns (`pathlib`/`os.path`)
**Lessons**:
1. `PurePath` operations: parsing without touching the filesystem.
2. Joining, normalizing, and computing relative paths as string logic.
3. Extension/stem/parent manipulation idioms.
**Exercises**:
1. `get_extension(path_str)`
2. `get_stem(path_str)`
3. `join_paths(parts)`
4. `normalize_path(path_str)`
5. `relative_path(base, target)`
6. `change_extension(path_str, new_ext)`
7. `parent_chain(path_str)` — list of ancestor path strings
8. `is_subpath(path_str, base_str)`
9. `split_path_components(path_str)`
10. `build_path_with_suffix(path_str, suffix)`
11. `common_path_prefix(path_strs)`
12. `sanitize_filename(name)` — strip illegal characters
**Quizzes**: (1) `pathlib.Path` vs `os.path` API mapping; (2) real filesystem operations (`glob`, existence checks) — conceptual only.
**Tier**: Intermediate. **Path**: Applied Python. *(Pairs with in-progress files/JSON/CSV wave.)*

#### `cli-argument-parsing-model`
**Title**: CLI Argument Parsing — The Model Behind argparse
**Lessons**:
1. Anatomy of a CLI call: positional args, flags, defaults.
2. Building a parser model by hand before meeting `argparse`.
3. Real `argparse`: subcommands, `--help` generation (lesson tour).
**Exercises**:
1. `parse_flags(argv)` — manual `--flag value` parser returning dict
2. `parse_positional_args(argv, spec)`
3. `apply_defaults(parsed, defaults)`
4. `validate_required_args(parsed, required)` — return missing-args list
5. `parse_boolean_flag(argv, flag_name)` — presence-as-true flag
6. `parse_repeated_flag(argv, flag_name)` — collect multiple `--tag x --tag y`
7. `split_subcommand(argv)` — separate subcommand from its args
8. `coerce_arg_types(parsed, type_spec)` — string → int/float/bool coercion
9. `build_usage_string(spec)` — generate a usage line from a spec dict
10. `merge_config_and_args(config_defaults, parsed_args)` — precedence logic
11. `parse_key_value_pairs(argv)` — `--set key=value` style parsing
12. `predict_namespace(spec, argv)` — given an argparse-style spec description, predict resulting dict
**Quizzes**: (1) real `argparse.ArgumentParser` usage and subcommands; (2) `--help` text generation and exit codes.
**Tier**: Intermediate. **Path**: Applied Python.

#### `http-request-shapes`
**Title**: HTTP & API Request/Response Shapes (No Network)
**Lessons**:
1. URL anatomy: scheme, host, path, query string.
2. Building/parsing requests without making them: `urllib.parse` logic.
3. Status-code branching and response-shape validation as pure logic.
**Exercises**:
1. `build_query_string(params)` — `urlencode`-style logic
2. `parse_query_string(qs)` — `parse_qs`-style logic
3. `parse_url_components(url)` — scheme/host/path/query breakdown
4. `join_url(base, path)`
5. `is_success_status(code)` / `is_client_error(code)` / `is_server_error(code)`
6. `classify_status_code(code)` — category string
7. `validate_json_response_shape(response_dict, required_keys)`
8. `extract_pagination_links(headers_dict)` — parse a mock `Link` header
9. `build_auth_header(token)` — `Authorization: Bearer ...` string builder
10. `retry_decision(status_code, attempt, max_attempts)` — pure retry-policy logic
11. `merge_query_params(base_params, overrides)`
12. `mock_response_to_error(response_dict)` — map response dict to a raised-exception summary
**Quizzes**: (1) REST verbs/headers/auth conceptual tour; (2) `urllib.request.urlopen` vs `requests` — why stdlib-only teaching uses `urllib`.
**Tier**: Intermediate/Advanced. **Path**: Applied Python.

#### `sqlite-in-memory-patterns`
**Title**: SQLite In-Memory — Structured Data Without a Server
**Lessons**:
1. `sqlite3.connect(":memory:")`: a real relational DB inside a single function call.
2. Parameterized queries: building safe SQL (ties to security).
3. Schema design and joins (lesson tour) vs. what's gradeable as pure logic.
**Exercises** (each opens/seeds/queries an in-memory DB within the function body):
1. `create_and_insert(records)` — build table, insert rows, return row count
2. `select_where(records, condition_col, condition_val)`
3. `parameterized_query_safe(query_template, params)` — returns whether template uses `?` placeholders correctly
4. `detect_injection_risk(query_template)` — string-concatenation-vs-parameterized detector
5. `join_two_tables(table_a_rows, table_b_rows, join_key)`
6. `aggregate_group_by(records, group_col, agg_col)` — `SUM`/`COUNT` via SQL
7. `order_and_limit(records, order_col, limit)`
8. `upsert_record(existing_records, new_record, key_col)`
9. `transaction_rollback_on_error(records, bad_record)` — commit/rollback semantics, return final state
10. `unique_constraint_violation_check(records, unique_col)`
11. `count_rows_matching(records, predicate_sql)`
12. `schema_from_records(records)` — infer column types from a list of dicts
**Quizzes**: (1) schema design/normalization tour; (2) transactions/commit semantics conceptual check.
**Tier**: Advanced. **Path**: Applied Python.

#### `logging-and-diagnostics`
**Title**: Logging & Diagnostics Logic
**Lessons**:
1. Why `logging` beats `print`: levels, handlers, formatters.
2. Effective-level resolution and propagation through a logger hierarchy.
3. Structuring log messages for real diagnostics (lesson tour of `basicConfig`, handlers).
**Exercises**:
1. `format_log_message(level, msg, context)` — formatter-style string builder
2. `effective_level(logger_level, handler_level)` — propagation resolution logic
3. `should_emit(record_level, threshold_level)`
4. `build_structured_log_entry(level, msg, extra_fields)` — dict builder
5. `redact_sensitive_fields(log_dict, sensitive_keys)`
6. `merge_logger_hierarchy_levels(hierarchy)` — resolve effective level up a chain
7. `format_exception_log(exc, include_traceback_summary)`
8. `rate_limit_log_decision(recent_timestamps, window, max_count)` — pure logic over a timestamp list (no real time.sleep)
9. `log_level_from_string(name)` — name → numeric level mapping
10. `filter_logs_by_level(log_entries, min_level)`
11. `aggregate_log_counts_by_level(log_entries)`
12. `build_context_prefix(context_dict)` — `[user=1 req=abc]`-style prefix builder
**Quizzes**: (1) real `logging.basicConfig`/handlers writing to files/streams; (2) logger hierarchy/propagation in a live app.
**Tier**: Intermediate. **Path**: Applied Python. *(Pairs with existing `error-handling`.)*

#### `config-parsing-precedence`
**Title**: Config Parsing & Precedence (TOML/INI/Env)
**Lessons**:
1. Config-as-text: parsing INI/TOML strings into dicts (`tomllib`, 3.11+).
2. Precedence chains: defaults < file < env vars < CLI flags.
3. Real file/env interaction (lesson tour).
**Exercises**:
1. `parse_ini_string(text)` — manual INI parser (section/key/value)
2. `parse_toml_string(text)` — using `tomllib.loads`
3. `merge_config_layers(defaults, file_config, env_overrides)` — precedence merge
4. `flatten_nested_config(config_dict)` — dotted-key flattening
5. `coerce_env_value(value_str)` — string → bool/int/float coercion
6. `validate_config_schema(config, required_keys, types)`
7. `resolve_env_var_reference(value_str, env_dict)` — `${VAR}`-style interpolation
8. `diff_configs(old, new)` — changed-keys summary
9. `config_from_cli_overrides(base_config, cli_pairs)`
10. `redact_secrets_in_config(config, secret_keys)`
11. `default_config_template(schema)` — build a defaults dict from a schema
12. `parse_env_file_string(text)` — `.env`-style `KEY=value` line parser
**Quizzes**: (1) reading real `.toml`/`.ini` files from disk, `os.environ` interaction; (2) why env-var overrides are the standard 12-factor pattern.
**Tier**: Intermediate. **Path**: Applied Python.

#### `functional-style-patterns`
**Title**: Functional Programming Style in Python
**Lessons**:
1. `map`/`filter`/`reduce` and when they read better than loops.
2. Composition and point-free style with `functools.partial`.
3. Closures as strategy objects (ties to existing `decorators-closures`).
**Exercises**:
1. `pipeline_compose(funcs)` — left-to-right function composition
2. `curry_two_arg(func)` — manual currying via closures
3. `map_filter_chain(items, transform, predicate)`
4. `reduce_to_dict(items, key_func, value_func)`
5. `partial_apply_chain(func, *fixed_args)` — behavior check via `functools.partial`
6. `memoize_pure(func)` — manual memoization wrapper, graded via call behavior
7. `flatten_with_reduce(nested_lists)`
8. `zip_apply(list_a, list_b, combiner)`
9. `first_matching(items, predicate, default)`
10. `group_by_functional(items, key_func)` — dict-of-lists via reduce
11. `pointfree_pipeline_result(value, funcs)`
12. `strategy_dispatch(strategy_name, strategies, *args)` — closures-as-strategy pattern
**Quizzes**: (1) FP vs imperative philosophy — when NOT to use FP style in Python; (2) immutability discipline in a language without enforced immutability.
**Tier**: Intermediate. **Path**: Applied Python / Professional Python.

#### `caching-and-memory-efficiency`
**Title**: Caching & Memory-Efficient Patterns
**Lessons**:
1. Memoization with `functools.lru_cache`/`@cache` — mechanics, not just DP speedup.
2. Generators vs lists: the memory-tradeoff mental model (can't measure real memory, but can compare output shape/behavior).
3. Big-O identification as a reading skill.
**Exercises**:
1. `memoized_fib(n)` — `lru_cache`-decorated, graded on correctness + `cache_info()` hits
2. `manual_memo_wrapper(func)` — hand-rolled memoization decorator
3. `cache_eviction_behavior(maxsize, call_sequence)` — LRU eviction order simulation
4. `generator_vs_list_output(n)` — same sequence via generator and list, compare outputs
5. `lazy_pipeline_sum(generator_stages)` — chained generator pipeline result
6. `first_n_from_infinite_generator(gen_func, n)`
7. `memoize_with_ttl_logic(func, calls_with_timestamps, ttl)` — deterministic pseudo-time TTL eviction
8. `identify_bigo_class(code_shape_description)` — structured input describing loop nesting → complexity class string
9. `cache_hit_rate(call_sequence, cache_size)`
10. `dedupe_streaming(iterable)` — generator-based dedupe without full materialization
11. `windowed_generator(iterable, size)` — sliding window via generator
12. `compare_recursive_vs_memoized_calls(n)` — return call-count difference (naive vs memoized recursion)
**Quizzes**: (1) `cProfile`/`timeit` real profiling workflow (conceptual); (2) algorithmic complexity analysis on realistic dataset sizes.
**Tier**: Advanced. **Path**: Applied Python / Professional Python. *(Pairs with existing `dp-recognition`, `iterators-generators`.)*

#### `secure-coding-patterns`
**Title**: Secure Coding Patterns
**Lessons**:
1. Input validation and sanitization: the trust boundary.
2. Injection classes: SQL/OS/template injection via string concatenation vs parameterization.
3. Constant-time comparison and the `secrets` module for crypto-safe randomness.
**Exercises**:
1. `validate_email_format(s)`
2. `sanitize_html_input(s)` — strip/escape dangerous characters
3. `is_safe_filename(name)` — reject path traversal patterns (`../`)
4. `bounds_check_numeric(value, min_v, max_v)`
5. `detect_sql_injection_pattern(query_template)` — flag string-concat vs parameterized
6. `detect_shell_injection_risk(command_str)` — flag unsafe shell metacharacters
7. `safe_shlex_split(command_str)` — using `shlex.split` correctly
8. `constant_time_compare(a, b)` — `secrets.compare_digest`-style logic
9. `generate_token_hex(n_bytes)` — `secrets.token_hex`, graded on length/format properties (not exact value)
10. `mask_sensitive_value(value, visible_chars)`
11. `validate_password_strength(password, rules)`
12. `strip_null_bytes(s)` — defensive input cleanup
**Quizzes**: (1) real SQL injection demo against a live DB, `subprocess shell=True` risk (conceptual); (2) secrets-in-env-vars vs hardcoded credentials, threat modeling.
**Tier**: Advanced. **Path**: Applied Python / Security-adjacent. *(Ties together `error-handling` + `regex-text-processing` + `sqlite-in-memory-patterns`.)*

#### `dataframe-thinking-without-libraries`
**Title**: DataFrame Thinking — Pandas/NumPy Mental Models in Pure Python
**Lessons**:
1. Columnar thinking: rows-of-dicts vs columns-of-lists, and why vectorized code avoids explicit loops.
2. Broadcasting, boolean masking, and groupby as a dict-accumulation pattern.
3. Why real numpy/pandas is faster (C-level vectorization) — when to reach for the real library (lesson tour).
**Exercises**:
1. `boolean_mask_filter(rows, predicate)`
2. `column_select(rows, columns)`
3. `apply_transform_all_rows(rows, column, func)`
4. `groupby_aggregate(rows, group_col, agg_col, agg_func)`
5. `pivot_longer(rows, id_cols, value_cols)`
6. `pivot_wider(rows, index_col, columns_col, values_col)`
7. `inner_join(rows_a, rows_b, key)`
8. `left_join(rows_a, rows_b, key)`
9. `broadcast_scalar_op(rows, column, scalar, op)`
10. `rolling_window_stat(values, window, stat_func)`
11. `fillna_column(rows, column, fill_value)`
12. `describe_column(values)` — count/mean/std/min/max summary dict (stdlib `statistics`)
**Quizzes**: (1) why vectorized numpy operations beat Python loops (C-level execution); (2) when to reach for real pandas/numpy vs staying in pure Python.
**Tier**: Advanced. **Path**: Applied Python / Data. *(Builds directly on existing `data-wrangling-python`.)*

---

## 2. Lesson/Quiz-Only Topics (Ecosystem Literacy — No Exercise)

These cannot be honestly graded as single pure functions (require external deps, real I/O/network/time, non-deterministic timing, CPython-implementation-detail values, or are purely static-typing constructs with no runtime behavior). Each is slotted into an existing or proposed area as lesson content + MCQ quiz only.

| Topic | Why exercise-incompatible | Slot into |
|---|---|---|
| GIL semantics (what it protects, when released) | Not function-shaped; needs live thread interleaving | `concurrency-foundations` lesson 1 |
| Free-threading / PEP 703 (3.13+ `--disable-gil`) | Sandbox runs standard GIL build; can't test the difference | `concurrency-foundations` "what's new" lesson |
| Subinterpreters (PEP 734-adjacent) | Same — runtime/build-dependent | `concurrency-foundations` lesson |
| `dis` exact bytecode disassembly | Output is version-fragile across 3.x point releases | `introspection-and-metaprogramming` lesson 3 (loose regex-presence exercise only, not exact match) |
| `sys.settrace`/`sys.setprofile` | Debugger/profiler internals, not a sane grading target | `introspection-and-metaprogramming` lesson |
| Timsort internals (galloping, run detection) | Algorithm-internals trivia, not exercise-shaped | Sequel lesson to existing sorting content |
| Reference counting exact values (`sys.getrefcount`) | Off-by-one from temp arg, non-portable across container/version | `memory-and-object-lifetime` lesson 1 |
| `ParamSpec`/`Concatenate` (PEP 612) | Purely static-typing, zero runtime behavior | `typing-runtime-boundary` lesson/quiz |
| `TypeVarTuple`/variadic generics (PEP 646) | Same — static-only | `typing-runtime-boundary` lesson/quiz |
| `subprocess` (`run`, `shell=True`, `Popen`) | Spawns real external processes, non-deterministic in a grader | `scripting-automation-logic` and `secure-coding-patterns` lessons |
| Real HTTP calls (`urllib.request.urlopen`, `requests`) | Network I/O, no pip, non-deterministic | `http-request-shapes` lesson tour |
| venv / pip / poetry / uv / `pyproject.toml` | Pure tooling/workflow, no function-level logic | New standalone lesson-only module: "How Real Python Projects Are Structured" |
| Package structure (`__init__.py`, entry points) | Same — project scaffolding, not computable | Same module as above |
| Actual filesystem traversal (`os.walk`, `Path.glob`, file existence) | Needs real FS, non-deterministic across containers | `pathlib-string-patterns` and `scripting-automation-logic` lessons |
| `cProfile`/`timeit` real profiling | Needs real wall-clock measurement | `caching-and-memory-efficiency` lesson 3 |
| Real memory measurement (`sys.getsizeof` in practice, `tracemalloc`) | Environment-dependent absolute values | `caching-and-memory-efficiency` and `memory-and-object-lifetime` lessons |
| `logging.basicConfig`, handlers to files/streams, live propagation | Real I/O side effects | `logging-and-diagnostics` lesson 3 |
| fast.ai-style top-down transfer learning, real pretrained models | Needs GPU frameworks/pretrained weights | AI wave intro lesson: "why this platform teaches bottom-up mechanics" |
| Full NN training loops, BatchNorm, GPT/transformer assembly | Stateful multi-epoch training, not a pure function | Capstone-tier lesson/project in AI Engineer path (see Section 3) |
| Vector databases, real embedding APIs, reranking services | External infra/API dependency | `embeddings-similarity-search` lesson 3, RAG capstone lesson |
| Prompt engineering practice / prompt architecture | No code execution, needs live LLM interaction | New lesson-only module in AI Engineer path (Section 3, unit 7) |
| Metaclasses (`type()`, custom `__new__`) beyond `__init_subclass__` | Full custom metaclass grading is fragile; favor `__init_subclass__` instead | `oop-internals-descriptors-mro` lesson 1 (concept only; exercises use `__init_subclass__`) |
| Import system internals (`importlib`, `sys.modules` caching, import hooks) | Dynamic code loading unsafe/fragile in sandboxed grader | `introspection-and-metaprogramming` or new packaging lesson module |
| Andrew Ng ML Specialization ordering, fast.ai pedagogy contrast | Reference/roadmap material, not content itself | Used to validate Section 3 ordering only |
| Numpy/pandas real vectorization performance | Needs real numpy to benchmark | `dataframe-thinking-without-libraries` lesson 3 |

---

## 3. Proposed "AI Engineer Python" Career Path — Unit Ordering

Sequencing follows the math-lite → transformer ramp validated across Karpathy's zero-to-hero, fast.ai, and Ng's specialization (Report 1 §3), gated by existing prerequisites already in the catalog (fundamentals, loops/lists/strings, dicts/sets, recursion, OOP, iterators/generators, decorators).

1. **Foundations gate** (existing content, prerequisite check): `python-refresh`, `loops-lists-strings`, `dicts-sets-tuples`, `recursion-backtracking`, `oop-classes` — no new content, just a declared prerequisite edge.
2. **`classic-ml-from-scratch`** — distance metrics, k-means, k-NN, perceptron/gradient-descent steps, loss functions. Entry point: concrete, visual, low math bar.
3. **`autodiff-scalar-engine`** — scalar `Value` graph, forward/backward ops, topological sort, capstone `.backward()` engine. The conceptual core of "how training works."
4. **`eval-metrics-for-models`** — precision/recall/F1/perplexity groundwork, introduced early so later units can reference "how we'd measure this."
5. **`language-models-from-scratch`** — bigram/n-gram counting LMs, smoothing, perplexity in practice (reuses metrics from unit 4).
6. **`tokenization-bpe`** — BPE training/encoding ladder; natural sequel once learners have handled raw text as a corpus in unit 5.
7. **`embeddings-similarity-search`** — dot product, cosine similarity, nearest-neighbor retrieval, chunking, BM25; bridges toward retrieval/RAG.
8. **`attention-mechanics`** — softmax, scaled dot-product attention, causal masking, toy multi-head composition. Capstone-adjacent, highest math bar in the autogradeable set.
9. **Lesson-only capstone unit**: "Assembling a Transformer" — full NN training loops, BatchNorm, GPT/tokenizer assembly (Karpathy build-GPT lecture as reference), presented as a guided project/capstone rather than autograded exercises.
10. **Lesson-only unit**: "Prompt Engineering & Eval Harnesses" — prompt design/architecture, RAG pipeline mechanics end-to-end (chunking → BM25 → embeddings → vector DB → rerank → generate), model evaluation practice, real vector DBs and embedding APIs, all conceptual/lesson-and-quiz since they require external services.
11. **Lesson-only unit**: "Ecosystem Landscape" — numpy/pandas/PyTorch mental models (cross-reference `dataframe-thinking-without-libraries` from Applied wave), fast.ai vs Karpathy pedagogy contrast, Andrew Ng specialization roadmap reference, GPU/training-infrastructure overview, packaging/deployment basics for ML code.

Path badge: "AI Engineer Python" unlocks after units 1-8 (all autogradeable content) are complete; units 9-11 are marked as the "professional context" capstone tier, consistent with freeCodeCamp's checkpoint-certification pattern and Exercism's concept/practice split (Report 4).

---

## 4. Explicit Exclusions (Not Teachable On This Platform)

| Excluded topic | Reason |
|---|---|
| Real PyTorch/TensorFlow/JAX model training | Requires pip-installed frameworks and GPU acceleration; violates stdlib-only constraint outright |
| Real numpy/pandas/scikit-learn exercises | No pip in sandbox; can only teach the *mental model* in pure Python (see `dataframe-thinking-without-libraries`) |
| Full transformer/GPT training runs, fine-tuning, RLHF | Multi-epoch stateful training with real tensors — not a single pure function, not stdlib-feasible at any meaningful scale |
| Real embedding models (OpenAI/Cohere/sentence-transformers) | Requires network calls or pip-installed models; can only use precomputed toy vectors as fixtures |
| Vector databases (Pinecone, Weaviate, pgvector, FAISS) | External services or pip packages; lesson-only |
| Real HTTP/REST API calls, webhook handling | Network access disabled in sandbox; nondeterministic even if enabled |
| `subprocess`/shell execution exercises | Spawns real external processes — can't safely or deterministically grade in a shared sandboxed grader |
| Multithreading/multiprocessing with real timing | Real concurrency is inherently non-deterministic; only deterministic *simulations* of scheduling/locking logic are gradeable |
| Free-threaded Python (3.13t `--disable-gil`) behavior differences | Grader almost certainly runs a standard GIL build; can't exercise the distinction |
| Real filesystem operations (create/delete/walk real files) | No real FS access in a stateless per-function grader; only string/path-logic and simulated-record versions are gradeable |
| `venv`/pip/poetry/uv/dependency resolution | Pure tooling workflow with no computable input/output — lesson only |
| Database servers (Postgres/MySQL/Redis) | External services; only `sqlite3` in-memory is stdlib-safe |
| GPU/CUDA programming, model quantization, deployment/serving infra | Requires hardware/frameworks entirely outside stdlib scope |
| Exact bytecode (`dis`) matching, exact refcount values | CPython-version-fragile and implementation-detail-fragile; not stable across container patch versions |
| Prompt engineering practice (live LLM interaction) | Needs a real LLM API call; no network access, no pip for SDKs |
| Web scraping, browser automation | Needs network/browser runtime, no pip (`playwright`/`selenium`/`bs4`) |
| Real-time/streaming data pipelines | Needs real time-based execution and often external brokers (Kafka, etc.) |

---

## 5. Sources

**AI/ML**
- Karpathy Zero to Hero: https://karpathy.ai/zero-to-hero.html · https://github.com/karpathy/nn-zero-to-hero
- Micrograd: https://github.com/karpathy/micrograd
- Makemore/bigram LM walkthroughs: https://swe-to-mle.pages.dev/posts/makemore-implement-a-bigram-character-level-language-model/ · https://github.com/prigarg/Bigram-Language-Model-from-Scratch
- BPE from scratch: https://sebastianraschka.com/blog/2025/bpe-from-scratch.html · https://github.com/rasbt/LLMs-from-scratch
- Perceptron/backprop from scratch: https://machinelearningmastery.com/implement-perceptron-algorithm-scratch-python/ · https://machinelearningmastery.com/implement-backpropagation-algorithm-scratch-python/
- k-means/k-NN from scratch: https://gist.github.com/iandanforth/5862470 · https://machinelearningplus.com/predictive-modeling/k-means-clustering/
- fast.ai: https://course.fast.ai/
- Andrew Ng ML Specialization: https://www.coursera.org/specializations/machine-learning-introduction
- Cosine similarity/semantic search: https://www.tigerdata.com/learn/implementing-cosine-similarity-in-python · https://milvus.io/ai-quick-reference/how-do-i-implement-semantic-search-with-python
- RAG course sequencing: https://www.boot.dev/courses/learn-retrieval-augmented-generation · https://learn.deeplearning.ai/courses/retrieval-augmented-generation/information
- Softmax/attention formula: https://www.datacamp.com/tutorial/softmax-activation-function-in-python · https://medium.com/@weidagang/demystifying-the-attention-formula-8f5ad602546f
- Eval metrics: https://developers.google.com/machine-learning/crash-course/classification/accuracy-precision-recall · https://machinelearningmastery.com/llm-evaluation-metrics-made-easy/

**Niche/Advanced Internals**
- Descriptor HOWTO: https://docs.python.org/3/howto/descriptor.html
- RealPython Metaclasses/Descriptors: https://realpython.com/python-metaclasses/ · https://realpython.com/python-descriptors/
- CPython string interning: https://github.com/python/cpython/blob/main/InternalDocs/string_interning.md
- contextvars: https://docs.python.org/3/library/contextvars.html · PEP 567 https://peps.python.org/pep-0567/
- Exception groups: PEP 654 https://peps.python.org/pep-0654/ · What's New 3.11 https://docs.python.org/3/whatsnew/3.11.html
- typing module: https://docs.python.org/3/library/typing.html · PEP 612 https://peps.python.org/pep-0612/ · PEP 695 https://peps.python.org/pep-0695/
- Free-threading: https://py-free-threading.github.io/ · https://labs.quansight.org/blog/free-threaded-one-year-recap · https://lwn.net/Articles/985041/
- Python Behind the Scenes (async/await, CPython VM): https://tenthousandmeters.com/blog/python-behind-the-scenes-12-how-asyncawait-works-in-python/ · https://tenthousandmeters.com/materials/python-behind-the-scenes-a-list-of-resources/
- Fluent Python 2e: https://www.oreilly.com/library/view/fluent-python-2nd/9781492056348/ · https://github.com/fluentpython/example-code-2e

**Applied Python**
- Codecademy: https://www.codecademy.com/learn/paths/computer-science · https://www.codecademy.com/learn/learn-advanced-python-3-database-operations
- boot.dev: https://www.boot.dev/for-it-teams · https://github.com/bootdotdev/curriculum
- RealPython learning paths/pathlib/subprocess/argparse/logging/urllib/toml: https://realpython.com/learning-paths/ · https://realpython.com/courses/pathlib-python/ · https://realpython.com/python-subprocess/ · https://realpython.com/command-line-interfaces-python-argparse/ · https://realpython.com/python-logging/ · https://realpython.com/ref/stdlib/urllib/ · https://realpython.com/python-toml/
- argparse HOWTO: https://docs.python.org/3/howto/argparse.html
- tomllib: https://docs.python.org/3/library/tomllib.html
- pyproject.toml guide: https://packaging.python.org/en/latest/guides/writing-pyproject-toml/
- Functional programming: https://realpython.com/python-reduce-function/ · https://www.learnpython.org/en/Map,_Filter,_Reduce
- Performance/caching: https://dev.to/nkpydev/python-performance-optimization-profiling-caching-and-code-efficiency-55mc · https://www.pythonsnacks.com/p/python-functools-lrucache
- Secure coding: https://openssf.org/blog/2026/05/12/secure-coding-guide-for-python-pyscg-first-release/ · https://cisserv1.towson.edu/~cyber4all/modules/nanomodules/Input_Validation-CS1_Python.html

**Curriculum Shape**
- Exercism Python config: https://github.com/exercism/python/blob/main/config.json · https://exercism.org/tracks/python
- Hyperskill: https://support.hyperskill.org/hc/en-us/articles/4406586984468-Knowledge-map-and-what-it-is-for · https://hyperskill.org/knowledge-map · https://hyperskill.org/courses/22-python-core
- freeCodeCamp CFSD relaunch: https://www.freecodecamp.org/news/freecodecamp-turns-10-major-curriculum-updates/ · https://www.freecodecamp.org/learn/scientific-computing-with-python
- roadmap.sh: https://roadmap.sh/python · https://roadmap.sh/pdfs/roadmaps/python.pdf
- CS50P syllabus: https://cs50.harvard.edu/python/syllabus/
- CS2 pattern references: https://www.memphis.edu/cs/courses/syllabi/2150.pdf · SJSU CS146 syllabus
