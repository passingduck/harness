# Qwen Export Campaign Phase 1 Readiness Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the harness readiness gate for the Qwen export campaign, bootstrap the external campaign repo, and prove the first end-to-end queue/worktree/review/finish flow before starting the actual ML/export work.

**Architecture:** Build the missing readiness features in the source `harness/` repo first: review-result receipts, deterministic task-linked review packs, local finish/publish commands, and a deterministic source-to-generated sync command. Then initialize `external/qwen-export-campaign/`, write the first queue items and campaign docs, and run one real `campaign-setup` task through the new workflow so the later ML work starts from a proven control plane.

**Tech Stack:** Python 3 standard library, markdown frontmatter files, shell wrappers, git worktrees, optional `gh` CLI adapter, nested git repo under `external/`, Codex repo-local skills.

---

## Scope Check

This plan intentionally covers only the first executable slice from the approved campaign spec:

- included: readiness-gate runtime support, deterministic sync, generated-repo scaffolding updates, external campaign repo bootstrap, first end-to-end smoke task
- excluded: Qwen model loading, quantized baseline eval, PT2 export, Triton kernels, interpreter parity

Those ML-heavy items should be planned next only after this phase proves the harness mechanics are usable.

## File Structure

- Create: `harness_kit/review_results.py`
  - Runtime helpers for writing, loading, and validating task-scoped review-result receipts.
- Create: `harness_kit/finish_worktree.py`
  - Core local finish flow for `review -> done`, merge metadata, cleanup, and optional push state.
- Create: `harness_kit/publish_pr.py`
  - Optional GitHub publication adapter for pre-finish PR creation/update.
- Create: `harness_kit/sync_project.py`
  - Deterministic source-to-generated sync logic plus provenance metadata updates.
- Modify: `harness_kit/cli.py`
  - Add `write-review-result`, `finish-worktree`, `publish-pr`, and `sync-project` subcommands.
- Modify: `harness_kit/review_pack.py`
  - Support deterministic task-scoped PR review-pack paths and registry-linked promotion behavior.
- Modify: `harness_kit/worktree.py`
  - Extend registry field coverage so finish/publish metadata can be persisted safely.
- Modify: `harness_kit/runtime_bundle.py`
  - Vendor new runtime modules into generated repos.
- Modify: `harness_kit/scaffold.py`
  - Create new runtime directories and call the same sync/provenance logic used by later resyncs.
- Modify: `.gitignore`
  - Ignore `/external/` so the nested campaign repo does not pollute source-repo status.
- Create: `install/sync-project.sh`
  - Thin source-repo wrapper around `python3 -m harness_kit.cli sync-project`.
- Create: `skills/merge-worktree/SKILL.md`
  - Repo-local worker guidance for review receipts, PR narration, finish, and optional publish.
- Create: `templates/project/scripts/harness/write-review-result.sh`
  - Generated wrapper for task-scoped review-result receipts.
- Create: `templates/project/scripts/harness/finish-worktree.sh`
  - Generated wrapper for local finish/merge.
- Create: `templates/project/scripts/harness/publish-pr.sh`
  - Generated wrapper for optional PR publication.
- Modify: `templates/project/README.md`
  - Mention new runtime commands and the generated-repo provenance file.
- Modify: `templates/project/SUMMARY.md`
  - Add readiness commands and campaign-relevant runtime map.
- Modify: `templates/project/REQUIREMENT.md`
  - Document optional `gh` dependency and vendored-runtime sync assumptions.
- Modify: `templates/project/AGENTS.md`
  - Mention review-result receipts and readiness-gate behavior.
- Modify: `templates/project/.harness/policies/review-stages.yaml`
  - Keep canonical result schema aligned with the new review-results runtime.
- Modify: `templates/project/.harness/templates/pr-pack.md`
  - Make task-linked PR review narratives explicit.
- Modify: `templates/project/.gitignore`
  - Keep runtime artifacts ignored while making their durable seed/replay mechanism explicit.
- Create: `tests/test_review_results.py`
  - Unit tests for receipt write/load/validation behavior.
- Create: `tests/test_finish_worktree.py`
  - Local git integration tests for finish preflight, merge, cleanup, and push failure handling.
- Create: `tests/test_publish_pr.py`
  - Adapter tests for `gh` availability/auth handling and deterministic registry updates.
- Create: `tests/test_sync_project.py`
  - Sync tests proving vendored runtime refresh updates metadata without mutating campaign-owned files.
