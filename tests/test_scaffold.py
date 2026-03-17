from pathlib import Path
import subprocess
import sys
import unittest


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
            "refresh-memory",
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
            "skills/orchestrate-queue/SKILL.md",
            "skills/refresh-memory/SKILL.md",
            "skills/prepare-review-pack/SKILL.md",
        ]
        for rel in required:
            self.assertTrue(Path(rel).is_file(), rel)

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
        self.assertIn(
            "The directory name is authoritative for queue state.",
            task_text,
        )
        self.assertIn("Frontmatter `status` must mirror", task_text)
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
            "## task_text",
            "acceptance_criteria",
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
