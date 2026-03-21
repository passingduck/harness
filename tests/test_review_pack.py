import tempfile
from pathlib import Path
import unittest

from harness_kit.review_pack import (
    build_commit_review_pack,
    build_pr_review_pack,
    build_review_pack,
    promote_review_pack,
)
from harness_kit.worktree import open_worktree


class ReviewPackTest(unittest.TestCase):
    def _init_git_repo(self, repo: Path) -> None:
        import subprocess

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

    def test_builds_task_scoped_runtime_pr_draft(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._write_templates(repo)
            open_worktree(
                repo_root=repo,
                task_id="task-1",
                branch_name="task-1",
                cleanup_policy="preserve",
            )

            pack = build_pr_review_pack(
                repo_root=repo,
                task_id="task-1",
                title="Queue state fix",
                changed_paths=["harness_kit/queue.py"],
                verification_commands=["python3 -m unittest tests.test_queue -v"],
            )

            self.assertEqual(pack.name, "task-1-pr.md")
            registry_text = (
                repo
                / ".harness"
                / "runtime"
                / "worktree-registry"
                / "task-1.md"
            ).read_text(encoding="utf-8")
            self.assertIn(
                "draft_pr_review_pack: .harness/runtime/review-packs/drafts/task-1-pr.md",
                registry_text,
            )

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

    def test_dispatches_task_scoped_pr_packs_by_review_type(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._write_templates(repo)

            pack = build_review_pack(
                repo_root=repo,
                review_type="pr",
                task_id="task-1",
                title="Queue state fix",
                changed_paths=["harness_kit/queue.py"],
                verification_commands=["python3 -m unittest tests.test_queue -v"],
            )

            self.assertEqual(pack.name, "task-1-pr.md")

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

    def test_git_worktree_task_scoped_pack_uses_control_runtime_and_branch_docs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_git_repo(repo)
            self._write_templates(repo)
            (repo / ".gitignore").write_text("/.worktrees/\n", encoding="utf-8")
            import subprocess

            subprocess.run(
                ["git", "add", ".gitignore", ".harness/templates"],
                cwd=repo,
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                ["git", "commit", "-m", "add templates"],
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
            worktree_root = repo / ".worktrees" / "task-1"

            draft = build_pr_review_pack(
                repo_root=worktree_root,
                task_id="task-1",
                title="Queue state fix",
                changed_paths=["AGENTS.md"],
                verification_commands=["true"],
            )

            self.assertTrue(draft.is_file())
            self.assertTrue(
                (
                    repo
                    / ".harness"
                    / "runtime"
                    / "review-packs"
                    / "drafts"
                    / "task-1-pr.md"
                ).is_file()
            )

            promoted = promote_review_pack(
                repo_root=worktree_root,
                draft_path=Path(".harness/runtime/review-packs/drafts/task-1-pr.md"),
                promote_to=Path("docs/reviews/task-1-pr.md"),
                task_id="task-1",
            )

            self.assertEqual(
                promoted,
                worktree_root / "docs" / "reviews" / "task-1-pr.md",
            )
            self.assertIn(
                "Queue state fix",
                promoted.read_text(encoding="utf-8"),
            )
            registry_text = (
                repo
                / ".harness"
                / "runtime"
                / "worktree-registry"
                / "task-1.md"
            ).read_text(encoding="utf-8")
            self.assertIn(
                "draft_pr_review_pack: .harness/runtime/review-packs/drafts/task-1-pr.md",
                registry_text,
            )
            self.assertIn(
                "promoted_review_pack: docs/reviews/task-1-pr.md",
                registry_text,
            )

    def test_task_scoped_pr_pack_updates_registry_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._write_templates(repo)
            open_worktree(
                repo_root=repo,
                task_id="task-1",
                branch_name="task-1",
                cleanup_policy="preserve",
            )
            draft = build_pr_review_pack(
                repo_root=repo,
                task_id="task-1",
                title="Queue state fix",
                changed_paths=["AGENTS.md"],
                verification_commands=["true"],
            )

            promoted = promote_review_pack(
                repo_root=repo,
                draft_path=draft,
                promote_to=Path("docs/reviews/task-1-pr.md"),
                task_id="task-1",
            )

            self.assertEqual(promoted, repo / "docs" / "reviews" / "task-1-pr.md")
            registry_text = (
                repo
                / ".harness"
                / "runtime"
                / "worktree-registry"
                / "task-1.md"
            ).read_text(encoding="utf-8")
            self.assertIn(
                "draft_pr_review_pack: .harness/runtime/review-packs/drafts/task-1-pr.md",
                registry_text,
            )
            self.assertIn(
                "promoted_review_pack: docs/reviews/task-1-pr.md",
                registry_text,
            )

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

    def test_promotion_rejects_normalized_path_escape(self) -> None:
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
                    promote_to=Path("docs/reviews/../escaped.md"),
                )


if __name__ == "__main__":
    unittest.main()