- Modify: `tests/test_review_pack.py`
  - Cover task-linked PR review-pack naming and promotion semantics.
- Modify: `tests/test_worktree.py`
  - Cover extended registry fields used by finish/publish.
- Modify: `tests/test_scaffold.py`
  - Cover new CLI commands, wrappers, runtime directories, and provenance file generation.
- Create: `external/qwen-export-campaign/` via `./install/init-project.sh`
  - Nested generated repo used as the real phase-1 proving ground.
- Create: `external/qwen-export-campaign/third_party/harness-source.txt`
  - Durable provenance metadata for the latest source-to-generated sync.
- Create: `external/qwen-export-campaign/docs/experiments/harness/scorecard.md`
  - Durable feature scorecard for `keep / improve / remove`.
- Create: `external/qwen-export-campaign/docs/experiments/harness/gaps/DIRECTORY.md`
  - Durable home for harness-gap summaries.
- Create: `external/qwen-export-campaign/scripts/setup/seed-runtime-state.sh`
  - Durable script that recreates ignored runtime queue items and related runtime state deterministically.

## Task 1: Add Review-Result Receipts and Deterministic PR Review-Pack Paths

**Files:**
- Create: `harness_kit/review_results.py`
- Modify: `harness_kit/review_pack.py`
- Modify: `harness_kit/worktree.py`
- Modify: `harness_kit/cli.py`
- Modify: `harness_kit/runtime_bundle.py`
- Modify: `harness_kit/scaffold.py`
- Create: `templates/project/scripts/harness/write-review-result.sh`
- Create: `tests/test_review_results.py`
- Modify: `tests/test_review_pack.py`
- Modify: `tests/test_worktree.py`
- Modify: `tests/test_queue.py`
- Modify: `tests/test_scaffold.py`

- [ ] **Step 1: Write the failing receipt and task-linked review-pack tests**

```python
class ReviewResultsTest(unittest.TestCase):
    def test_write_and_load_review_result_round_trip(self) -> None:
        receipt = write_review_result(
            repo_root=repo,
            task_id="task-1",
            stage="spec_scope_review",
            verdict="APPROVED",
            blocking_issues=[],
            advisory_notes=["looks good"],
            evidence_refs=["docs/reviews/task-1.md"],
            next_action="finish",
        )
        self.assertEqual(receipt.name, "spec_scope_review.md")

    def test_validate_review_results_requires_all_stages_approved(self) -> None:
        with self.assertRaises(ValueError):
            validate_review_results(repo_root=repo, task_id="task-1", required_stages=["spec_scope_review"])
```

```python
def test_builds_task_scoped_runtime_pr_draft(self) -> None:
    pack = build_pr_review_pack(
        repo_root=repo,
        task_id="task-1",
        title="Queue state fix",
        changed_paths=["AGENTS.md"],
        verification_commands=["true"],
    )
    assert pack.name == "task-1-pr.md"

def test_task_scoped_pr_pack_updates_registry_paths(self) -> None:
    ...
```

- [ ] **Step 2: Run the targeted tests to verify they fail**

Run:

```bash
python3 -m unittest tests.test_review_results -v
python3 -m unittest tests.test_review_pack.ReviewPackTest -v
```

Expected:

- `ModuleNotFoundError` or `ImportError` for `harness_kit.review_results`
- failing assertions because PR packs are still title-slugged instead of task-scoped
- failing assertions because registry-linked narrative paths are not updated yet

- [ ] **Step 3: Implement the receipt module and validation helper**

Add `harness_kit/review_results.py` with a minimal API like:

```python
REVIEW_RESULTS_ROOT = Path(".harness/runtime/review-results")
REQUIRED_FIELDS = (
    "stage",
    "verdict",
    "blocking_issues",
    "advisory_notes",
    "evidence_refs",
    "next_action",
)

def write_review_result(... ) -> Path: ...
def load_review_result(... ) -> dict[str, Any]: ...
def validate_review_results(repo_root: Path, task_id: str, required_stages: list[str]) -> list[dict[str, Any]]: ...
```

Use the same frontmatter parsing/rendering helpers already in `harness_kit.queue`.

- [ ] **Step 4: Make PR review packs deterministic by task id**

Update `harness_kit.review_pack` so PR packs can be task-scoped:

