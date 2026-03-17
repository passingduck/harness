# Harness Kit Phase 1 Codex Core Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the `harness-kit` distribution repository as a Codex-first phase-1 core with canonical templates, deterministic scaffold generation, queue/worktree contracts, and phase-1 memory/review-pack automation.

**Architecture:** Use a small standard-library Python module as the deterministic engine for template rendering, queue/state handling, memory/review-pack draft generation, and worktree orchestration. Keep shell usage thin by exposing small `scripts/harness/*.sh` wrappers that call the Python module. Treat canonical markdown and template files as the source of truth, and keep runtime state under `.harness/runtime/` in generated repos.

**Tech Stack:** Python 3 standard library, shell scripts, markdown templates, git worktrees, Codex-oriented repo-local skills.

---

## File Structure

- Create: `README.md`
  - Distribution repo overview, install flow, phase split, usage examples.
- Create: `REQUIREMENT.md`
  - Python version, git requirement, Codex-first assumptions, deterministic adapter policy.
- Create: `SUMMARY.md`
  - Short architecture map for this repo.
- Create: `harness_kit/__init__.py`
  - Package marker and version constant.
- Create: `harness_kit/cli.py`
  - CLI entrypoint for `init`, `claim-task`, `open-worktree`, `close-worktree`, `refresh-memory`, `build-review-pack`.
- Create: `harness_kit/scaffold.py`
  - Deterministic project scaffold renderer.
- Create: `harness_kit/template_loader.py`
  - Loads template files and performs placeholder substitution.
- Create: `harness_kit/runtime_bundle.py`
  - Declares which `harness_kit` modules are vendored into generated repos under `scripts/harness/runtime/harness_kit/`.
- Create: `harness_kit/queue.py`
  - Queue item schema validation, directory-authoritative state transitions, context pack helpers.
- Create: `harness_kit/worktree.py`
  - `.worktrees/` policy, ignore verification, open/close worktree helpers.
- Create: `harness_kit/memory.py`
  - Touched-directory detection and `DIRECTORY.md` refresh draft generation.
- Create: `harness_kit/review_pack.py`
  - Draft commit/PR review pack generation and durable promotion helper.
- Create: `templates/project/AGENTS.md`
  - Canonical generated root instruction template for produced repos.
- Create: `templates/project/README.md`
  - Generated project README template.
- Create: `templates/project/SUMMARY.md`
  - Generated project summary template.
- Create: `templates/project/REQUIREMENT.md`
  - Generated environment/constraints template.
- Create: `templates/project/DIRECTORY.md`
  - Root directory memory template.
- Create: `templates/project/.gitignore`
  - Ignores `.harness/runtime/`, `.worktrees/`, `.superpowers/`.
- Create: `templates/project/.harness/policies/model-routing.yaml`
  - Default `gpt-5.4` role mapping plus mini exceptions.
- Create: `templates/project/.harness/policies/review-stages.yaml`
  - `APPROVED | CHANGES_REQUIRED | ESCALATE` verdict schema and stage order.
- Create: `templates/project/.harness/policies/qa-rules.md`
  - Phase-1 QA policy contract and placeholders.
- Create: `templates/project/.harness/policies/doc-update-policy.md`
  - Documentation refresh trigger rules.
- Create: `templates/project/.harness/templates/task.md`
  - Queue item template.
- Create: `templates/project/.harness/templates/directory.md`
  - Reusable directory-memory draft template for generated repos.
- Create: `templates/project/.harness/templates/context-pack.md`
  - Context pack template with owned-path boundaries.
- Create: `templates/project/.harness/templates/evidence-pack.md`
  - Raw evidence template.
- Create: `templates/project/.harness/templates/commit-pack.md`
  - Runtime-only review pack template.
- Create: `templates/project/.harness/templates/pr-pack.md`
  - Durable PR review narrative template.
- Create: `templates/project/scripts/harness/claim-task.sh`
  - Thin wrapper around the vendored runtime `python3 -m harness_kit.cli claim-task`.
- Create: `templates/project/scripts/harness/open-worktree.sh`
  - Thin wrapper around the vendored runtime `python3 -m harness_kit.cli open-worktree`.
- Create: `templates/project/scripts/harness/close-worktree.sh`
  - Thin wrapper around the vendored runtime `python3 -m harness_kit.cli close-worktree`.
- Create: `templates/project/scripts/harness/refresh-memory.sh`
  - Thin wrapper around the vendored runtime `python3 -m harness_kit.cli refresh-memory`.
- Create: `templates/project/scripts/harness/run-qa.sh`
  - Phase-1 QA hook placeholder wrapper for repo-local rules/lint and regression commands.
- Create: `templates/project/scripts/harness/build-review-pack.sh`
  - Thin wrapper around the vendored runtime `python3 -m harness_kit.cli build-review-pack`.
- Create: `skills/orchestrate-queue/SKILL.md`
  - Codex-oriented queue/controller skill.
- Create: `skills/refresh-memory/SKILL.md`
  - Memory refresh workflow skill.
