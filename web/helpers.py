from pathlib import Path


def get_project_root(sentinel: str = ".git") -> Path:
    """Get the project root directory by looking for a sentinel file or directory.

    Args:
        sentinel: The sentinel file or directory to look for.

    Returns:
        The project root directory path.

    Raises:
        FileNotFoundError: If the project root cannot be found.
    """
    try:
        return next(p for p in Path(__file__).parents if (p / sentinel).exists())
    except StopIteration as exc:
        msg = f"Project root not found. No '{sentinel}' in parent directories of {__file__}"
        raise FileNotFoundError(msg) from exc


def get_data_file_path(filename: str = "weather.json") -> Path:
    """Get the path to a data file, working both locally and in Docker.

    In Docker, the data directory is mounted at /data.
    Locally, it's at the project root under data/.

    Args:
        filename: The name of the data file.

    Returns:
        The path to the data file.
    """
    docker_path = Path("/data") / filename
    if docker_path.parent.exists() and docker_path.parent.is_dir():
        return docker_path

    # Fallback to local development path
    try:
        root = get_project_root()
        return root / "data" / filename
    except FileNotFoundError:
        # If we can't find project root, assume we're in Docker
        return docker_path
