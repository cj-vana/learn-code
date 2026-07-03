# Learn Code

[![CI](https://github.com/cj-vana/learn-code/actions/workflows/ci.yml/badge.svg)](https://github.com/cj-vana/learn-code/actions/workflows/ci.yml)

A local, Dockerized platform for learning Python — from first variables to
building a transformer's attention mechanism by hand. Original exercises with
an autograding runner, structured lessons, quizzes, and curated skill and
career paths, all running on your own machine.

> The browser app is a gamified, neo-brutalist quest board: XP, streaks, and
> levels over white cards with hard black borders on a lavender field.

## What's inside

The catalogue is **1,300+ original items across 70+ topic areas**:

- **910 autograded exercises** — each a single Python function checked against
  hidden tests, with a tiered hint ladder and worked explanations.
- **235 lessons** — structured reading with self-check checkpoints.
- **180 quizzes** — pattern-recognition and syntax multiple choice.
- **30 learning paths** — 7 career arcs and 23 focused skill paths.

Coverage runs from fundamentals through the full interview-algorithm catalogue
(two pointers → dynamic programming → graphs → bits), professional Python (OOP,
generators, decorators, typing, testing), practical tooling (files, dates,
CLIs, HTTP, SQLite, logging, config, security, performance), Python internals
(descriptors, the MRO, the memory model, concurrency, bytecode), and a complete
**AI-from-scratch track** — classic ML, a micrograd-style autodiff engine,
n-gram language models, BPE tokenization, embeddings and retrieval, and scaled
dot-product attention — all implemented in pure standard-library Python.

Career paths end in **scaffolded capstone projects** (a market ledger, an
observatory log pipeline, a courier dispatch board) that compose everything the
path taught.

## Install

You need [Docker](https://docs.docker.com/get-docker/) with Compose v2
(Docker Desktop on macOS/Windows, Docker Engine + the compose plugin on
Linux). Everything else — app, API, sandbox, and the full content library —
ships inside the published multi-arch images (amd64 + arm64).

```bash
mkdir learn-code && cd learn-code
curl -fsSL https://raw.githubusercontent.com/cj-vana/learn-code/main/docker-compose.standalone.yml -o docker-compose.yml
docker compose up -d
```

Then open **http://127.0.0.1:5173**. No clone, no build; progress persists in
a Docker volume. Pin a release with `LEARN_CODE_TAG=1.3.0` (defaults to
`latest`).

**To update**: `docker compose pull && docker compose up -d` — or uncomment
the `watchtower` service in the compose file and updates apply themselves.
The app's status strip tells you when a newer release exists.

**Hacking on it instead?** Clone and build from source:

```bash
git clone https://github.com/cj-vana/learn-code.git
cd learn-code
docker compose up --build
```

The browser app and the CLI both talk to the same FastAPI backend. Learner code
runs in short-lived, sandboxed Python containers via the runner-broker — nothing
you write touches the host.

### CLI

```bash
# inside the repo (or the api container)
learn-code paths                 # list learning paths
learn-code path <path-id>        # show a path's syllabus
learn-code enroll <path-id>      # enroll (sets your active path)
learn-code validate-content      # validate the content library
```

## How it works

| Piece | Role |
|-------|------|
| `apps/web` | Vite + React browser app |
| `apps/api` | FastAPI backend — content, progress, grading, paths, planner |
| `apps/cli` | Typer CLI, an HTTP client of the same API |
| `services/runner-broker` | Spawns short-lived containers to run learner code |
| `services/python-runner` | The sandboxed `python:3.12-slim` execution image |
| `content/python` | The original YAML content library |
| `scripts/generate_paths.py` | Regenerates learning paths from the catalogue |

Progress is single-user and stored locally in SQLite; path completion is
**derived** from your activity, never stored. An adaptive planner surfaces what
to do next, with spaced review of past mistakes and optional timed practice.

## Content authoring

Content is original YAML under `content/python`, validated through a review flow
(briefed → drafted → reviewed → tests validated → published). Every exercise's
sample solution is executed against its own tests during validation.

```bash
learn-code validate-content            # structure, references, and solutions
python3 scripts/generate_paths.py      # regenerate paths after adding content
```

See `docs/content-authoring.md` and `docs/architecture.md` for details.

## Development

```bash
make test        # api, cli, runner-broker (pytest) + web (vitest)
make validate    # repo guard + tests + web build + compose config check
```

## Scope

- Python only in this version. JavaScript/TypeScript is next, with Go after
  that.
- Original practice content only — no third-party problems.
- Local, single-user, offline-capable (no web fonts, no accounts, no
  telemetry). The API's only outbound call is a once-a-day check of GitHub
  Releases for a newer version; it fails silently offline and
  `LEARN_CODE_UPDATE_CHECK=off` disables it.

## License

MIT — see [LICENSE](LICENSE).
