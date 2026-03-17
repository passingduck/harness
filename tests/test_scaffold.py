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
            "Status",
            "What you implemented",
            "What you tested and results",
            "Files changed",
            "Commit SHA",
            "Self-review findings",
            "Any issues or concerns",
        ]:
            self.assertIn(token, agents_text)

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
            "## Hook Points",
            "`rules/lint`",
            "`adversarial regression`",
            "## Command Placeholders",
            "scripts/harness/run-qa.sh --stage rules-lint",
            "scripts/harness/run-qa.sh --stage adversarial-regression",
            "## Required Evidence",
            "`APPROVED`",
        ]:
            self.assertIn(token, qa_rules_text)

        doc_update_policy_text = Path(
            "templates/project/.harness/policies/doc-update-policy.md"
        ).read_text(encoding="utf-8")
        for token in [
            "`README.md`",
            "`SUMMARY.md`",
            "`REQUIREMENT.md`",
            "`DIRECTORY.md`",
            "`docs/specs/`",
            "`docs/plans/`",
            "`docs/reviews/`",
            "`.harness/policies/*`",
            "`.harness/templates/*`",
            "`skills/*`",
            "`scripts/harness/*`",
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
            "status` must mirror",
            "worktree: null",
            ".harness/policies/review-stages.yaml",
            ".harness/templates/task.md",
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
            "verification evidence",
            "`.harness/templates/evidence-pack.md`",
            "`.harness/templates/commit-pack.md`",
            "`.harness/templates/pr-pack.md`",
            "`docs/reviews/`",
        ]:
            self.assertIn(token, prepare_review_pack_text)
