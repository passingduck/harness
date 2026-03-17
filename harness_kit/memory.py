from pathlib import Path, PurePosixPath


DIRECTORY_TEMPLATE_PATH = Path(".harness/templates/directory.md")
DIRECTORY_GUIDE_NAME = "DIRECTORY.md"
KNOWN_FILE_NAMES = {
    "AGENTS.md",
    "DIRECTORY.md",
    "Dockerfile",
    "LICENSE",
    "Makefile",
    "README",
    "README.md",
    "REQUIREMENT.md",
    "SUMMARY.md",
}
NON_MEANINGFUL_DIRECTORY_NAMES = {
    "models",
}


def _normalize_changed_path(changed_path: str) -> PurePosixPath | None:
    normalized = PurePosixPath(changed_path)
    if normalized.is_absolute():
        raise ValueError(f"changed path must be relative: {changed_path}")
    parts = tuple(part for part in normalized.parts if part not in ("", "."))
    if not parts:
        return None
    if ".." in parts:
        raise ValueError(f"changed path must stay within repo root: {changed_path}")
    return PurePosixPath(*parts)


def _directory_for_changed_path(changed_path: PurePosixPath) -> PurePosixPath:
    if changed_path.name == DIRECTORY_GUIDE_NAME:
        directory = changed_path.parent
    elif (
        changed_path.suffix
        or changed_path.name in KNOWN_FILE_NAMES
        or changed_path.name.startswith(".")
    ):
        directory = changed_path.parent
    else:
        directory = changed_path
    while directory.name in NON_MEANINGFUL_DIRECTORY_NAMES and directory.parent != directory:
        directory = directory.parent
    return directory


def _looks_like_extensionless_file_path(changed_path: PurePosixPath) -> bool:
    return (
        bool(changed_path.parts)
        and not changed_path.suffix
        and changed_path.name not in KNOWN_FILE_NAMES
        and not changed_path.name.startswith(".")
        and changed_path.name != DIRECTORY_GUIDE_NAME
    )


def _repo_relative_directory_for_changed_path(
    repo_root: Path,
    changed_path: PurePosixPath,
) -> PurePosixPath:
    resolved_repo_root = repo_root.resolve()
    resolved_path = (resolved_repo_root / Path(*changed_path.parts)).resolve()
    try:
        resolved_path.relative_to(resolved_repo_root)
    except ValueError as exc:
        raise ValueError(f"changed path must stay within repo root: {changed_path.as_posix()}") from exc
    if resolved_path.exists() and resolved_path.is_file():
        return _directory_for_changed_path(changed_path.parent)
    if (
        _looks_like_extensionless_file_path(changed_path)
        and changed_path.parent.parts
        and (resolved_repo_root / Path(*changed_path.parent.parts)).is_dir()
        and not resolved_path.exists()
    ):
        return _directory_for_changed_path(changed_path.parent)
    return _directory_for_changed_path(changed_path)


def _select_directory_for_changed_path(
    changed_path: PurePosixPath,
    repo_root: Path | None = None,
) -> PurePosixPath:
    if repo_root is not None:
        return _repo_relative_directory_for_changed_path(repo_root, changed_path)
    if _looks_like_extensionless_file_path(changed_path) and changed_path.parent.parts:
        return _directory_for_changed_path(changed_path.parent)
    return _directory_for_changed_path(changed_path)

def compute_directory_guides_to_refresh(
    changed_paths: list[str],
    repo_root: Path | None = None,
) -> set[str]:
    guides: set[str] = set()
    for changed_path in changed_paths:
        normalized = _normalize_changed_path(changed_path)
        if normalized is None:
            continue
        directory = _select_directory_for_changed_path(
            normalized,
            repo_root=repo_root.resolve() if repo_root is not None else None,
        )
        guide = directory / DIRECTORY_GUIDE_NAME
        guides.add(guide.as_posix() if guide.parts else DIRECTORY_GUIDE_NAME)
    return guides


def _resolve_repo_relative_path(repo_root: Path, rel_path: Path) -> Path:
    if rel_path.is_absolute():
        raise ValueError(f"path must be relative to repo root: {rel_path}")
    repo_root = repo_root.resolve()
    resolved = (repo_root / rel_path).resolve()
    resolved.relative_to(repo_root)
    return resolved


def ensure_directory_guide(repo_root: Path, guide_path: Path) -> Path:
    draft_path = _resolve_repo_relative_path(repo_root, guide_path)
    if draft_path.exists():
        return draft_path
    template_path = repo_root / DIRECTORY_TEMPLATE_PATH
    if not template_path.is_file():
        raise FileNotFoundError(template_path)
    draft_path.parent.mkdir(parents=True, exist_ok=True)
    draft_path.write_text(template_path.read_text(encoding="utf-8"), encoding="utf-8")
    return draft_path


def refresh_memory(repo_root: Path, changed_paths: list[str]) -> list[Path]:
    guides = compute_directory_guides_to_refresh(
        changed_paths,
        repo_root=repo_root,
    )
    return [
        ensure_directory_guide(repo_root, Path(guide_path))
        for guide_path in sorted(guides)
    ]
