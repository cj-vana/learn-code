# runner-broker is the only service allowed to mount /var/run/docker.sock. It
# is an internal-only Compose service with no host port (docs/superpowers/
# specs/2026-07-01-learn-code-design.md:232-246).
FROM python:3.12-slim

WORKDIR /srv

COPY pyproject.toml /srv/pyproject.toml
COPY app /srv/app

RUN pip install --no-cache-dir .

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
