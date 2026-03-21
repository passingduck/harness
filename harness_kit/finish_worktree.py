from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import subprocess

from harness_kit.queue import find_task_path, load_task, move_task, validate_phase1_task_id, write_task
from harness_kit.review_pack import promote_review_pack as promote_review_pack_doc
from harness_kit.review_results import validate_review_results
from harness_kit.worktree import (
    _remove_worktree,
    _resolve_registry_worktree_path,
    load_worktree_registry,
    write_worktree_registry,
)


@dataclass
class FinishResult:
    queue_path: Path
    registry_path: Path
    merged_commit: str
    target_branch: str
    promoted_review_pack: Path | None
    push_status: str


def _run_git(repo_root: Path, args: list[str]) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        message = proc.stderr.strip() or proc.stdout.strip() or "git command failed"
        raise RuntimeError(message)
    return proc.stdout.strip()


def _branch_exists(repo_root: Path, branch_name: str) -> bool:
    proc = subprocess.run(
        ["git", "-C", str(repo_root), "show-ref", "--verify", "--quiet", f"refs/heads/{branch_name}"],
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode == 0


def _require_clean_worktree(repo_root: Path) -> None:
    status = _run_git(repo_root, ["status", "--porcelain"])
    if status:
        raise RuntimeError("finish-worktree requires a clean git working tree.")


def _ensure_docs_updated(repo_root: Path, target_branch: str, source_branch: str, docs_to_update: list[str]) -> None:
    changed = {
        line.strip()
        for line in _run_git(repo_root, ["diff", "--name-only", f"{target_branch}..{source_branch}"]).splitlines()
        if line.strip()
    }
    missing = [path for path in docs_to_update if path not in changed]
    if missing:
        raise ValueError(
            "All docs_to_update paths must appear in the source diff: " + ", ".join(missing)
        )


def _resolve_review_pack_paths(repo_root: Path, task_id: str, record: dict[str, object]) -> tuple[Path, Path | None]:
    worktree_root: Path | None = None
    raw_worktree_path = record.get("path")
    if isinstance(raw_worktree_path, str) and raw_worktree_path:
        worktree_root = Path(raw_worktree_path).resolve(strict=False)

    def iter_candidates(raw_path: str) -> list[Path]:
        candidates: list[Path] = [(repo_root / raw_path).resolve(strict=False)]
        if worktree_root is not None:
            worktree_candidate = (worktree_root / raw_path).resolve(strict=False)
            if worktree_candidate not in candidates:
                candidates.append(worktree_candidate)
        return candidates

    promoted = record.get("promoted_review_pack")
    if isinstance(promoted, str) and promoted:
        for promoted_path in iter_candidates(promoted):
            if promoted_path.is_file():
                return promoted_path, None
    draft = record.get("draft_pr_review_pack")
    if isinstance(draft, str) and draft:
        for draft_path in iter_candidates(draft):
            if draft_path.is_file():
                return draft_path, repo_root / "docs" / "reviews" / f"{task_id}.md"
    default_draft = repo_root / ".harness" / "runtime" / "review-packs" / "drafts" / f"{task_id}-pr.md"
    if default_draft.is_file():
        return default_draft, repo_root / "docs" / "reviews" / f"{task_id}.md"
    default_promoted = repo_root / "docs" / "reviews" / f"{task_id}.md"
    if default_promoted.is_file():
        return default_promoted, None
    raise FileNotFoundError(f"Missing task-linked PR review narrative for {task_id}.")


def _finalize_queue(repo_root: Path, task_id: str) -> Path:
    task_path = find_task_path(repo_root, task_id)
    if task_path is None:
        raise FileNotFoundError(f"Missing queue item for {task_id}.")
    task = load_task(task_path)
    frontmatter = dict(task.frontmatter)
    frontmatter["worktree"] = None
    write_task(task_path, frontmatter, task.sections)
    return move_task(task_path, "done")


def _effective_cleanup(cleanup: str | None, record: dict[str, object]) -> str:
    if cleanup is not None:
        return cleanup
    cleanup_policy = str(record.get("cleanup_policy") or "preserve")
    if cleanup_policy == "delete":
        return "remove"
    return cleanup_policy


def finish_worktree(
    repo_root: Path,
    task_id: str,
    target_branch: str,
    strategy: str = "squash",
    push: bool = False,
    cleanup: str | None = None,
    promote_review_pack: Path | None = None,
    commit_title: str | None = None,
) -> FinishResult:
    task_id = validate_phase1_task_id(task_id)
    if strategy not in {"squash", "merge"}:
        raise ValueError(f"Unsupported finish-worktree strategy: {strategy}")
    if cleanup is not None and cleanup not in {"preserve", "remove"}:
        raise ValueError(f"Unsupported finish-worktree cleanup mode: {cleanup}")

    queue_path = find_task_path(repo_root, task_id)
    if queue_path is None:
        raise FileNotFoundError(f"Missing queue item for {task_id}.")
    task = load_task(queue_path)
    if task.state != "review":
        raise ValueError("finish-worktree requires the task to be in review.")

    registry_path, record = load_worktree_registry(repo_root, task_id)
    if record.get("status") not in {"preserved", "deleted"}:
        raise ValueError("finish-worktree requires preserved or deleted registry status.")
    if record.get("task_id") != task.frontmatter["id"]:
        raise ValueError("Queue item and registry task_id must match.")
    _resolve_registry_worktree_path(repo_root, task_id, str(record["path"]))

    source_branch = str(record["branch"])
    if not _branch_exists(repo_root, source_branch):
        raise ValueError(f"Missing source branch for task {task_id}: {source_branch}")
    if not _branch_exists(repo_root, target_branch):
        raise ValueError(f"Missing target branch: {target_branch}")
    existing_target = record.get("target_branch")
    if existing_target not in (None, "", target_branch):
        raise ValueError("finish-worktree target branch must match registry.target_branch.")

    try:
        validate_review_results(repo_root, task_id, list(task.frontmatter["review_stages"]))
    except FileNotFoundError as exc:
        raise ValueError(f"Missing required review result receipt: {exc.filename}") from exc
    _ensure_docs_updated(
        repo_root,
        target_branch,
        source_branch,
        list(task.frontmatter["docs_to_update"]),
    )

    review_source, default_promote_path = _resolve_review_pack_paths(repo_root, task_id, record)
    promote_target = promote_review_pack or default_promote_path

    _run_git(repo_root, ["checkout", target_branch])
    _require_clean_worktree(repo_root)

    if strategy == "squash":
        _run_git(repo_root, ["merge", "--squash", "--no-commit", source_branch])
    else:
        _run_git(repo_root, ["merge", "--no-ff", "--no-commit", source_branch])

    promoted_path: Path | None = None
    if promote_target is not None:
        promoted_path = promote_review_pack_doc(
            repo_root=repo_root,
            draft_path=review_source.relative_to(repo_root),
            promote_to=promote_target,
            task_id=task_id,
        )
        _run_git(repo_root, ["add", str(promoted_path.relative_to(repo_root))])
    elif review_source.is_relative_to(repo_root):
        review_source_rel = review_source.relative_to(repo_root)
        if not str(review_source_rel).startswith(".worktrees/"):
            _run_git(repo_root, ["add", str(review_source_rel)])

    title = commit_title or str(task.frontmatter["title"])
    _run_git(repo_root, ["commit", "-m", title])
    merged_commit = _run_git(repo_root, ["rev-parse", "HEAD"])

    done_task = _finalize_queue(repo_root, task_id)
    push_remote = str(record.get("push_remote") or "origin")
    push_status = "not_requested"
    final_status = "finalized_removed" if record.get("status") == "deleted" else "finalized_preserved"
    effective_cleanup = _effective_cleanup(cleanup, record)
    if effective_cleanup == "remove":
        final_status = "finalized_removed"
        _remove_worktree(repo_root, Path(str(record["path"])))

    record.update(
        {
            "target_branch": target_branch,
            "merge_strategy": strategy,
            "merge_status": "merged_local",
            "merged_commit": merged_commit,
            "push_status": push_status,
            "push_remote": push_remote,
            "status": final_status,
            "finished_at": datetime.now(UTC).isoformat(),
            "finalization_notes": "finish-worktree completed locally",
        }
    )
    if promoted_path is not None:
        record["promoted_review_pack"] = str(promoted_path.relative_to(repo_root))

    try:
        if push:
            _run_git(repo_root, ["push", push_remote, target_branch])
            record["push_status"] = "pushed"
        registry_path = write_worktree_registry(repo_root, task_id, record)
    except RuntimeError as exc:
        record["push_status"] = "failed"
        record["finalization_notes"] = "local merge succeeded but target push failed"
        registry_path = write_worktree_registry(repo_root, task_id, record)
        raise RuntimeError(str(exc)) from exc

    return FinishResult(
        queue_path=done_task,
        registry_path=registry_path,
        merged_commit=merged_commit,
        target_branch=target_branch,
        promoted_review_pack=promoted_path,
        push_status=str(record["push_status"]),
    )