```python
def build_pr_review_pack(..., task_id: str | None = None) -> Path:
    if task_id is not None:
        draft_name = f"{validate_phase1_task_id(task_id)}-pr.md"
    else:
        draft_name = f"pr-{_slugify_title(title)}.md"
```

Keep commit-pack behavior unchanged.

Also add deterministic registry linkage when a task id is supplied:

- `build-review-pack --type pr --task-id task-1` writes `draft_pr_review_pack`
- promotion with the same `task_id` writes `promoted_review_pack`
- later `finish-worktree` and `publish-pr` reuse those exact stored paths

- [ ] **Step 5: Wire CLI, generated wrapper, vendoring, and scaffold runtime roots**

Add:

- `write-review-result` subcommand in `harness_kit.cli`
- `build-review-pack --task-id` support in `harness_kit.cli`
- vendoring of `review_results.py` in `harness_kit.runtime_bundle`
- `.harness/runtime/review-results` creation in `harness_kit.scaffold`
- `templates/project/scripts/harness/write-review-result.sh`

Normalize legacy review stage ids in test fixtures from `spec_scope` / `rules_lint` to:

- `spec_scope_review`
- `rules_lint_review`
- `adversarial_regression_review`
- `human_review_pack_review`

Prefer a CLI surface like:

```bash
python3 -m harness_kit.cli write-review-result \
  --repo-root PATH \
  --task-id task-1 \
  --stage spec_scope_review \
  --verdict APPROVED \
  --next-action finish \
  --advisory-note "looks good" \
  --evidence-ref docs/reviews/task-1.md
```

- [ ] **Step 6: Re-run the targeted tests and the scaffold smoke test**

Run:

```bash
python3 -m unittest tests.test_review_results -v
python3 -m unittest tests.test_review_pack -v
python3 -m unittest tests.test_queue -v
python3 -m unittest tests.test_worktree -v
python3 -m unittest tests.test_scaffold.CliSmokeTest -v
```

Expected: PASS

- [ ] **Step 7: Commit**

Run:

```bash
git add harness_kit/review_results.py harness_kit/review_pack.py harness_kit/worktree.py harness_kit/cli.py harness_kit/runtime_bundle.py harness_kit/scaffold.py templates/project/scripts/harness/write-review-result.sh tests/test_review_results.py tests/test_review_pack.py tests/test_worktree.py tests/test_queue.py tests/test_scaffold.py
git commit -m "리뷰 결과 영수증과 태스크 리뷰팩 연동 추가"
```

## Task 2: Implement Local `finish-worktree` Core

**Files:**
- Create: `harness_kit/finish_worktree.py`
- Modify: `harness_kit/worktree.py`
- Modify: `harness_kit/cli.py`
- Modify: `harness_kit/runtime_bundle.py`
- Create: `templates/project/scripts/harness/finish-worktree.sh`
- Create: `tests/test_finish_worktree.py`
- Modify: `tests/test_worktree.py`
- Modify: `tests/test_scaffold.py`

- [ ] **Step 1: Write the failing finish-worktree tests**

```python
class FinishWorktreeTest(unittest.TestCase):
    def test_finish_worktree_moves_review_task_to_done(self) -> None:
        result = finish_worktree(
            repo_root=repo,
            task_id="task-1",
            target_branch="main",
            strategy="squash",
            push=False,
            cleanup="preserve",
        )
        self.assertEqual(result.queue_path.parent.name, "done")

    def test_finish_worktree_allows_deleted_registry_when_branch_exists(self) -> None:
        ...

    def test_finish_worktree_fails_when_required_review_result_missing(self) -> None:
        ...

    def test_finish_worktree_records_push_failure_without_reopening_queue(self) -> None:
        ...
```

- [ ] **Step 2: Run the new finish-worktree test file to confirm failure**

Run:

```bash
python3 -m unittest tests.test_finish_worktree -v
```

Expected: FAIL because `harness_kit.finish_worktree` and CLI wiring do not exist yet

- [ ] **Step 3: Extend worktree registry fields to support finalization metadata**

Update `harness_kit.worktree.WORKTREE_REGISTRY_FIELDS` to include at least:

- `target_branch`
- `merge_strategy`
- `merge_status`
- `merged_commit`
- `push_status`
- `push_remote`
- `draft_pr_review_pack`
- `promoted_review_pack`
- `finished_at`
- `finalization_notes`

Add a small helper that reads/writes the registry record without dropping unknown finish metadata.

- [ ] **Step 4: Implement the finish flow with strict preflight checks**