- Create: `skills/prepare-review-pack/SKILL.md`
  - Review-pack generation workflow skill.
- Create: `adapters/codex/README.md`
  - Codex-first adapter contract and optional fallback-link instructions.
- Create: `install/init-project.sh`
  - Thin installer wrapper around `python3 -m harness_kit.cli init`.
- Create: `tests/test_scaffold.py`
  - Scaffold rendering integration tests against a temp directory.
- Create: `tests/test_queue.py`
  - Queue state authority and transition tests.
- Create: `tests/test_worktree.py`
  - Worktree path/ignore behavior tests using temp git repos.
- Create: `tests/test_memory.py`
  - Memory refresh draft generation tests.
- Create: `tests/test_review_pack.py`
  - Review-pack draft and promotion tests.

## Scope Check

This plan intentionally implements only the Codex-first phase-1 core from the approved spec:

- included: scaffold generation, vendored repo-local runtime, canonical contracts, Codex adapter, queue/worktree mechanics, memory refresh drafts, review-pack drafts
- excluded: Claude adapter, Copilot adapter, `adopt`, `upgrade`, packaged `lint-rules-qa`, packaged `adversarial-regression`

## Task 1: Create Repository Baseline and Python Command Skeleton

**Files:**
- Create: `README.md`
- Create: `REQUIREMENT.md`
- Create: `SUMMARY.md`
- Create: `harness_kit/__init__.py`
- Create: `harness_kit/cli.py`
- Test: `tests/test_scaffold.py`

- [ ] **Step 1: Write the failing CLI smoke test**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_scaffold.CliSmokeTest.test_help_lists_phase1_commands -v`
Expected: FAIL because `harness_kit.cli` does not exist yet

- [ ] **Step 3: Write the minimal package and CLI**

```python
# harness_kit/__init__.py
__all__ = ["__version__"]
__version__ = "0.1.0"
```

```python
# harness_kit/cli.py
import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="harness-kit")
    sub = parser.add_subparsers(dest="command")
    for name in [
        "init",
        "claim-task",
        "open-worktree",
        "close-worktree",
        "refresh-memory",
        "build-review-pack",
    ]:
        sub.add_parser(name)
    return parser


def main() -> int:
    parser = build_parser()
    parser.parse_args()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Add baseline repo docs**

Add concise first-pass versions of:

- `README.md`
- `REQUIREMENT.md`
- `SUMMARY.md`

They should state:

- this repo builds `harness-kit`
- phase 1 is Codex-first
- docs are English
- commits are Korean
- Python 3 and git are required

- [ ] **Step 5: Run the smoke test again**

Run: `python3 -m unittest tests.test_scaffold.CliSmokeTest.test_help_lists_phase1_commands -v`
Expected: PASS

- [ ] **Step 6: Commit**

Run:

```bash
git add README.md REQUIREMENT.md SUMMARY.md harness_kit/__init__.py harness_kit/cli.py tests/test_scaffold.py
git commit -m "하네스 킷 기본 CLI 골격 추가"
```

## Task 2: Add Canonical Project Templates and Policy Files

**Files:**
- Create: `templates/project/AGENTS.md`
- Create: `templates/project/README.md`
- Create: `templates/project/SUMMARY.md`
- Create: `templates/project/REQUIREMENT.md`
- Create: `templates/project/DIRECTORY.md`
- Create: `templates/project/.gitignore`
- Create: `templates/project/.harness/policies/model-routing.yaml`
- Create: `templates/project/.harness/policies/review-stages.yaml`
- Create: `templates/project/.harness/policies/qa-rules.md`
- Create: `templates/project/.harness/policies/doc-update-policy.md`
- Create: `templates/project/.harness/templates/task.md`
- Create: `templates/project/.harness/templates/directory.md`
- Create: `templates/project/.harness/templates/context-pack.md`
- Create: `templates/project/.harness/templates/evidence-pack.md`
- Create: `templates/project/.harness/templates/commit-pack.md`
- Create: `templates/project/.harness/templates/pr-pack.md`
- Create: `templates/project/scripts/harness/run-qa.sh`
- Create: `skills/orchestrate-queue/SKILL.md`
- Create: `skills/refresh-memory/SKILL.md`
- Create: `skills/prepare-review-pack/SKILL.md`
- Test: `tests/test_scaffold.py`

- [ ] **Step 1: Write failing template-presence tests**

