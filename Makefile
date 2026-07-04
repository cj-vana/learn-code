.PHONY: setup validate test smoke-runner

# Prefer the repo venv when it exists; fall back to system python3.
PY := $(shell [ -x "$(CURDIR)/.venv/bin/python" ] && echo "$(CURDIR)/.venv/bin/python" || echo python3)

setup:
	uv --version
	uv sync --all-packages
	node --version || true
	docker --version || true

validate:
	$(PY) scripts/check_repo.py
	@if [ -f docker-compose.yml ]; then docker compose config >/dev/null; fi
	@if [ -f apps/api/pyproject.toml ]; then cd apps/api && $(PY) -m pytest -q; fi
	@if [ -f apps/cli/pyproject.toml ]; then cd apps/cli && $(PY) -m pytest -q; fi
	@if [ -f services/runner-broker/pyproject.toml ]; then cd services/runner-broker && $(PY) -m pytest -q; fi
	@if [ -f apps/web/package.json ]; then cd apps/web && npm run build; fi

test:
	@if [ -f apps/api/pyproject.toml ]; then cd apps/api && $(PY) -m pytest -q; fi
	@if [ -f apps/cli/pyproject.toml ]; then cd apps/cli && $(PY) -m pytest -q; fi
	@if [ -f services/runner-broker/pyproject.toml ]; then cd services/runner-broker && $(PY) -m pytest -q; fi
	@if [ -f apps/web/package.json ]; then cd apps/web && npm test -- --run; fi

smoke-runner:
	@if [ -f docker-compose.yml ]; then docker compose build runner-broker python-runner; fi
