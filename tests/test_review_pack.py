import tempfile
from pathlib import Path
import unittest

from harness_kit.review_pack import (
    build_commit_review_pack,
    build_pr_review_pack,
    build_review_pack,
    promote_review_pack,
)


class ReviewPackTest(unittest.TestCase):
    def _write_templates(self, repo: Path) -> None:
        templates = repo / ".harness" / "templates"
        templates.mkdir(parents=True, exist_ok=True)
        (templates / "pr-pack.md").write_text("# PR Review Pack\n", encoding="utf-8")
        (templates / "commit-pack.md").write_text(
            "# Commit Review Pack\n",
            encoding="utf-8",
        )

    def test_builds_runtime_pr_draft(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._write_templates(repo)

            pack = build_pr_review_pack(
                repo_root=repo,
                title="Queue state fix",
                changed_paths=["harness_kit/queue.py"],
                verification_commands=["python3 -m unittest tests.test_queue -v"],
            )

            self.assertTrue(pack.exists())
            self.assertEqual(
                pack.parent,
                repo / ".harness" / "runtime" / "review-packs" / "drafts",
            )
            text = pack.read_text(encoding="utf-8")
            self.assertIn("# PR Review Pack", text)
            self.assertIn("Queue state fix", text)
            self.assertIn("python3 -m unittest tests.test_queue -v", text)

    def test_builds_runtime_commit_draft(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._write_templates(repo)

            pack = build_commit_review_pack(
                repo_root=repo,
                title="Memory refresh wiring",
                changed_paths=["harness_kit/memory.py"],
                verification_commands=["python3 -m unittest tests.test_memory -v"],
            )

            self.assertTrue(pack.is_file())
            self.assertIn("# Commit Review Pack", pack.read_text(encoding="utf-8"))

    def test_dispatches_by_review_pack_type(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._write_templates(repo)

            pack = build_review_pack(
                repo_root=repo,
                review_type="pr",
                title="Queue state fix",
                changed_paths=["harness_kit/queue.py"],
                verification_commands=["python3 -m unittest tests.test_queue -v"],
            )

            self.assertTrue(pack.is_file())
            self.assertIn("Queue state fix", pack.read_text(encoding="utf-8"))

    def test_promotes_pr_review_pack_into_docs_reviews(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._write_templates(repo)
            draft = build_pr_review_pack(
                repo_root=repo,
                title="Queue state fix",
                changed_paths=["AGENTS.md"],
                verification_commands=["true"],
            )

            promoted = promote_review_pack(
                repo_root=repo,
                draft_path=draft,
                promote_to=Path("docs/reviews/queue-state-fix.md"),
            )

            self.assertTrue(promoted.is_file())
            self.assertEqual(promoted, repo / "docs" / "reviews" / "queue-state-fix.md")
            self.assertIn("Queue state fix", promoted.read_text(encoding="utf-8"))

    def test_promotion_rejects_paths_outside_docs_reviews(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._write_templates(repo)
            draft = build_pr_review_pack(
                repo_root=repo,
                title="Queue state fix",
                changed_paths=["AGENTS.md"],
                verification_commands=["true"],
            )

            with self.assertRaises(ValueError):
                promote_review_pack(
                    repo_root=repo,
                    draft_path=draft,
                    promote_to=Path("notes/queue-state-fix.md"),
                )


if __name__ == "__main__":
    unittest.main()
