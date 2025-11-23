from pathlib import Path


def get_project_root(sentinel=".git") -> Path:
    """Get the project root directory by looking for a sentinel file or directory.

    If the sentinel (default ``.git``) is not found, fall back to the directory
    containing this file (which works for the Docker image where the source is
    copied directly into ``/app``).
    """
    try:
        return next(p for p in Path(__file__).parents if (p / sentinel).exists())
    except StopIteration as exc:
        # Fallback for Docker where the repository root is not present.
        # Use the mounted /data directory if it exists; otherwise, use the script's directory.
        data_path = Path("/data")
        if data_path.is_dir():
            return data_path
        return Path(__file__).parent