`harness_kit.finish_worktree` should:

- require queue state `review`
- accept registry status `preserved` or `deleted`
- validate required review-result receipts are all `APPROVED`
- validate every `docs_to_update` path appears in the source-branch diff
- resolve the task-linked PR review narrative
- merge using `squash` or `merge`
- record merge metadata and optional push outcome
- move queue `review -> done`
- finalize registry status to `finalized_preserved` or `finalized_removed`

Minimal shape:

```python
def finish_worktree(
    repo_root: Path,
    task_id: str,
    target_branch: str,
    strategy: str = "squash",
    push: bool = False,
    cleanup: str | None = None,
    promote_review_pack: Path | None = None,
    commit_title: str | None = None,
) -> FinishResult:
    ...
```

- [ ] **Step 5: Wire CLI, generated wrapper, and vendoring**

Add:

- `finish-worktree` subcommand in `harness_kit.cli`
- `finish_worktree.py` to `harness_kit.runtime_bundle`
- `templates/project/scripts/harness/finish-worktree.sh`

Use the CLI shape from the approved merge-worktree design:

```bash
python3 -m harness_kit.cli finish-worktree \
  --repo-root PATH \
  --task-id task-1 \
  --target-branch main \
  --strategy squash \
  --cleanup preserve
```

- [ ] **Step 6: Re-run targeted tests plus existing worktree coverage**

Run:

```bash
python3 -m unittest tests.test_finish_worktree -v
python3 -m unittest tests.test_worktree -v
python3 -m unittest tests.test_scaffold.InitScaffoldTest -v
```

Expected: PASS

- [ ] **Step 7: Commit**

Run:

```bash
git add harness_kit/finish_worktree.py harness_kit/worktree.py harness_kit/cli.py harness_kit/runtime_bundle.py templates/project/scripts/harness/finish-worktree.sh tests/test_finish_worktree.py tests/test_worktree.py tests/test_scaffold.py
git commit -m "워크트리 종료와 로컬 머지 흐름 추가"
```

## Task 3: Implement `publish-pr` Adapter

**Files:**
- Create: `harness_kit/publish_pr.py`
- Modify: `harness_kit/cli.py`
- Modify: `harness_kit/runtime_bundle.py`
- Create: `templates/project/scripts/harness/publish-pr.sh`
- Create: `tests/test_publish_pr.py`
- Modify: `tests/test_scaffold.py`

- [ ] **Step 1: Write the failing publish-pr tests**

```python
class PublishPrTest(unittest.TestCase):
    def test_publish_pr_fails_when_gh_missing(self) -> None:
        with self.assertRaises(RuntimeError):
            publish_pr(repo_root=repo, task_id="task-1", target_branch="main")

    def test_publish_pr_persists_target_branch_and_head_ref(self) -> None:
        result = publish_pr(..., update_if_exists=True)
        self.assertEqual(result.target_branch, "main")
        self.assertEqual(result.publish_head_ref, "origin/task-1")
```

Stub `gh` by prepending a temporary executable to `PATH`; do not depend on a real GitHub account in unit tests.

- [ ] **Step 2: Run the publish-pr tests and confirm failure**

Run:

```bash
python3 -m unittest tests.test_publish_pr -v
```

Expected: FAIL because `harness_kit.publish_pr` does not exist yet

- [ ] **Step 3: Implement the adapter with deterministic registry updates**

`harness_kit.publish_pr` should:

- require queue state `review`
- require non-finalized registry status
- persist `target_branch` on first use and enforce an exact match later
- choose `push_remote` from registry or default `origin`
- push the source branch when needed so a head ref exists
- resolve the PR body from the exact task-linked narrative source
- record `publish_head_ref`, `pr_number`, `pr_url`, `adapter_status`

Minimal shape:

```python
def publish_pr(
    repo_root: Path,
    task_id: str,
    target_branch: str,
    title: str | None = None,
    body_from_review_pack: Path | None = None,
    draft: bool = False,
    update_if_exists: bool = False,
) -> PublishResult:
    ...
```

- [ ] **Step 4: Wire CLI, wrapper, and vendoring**

Add:

- `publish-pr` subcommand in `harness_kit.cli`
- `publish_pr.py` in `harness_kit.runtime_bundle`
- `templates/project/scripts/harness/publish-pr.sh`

- [ ] **Step 5: Re-run adapter and scaffold tests**

