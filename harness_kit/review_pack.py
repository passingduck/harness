import re
from pathlib import Path


RUNTIME_DRAFTS_PATH = Path(".harness/runtime/review-packs/drafts")
REVIEW_DOCS_ROOT = Path("docs/reviews")
PACK_TEMPLATE_BY_TYPE = {
    "commit": Path(".harness/templates/commit-pack.md"),
    "pr": Path(".harness/templates/pr-pack.md"),
}


def _resolve_repo_relative_path(repo_root: Path, rel_path: Path) -> Path:
    repo_root = repo_root.resolve()
    if rel_path.is_absolute():
        resolved = rel_path.resolve()
    else:
        resolved = (repo_root / rel_path).resolve()
    resolved.relative_to(repo_root)
    return resolved


def _slugify_title(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug or "review-pack"


def _load_template(repo_root: Path, review_type: str) -> str:
    try:
        template_path = PACK_TEMPLATE_BY_TYPE[review_type]
    except KeyError as exc:
        raise ValueError(f"unsupported review pack type: {review_type}") from exc
    full_path = repo_root / template_path
    if not full_path.is_file():
        raise FileNotFoundError(full_path)
    return full_path.read_text(encoding="utf-8").rstrip()


def _render_review_pack(
    template: str,
    title: str,
    changed_paths: list[str],
    verification_commands: list[str],
) -> str:
    changed_lines = "\n".join(f"- `{path}`" for path in changed_paths) or "- none provided"
    verification_lines = (
        "\n".join(f"- `{command}`" for command in verification_commands)
        or "- none provided"
    )
    return (
        f"{template}\n\n"
        "## Title\n\n"
        f"{title}\n\n"
        "## Changed Paths\n\n"
        f"{changed_lines}\n\n"
        "## Verification Commands\n\n"
        f"{verification_lines}\n"
    )


def build_review_pack(
    repo_root: Path,
    review_type: str,
    title: str,
    changed_paths: list[str],
    verification_commands: list[str],
) -> Path:
    template = _load_template(repo_root, review_type)
    draft_name = f"{review_type}-{_slugify_title(title)}.md"
    draft_path = _resolve_repo_relative_path(repo_root, RUNTIME_DRAFTS_PATH / draft_name)
    draft_path.parent.mkdir(parents=True, exist_ok=True)
    draft_path.write_text(
        _render_review_pack(template, title, changed_paths, verification_commands),
        encoding="utf-8",
    )
    return draft_path


def build_commit_review_pack(
    repo_root: Path,
    title: str,
    changed_paths: list[str],
    verification_commands: list[str],
) -> Path:
    return build_review_pack(
        repo_root=repo_root,
        review_type="commit",
        title=title,
        changed_paths=changed_paths,
        verification_commands=verification_commands,
    )


def build_pr_review_pack(
    repo_root: Path,
    title: str,
    changed_paths: list[str],
    verification_commands: list[str],
) -> Path:
    return build_review_pack(
        repo_root=repo_root,
        review_type="pr",
        title=title,
        changed_paths=changed_paths,
        verification_commands=verification_commands,
    )


def promote_review_pack(repo_root: Path, draft_path: Path, promote_to: Path) -> Path:
    review_docs_root = (repo_root.resolve() / REVIEW_DOCS_ROOT).resolve()
    source_path = _resolve_repo_relative_path(repo_root, draft_path)
    target_path = _resolve_repo_relative_path(repo_root, promote_to)
    try:
        target_path.relative_to(review_docs_root)
    except ValueError as exc:
        raise ValueError("promoted review packs must stay under docs/reviews") from exc
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(source_path.read_text(encoding="utf-8"), encoding="utf-8")
    return target_path
