from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any

from harness_kit.queue import (
    _parse_frontmatter,
    _render_frontmatter,
    _split_frontmatter_block,
    VALID_TRANSITIONS,
    canonical_task_filename,
    find_task_path,
    load_task,
    move_task,
    validate_phase1_task_id,
    write_task,
)


WORKTREE_REGISTRY_FIELDS = [
    "task_id",
    "worktree_name",
    "path",
    "branch",
    "status",
    "baseline_verified",
    "cleanup_policy",
    "target_branch",
    "merge_strategy",
    "merge_status",
    "merged_commit",
    "push_status",
    "push_remote",
    "publish_head_ref",
    "draft_pr_review_pack",
    "promoted_review_pack",
    "pr_number",
    "pr_url",
    "adapter_status",
    "finished_at",
    "finalization_notes",
]
WORKER_STATUS_TO_QUEUE_STATE = {
    "DONE": "review",
    "DONE_WITH_CONCERNS": "review",
    "NEEDS_CONTEXT": "ready",
    "BLOCKED": "blocked",
}


def choose_worktree_path(repo_root: Path, task_id: str) -> Path:
    return repo_root / ".worktrees" / validate_phase1_task_id(task_id)


def _registry_record_path(repo_root: Path, task_id: str) -> Path:
    return (
        repo_root
        / ".harness"
        / "runtime"
        / "worktree-registry"
        / canonical_task_filename(task_id)
    )


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
    result = subprocess.run(
        ["git", "-C", str(repo_root), "check-ignore", "-q", "--", ".worktrees/.probe"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 0:
        return
    if result.returncode != 1:
        message = result.stderr.strip() or result.stdout.strip() or "git check-ignore failed"
        raise RuntimeError(message)
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


def _repo_relative_registry_path(repo_root: Path, path: Path | str) -> str:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = repo_root / candidate
    resolved = candidate.resolve(strict=False)
    relative = resolved.relative_to(repo_root.resolve())
    return str(relative)


def load_worktree_registry(repo_root: Path, task_id: str) -> tuple[Path, dict[str, Any]]:
    task_id = validate_phase1_task_id(task_id)
    record_path = _registry_record_path(repo_root, task_id)
    if not record_path.is_file():
        raise FileNotFoundError(f"Missing worktree registry record: {record_path}")
    record = _read_registry_record(record_path)
    if record.get("task_id") != task_id:
        raise ValueError("Worktree registry task_id must match the requested task.")
    return record_path, record


def write_worktree_registry(repo_root: Path, task_id: str, record: dict[str, Any]) -> Path:
    task_id = validate_phase1_task_id(task_id)
    record = dict(record)
    record["task_id"] = task_id
    record_path = _registry_record_path(repo_root, task_id)
    _write_registry_record(record_path, record)
    return record_path


def record_review_pack_path(
    repo_root: Path,
    task_id: str,
    *,
    draft_path: Path | str | None = None,
    promoted_path: Path | str | None = None,
) -> Path | None:
    try:
        record_path, record = load_worktree_registry(repo_root, task_id)
    except FileNotFoundError:
        return None
    if draft_path is not None:
        record["draft_pr_review_pack"] = _repo_relative_registry_path(repo_root, draft_path)
    if promoted_path is not None:
        record["promoted_review_pack"] = _repo_relative_registry_path(repo_root, promoted_path)
    return write_worktree_registry(repo_root, task_id, record)


def _resolve_registry_worktree_path(repo_root: Path, task_id: str, raw_path: str) -> Path:
    worktrees_root = (repo_root / ".worktrees").resolve(strict=False)
    expected_path = choose_worktree_path(repo_root, task_id).resolve(strict=False)
    candidate = Path(raw_path)
    if not candidate.is_absolute():
        candidate = repo_root / candidate
    resolved = candidate.resolve(strict=False)
    if resolved != expected_path or not resolved.is_relative_to(worktrees_root):
        raise ValueError("Registry worktree path must match the task worktree location.")
    return resolved


def _validate_close_transition(repo_root: Path, task_id: str, worker_status: str) -> Path | None:
    task_path = find_task_path(repo_root, task_id)
    if task_path is None:
        return None
    task = load_task(task_path)
    target_state = WORKER_STATUS_TO_QUEUE_STATE[worker_status]
    if target_state not in VALID_TRANSITIONS[task.state]:
        raise ValueError(f"Invalid queue transition: {task.state} -> {target_state}")
    return task_path


def open_worktree(
    repo_root: Path,
    task_id: str,
    branch_name: str,
    cleanup_policy: str,
) -> Path:
    task_id = validate_phase1_task_id(task_id)
    if cleanup_policy not in {"preserve", "delete"}:
        raise ValueError(f"Unsupported cleanup policy: {cleanup_policy}")
    worktree_name = task_id
    if worktree_name != task_id:
        raise ValueError("Phase 1 requires worktree_name == task_id.")
    _verify_worktrees_ignored(repo_root)
    _ensure_worktree_roots(repo_root)
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
    return write_worktree_registry(repo_root, task_id, record)


def close_worktree(
    repo_root: Path,
    task_id: str,
    mode: str,
    worker_status: str,
) -> tuple[Path | None, Path]:
    task_id = validate_phase1_task_id(task_id)
    if worker_status not in WORKER_STATUS_TO_QUEUE_STATE:
        raise ValueError(f"Unsupported worker status: {worker_status}")
    if mode not in {"preserve", "delete"}:
        raise ValueError(f"Unsupported worktree close mode: {mode}")
    _ensure_worktree_roots(repo_root)
    record_path, record = load_worktree_registry(repo_root, task_id)
    worktree_path = _resolve_registry_worktree_path(repo_root, task_id, str(record["path"]))
    task_path = _validate_close_transition(repo_root, task_id, worker_status)
    if mode == "delete":
        _remove_worktree(repo_root, worktree_path)
        record["status"] = "deleted"
    else:
        record["status"] = "preserved"
    record["cleanup_policy"] = mode
    record_path = write_worktree_registry(repo_root, task_id, record)

    moved_task: Path | None = None
    if task_path is not None:
        task = load_task(task_path)
        frontmatter = dict(task.frontmatter)
        frontmatter["worktree"] = None
        write_task(task_path, frontmatter, task.sections)
        moved_task = move_task(task_path, WORKER_STATUS_TO_QUEUE_STATE[worker_status])
    return moved_task, record_path
