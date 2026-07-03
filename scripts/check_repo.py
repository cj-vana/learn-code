from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_DOCS = [
    "README.md",
    "CONTRIBUTING.md",
    "docs/architecture.md",
    "docs/content-authoring.md",
    "docs/runner-security.md",
    "docs/roadmap.md",
]


def git_lines(*args: str) -> list[str]:
    proc = subprocess.run(
        ["git", "-C", str(ROOT), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        print(proc.stderr.strip(), file=sys.stderr)
        return []
    return [line for line in proc.stdout.splitlines() if line.strip()]


def main() -> int:
    errors: list[str] = []

    tracked_plans = git_lines("ls-files", "docs/superpowers")
    if tracked_plans:
        errors.append("docs/superpowers is ignored and must never be tracked")

    tracked_env = git_lines("ls-files", ".env")
    if tracked_env:
        errors.append(".env must not be tracked; use .env.example")

    if (ROOT / "docs/superpowers").exists():
        ignored = subprocess.run(
            ["git", "-C", str(ROOT), "check-ignore", "-q", "docs/superpowers"],
            check=False,
        )
        if ignored.returncode != 0:
            errors.append("docs/superpowers exists but is not ignored")

    for doc in REQUIRED_DOCS:
        if not (ROOT / doc).exists():
            errors.append(f"missing required doc: {doc}")

    # The app is offline-capable: no web fonts or other external requests.
    web_sources = git_lines("ls-files", "apps/web/index.html", "apps/web/src")
    for rel in web_sources:
        path = ROOT / rel
        if path.suffix not in {".html", ".css", ".ts", ".tsx"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for lineno, line in enumerate(text.splitlines(), start=1):
            if "https://" in line and "//" != line.lstrip()[:2] and "* " != line.lstrip()[:2]:
                errors.append(
                    f"external URL in web app ({rel}:{lineno}): offline-capable scope forbids it"
                )

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print("repo guard passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
