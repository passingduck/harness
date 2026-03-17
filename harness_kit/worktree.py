from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any

from harness_kit.queue import (
    _parse_frontmatter,
    _render_frontmatter,
    _split_frontmatter_block,
    find_task_path,
    move_task,
)


WORKTREE_REGISTRY_FIELDS = [
    "task_id",
    "worktree_name",
    "path",
    "branch",
    "status",
    "baseline_verified",
    "cleanup_policy",
]
WORKER_STATUS_TO_QUEUE_STATE = {
    "DONE": "review",
    "DONE_WITH_CONCERNS": "review",
    "NEEDS_CONTEXT": "ready",
    "BLOCKED": "blocked",
}


def choose_worktree_path(repo_root: Path, task_id: str) -> Path:
    return repo_root / ".worktrees" / task_id


def _registry_record_path(repo_root: Path, task_id: str) -> Path:
    return repo_root / ".harness" / "runtime" / "worktree-registry" / f"{task_id}.md"


def _is_git_repo(repo_root: Path) -> bool:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "--is-inside-work-tree"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0


def _ensure_worktree_roots(repo_root: Path) -> None:
    (repo_root / ".harness" / "runtime" / "worktree-registry").mkdir(
        parents=True,
        exist_ok=True,
    )
    (repo_root / ".worktrees").mkdir(parents=True, exist_ok=True)


def _verify_worktrees_ignored(repo_root: Path) -> None:
    if not _is_git_repo(repo_root):
        return
    gitignore_path = repo_root / ".gitignore"
    if not gitignore_path.is_file():
        raise ValueError("Repository must ignore .worktrees/ in .gitignore.")
    ignored_entries = {
        line.strip()
        for line in gitignore_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    if ".worktrees/" not in ignored_entries:
        raise ValueError("Repository must ignore .worktrees/ in .gitignore.")


def _run_git(repo_root: Path, args: list[str]) -> None:
    proc = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        message = proc.stderr.strip() or proc.stdout.strip() or "git command failed"
        raise RuntimeError(message)


def _provision_worktree(repo_root: Path, worktree_path: Path, branch_name: str) -> None:
    if not _is_git_repo(repo_root):
        worktree_path.mkdir(parents=True, exist_ok=True)
        return
    try:
        _run_git(repo_root, ["worktree", "add", "-b", branch_name, str(worktree_path)])
    except RuntimeError:
        _run_git(repo_root, ["worktree", "add", str(worktree_path), branch_name])


def _remove_worktree(repo_root: Path, worktree_path: Path) -> None:
    if not worktree_path.exists():
        return
    if not _is_git_repo(repo_root):
        shutil.rmtree(worktree_path)
        return
    _run_git(repo_root, ["worktree", "remove", "--force", str(worktree_path)])


def _read_registry_record(record_path: Path) -> dict[str, Any]:
    frontmatter_text, _ = _split_frontmatter_block(record_path.read_text(encoding="utf-8"))
    return _parse_frontmatter(frontmatter_text)


def _write_registry_record(record_path: Path, record: dict[str, Any]) -> None:
    record_path.parent.mkdir(parents=True, exist_ok=True)
    frontmatter_text = _render_frontmatter(record, WORKTREE_REGISTRY_FIELDS)
    record_path.write_text(f"{frontmatter_text}\n", encoding="utf-8")


def open_worktree(
    repo_root: Path,
    task_id: str,
    branch_name: str,
    cleanup_policy: str,
) -> Path:
    if cleanup_policy not in {"preserve", "delete"}:
        raise ValueError(f"Unsupported cleanup policy: {cleanup_policy}")
    worktree_name = task_id
    if worktree_name != task_id:
        raise ValueError("Phase 1 requires worktree_name == task_id.")
    _ensure_worktree_roots(repo_root)
    _verify_worktrees_ignored(repo_root)
    worktree_path = choose_worktree_path(repo_root, task_id)
    _provision_worktree(repo_root, worktree_path, branch_name)
    baseline_verified = worktree_path.exists()
    record = {
        "task_id": task_id,
        "worktree_name": worktree_name,
        "path": str(worktree_path),
        "branch": branch_name,
        "status": "attached",
        "baseline_verified": baseline_verified,
        "cleanup_policy": cleanup_policy,
    }
    record_path = _registry_record_path(repo_root, task_id)
    _write_registry_record(record_path, record)
    return record_path


def close_worktree(
    repo_root: Path,
    task_id: str,
    mode: str,
    worker_status: str,
) -> tuple[Path | None, Path]:
    if worker_status not in WORKER_STATUS_TO_QUEUE_STATE:
        raise ValueError(f"Unsupported worker status: {worker_status}")
    if mode not in {"preserve", "delete"}:
        raise ValueError(f"Unsupported worktree close mode: {mode}")
    _ensure_worktree_roots(repo_root)
    record_path = _registry_record_path(repo_root, task_id)
    if record_path.is_file():
        record = _read_registry_record(record_path)
    else:
        record = {
            "task_id": task_id,
            "worktree_name": task_id,
            "path": str(choose_worktree_path(repo_root, task_id)),
            "branch": task_id,
            "status": "attached",
            "baseline_verified": False,
            "cleanup_policy": mode,
        }
    worktree_path = Path(str(record["path"]))
    if mode == "delete":
        _remove_worktree(repo_root, worktree_path)
        record["status"] = "deleted"
    else:
        record["status"] = "preserved"
    record["cleanup_policy"] = mode
    _write_registry_record(record_path, record)

    task_path = find_task_path(repo_root, task_id)
    moved_task: Path | None = None
    if task_path is not None:
        moved_task = move_task(task_path, WORKER_STATUS_TO_QUEUE_STATE[worker_status])
    return moved_task, record_path
