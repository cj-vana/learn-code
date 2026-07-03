from __future__ import annotations

import pytest

from learn_code_api import update_check


@pytest.fixture(autouse=True)
def _reset_cache():
    update_check._cache["checked_at"] = None
    update_check._cache["latest"] = None
    yield
    update_check._cache["checked_at"] = None
    update_check._cache["latest"] = None


def test_disabled_by_env(monkeypatch):
    monkeypatch.setenv("LEARN_CODE_UPDATE_CHECK", "off")
    assert update_check.latest_version() is None


def test_caches_for_a_day(monkeypatch):
    calls = []

    def fake_fetch():
        calls.append(1)
        return "v0.2.0"

    monkeypatch.delenv("LEARN_CODE_UPDATE_CHECK", raising=False)
    monkeypatch.setattr(update_check, "_fetch_latest_tag", fake_fetch)
    assert update_check.latest_version(now=1000.0) == "v0.2.0"
    assert update_check.latest_version(now=2000.0) == "v0.2.0"
    assert len(calls) == 1
    assert update_check.latest_version(now=1000.0 + 25 * 60 * 60) == "v0.2.0"
    assert len(calls) == 2


def test_offline_failure_is_silent(monkeypatch):
    monkeypatch.delenv("LEARN_CODE_UPDATE_CHECK", raising=False)
    monkeypatch.setattr(update_check, "_fetch_latest_tag", lambda: None)
    assert update_check.latest_version(now=0.0) is None
    assert update_check.update_available(None) is False


def _bumped(version: str) -> str:
    major, rest = version.split(".", 1)
    return f"{int(major) + 1}.{rest}"


@pytest.mark.parametrize(
    ("latest", "expected"),
    [
        (_bumped(update_check.CURRENT_VERSION), True),
        ("v" + _bumped(update_check.CURRENT_VERSION), True),
        (update_check.CURRENT_VERSION, False),
        ("v" + update_check.CURRENT_VERSION, False),
        ("v0.0.1", False),
        ("not-a-version", False),
        (None, False),
    ],
)
def test_update_available_comparisons(latest, expected):
    assert update_check.update_available(latest) is expected
