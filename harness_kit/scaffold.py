from pathlib import Path

from harness_kit.runtime_bundle import iter_runtime_bundle
from harness_kit.template_loader import (
    iter_skill_files,
    iter_template_files,
    load_text,
    render_text,
)


PHASE1_EMPTY_DIRECTORIES = [
    Path("docs/specs"),
    Path("docs/plans"),
    Path("docs/reviews"),
    Path(".harness/runtime/queue/backlog"),
    Path(".harness/runtime/queue/ready"),
    Path(".harness/runtime/queue/in_progress"),
    Path(".harness/runtime/queue/review"),
    Path(".harness/runtime/queue/blocked"),
    Path(".harness/runtime/queue/done"),
    Path(".harness/runtime/context-packs"),
    Path(".harness/runtime/evidence/raw"),
    Path(".harness/runtime/review-packs/drafts"),
    Path(".harness/runtime/agent-runs"),
    Path(".harness/runtime/worktree-registry"),
    Path(".worktrees"),
]


def distribution_root() -> Path:
    return Path(__file__).resolve().parent.parent


def write_text_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def copy_rendered_tree(source_root: Path, target_root: Path, project_name: str) -> None:
    for source_path in iter_template_files(source_root):
        rel_path = source_path.relative_to(source_root)
        target_path = target_root / rel_path
        rendered = render_text(load_text(source_path), project_name)
        write_text_file(target_path, rendered)


def copy_skill_tree(source_root: Path, target_root: Path) -> None:
    for source_path in iter_skill_files(source_root):
        rel_path = source_path.relative_to(source_root)
        target_path = target_root / rel_path
        write_text_file(target_path, load_text(source_path))


def vendor_runtime_bundle(repo_root: Path, target_root: Path) -> None:
    for source_path, rel_target_path in iter_runtime_bundle(repo_root):
        target_path = target_root / rel_target_path
        write_text_file(target_path, load_text(source_path))


def create_empty_directories(target_root: Path) -> None:
    for rel_path in PHASE1_EMPTY_DIRECTORIES:
        (target_root / rel_path).mkdir(parents=True, exist_ok=True)


def init_project(target: Path, project_name: str) -> Path:
    repo_root = distribution_root()
    target = target.resolve()
    target.mkdir(parents=True, exist_ok=True)

    copy_rendered_tree(repo_root / "templates" / "project", target, project_name)
    copy_skill_tree(repo_root / "skills", target / "skills")
    vendor_runtime_bundle(repo_root, target)
    create_empty_directories(target)

    print(target)
    return target
