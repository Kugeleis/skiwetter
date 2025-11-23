from duty import duty


@duty
def check(ctx):
    """Check code quality (linting and testing)."""
    ctx.run("uv run ruff check .", title="Linting (Ruff)")
    ctx.run("uv run ruff format --check .", title="Checking formatting (Ruff)")
    ctx.run("uv run mypy scraper/ web/ --ignore-missing-imports", title="Running mypy type checks")


@duty
def format(ctx):
    """Format code and fix linting issues."""
    ctx.run("uv run ruff check --fix .", title="Fixing lint issues")
    ctx.run("uv run ruff format .", title="Formatting code")


@duty
def clean(ctx):
    """Clean up build artifacts and cache."""
    ctx.run("rm -rf .ruff_cache .pytest_cache .coverage htmlcov dist build", title="Cleaning caches")
    ctx.run("find . -type d -name __pycache__ -exec rm -rf {} +", title="Removing __pycache__")


@duty
def release(ctx, part="patch"):
    """Bump version and release.

    Args:
        part: The part of the version to bump (major, minor, patch).
    """
    ctx.run(f"uv run bump-my-version bump {part}", title=f"Bumping {part} version")
