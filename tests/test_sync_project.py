import subprocess
import tempfile
from pathlib import Path
import unittest

from harness_kit.runtime_bundle import VENDORED_RUNTIME_MODULES
from harness_kit.sync_project import sync_project


class SyncProjectTest(unittest.TestCase):
    def _run_git(self, repo: Path, *args: str) -> str:
        proc = subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)
        return proc.stdout.strip()

    def _write(self, path: Path, content: str, executable: bool = False) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        if executable:
            path.chmod(0o755)

    def _make_fake_distribution_repo(self, root: Path) -> None:
        for rel in VENDORED_RUNTIME_MODULES:
            self._write(root / "harness_kit" / rel, f"# {rel.as_posix()}\n")
        self._write(
            root / "templates" / "project" / "scripts" / "harness" / "open-worktree.sh",
            "#!/usr/bin/env bash\n# open wrapper\n",
            executable=True,
        )
        self._write(
            root / "templates" / "project" / ".harness" / "policies" / "model-routing.yaml",
            "default: gpt-5.4\n",
        )
        self._write(
            root / "templates" / "project" / ".harness" / "templates" / "task.md",
            "id: {{project_name}}\n",
        )
        self._write(
            root / "skills" / "orchestrate-queue" / "SKILL.md",
            "name: orchestrate-queue\n",
        )
        self._run_git(root, "init", "-b", "main")
        self._run_git(root, "config", "user.name", "Harness Tests")
        self._run_git(root, "config", "user.email", "harness-tests@example.com")
        self._run_git(root, "add", ".")
        self._run_git(root, "commit", "-m", "fake source")

    def test_sync_project_writes_provenance_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source_repo = Path(tmp) / "source"
            target_repo = Path(tmp) / "target"
            source_repo.mkdir()
            target_repo.mkdir()
            self._make_fake_distribution_repo(source_repo)

            sync_project(source_root=source_repo, target_root=target_repo)

            provenance = target_repo / "third_party" / "harness-source.txt"
            self.assertTrue(provenance.is_file())
            text = provenance.read_text(encoding="utf-8")
            self.assertIn("source_remote:", text)
            self.assertIn("source_branch: main", text)
            self.assertIn("source_commit:", text)
            self.assertIn("runtime_bundle_fileset:", text)
            self.assertIn("synced_at:", text)

    def test_sync_project_refreshes_vendored_runtime_without_touching_campaign_code(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source_repo = Path(tmp) / "source"
            target_repo = Path(tmp) / "target"
            source_repo.mkdir()
            target_repo.mkdir()
            self._make_fake_distribution_repo(source_repo)

            self._write(
                target_repo / "scripts" / "harness" / "runtime" / "harness_kit" / "cli.py",
                "# stale runtime\n",
            )
            self._write(
                target_repo / "scripts" / "harness" / "open-worktree.sh",
                "# stale wrapper\n",
                executable=True,
            )
            self._write(
                target_repo / "skills" / "orchestrate-queue" / "SKILL.md",
                "stale skill\n",
            )
            self._write(
                target_repo / ".harness" / "policies" / "model-routing.yaml",
                "default: stale\n",
            )
            self._write(
                target_repo / ".harness" / "templates" / "task.md",
                "stale task template\n",
            )
            self._write(target_repo / "README.md", "campaign-owned readme\n")
            self._write(target_repo / "src" / "model.py", "campaign code\n")
            self._write(target_repo / "docs" / "experiments" / "notes.md", "campaign notes\n")

            sync_project(source_root=source_repo, target_root=target_repo, project_name="demo-campaign")

            self.assertEqual(
                (target_repo / "scripts" / "harness" / "runtime" / "harness_kit" / "cli.py").read_text(encoding="utf-8"),
                "# cli.py\n",
            )
            self.assertEqual(
                (target_repo / "scripts" / "harness" / "open-worktree.sh").read_text(encoding="utf-8"),
                "#!/usr/bin/env bash\n# open wrapper\n",
            )
            self.assertEqual(
                (target_repo / "skills" / "orchestrate-queue" / "SKILL.md").read_text(encoding="utf-8"),
                "name: orchestrate-queue\n",
            )
            self.assertEqual(
                (target_repo / ".harness" / "policies" / "model-routing.yaml").read_text(encoding="utf-8"),
                "default: gpt-5.4\n",
            )
            self.assertEqual(
                (target_repo / ".harness" / "templates" / "task.md").read_text(encoding="utf-8"),
                "id: demo-campaign\n",
            )
            self.assertEqual((target_repo / "README.md").read_text(encoding="utf-8"), "campaign-owned readme\n")
            self.assertEqual((target_repo / "src" / "model.py").read_text(encoding="utf-8"), "campaign code\n")
            self.assertEqual(
                (target_repo / "docs" / "experiments" / "notes.md").read_text(encoding="utf-8"),
                "campaign notes\n",
            )


if __name__ == "__main__":
    unittest.main()
