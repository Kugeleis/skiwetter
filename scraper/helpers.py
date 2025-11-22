from pathlib import Path


def get_project_root(sentinel=".git") -> Path:
    """Get the project root directory by looking for a sentinel file or directory."""
    try:
        return next(p for p in Path(__file__).parents if (p / sentinel).exists())
    except StopIteration as exc:
        raise FileNotFoundError(
            f"Project root not found. No '{sentinel}' in parent directories of {__file__}"
        ) from exc