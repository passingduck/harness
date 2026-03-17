import tempfile
from pathlib import Path
import unittest

from harness_kit.memory import (
    compute_directory_guides_to_refresh,
    ensure_directory_guide,
    refresh_memory,
)


class MemoryRefreshTest(unittest.TestCase):
    def test_maps_changed_files_to_directory_guides(self) -> None:
        guides = compute_directory_guides_to_refresh(
            ["src/payments/service.py", "tests/payments/test_service.py"]
        )

        self.assertEqual(
            guides,
            {"src/payments/DIRECTORY.md", "tests/payments/DIRECTORY.md"},
        )

    def test_prefers_nearest_meaningful_directory_for_nested_files(self) -> None:
        guides = compute_directory_guides_to_refresh(
            [
                "src/payments/reconciliation/service.py",
                "src/payments/reconciliation/models/schema.py",
            ]
        )

        self.assertEqual(guides, {"src/payments/reconciliation/DIRECTORY.md"})

    def test_preserves_parent_and_child_guides_when_both_are_directly_implicated(self) -> None:
        guides = compute_directory_guides_to_refresh(
            [
                "src/payments/service.py",
                "src/payments/api/client.py",
            ]
        )

        self.assertEqual(
            guides,
            {
                "src/payments/DIRECTORY.md",
                "src/payments/api/DIRECTORY.md",
            },
        )

    def test_helper_maps_extensionless_path_to_parent_directory_guide(self) -> None:
        guides = compute_directory_guides_to_refresh(["bin/deploy"])

        self.assertEqual(guides, {"bin/DIRECTORY.md"})

    def test_creates_missing_directory_guide_from_repo_template(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            template = repo / ".harness" / "templates" / "directory.md"
            template.parent.mkdir(parents=True, exist_ok=True)
            template.write_text("# Directory Guide\n", encoding="utf-8")

            draft = ensure_directory_guide(repo, Path("src/payments/DIRECTORY.md"))

            self.assertTrue(draft.is_file())
            self.assertEqual(draft, repo / "src" / "payments" / "DIRECTORY.md")
            self.assertIn("Directory Guide", draft.read_text(encoding="utf-8"))

    def test_keeps_existing_directory_guide_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            guide = repo / "src" / "payments" / "DIRECTORY.md"
            guide.parent.mkdir(parents=True, exist_ok=True)
            guide.write_text("existing\n", encoding="utf-8")

            ensured = ensure_directory_guide(repo, Path("src/payments/DIRECTORY.md"))

            self.assertEqual(ensured.read_text(encoding="utf-8"), "existing\n")

    def test_refresh_memory_returns_created_guides(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            template = repo / ".harness" / "templates" / "directory.md"
            template.parent.mkdir(parents=True, exist_ok=True)
            template.write_text("# Directory Guide\n", encoding="utf-8")

            guides = refresh_memory(
                repo_root=repo,
                changed_paths=[
                    "src/payments/service.py",
                    "tests/payments/test_service.py",
                ],
            )

            self.assertEqual(
                guides,
                [
                    repo / "src" / "payments" / "DIRECTORY.md",
                    repo / "tests" / "payments" / "DIRECTORY.md",
                ],
            )
            for guide in guides:
                self.assertTrue(guide.is_file())

    def test_refresh_memory_maps_extensionless_file_to_parent_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            template = repo / ".harness" / "templates" / "directory.md"
            template.parent.mkdir(parents=True, exist_ok=True)
            template.write_text("# Directory Guide\n", encoding="utf-8")
            deploy_script = repo / "bin" / "deploy"
            deploy_script.parent.mkdir(parents=True, exist_ok=True)
            deploy_script.write_text("#!/usr/bin/env bash\n", encoding="utf-8")

            guides = refresh_memory(
                repo_root=repo,
                changed_paths=["bin/deploy"],
            )

            self.assertEqual(guides, [repo / "bin" / "DIRECTORY.md"])
            self.assertTrue(guides[0].is_file())

    def test_refresh_memory_maps_missing_extensionless_path_to_parent_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            template = repo / ".harness" / "templates" / "directory.md"
            template.parent.mkdir(parents=True, exist_ok=True)
            template.write_text("# Directory Guide\n", encoding="utf-8")
            (repo / "bin").mkdir(parents=True, exist_ok=True)

            guides = refresh_memory(
                repo_root=repo,
                changed_paths=["bin/deploy"],
            )

            self.assertEqual(guides, [repo / "bin" / "DIRECTORY.md"])
            self.assertTrue(guides[0].is_file())

    def test_refresh_memory_maps_deleted_extensionless_path_to_parent_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            template = repo / ".harness" / "templates" / "directory.md"
            template.parent.mkdir(parents=True, exist_ok=True)
            template.write_text("# Directory Guide\n", encoding="utf-8")
            deploy_script = repo / "bin" / "deploy"
            deploy_script.parent.mkdir(parents=True, exist_ok=True)
            deploy_script.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
            deploy_script.unlink()

            guides = refresh_memory(
                repo_root=repo,
                changed_paths=["bin/deploy"],
            )

            self.assertEqual(guides, [repo / "bin" / "DIRECTORY.md"])
            self.assertTrue(guides[0].is_file())

    def test_refresh_memory_falls_back_to_nearest_surviving_guide_for_missing_extensionless_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            template = repo / ".harness" / "templates" / "directory.md"
            template.parent.mkdir(parents=True, exist_ok=True)
            template.write_text("# Directory Guide\n", encoding="utf-8")

            guides = refresh_memory(
                repo_root=repo,
                changed_paths=["bin/deploy"],
            )

            self.assertEqual(guides, [repo / "DIRECTORY.md"])
            self.assertTrue(guides[0].is_file())

    def test_raises_when_directory_template_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)

            with self.assertRaises(FileNotFoundError):
                ensure_directory_guide(repo, Path("src/payments/DIRECTORY.md"))


if __name__ == "__main__":
    unittest.main()
