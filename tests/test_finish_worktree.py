import subprocess
import tempfile
from pathlib import Path
import unittest

from harness_kit.finish_worktree import finish_worktree
from harness_kit.queue import claim_task
from harness_kit.review_results import write_review_result
from harness_kit.worktree import close_worktree, open_worktree


TASK_TEXT = """---
id: task-1
title: Finish worktree test
status: ready
priority: high
owner_role: implementer
model_hint: gpt-5.4
worktree: null
parent_spec: docs/specs/spec.md
parent_plan: docs/plans/plan.md
why_this_task_exists: Exercise finish-worktree.
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
  - python3 -m unittest tests.test_finish_worktree -v
expected_report_schema:
  - Status
  - Files changed
review_stages:
  - spec_scope_review
dependencies: []
---
## task_text
Land a reviewed task into the target branch.

## acceptance_criteria
- queue moves to done
- merge metadata is persisted

## non_goals
- publish-pr coverage
"""


class FinishWorktreeTest(unittest.TestCase):
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

    def _write_ready_task(self, repo: Path) -> Path:
        task = repo / ".harness" / "runtime" / "queue" / "ready" / "task-1.md"
        task.parent.mkdir(parents=True, exist_ok=True)
        task.write_text(TASK_TEXT, encoding="utf-8")
        return task

    def _write_review_pack(self, repo: Path) -> Path:
        draft = repo / ".harness" / "runtime" / "review-packs" / "drafts" / "task-1-pr.md"
        draft.parent.mkdir(parents=True, exist_ok=True)
        draft.write_text("# PR Review Pack\n\nTask 1 narrative.\n", encoding="utf-8")
        return draft

    def _prepare_review_task(
        self,
        repo: Path,
        *,
        close_mode: str = "preserve",
        include_receipt: bool = True,
    ) -> None:
        self._init_git_repo(repo)
        task = self._write_ready_task(repo)
        claim_task(task_path=task, repo_root=repo)
        open_worktree(
            repo_root=repo,
            task_id="task-1",
            branch_name="task-1",
            cleanup_policy=close_mode,
        )

        worktree = repo / ".worktrees" / "task-1"
        (worktree / "src").mkdir(parents=True, exist_ok=True)
        (worktree / "src" / "feature.txt").write_text("task work\n", encoding="utf-8")
        self._run_git(worktree, "add", "src/feature.txt")
        self._run_git(worktree, "commit", "-m", "태스크 구현")

        close_worktree(
            repo_root=repo,
            task_id="task-1",
            mode=close_mode,
            worker_status="DONE",
        )
        self._write_review_pack(repo)
        if include_receipt:
            write_review_result(
                repo_root=repo,
                task_id="task-1",
                stage="spec_scope_review",
                verdict="APPROVED",
                blocking_issues=[],
                advisory_notes=["ready to finish"],
                evidence_refs=[".harness/runtime/review-packs/drafts/task-1-pr.md"],
                next_action="finish",
            )

    def test_finish_worktree_moves_review_task_to_done(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._prepare_review_task(repo, close_mode="preserve")

            result = finish_worktree(
                repo_root=repo,
                task_id="task-1",
                target_branch="main",
                strategy="squash",
                push=False,
                cleanup="preserve",
                commit_title="태스크 머지",
            )

            self.assertEqual(result.queue_path.parent.name, "done")
            self.assertEqual(
                self._run_git(repo, "branch", "--show-current"),
                "main",
            )
            self.assertEqual((repo / "src" / "feature.txt").read_text(encoding="utf-8"), "task work\n")
            registry_text = result.registry_path.read_text(encoding="utf-8")
            self.assertIn("status: finalized_preserved", registry_text)
            self.assertIn("target_branch: main", registry_text)
            self.assertIn("merge_strategy: squash", registry_text)
            self.assertIn("merge_status: merged_local", registry_text)
            self.assertIn("push_status: not_requested", registry_text)
            self.assertIn("promoted_review_pack: docs/reviews/task-1.md", registry_text)

    def test_finish_worktree_allows_deleted_registry_when_branch_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._prepare_review_task(repo, close_mode="delete")

            result = finish_worktree(
                repo_root=repo,
                task_id="task-1",
                target_branch="main",
                strategy="squash",
                push=False,
                commit_title="태스크 머지",
            )

            self.assertEqual(result.queue_path.parent.name, "done")
            self.assertFalse((repo / ".worktrees" / "task-1").exists())
            self.assertIn(
                "status: finalized_removed",
                result.registry_path.read_text(encoding="utf-8"),
            )

    def test_finish_worktree_fails_when_required_review_result_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._prepare_review_task(repo, close_mode="preserve", include_receipt=False)

            with self.assertRaises(ValueError):
                finish_worktree(
                    repo_root=repo,
                    task_id="task-1",
                    target_branch="main",
                )

            review_task = repo / ".harness" / "runtime" / "queue" / "review" / "task-1.md"
            self.assertTrue(review_task.is_file())
            registry_text = (
                repo / ".harness" / "runtime" / "worktree-registry" / "task-1.md"
            ).read_text(encoding="utf-8")
            self.assertNotIn("status: finalized_", registry_text)

    def test_finish_worktree_records_push_failure_without_reopening_queue(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._prepare_review_task(repo, close_mode="preserve")

            with self.assertRaises(RuntimeError):
                finish_worktree(
                    repo_root=repo,
                    task_id="task-1",
                    target_branch="main",
                    strategy="squash",
                    push=True,
                    cleanup="preserve",
                    commit_title="태스크 머지",
                )

            done_task = repo / ".harness" / "runtime" / "queue" / "done" / "task-1.md"
            self.assertTrue(done_task.is_file())
            registry_text = (
                repo / ".harness" / "runtime" / "worktree-registry" / "task-1.md"
            ).read_text(encoding="utf-8")
            self.assertIn("status: finalized_preserved", registry_text)
            self.assertIn("merge_status: merged_local", registry_text)
            self.assertIn("push_status: failed", registry_text)
            self.assertIn("merged_commit:", registry_text)


if __name__ == "__main__":
    unittest.main()