```python
from pathlib import Path
import unittest


class TemplatePresenceTest(unittest.TestCase):
    def test_phase1_templates_exist(self) -> None:
        required = [
            "templates/project/AGENTS.md",
            "templates/project/.harness/policies/doc-update-policy.md",
            "templates/project/.harness/policies/model-routing.yaml",
            "templates/project/.harness/policies/qa-rules.md",
            "templates/project/.harness/policies/review-stages.yaml",
            "templates/project/.harness/templates/context-pack.md",
            "templates/project/.harness/templates/directory.md",
            "templates/project/.harness/templates/evidence-pack.md",
            "templates/project/.harness/templates/task.md",
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
        self.assertIn("APPROVED", review_stage_text)
        self.assertIn("CHANGES_REQUIRED", review_stage_text)
        for token in [
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
        self.assertIn("why_this_task_exists", context_pack_text)
        self.assertIn("owned_paths", context_pack_text)
        self.assertIn("disallowed_edits", context_pack_text)
        self.assertIn("verification_commands", context_pack_text)
        self.assertIn("expected_report_schema", context_pack_text)
        task_text = Path(
            "templates/project/.harness/templates/task.md"
        ).read_text(encoding="utf-8")
        self.assertIn("why_this_task_exists", task_text)
        self.assertIn("acceptance_criteria", task_text)
        self.assertIn("expected_report_schema", task_text)
        pr_pack_text = Path(
            "templates/project/.harness/templates/pr-pack.md"
        ).read_text(encoding="utf-8")
        self.assertIn("verification evidence", pr_pack_text.lower())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_scaffold.TemplatePresenceTest.test_phase1_templates_exist -v`
Expected: FAIL because template files do not exist yet

- [ ] **Step 3: Create the canonical template set**

Template requirements:

- `AGENTS.md` must declare instruction priority, required reads, default workflow, model routing default, documentation gate, QA gate, worktree rule, output convention
- `model-routing.yaml` must include the concrete phase-1 mapping from the spec, with `gpt-5.4` for judgment-heavy roles and `gpt-5.1-codex-mini` only for inventory-only work
- `review-stages.yaml` must use uppercase verdicts: `APPROVED`, `CHANGES_REQUIRED`, `ESCALATE`
- `review-stages.yaml` must also encode the required review-result fields:
  - `stage`
  - `verdict`
  - `blocking_issues`
  - `advisory_notes`
  - `evidence_refs`
  - `next_action`
- `context-pack.md` must use the exact contract names:
  - `why_this_task_exists`
  - `owned_paths`
  - `required_reads`
  - `disallowed_edits`
  - `constraints`
  - `verification_commands`
  - `expected_report_schema`
- `.harness/templates/directory.md` must exist so `refresh-memory` can create missing directory guides inside generated repos
- `task.md` must state that directory name is authoritative for queue state and frontmatter `status` must mirror it
- `task.md` must include the full phase-1 queue frontmatter keys, including `why_this_task_exists`, `disallowed_edits`, `constraints`, and `expected_report_schema`
- `task.md` must define stable body sections for `task_text`, `acceptance_criteria`, and `non_goals`
- `qa-rules.md` must define phase-1 hook points and command placeholders for rules/lint QA and adversarial regression
- `evidence-pack.md`, `commit-pack.md`, and `pr-pack.md` must include the section headings needed by the spec
- `scripts/harness/run-qa.sh` must exist as a repo-local phase-1 placeholder entry point
- root `skills/*` must exist as canonical scaffold-copy sources, even if their deeper operational details are refined later in Task 5
- `.gitignore` must ignore `.harness/runtime/`, `.worktrees/`, `.superpowers/`

- [ ] **Step 4: Re-run the template test**

Run: `python3 -m unittest tests.test_scaffold.TemplatePresenceTest.test_phase1_templates_exist -v`
Expected: PASS

- [ ] **Step 5: Commit**

Run:

```bash
git add templates/project skills tests/test_scaffold.py
git commit -m "프로젝트 템플릿과 정책 문서 추가"
```

## Task 3: Implement Deterministic Scaffold Rendering and `init` Installer

**Files:**
- Create: `harness_kit/template_loader.py`
- Create: `harness_kit/runtime_bundle.py`
- Create: `harness_kit/scaffold.py`
- Modify: `harness_kit/cli.py`
- Create: `install/init-project.sh`
- Create: `adapters/codex/README.md`
- Test: `tests/test_scaffold.py`

- [ ] **Step 1: Write the failing scaffold integration test**

```python
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest


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
            self.assertTrue((target / "skills" / "orchestrate-queue" / "SKILL.md").is_file())
            self.assertTrue((target / "docs" / "specs").is_dir())
            self.assertTrue((target / "docs" / "plans").is_dir())
            self.assertTrue((target / "docs" / "reviews").is_dir())
            self.assertTrue((target / ".harness" / "policies" / "model-routing.yaml").is_file())
            self.assertTrue((target / ".harness" / "runtime" / "queue" / "ready").is_dir())
            self.assertTrue((target / ".harness" / "runtime" / "context-packs").is_dir())
            self.assertTrue((target / ".harness" / "runtime" / "evidence" / "raw").is_dir())
            self.assertTrue((target / ".harness" / "runtime" / "review-packs" / "drafts").is_dir())
            self.assertTrue((target / ".harness" / "runtime" / "agent-runs").is_dir())
            self.assertTrue((target / ".harness" / "runtime" / "worktree-registry").is_dir())
            self.assertTrue((target / ".worktrees").is_dir())
            self.assertTrue((target / ".harness" / "templates" / "directory.md").is_file())
            self.assertTrue((target / "scripts" / "harness" / "run-qa.sh").is_file())
            self.assertTrue((target / "scripts" / "harness" / "runtime" / "harness_kit" / "cli.py").is_file())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_scaffold.InitScaffoldTest.test_init_creates_codex_first_repo -v`
