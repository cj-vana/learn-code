from __future__ import annotations

from learn_code_api.content.concepts import CONCEPT_TITLES, concept_label
from learn_code_api.content.validator import LIBRARY_KNOWN_CONCEPTS


def test_every_known_concept_has_a_label():
    missing = LIBRARY_KNOWN_CONCEPTS - CONCEPT_TITLES.keys()
    assert not missing, f"add labels to CONCEPT_TITLES for: {sorted(missing)}"


def test_no_stale_labels():
    stale = CONCEPT_TITLES.keys() - LIBRARY_KNOWN_CONCEPTS
    assert not stale, f"labels for concepts not in the taxonomy: {sorted(stale)}"


def test_concept_label_falls_back_readably():
    assert concept_label("python.loops") == "Loops"
    assert concept_label("python.some_future_thing") == "Some Future Thing"
