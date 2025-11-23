from pathlib import Path


def get_project_root(sentinel: str = ".git") -> Path:
    """Get the project root directory by looking for a sentinel file or directory.

    If the sentinel (default ``.git``) is not found, this function raises a
    ``FileNotFoundError``.

    Args:
        sentinel: The file or directory to look for.

    Returns:
        The path to the project root.

    Raises:
        FileNotFoundError: If the sentinel is not found in any parent directory.
    """
    current_path = Path(__file__).resolve()
    for parent in current_path.parents:
        if (parent / sentinel).exists():
            return parent
    raise FileNotFoundError(f"Could not find project root with sentinel '{sentinel}'")
