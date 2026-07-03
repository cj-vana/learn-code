# runner-broker is the only service allowed to mount /var/run/docker.sock. It
# is an internal-only Compose service with no host port.
#
# Build context is the REPO ROOT (compose passes context: . with this file) so
# the content library — the broker resolves exercise test cases from it — can
# be baked in for checkout-free installs. The dev compose flow bind-mounts a
# checkout's ./content over /srv/content, shadowing the baked copy.
FROM python:3.12-slim

WORKDIR /srv

COPY services/runner-broker/pyproject.toml /srv/pyproject.toml
COPY services/runner-broker/app /srv/app
COPY content /srv/content

RUN pip install --no-cache-dir .

ENV LEARN_CODE_CONTENT_ROOT=/srv/content/python

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
