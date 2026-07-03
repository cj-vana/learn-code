"""Optional update check against GitHub Releases.

The app is offline-first, so this is the one outbound call it ever makes: at
most once a day, 2-second timeout, silent failure, and
``LEARN_CODE_UPDATE_CHECK=off`` disables it entirely. The browser never talks
to GitHub — it only reads this API's cached answer.
"""

from __future__ import annotations

import json
import os
import time
import urllib.request

# Keep in step with apps/api/pyproject.toml.
CURRENT_VERSION = "1.3.0"

RELEASES_URL = "https://api.github.com/repos/cj-vana/learn-code/releases/latest"
_CACHE_TTL_SECONDS = 24 * 60 * 60

_cache: dict[str, object] = {"checked_at": None, "latest": None}


def _enabled() -> bool:
    return os.environ.get("LEARN_CODE_UPDATE_CHECK", "on").lower() not in {"off", "0", "false"}


def _fetch_latest_tag() -> str | None:
    request = urllib.request.Request(
        RELEASES_URL, headers={"Accept": "application/vnd.github+json"}
    )
    try:
        with urllib.request.urlopen(request, timeout=2) as response:
            payload = json.load(response)
    except Exception:
        return None
    tag = payload.get("tag_name")
    return tag if isinstance(tag, str) and tag else None


def _parse(version: str) -> tuple[int, ...]:
    try:
        return tuple(int(part) for part in version.lstrip("vV").split("."))
    except ValueError:
        return ()


def latest_version(now: float | None = None) -> str | None:
    """Cached latest release tag, or None when disabled, offline, or unreleased."""
    if not _enabled():
        return None
    current_time = time.monotonic() if now is None else now
    checked_at = _cache["checked_at"]
    if checked_at is None or current_time - float(checked_at) > _CACHE_TTL_SECONDS:  # type: ignore[arg-type]
        _cache["latest"] = _fetch_latest_tag()
        _cache["checked_at"] = current_time
    latest = _cache["latest"]
    return latest if isinstance(latest, str) else None


def update_available(latest: str | None) -> bool:
    if latest is None:
        return False
    latest_parts = _parse(latest)
    current_parts = _parse(CURRENT_VERSION)
    return bool(latest_parts) and bool(current_parts) and latest_parts > current_parts
