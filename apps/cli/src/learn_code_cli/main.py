"""Typer command surface for the Learn Code CLI.

Commands are thin: read args, call the API over httpx, render the response.
Learner actions never touch the database or run code locally. The only local
actions are ``validate-content`` and ``up``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from learn_code_cli import config, content_validation, docker_compose, render
from learn_code_cli.http_client import ApiClient, ApiConnectionError, ApiError

app = typer.Typer(
    help="Thin HTTP client for the Learn Code API.",
    no_args_is_help=True,
    add_completion=False,
)


def _client() -> ApiClient:
    return ApiClient()


def _fail(message: str) -> None:
    typer.echo(message, err=False)
    raise typer.Exit(code=1)


def _read_source(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        _fail(f"Can't read {path}: {exc}")
        raise  # unreachable; keeps type checkers happy
    except UnicodeDecodeError:
        _fail(f"Can't read {path}: not a UTF-8 text file")
        raise  # unreachable; keeps type checkers happy


def _handle(action):
    """Run an API-calling action, converting failures to terse CLI errors."""
    try:
        return action()
    except ApiConnectionError:
        _fail(render.unreachable(config.api_root()))
    except ApiError as exc:
        _fail(render.friendly_error(exc))


@app.command()
def status() -> None:
    """Check that the API is reachable."""
    _handle(lambda: _client().health())
    typer.echo(render.render_status(config.api_root()))


@app.command()
def up() -> None:
    """Bring the stack up with Docker Compose, or print the command."""
    outcome = docker_compose.bring_up(config.repo_root())
    if outcome.message:
        typer.echo(outcome.message)
    if outcome.returncode != 0:
        raise typer.Exit(code=outcome.returncode)


@app.command()
def next() -> None:
    """Show today's adaptive plan."""
    plan = _handle(lambda: _client().plan())
    typer.echo(render.render_plan(plan))


@app.command()
def run(exercise_id: str, solution_file: Path) -> None:
    """Run public tests for an exercise against a solution file."""
    source = _read_source(solution_file)
    result = _handle(lambda: _client().run_exercise(exercise_id, source))
    typer.echo(render.render_run(result))


@app.command()
def submit(
    exercise_id: str,
    solution_file: Path,
    predicted_pattern: Optional[str] = typer.Option(None, "--predicted-pattern"),
    confidence: Optional[int] = typer.Option(None, "--confidence"),
    hints_used: int = typer.Option(0, "--hints-used"),
) -> None:
    """Submit a solution against the validation suite and record progress."""
    source = _read_source(solution_file)
    detail = _handle(lambda: _client().content_detail(exercise_id))
    response = _handle(
        lambda: _client().submit_exercise(
            exercise_id,
            detail["version"],
            source,
            predicted_pattern=predicted_pattern,
            confidence=confidence,
            hints_used=hints_used,
        )
    )
    typer.echo(render.render_submission(response))


@app.command()
def playground(
    file: Path,
    stdin: Optional[str] = typer.Option(None, "--stdin", help="Text piped to the program's stdin."),
) -> None:
    """Run an arbitrary Python file in the sandbox."""
    source = _read_source(file)
    result = _handle(lambda: _client().playground(source, stdin))
    typer.echo(render.render_run(result))


@app.command()
def lesson(lesson_id: str) -> None:
    """Read a lesson and its self-check questions."""
    detail = _handle(lambda: _client().content_detail(lesson_id))
    if detail.get("kind") != "lesson":
        _fail(f"{lesson_id} is not a lesson.")
    typer.echo(render.render_lesson(detail))


