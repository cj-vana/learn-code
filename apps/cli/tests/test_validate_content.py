from __future__ import annotations

from learn_code_cli import config
from learn_code_cli.main import app


def test_validate_content_passes_on_seed_tree(runner):
    result = runner.invoke(
        app,
        [
            "validate-content",
            "--content-root",
            str(config.default_content_root()),
            "--no-run-solutions",
        ],
    )
    assert result.exit_code == 0
    assert "content OK" in result.stdout


def test_validate_content_reports_failure(runner, tmp_path):
    result = runner.invoke(
        app,
        [
            "validate-content",
            "--content-root",
            str(tmp_path / "missing"),
            "--no-run-solutions",
        ],
    )
    assert result.exit_code == 1
    assert "content INVALID" in result.stdout
