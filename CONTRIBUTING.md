# Contributing

Contributions are welcome — original content, bug fixes, and features alike.
Agent-written PRs are fine; you are responsible for what you submit. Point
your agent at `AGENTS.md` for the codebase map and conventions.

**Target the `dev` branch with your PRs.** `main` is the release branch;
changes land on `dev` first and ship to `main` (and the GHCR images) from
there.

## Dev setup

```bash
python3 -m venv .venv
.venv/bin/pip install -e "apps/api[test]" pytest-timeout
.venv/bin/pip install -e "apps/cli[test]"
.venv/bin/pip install -e "services/runner-broker[test]"
cd apps/web && npm install
```

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
PYTHONPATH=apps/cli/src:apps/api .venv/bin/python -m learn_code_cli.main validate-content
```

After adding content, regenerate the learning paths so unit ordering and each
path's assumed concepts stay correct:

```bash
.venv/bin/python scripts/generate_paths.py
```

See `docs/content-authoring.md` for the authoring flow.

## House rules

- The web app is offline-capable: no external URLs (fonts, CDNs, analytics)
  in `apps/web` — the repo guard enforces this.
- Only `services/runner-broker` may touch the Docker socket.
