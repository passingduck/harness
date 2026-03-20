import os
import subprocess
import tempfile
from pathlib import Path
import unittest
from unittest import mock

from harness_kit.publish_pr import publish_pr
from harness_kit.queue import claim_task
from harness_kit.worktree import close_worktree, open_worktree


TASK_TEXT = """---
id: task-1
title: Publish PR test
status: ready
priority: high
owner_role: implementer
model_hint: gpt-5.4
worktree: null
parent_spec: docs/specs/spec.md
parent_plan: docs/plans/plan.md
why_this_task_exists: Exercise publish-pr.
owned_paths:
  - src/
required_reads:
  - AGENTS.md
disallowed_edits:
  - infra/
docs_to_update: []
constraints:
  - stay within phase 1 scope
verification_commands:
  - python3 -m unittest tests.test_publish_pr -v
expected_report_schema:
  - Status
  - Files changed
review_stages:
  - spec_scope_review
dependencies: []
---
## task_text
Publish or update a PR for a review-state task.

## acceptance_criteria
- registry records publish metadata

## non_goals
- finish-worktree coverage
"""


class PublishPrTest(unittest.TestCase):
    def _run_git(self, repo: Path, *args: str) -> str:
        proc = subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)
        return proc.stdout.strip()

    def _init_git_repo(self, repo: Path) -> None:
        self._run_git(repo, "init", "-b", "main")
        self._run_git(repo, "config", "user.name", "Harness Tests")
        self._run_git(repo, "config", "user.email", "harness-tests@example.com")
        (repo / ".gitignore").write_text("/.harness/runtime/\n/.worktrees/\n", encoding="utf-8")
        (repo / "AGENTS.md").write_text("test\n", encoding="utf-8")
        (repo / "README.md").write_text("baseline\n", encoding="utf-8")
        self._run_git(repo, "add", ".gitignore", "AGENTS.md", "README.md")
        self._run_git(repo, "commit", "-m", "초기 커밋")

    def _prepare_review_task(self, repo: Path) -> None:
        self._init_git_repo(repo)
        task = repo / ".harness" / "runtime" / "queue" / "ready" / "task-1.md"
        task.parent.mkdir(parents=True, exist_ok=True)
        task.write_text(TASK_TEXT, encoding="utf-8")
        claim_task(task_path=task, repo_root=repo)
        open_worktree(
            repo_root=repo,
            task_id="task-1",
            branch_name="task-1",
            cleanup_policy="preserve",
        )

        worktree = repo / ".worktrees" / "task-1"
        (worktree / "src").mkdir(parents=True, exist_ok=True)
        (worktree / "src" / "feature.txt").write_text("task work\n", encoding="utf-8")
        self._run_git(worktree, "add", "src/feature.txt")
        self._run_git(worktree, "commit", "-m", "태스크 구현")
        close_worktree(
            repo_root=repo,
            task_id="task-1",
            mode="preserve",
            worker_status="DONE",
        )

        draft = repo / ".harness" / "runtime" / "review-packs" / "drafts" / "task-1-pr.md"
        draft.parent.mkdir(parents=True, exist_ok=True)
        draft.write_text("# PR Review Pack\n\nTask 1 narrative.\n", encoding="utf-8")

    def _write_fake_gh(self, bin_dir: Path, state_file: Path, log_file: Path) -> None:
        gh = bin_dir / "gh"
        gh.write_text(
            """#!/usr/bin/env bash
set -euo pipefail
printf '%s\\n' "$*" >> "${GH_LOG_FILE}"
if [[ "${1:-}" == "auth" && "${2:-}" == "status" ]]; then
  exit 0
fi
if [[ "${1:-}" == "pr" && "${2:-}" == "view" ]]; then
  if [[ -f "${GH_STATE_FILE}" ]]; then
    cat "${GH_STATE_FILE}"
    exit 0
  fi
  exit 1
fi
if [[ "${1:-}" == "pr" && "${2:-}" == "create" ]]; then
  printf '{"number":"17","url":"https://example.com/pr/17"}\\n' > "${GH_STATE_FILE}"
  exit 0
fi
if [[ "${1:-}" == "pr" && "${2:-}" == "edit" ]]; then
  exit 0
fi
exit 2
""",
            encoding="utf-8",
        )
        gh.chmod(0o755)

    def test_publish_pr_fails_when_gh_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._prepare_review_task(repo)

            with mock.patch.dict(os.environ, {"PATH": ""}, clear=False):
                with self.assertRaises(RuntimeError):
                    publish_pr(repo_root=repo, task_id="task-1", target_branch="main")

    def test_publish_pr_persists_target_branch_and_head_ref(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            origin = Path(tmp) / "origin.git"
            bin_dir = Path(tmp) / "bin"
            state_file = Path(tmp) / "gh-state.json"
            log_file = Path(tmp) / "gh.log"
            repo.mkdir()
            origin.mkdir()
            bin_dir.mkdir()

            self._prepare_review_task(repo)
            self._run_git(origin, "init", "--bare")
            self._run_git(repo, "remote", "add", "origin", str(origin))
            self._write_fake_gh(bin_dir, state_file, log_file)

            env = dict(os.environ)
            env["PATH"] = f"{bin_dir}:{env['PATH']}"
            env["GH_STATE_FILE"] = str(state_file)
            env["GH_LOG_FILE"] = str(log_file)
            with mock.patch.dict(os.environ, env, clear=False):
                result = publish_pr(
                    repo_root=repo,
                    task_id="task-1",
                    target_branch="main",
                    update_if_exists=True,
                )

            self.assertEqual(result.target_branch, "main")
            self.assertEqual(result.publish_head_ref, "origin/task-1")
            registry_text = (
                repo / ".harness" / "runtime" / "worktree-registry" / "task-1.md"
            ).read_text(encoding="utf-8")
            self.assertIn("target_branch: main", registry_text)
            self.assertIn("push_remote: origin", registry_text)
            self.assertIn("publish_head_ref: origin/task-1", registry_text)
            self.assertIn("draft_pr_review_pack: .harness/runtime/review-packs/drafts/task-1-pr.md", registry_text)
            self.assertIn("pr_number: 17", registry_text)
            self.assertIn("pr_url: https://example.com/pr/17", registry_text)
            self.assertIn("adapter_status: published", registry_text)
            self.assertTrue((origin / "refs" / "heads" / "task-1").is_file())


if __name__ == "__main__":
    unittest.main()
