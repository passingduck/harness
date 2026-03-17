import tempfile
from pathlib import Path
import unittest

from harness_kit.queue import claim_task, move_task


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
  - python3 -m unittest tests.test_queue -v
expected_report_schema:
  - Status
  - Files changed
review_stages:
  - spec_scope
  - rules_lint
dependencies: []
---
## task_text
Implement the queue contract.

## acceptance_criteria
- context pack written

## non_goals
- no phase 2 adapter work
"""


class QueueStateAuthorityTest(unittest.TestCase):
    def test_directory_state_is_authoritative(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task = root / ".harness" / "runtime" / "queue" / "ready" / "task-1.md"
            task.parent.mkdir(parents=True)
            task.write_text(TASK_TEXT.replace("status: ready", "status: backlog"), encoding="utf-8")

            moved = move_task(task, "in_progress")

            self.assertEqual(moved.parent.name, "in_progress")
            self.assertIn("status: in_progress", moved.read_text(encoding="utf-8"))

    def test_claim_task_creates_context_pack_from_queue_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task = root / ".harness" / "runtime" / "queue" / "ready" / "task-1.md"
            task.parent.mkdir(parents=True)
            task.write_text(TASK_TEXT, encoding="utf-8")

            claimed_task, context_pack = claim_task(task_path=task, repo_root=root)

            self.assertEqual(claimed_task.parent.name, "in_progress")
            claimed_text = claimed_task.read_text(encoding="utf-8")
            self.assertIn("status: in_progress", claimed_text)
            self.assertIn("worktree: task-1", claimed_text)
            self.assertEqual(
                context_pack,
                root / ".harness" / "runtime" / "context-packs" / "task-1.md",
            )
            self.assertTrue((root / ".harness" / "runtime" / "context-packs").is_dir())
            context_text = context_pack.read_text(encoding="utf-8")
            for token in [
                "## task_text",
                "## why_this_task_exists",
                "## owned_paths",
                "## required_reads",
                "## disallowed_edits",
                "## constraints",
                "## verification_commands",
                "## expected_report_schema",
                "Preserve queue determinism",
                "src/payments",
                "AGENTS.md",
            ]:
                self.assertIn(token, context_text)