Run:

```bash
python3 -m unittest tests.test_publish_pr -v
python3 -m unittest tests.test_scaffold.CliSmokeTest.test_help_lists_phase1_commands -v
```

Expected: PASS

- [ ] **Step 6: Commit**

Run:

```bash
git add harness_kit/publish_pr.py harness_kit/cli.py harness_kit/runtime_bundle.py templates/project/scripts/harness/publish-pr.sh tests/test_publish_pr.py tests/test_scaffold.py
git commit -m "풀리퀘스트 발행 어댑터 추가"
```

## Task 4: Implement Deterministic Source-to-Generated Sync and Provenance

**Files:**
- Create: `harness_kit/sync_project.py`
- Modify: `harness_kit/scaffold.py`
- Modify: `harness_kit/cli.py`
- Modify: `README.md`
- Modify: `SUMMARY.md`
- Modify: `REQUIREMENT.md`
- Modify: `.gitignore`
- Create: `install/sync-project.sh`
- Create: `tests/test_sync_project.py`
- Modify: `tests/test_scaffold.py`

- [ ] **Step 1: Write the failing sync tests**

```python
class SyncProjectTest(unittest.TestCase):
    def test_sync_project_writes_provenance_file(self) -> None:
        sync_project(source_root=source_repo, target_root=target_repo)
        provenance = target_repo / "third_party" / "harness-source.txt"
        self.assertIn("source_commit:", provenance.read_text(encoding="utf-8"))

    def test_sync_project_refreshes_vendored_runtime_without_touching_campaign_code(self) -> None:
        ...
```

- [ ] **Step 2: Run the sync tests and confirm failure**

Run:

```bash
python3 -m unittest tests.test_sync_project -v
```

Expected: FAIL because `harness_kit.sync_project` and provenance writes do not exist yet

- [ ] **Step 3: Implement a reusable sync engine and make `init` call it**

`harness_kit.sync_project` should:

- copy the runtime bundle declared by `harness_kit.runtime_bundle`
- copy generated wrapper scripts from `templates/project/scripts/harness/`
- copy source-owned `skills/`
- copy source-owned `.harness/policies/` and `.harness/templates/`
- update `third_party/harness-source.txt`
- preserve campaign-owned files outside the managed sync surface, especially top-level campaign docs, experiment docs, and source code

Use a provenance format like:

```text
source_remote: local
source_branch: qwen-export-campaign-plan
source_commit: <sha>
runtime_bundle_fileset: harness_kit/__init__.py,harness_kit/cli.py,...
synced_at: 2026-03-20T00:00:00Z
```

Refactor `harness_kit.scaffold.init_project` to call the same sync helper after template copy so `init` and later `sync-project` do not drift.

- [ ] **Step 4: Add CLI/install wrapper and source-repo docs**

Add:

- `sync-project` subcommand in `harness_kit.cli`
- `install/sync-project.sh`
- `/external/` to root `.gitignore`
- short command docs in `README.md`, `SUMMARY.md`, and `REQUIREMENT.md`

- [ ] **Step 5: Re-run sync and scaffold coverage**

Run:

```bash
python3 -m unittest tests.test_sync_project -v
python3 -m unittest tests.test_scaffold -v
```

Expected: PASS

- [ ] **Step 6: Commit**

Run:

```bash
git add harness_kit/sync_project.py harness_kit/scaffold.py harness_kit/cli.py README.md SUMMARY.md REQUIREMENT.md .gitignore install/sync-project.sh tests/test_sync_project.py tests/test_scaffold.py
git commit -m "생성 레포 동기화와 출처 메타데이터 추가"
```

## Task 5: Update Generated-Repo Docs and Add the Merge-Worktree Skill

**Files:**
- Modify: `templates/project/AGENTS.md`
- Modify: `templates/project/README.md`
- Modify: `templates/project/SUMMARY.md`
- Modify: `templates/project/REQUIREMENT.md`
- Modify: `templates/project/.harness/policies/review-stages.yaml`
- Modify: `templates/project/.harness/templates/pr-pack.md`
- Modify: `templates/project/.gitignore`
- Create: `skills/merge-worktree/SKILL.md`
- Modify: `tests/test_scaffold.py`

- [ ] **Step 1: Extend template-presence tests for the new wrappers and skill**

Add assertions for:

