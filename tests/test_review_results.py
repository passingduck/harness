import subprocess
import sys
import tempfile
from pathlib import Path
import unittest

from harness_kit.review_results import (
    load_review_result,
    validate_review_results,
    write_review_result,
)


class ReviewResultsTest(unittest.TestCase):
    def test_write_and_load_review_result_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)

            receipt = write_review_result(
                repo_root=repo,
                task_id="task-1",
                stage="spec_scope_review",
                verdict="APPROVED",
                blocking_issues=[],
                advisory_notes=["looks good"],
                evidence_refs=["docs/reviews/task-1-pr.md"],
                next_action="finish",
            )

            self.assertEqual(receipt.name, "spec_scope_review.md")
            self.assertEqual(
                receipt,
                repo
                / ".harness"
                / "runtime"
                / "review-results"
                / "task-1"
                / "spec_scope_review.md",
            )
            payload = load_review_result(
                repo_root=repo,
                task_id="task-1",
                stage="spec_scope_review",
            )
            self.assertEqual(payload["stage"], "spec_scope_review")
            self.assertEqual(payload["verdict"], "APPROVED")
            self.assertEqual(payload["advisory_notes"], ["looks good"])
            self.assertEqual(payload["evidence_refs"], ["docs/reviews/task-1-pr.md"])

    def test_validate_review_results_requires_all_stages_approved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            write_review_result(
                repo_root=repo,
                task_id="task-1",
                stage="spec_scope_review",
                verdict="CHANGES_REQUIRED",
                blocking_issues=["missing coverage"],
                advisory_notes=[],
                evidence_refs=["docs/reviews/task-1-pr.md"],
                next_action="revise",
            )

            with self.assertRaises(ValueError):
                validate_review_results(
                    repo_root=repo,
                    task_id="task-1",
                    required_stages=["spec_scope_review"],
                )

    def test_cli_writes_review_result_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)

            proc = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "harness_kit.cli",
                    "write-review-result",
                    "--repo-root",
                    str(repo),
                    "--task-id",
                    "task-1",
                    "--stage",
                    "rules_lint_review",
                    "--verdict",
                    "APPROVED",
                    "--next-action",
                    "finish",
                    "--advisory-note",
                    "lint is clean",
                    "--evidence-ref",
                    "docs/reviews/task-1-pr.md",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("rules_lint_review.md", proc.stdout)
            receipt = (
                repo
                / ".harness"
                / "runtime"
                / "review-results"
                / "task-1"
                / "rules_lint_review.md"
            )
            self.assertTrue(receipt.is_file())


if __name__ == "__main__":
    unittest.main()
