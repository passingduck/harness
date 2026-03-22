from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import shutil
import subprocess

from harness_kit.queue import find_task_path, load_task, validate_phase1_task_id
from harness_kit.worktree import load_worktree_registry, write_worktree_registry


@dataclass
class PublishResult:
    registry_path: Path
    target_branch: str
    publish_head_ref: str
    pr_number: str
    pr_url: str


def _run_command(args: list[str]) -> str:
    proc = subprocess.run(
        args,
        capture_output=True,
        text=True,
        check=False,
        env=os.environ.copy(),
    )
    if proc.returncode != 0:
        message = proc.stderr.strip() or proc.stdout.strip() or "command failed"
        raise RuntimeError(message)
    return proc.stdout.strip()


def _run_git(repo_root: Path, args: list[str]) -> str:
    return _run_command(["git", "-C", str(repo_root), *args])


def _branch_exists(repo_root: Path, branch_name: str) -> bool:
    proc = subprocess.run(
        ["git", "-C", str(repo_root), "show-ref", "--verify", "--quiet", f"refs/heads/{branch_name}"],
        capture_output=True,
        text=True,
        check=False,
        env=os.environ.copy(),
    )
    return proc.returncode == 0


def _resolve_review_pack_body(
    repo_root: Path,
    task_id: str,
    record: dict[str, object],
    body_from_review_pack: Path | None,
) -> tuple[Path, str]:
    allowed_draft_root = (repo_root / ".harness" / "runtime" / "review-packs" / "drafts").resolve()
    allowed_docs_root = (repo_root / "docs" / "reviews").resolve()

    candidates: list[Path] = []
    if body_from_review_pack is not None:
        candidate = body_from_review_pack
        if not candidate.is_absolute():
            candidate = repo_root / candidate
        candidates.append(candidate.resolve(strict=False))
    else:
        promoted = record.get("promoted_review_pack")
        draft = record.get("draft_pr_review_pack")
        if isinstance(promoted, str) and promoted:
            candidates.append((repo_root / promoted).resolve(strict=False))
        if isinstance(draft, str) and draft:
            candidates.append((repo_root / draft).resolve(strict=False))
        candidates.append((repo_root / ".harness" / "runtime" / "review-packs" / "drafts" / f"{task_id}-pr.md").resolve(strict=False))
        candidates.append((repo_root / "docs" / "reviews" / f"{task_id}.md").resolve(strict=False))

    for candidate in candidates:
        if not candidate.is_file():
            continue
        if candidate.is_relative_to(allowed_docs_root):
            return candidate, "promoted_review_pack"
        if candidate.is_relative_to(allowed_draft_root):
            return candidate, "draft_pr_review_pack"
        raise ValueError("publish-pr review-pack bodies must stay under docs/reviews or runtime drafts.")
    raise FileNotFoundError(f"Missing task-linked review-pack body for {task_id}.")


def _gh_json(args: list[str], *, allow_missing: bool = False) -> dict[str, str] | None:
    proc = subprocess.run(
        ["gh", *args],
        capture_output=True,
        text=True,
        check=False,
        env=os.environ.copy(),
    )
    if proc.returncode != 0:
        if allow_missing:
            return None
        message = proc.stderr.strip() or proc.stdout.strip() or "gh command failed"
        raise RuntimeError(message)
    return json.loads(proc.stdout or "{}")


def publish_pr(
    repo_root: Path,
    task_id: str,
    target_branch: str,
    title: str | None = None,
    body_from_review_pack: Path | None = None,
    draft: bool = False,
    update_if_exists: bool = False,
) -> PublishResult:
    task_id = validate_phase1_task_id(task_id)
    if shutil.which("gh") is None:
        raise RuntimeError("publish-pr requires the gh CLI.")
    _run_command(["gh", "auth", "status"])

    queue_path = find_task_path(repo_root, task_id)
    if queue_path is None:
        raise FileNotFoundError(f"Missing queue item for {task_id}.")
    task = load_task(queue_path)
    if task.state != "review":
        raise ValueError("publish-pr requires the task to be in review.")

    registry_path, record = load_worktree_registry(repo_root, task_id)
    if str(record.get("status", "")).startswith("finalized_"):
        raise ValueError("publish-pr cannot run after registry finalization.")
    source_branch = str(record["branch"])
    if not _branch_exists(repo_root, source_branch):
        raise ValueError(f"Missing source branch for task {task_id}: {source_branch}")
    if not _branch_exists(repo_root, target_branch):
        raise ValueError(f"Missing target branch: {target_branch}")

    existing_target = record.get("target_branch")
    if existing_target not in (None, "", target_branch):
        raise ValueError("publish-pr target branch must match registry.target_branch.")

    push_remote = str(record.get("push_remote") or "origin")
    publish_head_ref = f"{push_remote}/{source_branch}"
    body_path, registry_body_field = _resolve_review_pack_body(
        repo_root,
        task_id,
        record,
        body_from_review_pack,
    )
    record["target_branch"] = target_branch
    record["push_remote"] = push_remote
    record[registry_body_field] = str(body_path.relative_to(repo_root))

    try:
        _run_git(repo_root, ["push", push_remote, f"{source_branch}:{source_branch}"])
        record["publish_head_ref"] = publish_head_ref
        pr_title = title or str(task.frontmatter["title"])
        existing_pr = None
        if update_if_exists:
            existing_pr = _gh_json(
                ["pr", "view", "--head", source_branch, "--json", "number,url"],
                allow_missing=True,
            )
        if existing_pr is None:
            command = [
                "gh",
                "pr",
                "create",
                "--base",
                target_branch,
                "--head",
                source_branch,
                "--title",
                pr_title,
                "--body-file",
                str(body_path),
            ]
            if draft:
                command.append("--draft")
            _run_command(command)
            pr_metadata = _gh_json(["pr", "view", "--head", source_branch, "--json", "number,url"])
        else:
            _run_command(
                [
                    "gh",
                    "pr",
                    "edit",
                    str(existing_pr["number"]),
                    "--title",
                    pr_title,
                    "--body-file",
                    str(body_path),
                ]
            )
            pr_metadata = _gh_json(["pr", "view", "--head", source_branch, "--json", "number,url"])
        if pr_metadata is None:
            raise RuntimeError("Failed to resolve PR metadata after publish-pr.")
        record["pr_number"] = str(pr_metadata["number"])
        record["pr_url"] = str(pr_metadata["url"])
        record["adapter_status"] = "published"
        registry_path = write_worktree_registry(repo_root, task_id, record)
    except RuntimeError as exc:
        record["adapter_status"] = "failed"
        registry_path = write_worktree_registry(repo_root, task_id, record)
        raise RuntimeError(str(exc)) from exc

    return PublishResult(
        registry_path=registry_path,
        target_branch=target_branch,
        publish_head_ref=publish_head_ref,
        pr_number=str(record["pr_number"]),
        pr_url=str(record["pr_url"]),
    )