- `skills/merge-worktree/SKILL.md`
- `templates/project/scripts/harness/write-review-result.sh`
- `templates/project/scripts/harness/finish-worktree.sh`
- `templates/project/scripts/harness/publish-pr.sh`
- `third_party/harness-source.txt` after `init`

Keep the generated `.gitignore` expectation that `.harness/runtime/` remains ignored. This phase uses durable seed scripts and durable review docs, not committed runtime state.

- [ ] **Step 2: Run the updated scaffold test and confirm failure**

Run:

```bash
python3 -m unittest tests.test_scaffold.TemplatePresenceTest -v
python3 -m unittest tests.test_scaffold.InitScaffoldTest -v
```

Expected: FAIL because template docs and generated wrappers do not yet mention the new readiness surface

- [ ] **Step 3: Update generated-repo docs and the merge-worktree skill**

Template docs should clearly state:

- review-result receipts are required before `finish-worktree`
- `publish-pr` is optional and GitHub-specific
- `third_party/harness-source.txt` records the last source-to-generated sync
- generated repos should not treat vendored runtime files as hand-edited source of truth
- runtime queue items and review receipts are recreated by durable setup scripts rather than committed directly

`skills/merge-worktree/SKILL.md` should instruct workers to:

- verify approved review receipts exist
- ensure a task-linked PR review narrative exists
- optionally publish a PR while the task is still in `review`
- finish the task locally exactly once

- [ ] **Step 4: Re-run scaffold and command-help tests**

Run:

```bash
python3 -m unittest tests.test_scaffold -v
```

Expected: PASS

- [ ] **Step 5: Commit**

Run:

```bash
git add templates/project/AGENTS.md templates/project/README.md templates/project/SUMMARY.md templates/project/REQUIREMENT.md templates/project/.harness/policies/review-stages.yaml templates/project/.harness/templates/pr-pack.md templates/project/.gitignore skills/merge-worktree/SKILL.md tests/test_scaffold.py
git commit -m "생성 레포 문서와 머지 워크트리 스킬 보강"
```

## Task 6: Bootstrap the External Campaign Repo and Seed the First Real Queue Items

**Files:**
- Create: `external/qwen-export-campaign/` via scaffold command
- Create: `external/qwen-export-campaign/third_party/harness-source.txt`
- Create: `external/qwen-export-campaign/docs/experiments/harness/DIRECTORY.md`
- Create: `external/qwen-export-campaign/docs/experiments/harness/scorecard.md`
- Create: `external/qwen-export-campaign/docs/experiments/harness/gaps/DIRECTORY.md`
- Create: `external/qwen-export-campaign/docs/experiments/hardware/DIRECTORY.md`
- Create: `external/qwen-export-campaign/docs/experiments/export/DIRECTORY.md`
- Create: `external/qwen-export-campaign/docs/experiments/kernels/DIRECTORY.md`
- Create: `external/qwen-export-campaign/docs/experiments/eval/DIRECTORY.md`
- Create: `external/qwen-export-campaign/scripts/setup/DIRECTORY.md`
- Create: `external/qwen-export-campaign/scripts/setup/seed-runtime-state.sh`
- Create: `external/qwen-export-campaign/scripts/experiments/DIRECTORY.md`
- Create: `external/qwen-export-campaign/scripts/eval/DIRECTORY.md`
- Create: `external/qwen-export-campaign/src/baseline/DIRECTORY.md`
- Create: `external/qwen-export-campaign/src/export_pt2/DIRECTORY.md`
- Create: `external/qwen-export-campaign/src/kernels/DIRECTORY.md`
- Create: `external/qwen-export-campaign/src/interpreter/DIRECTORY.md`
- Create: `external/qwen-export-campaign/src/analysis/DIRECTORY.md`
- Create: `external/qwen-export-campaign/tests/DIRECTORY.md`
- Create: `external/qwen-export-campaign/tests/baseline/DIRECTORY.md`
- Create: `external/qwen-export-campaign/tests/export/DIRECTORY.md`
- Create: `external/qwen-export-campaign/tests/kernels/DIRECTORY.md`
- Create: `external/qwen-export-campaign/tests/integration/DIRECTORY.md`
- Create: `external/qwen-export-campaign/third_party/DIRECTORY.md`

- [ ] **Step 1: Initialize the nested campaign repo from the source repo**

Run:

```bash
./install/init-project.sh --target external/qwen-export-campaign --project-name qwen-export-campaign
```

Expected: the command prints the absolute target path and creates a harness-enabled generated repo

