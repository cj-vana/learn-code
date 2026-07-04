# Learn Code API: the only backend for the web app and CLI.
#
# Build context is the REPO ROOT (compose passes context: . with this file) so
# the content library can be baked in — standalone installs run purely from
# this image with no repo checkout.
#
# The API owns the SQLite database (its sole writer) and reaches the runner ONLY
# over HTTP to runner-broker (RUNNER_BROKER_URL). It never mounts the Docker
# socket and never executes learner code -- that boundary lives in runner-broker.
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.11.2 /uv /usr/local/bin/uv

WORKDIR /app

# Workspace metadata only, so this dependency layer caches until uv.lock
# changes. Every member pyproject must be present for uv to load the workspace.
COPY pyproject.toml uv.lock ./
COPY apps/api/pyproject.toml apps/api/
COPY apps/cli/pyproject.toml apps/cli/
COPY services/runner-broker/pyproject.toml services/runner-broker/

# Third-party deps straight from the lockfile; the package itself ships as a
# plain source copy below (PYTHONPATH import, same as before uv).
ENV UV_PYTHON=/usr/local/bin/python3
RUN uv sync --locked --no-dev --no-install-workspace --package learn-code-api

COPY apps/api/learn_code_api /app/learn_code_api

# The content library ships inside the image; the dev compose flow bind-mounts
# a checkout's ./content over /srv/content, which simply shadows this copy.
COPY content /srv/content

# uvicorn resolves the app object lazily via learn_code_api.main:__getattr__
# (build_default_dependencies() reads LEARN_CODE_* env at first access).
# PYTHONPATH makes the package importable regardless of uvicorn's cwd handling.
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH=/app
ENV LEARN_CODE_CONTENT_ROOT=/srv/content/python

EXPOSE 8000

CMD ["uvicorn", "learn_code_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
