# Build-only image for short-lived execution containers. Never run this as a
# long-lived Compose service; runner-broker creates a fresh container from
# this image per run and removes it when the run finishes.
FROM python:3.12-slim

# Fixed non-root uid/gid matching the executor's `user: "1000:1000"` container
# option (services/runner-broker/app/executor.py).
RUN groupadd --gid 1000 runner \
    && useradd --uid 1000 --gid 1000 --no-create-home --shell /usr/sbin/nologin runner

WORKDIR /app
COPY harness.py /app/harness.py

RUN mkdir -p /workspace && chown 1000:1000 /workspace

USER 1000:1000

# No ENTRYPOINT/CMD: runner-broker always supplies the full command
# (python3 /app/harness.py <job.json> <result.json>) when it creates a
# container from this image, so there is nothing sensible to run by default.
