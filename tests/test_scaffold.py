import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


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
  - AGENTS.md
required_reads:
  - AGENTS.md
disallowed_edits:
  - infra/
docs_to_update:
  - docs/reviews/queue-test.md
constraints:
  - stay within phase 1 scope
verification_commands:
  - python3 -m unittest tests.test_scaffold -v
expected_report_schema:
  - Status
  - Files changed
review_stages:
  - spec_scope_review
dependencies: []
---
## task_text
Exercise the generated scaffold end-to-end.

## acceptance_criteria
- context pack regenerated
- worktree registry regenerated
- review pack promoted

## non_goals
- no phase 2 adapter work
"""


class CliSmokeTest(unittest.TestCase):
    def test_help_lists_phase1_commands(self) -> None:
        proc = subprocess.run(
            [sys.executable, "-m", "harness_kit.cli", "--help"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0)
        for token in [
            "init",
            "claim-task",
            "open-worktree",
            "close-worktree",
            "finish-worktree",
            "publish-pr",
            "refresh-memory",
            "write-review-result",
            "build-review-pack",
        ]:
            self.assertIn(token, proc.stdout)


class TemplatePresenceTest(unittest.TestCase):
    def test_phase1_templates_exist(self) -> None:
        required = [
            "templates/project/AGENTS.md",
            "templates/project/README.md",
            "templates/project/SUMMARY.md",
            "templates/project/REQUIREMENT.md",
            "templates/project/DIRECTORY.md",
            "templates/project/.gitignore",
            "templates/project/.harness/policies/model-routing.yaml",
            "templates/project/.harness/policies/review-stages.yaml",
            "templates/project/.harness/policies/qa-rules.md",
            "templates/project/.harness/policies/doc-update-policy.md",
            "templates/project/.harness/templates/task.md",
            "templates/project/.harness/templates/directory.md",
            "templates/project/.harness/templates/context-pack.md",
            "templates/project/.harness/templates/evidence-pack.md",
            "templates/project/.harness/templates/commit-pack.md",
            "templates/project/.harness/templates/pr-pack.md",
            "templates/project/scripts/harness/run-qa.sh",
            "templates/project/scripts/harness/write-review-result.sh",
            "templates/project/scripts/harness/finish-worktree.sh",
            "templates/project/scripts/harness/publish-pr.sh",
            "skills/orchestrate-queue/SKILL.md",
            "skills/refresh-memory/SKILL.md",
            "skills/prepare-review-pack/SKILL.md",
        ]
        for rel in required:
            self.assertTrue(Path(rel).is_file(), rel)

        agents_text = Path("templates/project/AGENTS.md").read_text(encoding="utf-8")
        for token in [
            "## Instruction Priority",
            "## Required Reads",
            "## Default Workflow",
            "## Model Routing Default",
            "## Documentation Gate",
            "## QA Gate",
            "## Worktree Rule",
            "## Output Convention",
        ]:
            self.assertIn(token, agents_text)
        for field in [
            "Status",
            "What you implemented",
            "What you tested and results",
            "Files changed",
            "Commit SHA",
            "Self-review findings",
            "Any issues or concerns",
        ]:
            self.assertIn(f"- {field}", agents_text)

        gitignore_text = Path("templates/project/.gitignore").read_text(
            encoding="utf-8"
        )
        for token in [".harness/runtime/", ".worktrees/", ".superpowers/"]:
            self.assertIn(token, gitignore_text)

        model_routing_text = Path(
            "templates/project/.harness/policies/model-routing.yaml"
        ).read_text(encoding="utf-8")
        for token in [
            "default: gpt-5.4",
            "planner: gpt-5.4",
            "implementer: gpt-5.4",
            "spec_reviewer: gpt-5.4",
            "quality_reviewer: gpt-5.4",
            "adversarial_regression_reviewer: gpt-5.4",
            "model: gpt-5.1-codex-mini",
        ]:
            self.assertIn(token, model_routing_text)

        review_stage_text = Path(
            "templates/project/.harness/policies/review-stages.yaml"
        ).read_text(encoding="utf-8")
        for token in [
            "APPROVED",
            "CHANGES_REQUIRED",
            "ESCALATE",
            "stage",
            "verdict",
            "blocking_issues",
            "advisory_notes",
            "evidence_refs",
            "next_action",
        ]:
            self.assertIn(token, review_stage_text)

        qa_rules_text = Path(
            "templates/project/.harness/policies/qa-rules.md"
        ).read_text(encoding="utf-8")
        for token in [
            "# Phase 1 QA Rules",
            "## Hook Points",
            "## Command Placeholders",
            "## Required Evidence",
            "rules/lint",
            "adversarial regression",
            "scripts/harness/run-qa.sh --stage rules-lint",
            "scripts/harness/run-qa.sh --stage adversarial-regression",
        ]:
            self.assertIn(token, qa_rules_text)

        doc_update_policy_text = Path(
            "templates/project/.harness/policies/doc-update-policy.md"
        ).read_text(encoding="utf-8")
        for token in [
            "# Documentation Update Policy",
            "## Required Checks",
            "README.md",
            "SUMMARY.md",
            "REQUIREMENT.md",
            "DIRECTORY.md",
            "docs/specs/",
            "docs/plans/",
            "docs/reviews/",
            ".harness/policies/*",
            ".harness/templates/*",
            "skills/*",
            "scripts/harness/*",
            "If no durable docs changed, say why in the task report.",
        ]:
            self.assertIn(token, doc_update_policy_text)

        context_pack_text = Path(
            "templates/project/.harness/templates/context-pack.md"
        ).read_text(encoding="utf-8")
        for token in [
            "why_this_task_exists",
            "owned_paths",
            "required_reads",
            "disallowed_edits",
            "constraints",
            "verification_commands",
            "expected_report_schema",
        ]:
            self.assertIn(token, context_pack_text)

        task_text = Path(
            "templates/project/.harness/templates/task.md"
        ).read_text(encoding="utf-8")
        for token in [
            "id:",
            "title:",
            "status:",
            "priority:",
            "owner_role:",
            "model_hint:",
            "worktree:",
            "parent_spec:",
            "parent_plan:",
            "why_this_task_exists",
            "owned_paths:",
            "required_reads:",
            "disallowed_edits:",
            "docs_to_update:",
            "constraints:",
            "verification_commands:",
            "expected_report_schema:",
            "review_stages:",
            "dependencies:",
            "The directory name is authoritative for queue state.",
            "Frontmatter `status` must mirror",
            "## task_text",
            "## acceptance_criteria",
            "## non_goals",
        ]:
            self.assertIn(token, task_text)

        pr_pack_text = Path(
            "templates/project/.harness/templates/pr-pack.md"
        ).read_text(encoding="utf-8")
        for token in [
            "## What Changed",
            "## Why It Changed",
            "## Intended Scope",
            "## Major Risks",
            "## Verification Evidence",
            "## Documentation Updates",
            "## Deferred Questions",
        ]:
            self.assertIn(token, pr_pack_text)

        evidence_pack_text = Path(
            "templates/project/.harness/templates/evidence-pack.md"
        ).read_text(encoding="utf-8")
        for token in [
            "## Claim Being Justified",
            "## Commands Run",
            "## Exit Codes",
            "## Key Output",
            "## Files Verified",
            "## Regression Checks",
            "## Related Artifacts",
            "## Reviewer Notes",
        ]:
            self.assertIn(token, evidence_pack_text)

        commit_pack_text = Path(
            "templates/project/.harness/templates/commit-pack.md"
        ).read_text(encoding="utf-8")
        for token in [
            "## What Changed",
            "## Why It Changed",
            "## Intended Scope",
            "## Major Risks",
            "## Verification Evidence",
            "## Documentation Updates",
            "## Deferred Questions",
        ]:
            self.assertIn(token, commit_pack_text)

        orchestrate_queue_text = Path("skills/orchestrate-queue/SKILL.md").read_text(
            encoding="utf-8"
        )
        for token in [
            "name: orchestrate-queue",
            ".harness/runtime/queue/",
            "worktree: null",
            ".harness/policies/review-stages.yaml",
            ".harness/templates/task.md",
            "status` must mirror",
        ]:
            self.assertIn(token, orchestrate_queue_text)

        refresh_memory_text = Path("skills/refresh-memory/SKILL.md").read_text(
            encoding="utf-8"
        )
        for token in [
            "name: refresh-memory",
            "`SUMMARY.md`",
            "`DIRECTORY.md`",
            "`.harness/templates/directory.md`",
            "`README.md`",
            "`REQUIREMENT.md`",
        ]:
            self.assertIn(token, refresh_memory_text)

        prepare_review_pack_text = Path(
            "skills/prepare-review-pack/SKILL.md"
        ).read_text(encoding="utf-8")
        for token in [
            "name: prepare-review-pack",
            ".harness/templates/evidence-pack.md",
            ".harness/templates/commit-pack.md",
            ".harness/templates/pr-pack.md",
            "docs/reviews/",
        ]:
            self.assertIn(token, prepare_review_pack_text)


class InitScaffoldTest(unittest.TestCase):
    def test_init_creates_codex_first_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "sample-repo"
            proc = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "harness_kit.cli",
                    "init",
                    "--target",
                    str(target),
                    "--project-name",
                    "sample-repo",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertTrue((target / "AGENTS.md").is_file())
            self.assertTrue(
                (target / "skills" / "orchestrate-queue" / "SKILL.md").is_file()
            )
            self.assertTrue((target / "docs" / "specs").is_dir())
            self.assertTrue((target / "docs" / "plans").is_dir())
            self.assertTrue((target / "docs" / "reviews").is_dir())
            self.assertTrue(
                (target / ".harness" / "policies" / "model-routing.yaml").is_file()
            )
            self.assertTrue(
                (target / ".harness" / "runtime" / "queue" / "ready").is_dir()
            )
            self.assertTrue(
                (target / ".harness" / "runtime" / "context-packs").is_dir()
            )
            self.assertTrue(
                (target / ".harness" / "runtime" / "evidence" / "raw").is_dir()
            )
            self.assertTrue(
                (
                    target
                    / ".harness"
                    / "runtime"
                    / "review-results"
                ).is_dir()
            )
            self.assertTrue(
                (
                    target
                    / ".harness"
                    / "runtime"
                    / "review-packs"
                    / "drafts"
                ).is_dir()
            )
            self.assertTrue(
                (target / ".harness" / "runtime" / "agent-runs").is_dir()
            )
            self.assertTrue(
                (target / ".harness" / "runtime" / "worktree-registry").is_dir()
            )
            self.assertTrue((target / ".worktrees").is_dir())
            provenance = target / "third_party" / "harness-source.txt"
            self.assertTrue(provenance.is_file())
            self.assertIn("source_commit:", provenance.read_text(encoding="utf-8"))
            self.assertTrue(
                (target / ".harness" / "templates" / "directory.md").is_file()
            )
            run_qa_path = target / "scripts" / "harness" / "run-qa.sh"
            self.assertTrue(run_qa_path.is_file())
            self.assertTrue(os.access(run_qa_path, os.X_OK))
            write_review_result_path = (
                target / "scripts" / "harness" / "write-review-result.sh"
            )
            self.assertTrue(write_review_result_path.is_file())
            self.assertTrue(os.access(write_review_result_path, os.X_OK))
            finish_worktree_path = (
                target / "scripts" / "harness" / "finish-worktree.sh"
            )
            self.assertTrue(finish_worktree_path.is_file())
            self.assertTrue(os.access(finish_worktree_path, os.X_OK))
            publish_pr_path = (
                target / "scripts" / "harness" / "publish-pr.sh"
            )
            self.assertTrue(publish_pr_path.is_file())
            self.assertTrue(os.access(publish_pr_path, os.X_OK))
            self.assertTrue(
                (
                    target
                    / "scripts"
                    / "harness"
                    / "runtime"
                    / "harness_kit"
                    / "cli.py"
                ).is_file()
            )
            self.assertTrue(
                (
                    target
                    / "scripts"
                    / "harness"
                    / "runtime"
                    / "harness_kit"
                    / "finish_worktree.py"
                ).is_file()
            )
            self.assertTrue(
                (
                    target
                    / "scripts"
                    / "harness"
                    / "runtime"
                    / "harness_kit"
                    / "publish_pr.py"
                ).is_file()
            )
            self.assertTrue(
                (
                    target
                    / "scripts"
                    / "harness"
                    / "runtime"
                    / "harness_kit"
                    / "review_results.py"
                ).is_file()
            )

            runtime_env = dict(os.environ)
            runtime_env["PYTHONPATH"] = str(
                target / "scripts" / "harness" / "runtime"
            )
            runtime_help = subprocess.run(
                [sys.executable, "-m", "harness_kit.cli", "--help"],
                cwd=target,
                env=runtime_env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(runtime_help.returncode, 0, runtime_help.stderr)
            self.assertNotIn("init", runtime_help.stdout)
            for token in [
                "claim-task",
                "open-worktree",
                "close-worktree",
                "finish-worktree",
                "publish-pr",
                "refresh-memory",
                "write-review-result",
                "build-review-pack",
            ]:
                self.assertIn(token, runtime_help.stdout)

    def test_generated_repo_runtime_scripts_survive_clone_like_cleanup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "demo"
            init_proc = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "harness_kit.cli",
                    "init",
                    "--target",
                    str(target),
                    "--project-name",
                    "demo",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(init_proc.returncode, 0, init_proc.stderr)

            required_paths = [
                target / "AGENTS.md",
                target / "skills" / "orchestrate-queue" / "SKILL.md",
                target / ".harness" / "policies" / "model-routing.yaml",
                target / ".harness" / "templates" / "directory.md",
                target / ".harness" / "templates" / "evidence-pack.md",
                target / "third_party" / "harness-source.txt",
                target / "scripts" / "harness" / "open-worktree.sh",
                target / "scripts" / "harness" / "finish-worktree.sh",
                target / "scripts" / "harness" / "publish-pr.sh",
                target / "scripts" / "harness" / "run-qa.sh",
                target / "scripts" / "harness" / "write-review-result.sh",
                target / "scripts" / "harness" / "runtime" / "harness_kit" / "cli.py",
                target
                / "scripts"
                / "harness"
                / "runtime"
                / "harness_kit"
                / "finish_worktree.py",
                target
                / "scripts"
                / "harness"
                / "runtime"
                / "harness_kit"
                / "publish_pr.py",
                target
                / "scripts"
                / "harness"
                / "runtime"
                / "harness_kit"
                / "review_results.py",
                target / "docs" / "specs",
                target / "docs" / "plans",
                target / "docs" / "reviews",
            ]
            for path in required_paths:
                if path.suffix:
                    self.assertTrue(path.is_file(), path)
                else:
                    self.assertTrue(path.is_dir(), path)

            task_path = target / ".harness" / "runtime" / "queue" / "ready" / "task-1.md"
            task_path.parent.mkdir(parents=True, exist_ok=True)
            task_path.write_text(TASK_TEXT, encoding="utf-8")

            for rel_path in [
                ".harness/runtime/context-packs",
                ".harness/runtime/review-results",
                ".harness/runtime/review-packs/drafts",
                ".harness/runtime/worktree-registry",
                ".worktrees",
            ]:
                shutil.rmtree(target / rel_path)

            claim_proc = subprocess.run(
                [
                    "scripts/harness/claim-task.sh",
                    "--repo-root",
                    ".",
                    "--task",
                    ".harness/runtime/queue/ready/task-1.md",
                ],
                cwd=target,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(claim_proc.returncode, 0, claim_proc.stderr)
            context_packs_dir = target / ".harness" / "runtime" / "context-packs"
            context_pack = context_packs_dir / "task-1.md"
            self.assertTrue(context_packs_dir.is_dir())
            self.assertTrue(context_pack.is_file())

            open_proc = subprocess.run(
                [
                    "scripts/harness/open-worktree.sh",
                    "--repo-root",
                    ".",
                    "--task-id",
                    "task-1",
                    "--branch",
                    "task-1",
                    "--cleanup-policy",
                    "preserve",
                ],
                cwd=target,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(open_proc.returncode, 0, open_proc.stderr)
            registry_record = (
                target / ".harness" / "runtime" / "worktree-registry" / "task-1.md"
            )
            self.assertTrue(registry_record.is_file())

            close_proc = subprocess.run(
                [
                    "scripts/harness/close-worktree.sh",
                    "--repo-root",
                    ".",
                    "--task-id",
                    "task-1",
                    "--mode",
                    "preserve",
                    "--worker-status",
                    "DONE",
                ],
                cwd=target,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(close_proc.returncode, 0, close_proc.stderr)
            self.assertFalse(
                (target / ".harness" / "runtime" / "queue" / "in_progress" / "task-1.md").exists()
            )
            self.assertTrue(
                (target / ".harness" / "runtime" / "queue" / "review" / "task-1.md").is_file()
            )

            review_pack_proc = subprocess.run(
                [
                    "scripts/harness/build-review-pack.sh",
                    "--repo-root",
                    ".",
                    "--type",
                    "pr",
                    "--task-id",
                    "task-1",
                    "--title",
                    "Queue test",
                    "--changed-path",
                    "AGENTS.md",
                    "--verification-command",
                    "true",
                    "--promote-to",
                    "docs/reviews/queue-test.md",
                ],
                cwd=target,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(review_pack_proc.returncode, 0, review_pack_proc.stderr)
            self.assertTrue(
                (
                    target
                    / ".harness"
                    / "runtime"
                    / "review-packs"
                    / "drafts"
                    / "task-1-pr.md"
                ).is_file()
            )
            self.assertTrue((target / "docs" / "reviews" / "queue-test.md").is_file())
            self.assertIn(
                "draft_pr_review_pack: .harness/runtime/review-packs/drafts/task-1-pr.md",
                registry_record.read_text(encoding="utf-8"),
            )
            self.assertIn(
                "promoted_review_pack: docs/reviews/queue-test.md",
                registry_record.read_text(encoding="utf-8"),
            )

            review_result_proc = subprocess.run(
                [
                    "scripts/harness/write-review-result.sh",
                    "--repo-root",
                    ".",
                    "--task-id",
                    "task-1",
                    "--stage",
                    "spec_scope_review",
                    "--verdict",
                    "APPROVED",
                    "--next-action",
                    "finish",
                    "--evidence-ref",
                    "docs/reviews/queue-test.md",
                ],
                cwd=target,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(review_result_proc.returncode, 0, review_result_proc.stderr)
            self.assertTrue(
                (
                    target
                    / ".harness"
                    / "runtime"
                    / "review-results"
                    / "task-1"
                    / "spec_scope_review.md"
                ).is_file()
            )

    def test_init_refuses_non_empty_target_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "existing-repo"
            target.mkdir()
            readme = target / "README.md"
            readme.write_text("preexisting\n", encoding="utf-8")

            proc = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "harness_kit.cli",
                    "init",
                    "--target",
                    str(target),
                    "--project-name",
                    "existing-repo",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertNotEqual(proc.returncode, 0)
            self.assertEqual(readme.read_text(encoding="utf-8"), "preexisting\n")
            self.assertFalse((target / "AGENTS.md").exists())
