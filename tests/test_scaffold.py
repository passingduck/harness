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