@app.command()
def quiz(quiz_id: str) -> None:
    """Take a quiz; each answer is graded by the API."""
    detail = _handle(lambda: _client().content_detail(quiz_id))
    if detail.get("kind") != "quiz":
        _fail(f"{quiz_id} is not a quiz.")
    questions = detail["questions"]
    correct_count = 0
    for number, question in enumerate(questions, start=1):
        typer.echo(f"\n[{number}/{len(questions)}] {question['prompt']}")
        for choice_number, choice in enumerate(question["choices"], start=1):
            typer.echo(f"  {choice_number}. {choice}")
        picked = typer.prompt("Answer number", type=int)
        if not 1 <= picked <= len(question["choices"]):
            _fail(f"Pick a number between 1 and {len(question['choices'])}.")
        response = _handle(
            lambda q=question, p=picked: _client().answer_quiz(
                detail["id"], q["id"], q["choices"][p - 1]
            )
        )
        correct_count += 1 if response["correct"] else 0
        verdict = "Correct." if response["correct"] else "Not this time."
        typer.echo(f"{verdict} {response['explanation']}")
    typer.echo(f"\nScore: {correct_count}/{len(questions)}")


@app.command()
def timed(
    count: int = typer.Option(3, "--count", min=1, max=10),
    minutes: int = typer.Option(15, "--minutes", min=1, max=60),
    concept: Optional[str] = typer.Option(None, "--concept"),
) -> None:
    """Start a timed practice set: eligible problems plus a per-problem budget."""
    session = _handle(
        lambda: _client().timed_session(count, minutes, concept)
    )
    exercises = session["exercises"]
    if not exercises:
        typer.echo(
            "Nothing is timed-ready yet - get a few concepts to practicing mastery first."
        )
        return
    typer.echo(
        f"Timed set ({len(exercises)} problems, {session['minutes_per_problem']} min each):"
    )
    for number, exercise in enumerate(exercises, start=1):
        typer.echo(f"  {number}. {exercise['title']}  ({exercise['id']})")
    typer.echo("")
    typer.echo(
        "Set a timer per problem, then grade each with: learn-code submit <id> <file>"
    )


@app.command()
def paths() -> None:
    """List learning paths with enrollment and progress."""
    items = _handle(lambda: _client().paths())
    typer.echo(render.render_paths(items))


@app.command()
def path(path_id: str) -> None:
    """Show a path's syllabus with per-item status."""
    detail = _handle(lambda: _client().path_detail(path_id))
    typer.echo(render.render_path_detail(detail))


@app.command()
def enroll(path_id: str) -> None:
    """Enroll in a path (supersedes any current enrollment)."""
    response = _handle(lambda: _client().enroll_path(path_id))
    typer.echo(f"Enrolled in {response['path_id']}.")


@app.command()
def unenroll(path_id: str) -> None:
    """Leave a path; derived progress is kept."""
    response = _handle(lambda: _client().unenroll_path(path_id))
    typer.echo(f"Unenrolled from {response['path_id']}.")


@app.command()
def progress() -> None:
    """Show mastery, streak, and the next recommended action."""
    summary = _handle(lambda: _client().progress())
    typer.echo(render.render_progress(summary))


@app.command()
def review(
    exercise_id: str,
    solution_file: Path,
    test_summary: str = typer.Option("not provided", "--test-summary"),
    allow_solution_disclosure: bool = typer.Option(False, "--allow-solution-disclosure"),
) -> None:
    """Ask the optional Ollama reviewer for feedback."""
    source = _read_source(solution_file)
    result = _handle(
        lambda: _client().review(
            exercise_id,
            source,
            test_summary,
            allow_solution_disclosure=allow_solution_disclosure,
        )
    )
    typer.echo(render.render_review(result))


@app.command(name="validate-content")
def validate_content(
    content_root: Optional[Path] = typer.Option(
        None, "--content-root", help="Defaults to the repo's content/python tree."
    ),
    profile: str = typer.Option("library", "--profile"),
    include_drafts: bool = typer.Option(False, "--include-drafts"),
    run_solutions: bool = typer.Option(True, "--run-solutions/--no-run-solutions"),
) -> None:
    """Validate the repo content tree (local; not a learner action)."""
    root = content_root or config.default_content_root()
    report = content_validation.validate(
        root,
        profile=profile,
        include_drafts=include_drafts,
        run_solutions=run_solutions,
    )
    typer.echo(content_validation.render_report(report))
    if not report.ok:
        raise typer.Exit(code=1)


if __name__ == "__main__":  # pragma: no cover
    app()