Expected: FAIL because `init` is not implemented

- [ ] **Step 3: Implement deterministic template loading**

`harness_kit/template_loader.py` should:

- enumerate all files under `templates/project/`
- enumerate canonical root `skills/` for scaffold copy into generated repo root `skills/`
- load text files as UTF-8
- substitute `{{project_name}}`
- preserve relative paths exactly

`harness_kit/runtime_bundle.py` should:

- define the phase-1 vendored runtime module list copied from the distribution repo package into generated repos
- map those files into `scripts/harness/runtime/harness_kit/`
- start with `__init__.py` and `cli.py`, then expand in later tasks as queue/worktree/memory/review-pack modules are added

Minimal interface:

```python
from pathlib import Path


def iter_template_files(root: Path) -> list[Path]:
    return [p for p in root.rglob("*") if p.is_file()]


def render_text(template: str, project_name: str) -> str:
    return template.replace("{{project_name}}", project_name)
```

- [ ] **Step 4: Implement scaffold writer and CLI `init`**

`harness_kit/scaffold.py` should:

- create target directory
- copy rendered project templates from `templates/project/`
- copy canonical distribution skill bodies from repo root `skills/` into generated repo root `skills/`
- vendor the phase-1 runtime bundle into `scripts/harness/runtime/harness_kit/`
- create empty phase-1 directories that templates do not materialize automatically:
  - `docs/specs`
  - `docs/plans`
  - `docs/reviews`
  - `.harness/runtime/queue/backlog`
  - `.harness/runtime/queue/ready`
  - `.harness/runtime/queue/in_progress`
  - `.harness/runtime/queue/review`
  - `.harness/runtime/queue/blocked`
  - `.harness/runtime/queue/done`
  - `.harness/runtime/context-packs`
  - `.harness/runtime/evidence/raw`
  - `.harness/runtime/review-packs/drafts`
  - `.harness/runtime/agent-runs`
  - `.harness/runtime/worktree-registry`
  - `.worktrees`
- print the generated root path

Phase-1 note:

- end-state `scripts/harness/init.sh` remains deferred
- the only required initializer in this plan is distribution-level `install/init-project.sh`
- runtime-writing commands added later in the plan must still recreate missing ignored directories lazily after clone

`harness_kit/cli.py` should implement:

- `init --target PATH --project-name NAME`

`install/init-project.sh` should be a thin wrapper:

```bash
#!/usr/bin/env bash
set -euo pipefail
python3 -m harness_kit.cli init "$@"
```

`adapters/codex/README.md` must document:

- repo-local `AGENTS.md`
- repo-local `skills/`
- vendored repo-local runtime under `scripts/harness/runtime/harness_kit/`
- optional fallback link helper for environments that need external Codex skill discovery

- [ ] **Step 5: Run the scaffold test**

Run: `python3 -m unittest tests.test_scaffold.InitScaffoldTest.test_init_creates_codex_first_repo -v`
Expected: PASS

- [ ] **Step 6: Commit**

Run:

```bash
git add harness_kit/template_loader.py harness_kit/runtime_bundle.py harness_kit/scaffold.py harness_kit/cli.py install/init-project.sh adapters/codex/README.md tests/test_scaffold.py
git commit -m "스캐폴드 렌더러와 초기화 경로 추가"
```

## Task 4: Implement Queue Contracts, State Transitions, and Worktree Helpers

**Files:**
- Create: `harness_kit/queue.py`
- Create: `harness_kit/worktree.py`
- Modify: `harness_kit/runtime_bundle.py`
- Modify: `harness_kit/cli.py`
- Create: `templates/project/scripts/harness/claim-task.sh`
- Create: `templates/project/scripts/harness/open-worktree.sh`
- Create: `templates/project/scripts/harness/close-worktree.sh`
- Test: `tests/test_queue.py`
- Test: `tests/test_worktree.py`

- [ ] **Step 1: Write the failing queue-state test**

