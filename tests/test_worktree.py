import tempfile
from pathlib import Path
import subprocess
import unittest

from harness_kit.queue import claim_task, move_task
from harness_kit.worktree import (
    choose_worktree_path,
    close_worktree,
    open_worktree,
    record_review_pack_path,
)


TASK_TEXT = """---
id: task-1
title: Queue contract test
status: ready
priority: high
owner_role: implementer
model_hint: gpt-5.4
worktree: null
parent_spec: docs/specs/spec.md
parent_plan: docs/plans/plan.md
why_this_task_exists: Preserve queue determinism
owned_paths:
  - src/payments
required_reads:
  - AGENTS.md
disallowed_edits:
  - infra/
docs_to_update:
  - src/payments/DIRECTORY.md
constraints:
  - stay within payments scope
verification_commands:
  - python3 -m unittest tests.test_worktree -v
expected_report_schema:
  - Status
  - Files changed
review_stages:
  - spec_scope_review
dependencies: []
---
## task_text
Implement the queue contract.

## acceptance_criteria
- context pack written

## non_goals
- no phase 2 adapter work
"""


class WorktreePathTest(unittest.TestCase):
    def _write_registry_record(
        self,
        repo: Path,
        task_id: str,
        path: Path,
        status: str = "attached",
        cleanup_policy: str = "preserve",
    ) -> Path:
        record = repo / ".harness" / "runtime" / "worktree-registry" / f"{task_id}.md"
        record.parent.mkdir(parents=True, exist_ok=True)
        record.write_text(
            (
                "---\n"
                f"task_id: {task_id}\n"
                f"worktree_name: {task_id}\n"
                f"path: {path}\n"
                f"branch: {task_id}\n"
                f"status: {status}\n"
                "baseline_verified: true\n"
                f"cleanup_policy: {cleanup_policy}\n"
                "---\n"
            ),
            encoding="utf-8",
        )
        return record

    def _init_git_repo(self, repo: Path) -> None:
        subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, text=True)
        subprocess.run(
            ["git", "config", "user.name", "Harness Tests"],
            cwd=repo,
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "harness-tests@example.com"],
            cwd=repo,
            check=True,
            capture_output=True,
            text=True,
        )
        (repo / "README.md").write_text("test repo\n", encoding="utf-8")
        subprocess.run(["git", "add", "README.md"], cwd=repo, check=True, capture_output=True, text=True)
        subprocess.run(
            ["git", "commit", "-m", "init"],
            cwd=repo,
            check=True,
            capture_output=True,
            text=True,
        )

    def test_choose_worktree_path_uses_project_local_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)

            path = choose_worktree_path(repo, "task-1")

            self.assertEqual(path, repo / ".worktrees" / "task-1")

    def test_open_worktree_creates_runtime_directories_and_registry_record(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)

            record = open_worktree(
                repo_root=repo,
                task_id="task-1",
                branch_name="task-1",
                cleanup_policy="preserve",
            )

            self.assertTrue((repo / ".harness" / "runtime" / "worktree-registry").is_dir())
            self.assertTrue((repo / ".worktrees").is_dir())
            self.assertTrue((repo / ".worktrees" / "task-1").is_dir())
            text = record.read_text(encoding="utf-8")
            self.assertIn("status: attached", text)
            self.assertIn("baseline_verified: true", text)
            self.assertIn("cleanup_policy: preserve", text)

    def test_open_worktree_accepts_effective_gitignore_rules(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_git_repo(repo)
            (repo / ".gitignore").write_text("/.worktrees/\n", encoding="utf-8")
            subprocess.run(
                ["git", "add", ".gitignore"],
                cwd=repo,
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                ["git", "commit", "-m", "ignore worktrees"],
                cwd=repo,
                check=True,
                capture_output=True,
                text=True,
            )

            record = open_worktree(
                repo_root=repo,
                task_id="task-1",
                branch_name="task-1",
                cleanup_policy="preserve",
            )

            self.assertTrue(record.is_file())
            self.assertTrue((repo / ".worktrees" / "task-1").is_dir())

    def test_open_worktree_links_runtime_back_to_control_root_for_git_worktrees(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_git_repo(repo)
            (repo / ".gitignore").write_text("/.worktrees/\n", encoding="utf-8")
            subprocess.run(
                ["git", "add", ".gitignore"],
                cwd=repo,
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                ["git", "commit", "-m", "ignore worktrees"],
                cwd=repo,
                check=True,
                capture_output=True,
                text=True,
            )

            open_worktree(
                repo_root=repo,
                task_id="task-1",
                branch_name="task-1",
                cleanup_policy="preserve",
            )

            runtime_link = repo / ".worktrees" / "task-1" / ".harness" / "runtime"
            self.assertTrue(runtime_link.is_symlink())
            self.assertEqual(
                runtime_link.resolve(),
                (repo / ".harness" / "runtime").resolve(),
            )

    def test_open_worktree_fails_when_gitignore_lacks_worktrees_rule(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_git_repo(repo)
            (repo / ".gitignore").write_text("*.log\n", encoding="utf-8")
            subprocess.run(
                ["git", "add", ".gitignore"],
                cwd=repo,
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                ["git", "commit", "-m", "ignore logs only"],
                cwd=repo,
                check=True,
                capture_output=True,
                text=True,
            )

            with self.assertRaises(ValueError):
                open_worktree(
                    repo_root=repo,
                    task_id="task-1",
                    branch_name="task-1",
                    cleanup_policy="preserve",
                )
            self.assertFalse((repo / ".worktrees").exists())
            self.assertFalse(
                (repo / ".harness" / "runtime" / "worktree-registry").exists()
            )

    def test_open_worktree_rejects_unsafe_task_identifier(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)

            with self.assertRaises(ValueError):
                open_worktree(
                    repo_root=repo,
                    task_id="../escaped",
                    branch_name="task-1",
                    cleanup_policy="preserve",
                )

            self.assertFalse((repo / ".worktrees").exists())
            self.assertFalse(
                (repo / ".harness" / "runtime" / "worktree-registry").exists()
            )

    def test_close_worktree_maps_done_statuses_to_review(self) -> None:
        for worker_status in ["DONE", "DONE_WITH_CONCERNS"]:
            with self.subTest(worker_status=worker_status):
                with tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    task = root / ".harness" / "runtime" / "queue" / "ready" / "task-1.md"
                    task.parent.mkdir(parents=True)
                    task.write_text(TASK_TEXT, encoding="utf-8")
                    claim_task(task_path=task, repo_root=root)
                    open_worktree(
                        repo_root=root,
                        task_id="task-1",
                        branch_name="task-1",
                        cleanup_policy="preserve",
                    )

                    closed_task, record = close_worktree(
                        repo_root=root,
                        task_id="task-1",
                        mode="preserve",
                        worker_status=worker_status,
                    )

                    self.assertIsNotNone(closed_task)
                    self.assertEqual(closed_task.parent.name, "review")
                    self.assertIn("status: preserved", record.read_text(encoding="utf-8"))
                    self.assertIn(
                        "worktree: null",
                        closed_task.read_text(encoding="utf-8"),
                    )

    def test_close_worktree_maps_needs_context_to_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task = root / ".harness" / "runtime" / "queue" / "ready" / "task-1.md"
            task.parent.mkdir(parents=True)
            task.write_text(TASK_TEXT, encoding="utf-8")
            claim_task(task_path=task, repo_root=root)
            open_worktree(
                repo_root=root,
                task_id="task-1",
                branch_name="task-1",
                cleanup_policy="preserve",
            )

            closed_task, _ = close_worktree(
                repo_root=root,
                task_id="task-1",
                mode="preserve",
                worker_status="NEEDS_CONTEXT",
            )

            self.assertIsNotNone(closed_task)
            self.assertEqual(closed_task.parent.name, "ready")

    def test_close_worktree_maps_blocked_to_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task = root / ".harness" / "runtime" / "queue" / "ready" / "task-1.md"
            task.parent.mkdir(parents=True)
            task.write_text(TASK_TEXT, encoding="utf-8")
            claim_task(task_path=task, repo_root=root)
            open_worktree(
                repo_root=root,
                task_id="task-1",
                branch_name="task-1",
                cleanup_policy="preserve",
            )

            closed_task, _ = close_worktree(
                repo_root=root,
                task_id="task-1",
                mode="preserve",
                worker_status="BLOCKED",
            )

            self.assertIsNotNone(closed_task)
            self.assertEqual(closed_task.parent.name, "blocked")

    def test_close_worktree_delete_marks_cleanup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            open_worktree(
                repo_root=root,
                task_id="task-1",
                branch_name="task-1",
                cleanup_policy="delete",
            )

            _, record = close_worktree(
                repo_root=root,
                task_id="task-1",
                mode="delete",
                worker_status="DONE_WITH_CONCERNS",
            )

            self.assertIn("status: deleted", record.read_text(encoding="utf-8"))

    def test_close_worktree_requires_existing_registry_record(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task = root / ".harness" / "runtime" / "queue" / "ready" / "task-1.md"
            task.parent.mkdir(parents=True)
            task.write_text(TASK_TEXT, encoding="utf-8")
            claimed_task, _ = claim_task(task_path=task, repo_root=root)

            with self.assertRaises(FileNotFoundError):
                close_worktree(
                    repo_root=root,
                    task_id="task-1",
                    mode="preserve",
                    worker_status="DONE",
                )

            self.assertTrue(claimed_task.is_file())
            self.assertEqual(claimed_task.parent.name, "in_progress")

    def test_close_worktree_rejects_registry_paths_outside_project_worktrees(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            victim = root.parent / f"{root.name}-external-worktree"
            victim.mkdir()
            record = self._write_registry_record(root, "task-1", victim, cleanup_policy="delete")
            before = record.read_text(encoding="utf-8")

            with self.assertRaises(ValueError):
                close_worktree(
                    repo_root=root,
                    task_id="task-1",
                    mode="delete",
                    worker_status="DONE",
                )

            self.assertTrue(victim.is_dir())
            self.assertEqual(record.read_text(encoding="utf-8"), before)

    def test_close_worktree_does_not_side_effect_on_invalid_transition(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task = root / ".harness" / "runtime" / "queue" / "ready" / "task-1.md"
            task.parent.mkdir(parents=True)
            task.write_text(TASK_TEXT, encoding="utf-8")
            claimed_task, _ = claim_task(task_path=task, repo_root=root)
            record = open_worktree(
                repo_root=root,
                task_id="task-1",
                branch_name="task-1",
                cleanup_policy="preserve",
            )
            review_task = move_task(claimed_task, "review")
            before = record.read_text(encoding="utf-8")

            with self.assertRaises(ValueError):
                close_worktree(
                    repo_root=root,
                    task_id="task-1",
                    mode="delete",
                    worker_status="DONE",
                )

            self.assertTrue((root / ".worktrees" / "task-1").is_dir())
            self.assertTrue(review_task.is_file())
            self.assertEqual(review_task.parent.name, "review")
            self.assertEqual(record.read_text(encoding="utf-8"), before)

    def test_record_review_pack_path_preserves_existing_finish_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            record = self._write_registry_record(root, "task-1", root / ".worktrees" / "task-1")
            record.write_text(
                record.read_text(encoding="utf-8").replace(
                    "---\n",
                    "---\n"
                    "target_branch: main\n"
                    "merge_strategy: squash\n"
                    "merge_status: merged_local\n",
                    1,
                ),
                encoding="utf-8",
            )

            record_review_pack_path(
                root,
                "task-1",
                draft_path=Path(".harness/runtime/review-packs/drafts/task-1-pr.md"),
            )

            text = record.read_text(encoding="utf-8")
            self.assertIn("target_branch: main", text)
            self.assertIn("merge_strategy: squash", text)
            self.assertIn("merge_status: merged_local", text)
            self.assertIn(
                "draft_pr_review_pack: .harness/runtime/review-packs/drafts/task-1-pr.md",
                text,
            )