- [ ] **Step 2: Initialize the nested git repository and create the bootstrap commit**

Run:

```bash
git -C external/qwen-export-campaign init
if ! git -C external/qwen-export-campaign config user.name >/dev/null; then git -C external/qwen-export-campaign config user.name "Campaign Local User"; fi
if ! git -C external/qwen-export-campaign config user.email >/dev/null; then git -C external/qwen-export-campaign config user.email "campaign-local@example.com"; fi
git -C external/qwen-export-campaign add .
git -C external/qwen-export-campaign commit -m "캠페인 저장소 초기화"
```

Expected: PASS

- [ ] **Step 3: Author campaign-specific directories, docs, and the harness scorecard skeleton**

Use the repo-local `DIRECTORY.md` pattern everywhere. The scorecard should start with rows for:

- queue/task packet structure
- context packs
- worktree isolation
- directory memory refresh
- review-result receipts
- review packs
- finish/merge/publish flow
- campaign repo resync flow

- [ ] **Step 4: Write a durable runtime-seed script for the first five queue items**

Create `scripts/setup/seed-runtime-state.sh` so runtime queue items remain ignored but reproducible. It must recreate at least:

- `campaign-setup`
- `hardware-profile`
- `baseline-qwen`
- `dynamic-export`
- `triton-kernel-coverage`

The seed script must be idempotent and non-destructive:

- it may create missing runtime files
- it may refresh `ready` queue items that are absent
- it must not overwrite active `in_progress`, `review`, `blocked`, or `done` task files on rerun

Each generated queue file must include:

- `owned_paths`
- `required_reads`
- `docs_to_update`
- `verification_commands`
- `review_stages`
- `dependencies`

At minimum, the generated `campaign-setup.md` should own:

- `AGENTS.md`
- `SUMMARY.md`
- `REQUIREMENT.md`
- `docs/experiments/harness/`
- `scripts/setup/`

- [ ] **Step 5: Sync the generated repo once through the new deterministic command**

Run:

```bash
./install/sync-project.sh --target external/qwen-export-campaign
```

Expected:

- vendored runtime refreshed
- wrapper scripts refreshed
- source-owned policies/templates/skills refreshed
- `external/qwen-export-campaign/third_party/harness-source.txt` updated

- [ ] **Step 6: Seed runtime state and verify the queue files exist locally**

Run:

```bash
external/qwen-export-campaign/scripts/setup/seed-runtime-state.sh
find external/qwen-export-campaign/.harness/runtime/queue/ready -maxdepth 1 -type f | sort
git -C external/qwen-export-campaign status --short --ignored
git -C external/qwen-export-campaign check-ignore -v .harness/runtime/queue/ready/campaign-setup.md
```

Expected:

- five ready queue items exist in runtime
- runtime queue files are still ignored by git

- [ ] **Step 7: Commit the external bootstrap state**

Run:

```bash
git -C external/qwen-export-campaign add .
git -C external/qwen-export-campaign commit -m "캠페인 초기 태스크와 문서 골격 추가"
```

Expected: PASS

## Task 7: Run One End-to-End `campaign-setup` Smoke Task

**Files:**
- Modify: `external/qwen-export-campaign/AGENTS.md`
- Modify: `external/qwen-export-campaign/SUMMARY.md`
- Modify: `external/qwen-export-campaign/REQUIREMENT.md`
- Modify: `external/qwen-export-campaign/DIRECTORY.md`
- Modify: `external/qwen-export-campaign/docs/experiments/harness/scorecard.md`
- Create: `external/qwen-export-campaign/.harness/runtime/review-results/campaign-setup/spec_scope_review.md`
- Create: `external/qwen-export-campaign/.harness/runtime/review-results/campaign-setup/rules_lint_review.md`
- Create: `external/qwen-export-campaign/.harness/runtime/review-results/campaign-setup/adversarial_regression_review.md`
- Create: `external/qwen-export-campaign/.harness/runtime/review-results/campaign-setup/human_review_pack_review.md`
- Create: `external/qwen-export-campaign/docs/reviews/campaign-setup.md`

- [ ] **Step 1: Claim the first real queue item and open its worktree**

Run:

```bash
cd external/qwen-export-campaign
scripts/harness/claim-task.sh --task .harness/runtime/queue/ready/campaign-setup.md
scripts/harness/open-worktree.sh --task-id campaign-setup --branch campaign-setup --cleanup-policy preserve
```

