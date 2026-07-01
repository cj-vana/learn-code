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

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print("repo guard passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
