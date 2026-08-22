from pathlib import Path


_IGNORED_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "reports",
}


def discover_python_files(project_root: Path) -> tuple[str, ...]:
    root = project_root.resolve()
    selected: list[str] = []

    for path in sorted(root.rglob("*.py")):
        relative = path.relative_to(root)
        if any(part in _IGNORED_DIRS for part in relative.parts[:-1]):
            continue
        selected.append(relative.as_posix())

    return tuple(selected)