```python
import tempfile
from pathlib import Path
import unittest

from harness_kit.queue import claim_task, move_task


class QueueStateAuthorityTest(unittest.TestCase):
    def test_directory_state_is_authoritative(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task = root / ".harness" / "runtime" / "queue" / "ready" / "task-1.md"
            task.parent.mkdir(parents=True)
            task.write_text("---\nstatus: backlog\n---\n", encoding="utf-8")
            moved = move_task(task, "in_progress")
            self.assertEqual(moved.parent.name, "in_progress")
            self.assertIn("status: in_progress", moved.read_text(encoding="utf-8"))

    def test_claim_task_creates_context_pack_from_queue_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task = root / ".harness" / "runtime" / "queue" / "ready" / "task-1.md"
            task.parent.mkdir(parents=True)
            task.write_text(
                (
                    "---\n"
                    "id: task-1\n"
                    "title: Queue contract test\n"
                    "status: ready\n"
                    "priority: high\n"
                    "owner_role: implementer\n"
                    "model_hint: gpt-5.4\n"
                    "worktree: null\n"
                    "parent_spec: docs/specs/spec.md\n"
                    "parent_plan: docs/plans/plan.md\n"
                    "why_this_task_exists: Preserve queue determinism\n"
                    "owned_paths:\n"
                    "  - src/payments\n"
                    "required_reads:\n"
                    "  - AGENTS.md\n"
                    "disallowed_edits:\n"
                    "  - infra/\n"
                    "docs_to_update:\n"
                    "  - src/payments/DIRECTORY.md\n"
                    "constraints:\n"
                    "  - stay within payments scope\n"
                    "verification_commands:\n"
                    "  - python3 -m unittest tests.test_queue -v\n"
                    "expected_report_schema:\n"
                    "  - status\n"
                    "  - files_changed\n"
                    "review_stages:\n"
                    "  - spec_scope\n"
                    "  - rules_lint\n"
                    "dependencies: []\n"
                    "---\n"
                    "## task_text\nImplement the queue contract.\n"
                    "## acceptance_criteria\n- context pack written\n"
                    "## non_goals\n- no phase 2 adapter work\n"
                ),
                encoding="utf-8",
            )
            claimed_task, context_pack = claim_task(task_path=task, repo_root=root)
            self.assertEqual(claimed_task.parent.name, "in_progress")
            self.assertIn("worktree: task-1", claimed_task.read_text(encoding="utf-8"))
            self.assertTrue((root / ".harness" / "runtime" / "context-packs").is_dir())
            self.assertTrue(context_pack.is_file())
            context_text = context_pack.read_text(encoding="utf-8")
            self.assertIn("task_text", context_text)
            self.assertIn("why_this_task_exists", context_text)
            self.assertIn("owned_paths", context_text)
            self.assertIn("disallowed_edits", context_text)
            self.assertIn("constraints", context_text)
            self.assertIn("verification_commands", context_text)
            self.assertIn("expected_report_schema", context_text)
```

- [ ] **Step 2: Write the failing worktree helper test**

