import tempfile
from pathlib import Path
import unittest

from harness_kit.queue import claim_task
from harness_kit.worktree import choose_worktree_path, close_worktree, open_worktree


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
  - spec_scope
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

