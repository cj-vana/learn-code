# runner-broker is the only service allowed to mount /var/run/docker.sock. It
# is an internal-only Compose service with no host port.
#
# Build context is the REPO ROOT (compose passes context: . with this file) so
# the content library — the broker resolves exercise test cases from it — can
# be baked in for checkout-free installs. The dev compose flow bind-mounts a
# checkout's ./content over /srv/content, shadowing the baked copy.
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.11.2 /uv /usr/local/bin/uv

WORKDIR /srv

# Workspace metadata only, so this dependency layer caches until uv.lock
# changes. Every member pyproject must be present for uv to load the workspace.
COPY pyproject.toml uv.lock ./
COPY apps/api/pyproject.toml apps/api/
COPY apps/cli/pyproject.toml apps/cli/
COPY services/runner-broker/pyproject.toml services/runner-broker/

# Third-party deps straight from the lockfile; the app package ships as a
# plain source copy below (PYTHONPATH import).
ENV UV_PYTHON=/usr/local/bin/python3
RUN uv sync --locked --no-dev --no-install-workspace --package learn-code-runner-broker

COPY services/runner-broker/app /srv/app
COPY content /srv/content

ENV PATH="/srv/.venv/bin:$PATH"
ENV PYTHONPATH=/srv
ENV LEARN_CODE_CONTENT_ROOT=/srv/content/python

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
