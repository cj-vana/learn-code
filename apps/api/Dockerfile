# Learn Code API: the only backend for the web app and CLI.
#
# The API owns the SQLite database (its sole writer) and reaches the runner ONLY
# over HTTP to runner-broker (RUNNER_BROKER_URL). It never mounts the Docker
# socket and never executes learner code -- that boundary lives in runner-broker.
FROM python:3.12-slim

WORKDIR /app

# apps/api/pyproject.toml declares no build backend, so install the pinned
# runtime dependency set directly rather than `pip install .` (keep this list in
# sync with apps/api/pyproject.toml `dependencies`).
RUN pip install --no-cache-dir \
    "fastapi>=0.128.0" \
    "uvicorn[standard]" \
    "pydantic>=2.12" \
    pyyaml \
    httpx

COPY learn_code_api /app/learn_code_api

# uvicorn resolves the app object lazily via learn_code_api.main:__getattr__
# (build_default_dependencies() reads LEARN_CODE_* env at first access).
# PYTHONPATH makes the package importable regardless of uvicorn's cwd handling.
ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["uvicorn", "learn_code_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
