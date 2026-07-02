from __future__ import annotations

import httpx
import respx

from learn_code_cli.main import app


@respx.mock
def test_status_reports_healthy_api(runner, api_base):
    respx.get(f"{api_base}/health").mock(
        return_value=httpx.Response(200, json={"status": "ok"})
    )
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0
    assert "ok" in result.stdout.lower()
    assert "127.0.0.1:8000" in result.stdout


@respx.mock
def test_status_prints_compose_hint_when_api_unreachable(runner, api_base):
    respx.get(f"{api_base}/health").mock(
        side_effect=httpx.ConnectError("connection refused")
    )
    result = runner.invoke(app, ["status"])
    assert result.exit_code != 0
    assert "docker compose up --build" in result.stdout