Expected:

- queue item moves to `in_progress`
- `.harness/runtime/context-packs/campaign-setup.md` exists
- `.harness/runtime/worktree-registry/campaign-setup.md` exists

- [ ] **Step 2: Make a minimal but real campaign-setup change inside the worktree**

Update:

- root docs to mention the campaign purpose and readiness commands
- `docs/experiments/harness/scorecard.md` with initial feature rows

Then refresh directory memory as needed:

```bash
scripts/harness/refresh-memory.sh --changed-path AGENTS.md --changed-path docs/experiments/harness/scorecard.md
```

- [ ] **Step 3: Close the worker phase into `review`**

Run:

```bash
scripts/harness/close-worktree.sh --task-id campaign-setup --mode preserve --worker-status DONE
```

Expected: queue item moves to `.harness/runtime/queue/review/campaign-setup.md`

- [ ] **Step 4: Run the placeholder QA stages and write approved non-human review receipts**

Run the placeholder QA hooks first:

```bash
scripts/harness/run-qa.sh --stage rules-lint
scripts/harness/run-qa.sh --stage adversarial-regression
```

Treat these outputs as workflow-validation evidence only in this phase. Do not describe them as substantive lint or regression coverage yet.

Then write three review-result receipts like:

```bash
scripts/harness/write-review-result.sh \
  --task-id campaign-setup \
  --stage spec_scope_review \
  --verdict APPROVED \
  --next-action "ready to finish" \
  --evidence-ref docs/experiments/harness/scorecard.md
```

Repeat for:

- `rules_lint_review`
- `adversarial_regression_review`

- [ ] **Step 5: Build and promote the task-linked PR review narrative**

Run:

```bash
scripts/harness/build-review-pack.sh \
  --task-id campaign-setup \
  --type pr \
  --title "Campaign setup harness smoke" \
  --changed-path AGENTS.md \
  --changed-path docs/experiments/harness/scorecard.md \
  --verification-command "scripts/harness/claim-task.sh --task .harness/runtime/queue/ready/campaign-setup.md" \
  --verification-command "scripts/harness/open-worktree.sh --task-id campaign-setup --branch campaign-setup --cleanup-policy preserve" \
  --promote-to docs/reviews/campaign-setup.md
```

Expected: both runtime draft and durable review doc exist

- [ ] **Step 6: Record `human_review_pack_review` only after the narrative exists**

Run:

```bash
scripts/harness/write-review-result.sh \
  --task-id campaign-setup \
  --stage human_review_pack_review \
  --verdict APPROVED \
  --next-action "ready to finish" \
  --evidence-ref docs/reviews/campaign-setup.md
```

- [ ] **Step 7: Finish the task locally and verify the queue/registry result**

Run:

```bash
scripts/harness/finish-worktree.sh \
  --task-id campaign-setup \
  --target-branch master \
  --strategy squash \
  --cleanup preserve
```

If the nested repo uses `main` instead of `master`, use `main`; do not force the wrong branch name.

Expected:

- queue item moves to `.harness/runtime/queue/done/campaign-setup.md`
- registry status is finalized
- no review receipt is missing

- [ ] **Step 8: Verify source-repo and nested-repo state, then commit the durable smoke result**

Run:

```bash
git -C /home/sungjin/workspace/harness status --short
git -C external/qwen-export-campaign status --short
git -C external/qwen-export-campaign add .
git -C external/qwen-export-campaign commit -m "캠페인 셋업 스모크 태스크 완료"
```

Expected:

- source repo stays clean except for planned harness changes
- nested campaign repo records the durable docs for the first fully finished task
- runtime queue and receipt artifacts remain local-only and ignored

## Verification

Before handing execution off, run the full source-repo suite:

```bash
python3 -m unittest discover -s tests -v
```

And run these nested-repo smoke checks after Task 7:

```bash
git -C external/qwen-export-campaign status --short
find external/qwen-export-campaign/.harness/runtime/review-results -maxdepth 2 -type f | sort
find external/qwen-export-campaign/docs/reviews -maxdepth 1 -type f | sort
```

## Follow-On Plan Boundary

Do not begin the actual Qwen model/bootstrap/export/kernel work in this plan. Once Task 7 passes, write a new plan covering:

- `hardware-profile`
- `baseline-qwen`
- `dynamic-export`
- `export-parity`

That next plan should assume the readiness surface from this phase is already proven.
