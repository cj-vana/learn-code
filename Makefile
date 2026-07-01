.PHONY: setup validate test smoke-runner

setup:
	python3 --version
	node --version || true
	docker --version || true

validate:
	python3 scripts/check_repo.py
	@if [ -f docker-compose.yml ]; then docker compose config >/dev/null; fi
	@if [ -f apps/api/pyproject.toml ]; then cd apps/api && python3 -m pytest -q; fi
	@if [ -f apps/cli/pyproject.toml ]; then cd apps/cli && python3 -m pytest -q; fi
	@if [ -f services/runner-broker/pyproject.toml ]; then cd services/runner-broker && python3 -m pytest -q; fi
	@if [ -f apps/web/package.json ]; then cd apps/web && npm run build; fi

test:
	@if [ -f apps/api/pyproject.toml ]; then cd apps/api && python3 -m pytest -q; fi
	@if [ -f apps/cli/pyproject.toml ]; then cd apps/cli && python3 -m pytest -q; fi
	@if [ -f services/runner-broker/pyproject.toml ]; then cd services/runner-broker && python3 -m pytest -q; fi
	@if [ -f apps/web/package.json ]; then cd apps/web && npm test -- --run; fi

smoke-runner:
	@if [ -f docker-compose.yml ]; then docker compose build runner-broker python-runner; fi