```python
import tempfile
from pathlib import Path
import unittest

from harness_kit.queue import claim_task
from harness_kit.worktree import choose_worktree_path, close_worktree, open_worktree


class WorktreePathTest(unittest.TestCase):
    def test_uses_project_local_worktrees_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            path = choose_worktree_path(repo, "task-1")
            self.assertEqual(path, repo / ".worktrees" / "task-1")

    def test_open_worktree_marks_baseline_verified(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            record = open_worktree(
                repo_root=repo,
                task_id="task-1",
                branch_name="task-1",
                cleanup_policy="preserve",
            )
            self.assertTrue((repo / ".harness" / "runtime" / "worktree-registry").is_dir())
            self.assertTrue((repo / ".worktrees").is_dir())
            text = record.read_text(encoding="utf-8")
            self.assertIn("status: attached", text)
            self.assertIn("baseline_verified: true", text)

    def test_close_worktree_uses_worker_status_for_queue_transition(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task = root / ".harness" / "runtime" / "queue" / "ready" / "task-1.md"
            task.parent.mkdir(parents=True)
            task.write_text(
                (
                    "---\n"
                    "id: task-1\n"
                    "title: Queue contract test\n"
                    "status: ready\n"
                    "priority: high\n"
                    "owner_role: implementer\n"
                    "model_hint: gpt-5.4\n"
                    "worktree: null\n"
                    "parent_spec: docs/specs/spec.md\n"
                    "parent_plan: docs/plans/plan.md\n"
                    "why_this_task_exists: Preserve queue determinism\n"
                    "owned_paths:\n"
                    "  - src/payments\n"
                    "required_reads:\n"
                    "  - AGENTS.md\n"
                    "disallowed_edits:\n"
                    "  - infra/\n"
                    "docs_to_update:\n"
                    "  - src/payments/DIRECTORY.md\n"
                    "constraints:\n"
                    "  - stay within payments scope\n"
                    "verification_commands:\n"
                    "  - python3 -m unittest tests.test_queue -v\n"
                    "expected_report_schema:\n"
                    "  - status\n"
                    "review_stages:\n"
                    "  - spec_scope\n"
                    "dependencies: []\n"
                    "---\n"
                    "## task_text\nImplement the queue contract.\n"
                    "## acceptance_criteria\n- context pack written\n"
                    "## non_goals\n- no phase 2 adapter work\n"
                ),
                encoding="utf-8",
            )
            claimed_task, _ = claim_task(task_path=task, repo_root=root)
            open_worktree(
                repo_root=root,
                task_id="task-1",
                branch_name="task-1",
                cleanup_policy="preserve",
            )
            closed_task, record = close_worktree(
                repo_root=root,
                task_id="task-1",
                mode="preserve",
                worker_status="DONE",
            )
            self.assertEqual(closed_task.parent.name, "review")
            self.assertIn("status: preserved", record.read_text(encoding="utf-8"))

    def test_close_worktree_delete_marks_cleanup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            open_worktree(
                repo_root=root,
                task_id="task-1",
                branch_name="task-1",
                cleanup_policy="delete",
            )
            _, record = close_worktree(
                repo_root=root,
                task_id="task-1",
                mode="delete",
                worker_status="DONE_WITH_CONCERNS",
            )
            self.assertIn("status: deleted", record.read_text(encoding="utf-8"))
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `python3 -m unittest tests.test_queue.QueueStateAuthorityTest.test_directory_state_is_authoritative -v`
Expected: FAIL because queue module does not exist

Run: `python3 -m unittest tests.test_queue.QueueStateAuthorityTest.test_claim_task_creates_context_pack_from_queue_contract -v`
Expected: FAIL because queue module does not exist

Run: `python3 -m unittest tests.test_worktree.WorktreePathTest.test_uses_project_local_worktrees_directory -v`
Expected: FAIL because worktree module does not exist

Run: `python3 -m unittest tests.test_worktree.WorktreePathTest.test_open_worktree_marks_baseline_verified -v`
Expected: FAIL because worktree module does not exist

Run: `python3 -m unittest tests.test_worktree.WorktreePathTest.test_close_worktree_uses_worker_status_for_queue_transition -v`
Expected: FAIL because worktree module does not exist

Run: `python3 -m unittest tests.test_worktree.WorktreePathTest.test_close_worktree_delete_marks_cleanup -v`
Expected: FAIL because worktree module does not exist

- [ ] **Step 4: Implement queue state authority and transitions**

`harness_kit/queue.py` must:

- define valid states: `backlog`, `ready`, `in_progress`, `review`, `blocked`, `done`
- validate the full queue frontmatter contract:
  - `id`
  - `title`
  - `status`
  - `priority`
  - `owner_role`
  - `model_hint`
  - `worktree`
  - `parent_spec`
  - `parent_plan`
  - `why_this_task_exists`
  - `owned_paths`
  - `required_reads`
  - `disallowed_edits`
  - `docs_to_update`
  - `constraints`
  - `verification_commands`
  - `expected_report_schema`
  - `review_stages`
  - `dependencies`
- validate stable body sections for `task_text`, `acceptance_criteria`, and `non_goals`
- treat directory state as authoritative
- update frontmatter `status` to mirror the directory state
- reject invalid transitions
- keep `worktree` nullable until claim time
- in phase 1, assign `worktree == id` at claim time so `task_id` is the only workspace identity source
- implement `claim_task(...)` that:
  - moves a queue item from `ready` to `in_progress`
  - assigns `worktree` equal to the task id
  - writes `.harness/runtime/context-packs/<id>.md`
  - lazily creates missing runtime parent directories before writing
  - copies the canonical context-pack fields from the queue contract into that file

Minimal interface:

```python
VALID_TRANSITIONS = {
    "backlog": {"ready"},
    "ready": {"in_progress"},
    "in_progress": {"review", "blocked", "ready"},
    "review": {"in_progress", "done"},
    "blocked": {"ready"},
    "done": set(),
}
```

- [ ] **Step 5: Implement worktree helpers and CLI wiring**

`harness_kit/worktree.py` must:

- resolve `.worktrees/<task-id>`
- verify `.worktrees/` is ignored when inside a repo
- lazily create missing `.harness/runtime/*` and `.worktrees/*` parents before writing
- expose open/close helpers that shell out to `git worktree`
- write authoritative registry records under `.harness/runtime/worktree-registry/<task-id>.md`
- treat the registry record as authoritative for workspace lifecycle, with queue-item `worktree` as a mirrored pointer only
- in phase 1, require `worktree_name == task_id`
- `open_worktree(...)` must provision, baseline verify, attach, and then persist `baseline_verified: true`
- `close_worktree(...)` must preserve or delete the workspace according to `mode`, persist the resulting lifecycle status, and update queue state from typed worker status:
  - `DONE` or `DONE_WITH_CONCERNS` -> move queue item to `review`
  - `NEEDS_CONTEXT` -> move queue item to `ready`
  - `BLOCKED` -> move queue item to `blocked`
- record at least:
  - `task_id`
  - `worktree_name`
  - `path`
  - `branch`
  - `status`
  - `baseline_verified`
  - `cleanup_policy`

`harness_kit/runtime_bundle.py` must be extended so generated repos receive `queue.py` and `worktree.py` in the vendored runtime.

`harness_kit/cli.py` must implement:

- `claim-task --repo-root PATH --task PATH`
- `open-worktree --repo-root PATH --task-id ID --branch NAME [--cleanup-policy preserve|delete]`
- `close-worktree --repo-root PATH --task-id ID --mode preserve|delete --worker-status DONE|DONE_WITH_CONCERNS|NEEDS_CONTEXT|BLOCKED`

`templates/project/scripts/harness/*.sh` should forward to the vendored runtime, for example:

```bash
#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PYTHONPATH="$ROOT/scripts/harness/runtime${PYTHONPATH:+:$PYTHONPATH}" \
  python3 -m harness_kit.cli claim-task --repo-root "$ROOT" "$@"
```

- [ ] **Step 6: Run the targeted tests**

Run: `python3 -m unittest tests.test_queue tests.test_worktree -v`
Expected: PASS

- [ ] **Step 7: Commit**

Run:

```bash
git add harness_kit/queue.py harness_kit/worktree.py harness_kit/runtime_bundle.py harness_kit/cli.py templates/project/scripts/harness/claim-task.sh templates/project/scripts/harness/open-worktree.sh templates/project/scripts/harness/close-worktree.sh tests/test_queue.py tests/test_worktree.py
git commit -m "큐 상태 머신과 워크트리 도우미 추가"
```

## Task 5: Implement Memory Refresh and Review-Pack Assembly Core Automation

**Files:**
- Create: `harness_kit/memory.py`
- Create: `harness_kit/review_pack.py`
- Modify: `harness_kit/runtime_bundle.py`
- Modify: `harness_kit/cli.py`
- Create: `templates/project/scripts/harness/refresh-memory.sh`
- Create: `templates/project/scripts/harness/build-review-pack.sh`
- Modify: `skills/orchestrate-queue/SKILL.md`
- Modify: `skills/refresh-memory/SKILL.md`
- Modify: `skills/prepare-review-pack/SKILL.md`
- Test: `tests/test_memory.py`
- Test: `tests/test_review_pack.py`

- [ ] **Step 1: Write the failing memory refresh test**

```python
import tempfile
from pathlib import Path
import unittest

from harness_kit.memory import compute_directory_guides_to_refresh, ensure_directory_guide


class MemoryRefreshTest(unittest.TestCase):
    def test_maps_changed_files_to_directory_guides(self) -> None:
        changed = ["src/payments/service.py", "tests/payments/test_service.py"]
        guides = compute_directory_guides_to_refresh(changed)
        self.assertEqual(guides, {"src/payments/DIRECTORY.md", "tests/payments/DIRECTORY.md"})

    def test_creates_missing_directory_guide_from_repo_template(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            template = repo / ".harness" / "templates" / "directory.md"
            template.parent.mkdir(parents=True)
            template.write_text("# Directory Guide\n", encoding="utf-8")
            draft = ensure_directory_guide(
                repo_root=repo,
                guide_path=Path("src/payments/DIRECTORY.md"),
            )
            self.assertTrue(draft.is_file())
            self.assertIn("Directory Guide", draft.read_text(encoding="utf-8"))
```

- [ ] **Step 2: Write the failing review-pack test**

```python
import tempfile
from pathlib import Path
import unittest

from harness_kit.review_pack import build_pr_review_pack, promote_review_pack


class ReviewPackTest(unittest.TestCase):
    def test_builds_runtime_pr_draft(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            pack = build_pr_review_pack(
                repo_root=repo,
                title="Queue state fix",
                changed_paths=["harness_kit/queue.py"],
                verification_commands=["python3 -m unittest tests.test_queue -v"],
            )
            self.assertTrue(pack.exists())
            text = pack.read_text(encoding="utf-8")
            self.assertIn("Queue state fix", text)
            self.assertIn("python3 -m unittest tests.test_queue -v", text)

    def test_promotes_pr_review_pack_into_docs_reviews(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
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
            self.assertIn("Queue state fix", promoted.read_text(encoding="utf-8"))
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `python3 -m unittest tests.test_memory tests.test_review_pack -v`
Expected: FAIL because memory/review-pack modules do not exist

- [ ] **Step 4: Implement deterministic memory refresh drafts**

`harness_kit/memory.py` must:

- accept changed paths
- map them to nearest meaningful directory guides
- create missing `DIRECTORY.md` drafts from `.harness/templates/directory.md` inside the generated repo
- lazily create missing parent directories before writing the guide
- return the guide list so the agent can fill semantic content

This is draft generation only, not automatic semantic summarization.

- [ ] **Step 5: Implement runtime review-pack assembly**

`harness_kit/review_pack.py` must:

- create runtime draft files under `.harness/runtime/review-packs/drafts/`
- support commit and PR pack skeletons
- support optional promotion into `docs/reviews/`
- lazily create runtime and promoted-review parent directories before writing
- never store durable raw evidence outside the promoted narrative

`harness_kit/cli.py` must implement:

- `refresh-memory --repo-root PATH --changed-path RELPATH [--changed-path RELPATH ...]`
- `build-review-pack --repo-root PATH --type commit|pr --title TEXT --changed-path RELPATH [--changed-path RELPATH ...] --verification-command CMD [--verification-command CMD ...] [--promote-to RELPATH]`

`harness_kit/runtime_bundle.py` must be extended so generated repos receive `memory.py` and `review_pack.py` in the vendored runtime.

- [ ] **Step 6: Fill phase-1 skill bodies**

`skills/orchestrate-queue/SKILL.md` should teach:

- turning approved plans into queue items
- context-pack generation
- deterministic status handling
- full queue schema expectations and `claim-task` behavior

`skills/refresh-memory/SKILL.md` should teach:

- when to update `DIRECTORY.md`
- how to use the script-generated draft and fill semantic content

`skills/prepare-review-pack/SKILL.md` should teach:

- how to turn runtime drafts and evidence into narrative-first human review docs

- [ ] **Step 7: Run targeted tests**

Run: `python3 -m unittest tests.test_memory tests.test_review_pack -v`
Expected: PASS

- [ ] **Step 8: Commit**

Run:

```bash
git add harness_kit/memory.py harness_kit/review_pack.py harness_kit/runtime_bundle.py harness_kit/cli.py templates/project/scripts/harness/refresh-memory.sh templates/project/scripts/harness/build-review-pack.sh skills/orchestrate-queue/SKILL.md skills/refresh-memory/SKILL.md skills/prepare-review-pack/SKILL.md tests/test_memory.py tests/test_review_pack.py
git commit -m "메모리 갱신과 리뷰 팩 자동화 추가"
```

## Task 6: Verify End-to-End Scaffold Generation and Document the Distribution Repo

**Files:**
- Modify: `README.md`
- Modify: `REQUIREMENT.md`
- Modify: `SUMMARY.md`
- Test: `tests/test_scaffold.py`
- Test: `tests/test_queue.py`
- Test: `tests/test_worktree.py`
- Test: `tests/test_memory.py`
- Test: `tests/test_review_pack.py`

- [ ] **Step 1: Add an end-to-end temp-repo integration test**

The integration test must:

- run `python3 -m harness_kit.cli init --target ... --project-name demo`
- assert the generated repo has:
  - `AGENTS.md`
  - `skills/orchestrate-queue/SKILL.md`
  - `.harness/policies/model-routing.yaml`
  - `.harness/templates/directory.md`
  - `.harness/templates/evidence-pack.md`
  - `scripts/harness/open-worktree.sh`
  - `scripts/harness/run-qa.sh`
  - `scripts/harness/runtime/harness_kit/cli.py`
  - `docs/specs/`
  - `docs/plans/`
  - `docs/reviews/`
- create a sample queue item
- delete the generated runtime directories that git would not preserve across clone:
  - `.harness/runtime/context-packs/`
  - `.harness/runtime/review-packs/drafts/`
  - `.harness/runtime/worktree-registry/`
  - `.worktrees/`
- run `scripts/harness/claim-task.sh --repo-root . --task .harness/runtime/queue/ready/task-1.md` inside the generated repo and confirm it recreates `.harness/runtime/context-packs/` and writes `.harness/runtime/context-packs/<id>.md`
- run `scripts/harness/open-worktree.sh --repo-root . --task-id task-1 --branch task-1 --cleanup-policy preserve` inside the generated repo and confirm it creates `.harness/runtime/worktree-registry/<id>.md`
- run `scripts/harness/close-worktree.sh --repo-root . --task-id task-1 --mode preserve --worker-status DONE` inside the generated repo and confirm it moves the queue item to `review`
- run `scripts/harness/build-review-pack.sh --repo-root . --type pr --title "Queue test" --changed-path AGENTS.md --verification-command true --promote-to docs/reviews/queue-test.md` inside the generated repo and confirm it recreates missing draft directories and writes both the runtime draft and the promoted review doc

- [ ] **Step 2: Run the integration test to verify it fails**

Run: `python3 -m unittest tests.test_scaffold -v`
Expected: FAIL until the missing behavior is implemented

- [ ] **Step 3: Implement any missing glue for the full flow**

Fix only the integration gaps revealed by the end-to-end test. Do not add phase-2 features.

- [ ] **Step 4: Update distribution repo docs**

`README.md` must include:

- what phase 1 includes
- what phase 1 excludes
- how to run `install/init-project.sh`
- how to run the Python test suite

`REQUIREMENT.md` must include:

- required Python and git assumptions
- deterministic adapter rule
- Codex-first support statement

`SUMMARY.md` must include:

- module map
- template tree summary
- vendored runtime map for generated repos
- CLI command map

- [ ] **Step 5: Run the full verification suite**

Run: `python3 -m unittest discover -s tests -v`
Expected: PASS

Run: `python3 -m compileall harness_kit`
Expected: exit 0

- [ ] **Step 6: Commit**

Run:

```bash
git add README.md REQUIREMENT.md SUMMARY.md harness_kit tests skills adapters install templates
git commit -m "하네스 킷 1단계 코어 검증 완료"
```

## Execution Notes

- Execute this plan on a dedicated worktree before making code changes.
- Use `gpt-5.4` for planner, implementer, and reviewer subagents by default.
- Keep `gpt-5.1-codex-mini` limited to shallow inventory or grep-only support work.
- Do not implement Claude/Copilot adapters or packaged reusable QA skills in this plan.
- Review after each task must check both:
  - scope compliance
  - code quality and maintainability
