# Contributing

Contributions are welcome — original content, bug fixes, and features alike.
Agent-written PRs are fine; you are responsible for what you submit. Point
your agent at `AGENTS.md` for the codebase map and conventions.

**Target the `dev` branch with your PRs.** `main` is the release branch;
changes land on `dev` first and ship to `main` (and the GHCR images) from
there.

## Dev setup

The Python side is a [uv](https://docs.astral.sh/uv/) workspace: one lockfile
(`uv.lock`), one `.venv`, every package installed editable.

```bash
uv sync --all-packages    # or: make setup
cd apps/web && npm install
```

If you add or change a dependency, edit the relevant `pyproject.toml`, run
`uv lock`, and commit the lockfile — CI installs with `--locked` and fails if
it is stale.

Run everything the CI runs before opening a PR:

```bash
make validate    # repo guard + compose config + pytest suites + web build
make test        # pytest suites + web vitest
```

## Content rules

All built-in content must be original. Do not copy or closely paraphrase
LeetCode, HackerRank, CodeSignal, editorials, examples, tests, or distinctive
problem stories.

New or changed content must pass the full validation, which executes every
exercise's sample solution against its own tests:

```bash
uv run learn-code validate-content
```

After adding content, regenerate the learning paths so unit ordering and each
path's assumed concepts stay correct:

```bash
uv run scripts/generate_paths.py
```

See `docs/content-authoring.md` for the authoring flow.

## House rules

- The web app is offline-capable: no external URLs (fonts, CDNs, analytics)
  in `apps/web` — the repo guard enforces this.
- Only `services/runner-broker` may touch the Docker socket.
