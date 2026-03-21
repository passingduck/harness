# Qwen Export Campaign Phase 2A Dual Baseline Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Realign the campaign around the approved multimodal spec delta by recording source-readiness provenance, splitting the stale baseline task into `baseline-contract-refresh` and `baseline-qwen-dual`, and proving a real `8bit` text+VL baseline in `external/qwen-export-campaign/`.

**Architecture:** Treat this as a harness-first phase. First make the queue/context/docs reflect reality, then run the dual baseline on top of that contract. Keep export out of scope here except for documenting that phase 2 export remains text decode only and must reuse the same text-lane quantization regime.

**Tech Stack:** Python 3, PyTorch, Transformers, Datasets, Accelerate, BitsAndBytes `8bit`, shell wrappers, markdown queue packets, git worktrees.

---

## Scope Check

This plan is intentionally narrower than the earlier phase-2 draft.

This plan supersedes `docs/superpowers/plans/2026-03-20-qwen-export-campaign-phase2-baseline-export.md` for active execution.

- included: source-readiness provenance, external queue/context reseed, `baseline-contract-refresh`, shared `8bit` loader, text-lane `WikiText2` baseline, VL `COCO captions` smoke baseline, review/finish flow for both tasks
- excluded: dynamic export implementation, PT2 parity execution, Triton kernels, interpreter path

This is a separate sub-project because the old `baseline-qwen` assumptions were invalidated by real workload evidence. Export and parity should resume only after this plan lands.

## File Structure

- Create: `docs/superpowers/plans/2026-03-21-qwen-export-campaign-phase2a-dual-baseline.md`
  - Durable source-repo plan for the realigned phase.
- Modify: `external/qwen-export-campaign/docs/specs/2026-03-20-qwen-export-campaign-design.md`
  - Mirror the approved source spec delta into the proving repo.
- Create: `external/qwen-export-campaign/docs/plans/2026-03-21-qwen-export-campaign-phase2a-dual-baseline.md`
  - Durable proving-repo mirror of this plan.
- Modify: `external/qwen-export-campaign/README.md`
  - Replace the stale single-lane baseline instructions with dual-baseline commands.
- Modify: `external/qwen-export-campaign/SUMMARY.md`
  - Show the new queue split and baseline artifacts.
- Modify: `external/qwen-export-campaign/REQUIREMENT.md`
  - Record `8bit`, text-lane parity regime, and fixed-size VL smoke contract.
- Modify: `external/qwen-export-campaign/scripts/setup/seed-runtime-state.sh`
  - Seed `source-readiness-*`, `baseline-contract-refresh`, and `baseline-qwen-dual`; retire the stale `baseline-qwen` packet deterministically.
- Modify: `external/qwen-export-campaign/docs/experiments/harness/scorecard.md`
  - Record contract invalidation, queue reseed behavior, and dual-baseline harness findings.
- Modify: `external/qwen-export-campaign/docs/experiments/eval/DIRECTORY.md`
  - Explain the split between text and VL baseline evidence.
- Create: `external/qwen-export-campaign/docs/experiments/eval/baseline-coco-vl-smoke.md`
  - Durable VL smoke report.
- Create: `external/qwen-export-campaign/third_party/coco-smoke-samples.json`
  - Fixed 5-sample manifest for reproducible VL smoke runs.
- Create: `external/qwen-export-campaign/src/baseline/loader.py`
  - Shared `8bit` model/config/tokenizer loading helpers for text and VL lanes.
- Modify: `external/qwen-export-campaign/src/baseline/config.py`
  - Add separate text/VL baseline settings and fixed-sample manifest paths.
- Modify: `external/qwen-export-campaign/src/baseline/wikitext2_eval.py`
  - Keep text eval helpers focused on the text lane.
- Create: `external/qwen-export-campaign/src/baseline/run_text_baseline.py`
  - Real text-lane baseline runner.
- Create: `external/qwen-export-campaign/src/baseline/run_vl_smoke.py`
  - Real VL smoke runner using the fixed COCO manifest.
- Create: `external/qwen-export-campaign/src/baseline/coco_smoke.py`
  - COCO sample manifest parsing and output-shape helpers.
- Create: `external/qwen-export-campaign/scripts/eval/run-baseline-wikitext2.sh`
  - Text baseline wrapper.
- Create: `external/qwen-export-campaign/scripts/eval/run-vl-coco-smoke.sh`
  - VL smoke wrapper.
- Create: `external/qwen-export-campaign/tests/baseline/test_loader.py`
  - Loader contract tests for text/VL classes and `8bit` policy.
- Modify: `external/qwen-export-campaign/tests/baseline/test_config.py`
  - Text/VL env-default tests and fixed-manifest path tests.
- Modify: `external/qwen-export-campaign/tests/baseline/test_wikitext2_eval.py`
  - Keep text-lane helper coverage aligned with the new runner.
- Create: `external/qwen-export-campaign/tests/baseline/test_coco_smoke.py`
  - Fixed 5-sample manifest parsing and artifact-shape tests.
- Create: `external/qwen-export-campaign/tests/baseline/test_run_text_baseline.py`
  - Text baseline payload and wrapper behavior tests.
- Create: `external/qwen-export-campaign/tests/baseline/test_run_vl_smoke.py`
  - VL smoke payload and acceptance tests.
- Modify: `external/qwen-export-campaign/src/baseline/DIRECTORY.md`
- Modify: `external/qwen-export-campaign/tests/baseline/DIRECTORY.md`

## Task 1: Reseed the Campaign Contract Around the Approved Spec

**Files:**
- Modify: `external/qwen-export-campaign/docs/specs/2026-03-20-qwen-export-campaign-design.md`
- Create: `external/qwen-export-campaign/docs/plans/2026-03-21-qwen-export-campaign-phase2a-dual-baseline.md`
- Modify: `external/qwen-export-campaign/README.md`
- Modify: `external/qwen-export-campaign/SUMMARY.md`
- Modify: `external/qwen-export-campaign/REQUIREMENT.md`
- Modify: `external/qwen-export-campaign/scripts/setup/seed-runtime-state.sh`
- Modify: `external/qwen-export-campaign/docs/experiments/harness/scorecard.md`
- Modify: `external/qwen-export-campaign/docs/experiments/eval/DIRECTORY.md`

- [ ] **Step 1: Mirror the approved source spec and this phase-2A plan into the external repo**

Copy the approved source spec into `external/qwen-export-campaign/docs/specs/2026-03-20-qwen-export-campaign-design.md` and write this plan to `external/qwen-export-campaign/docs/plans/2026-03-21-qwen-export-campaign-phase2a-dual-baseline.md`.

- [ ] **Step 2: Rewrite operator-facing docs for the new reality**

Update `README.md`, `SUMMARY.md`, `REQUIREMENT.md`, and `docs/experiments/eval/DIRECTORY.md` so they explicitly say:

- the checkpoint is treated as multimodal
- `8bit` is the default phase-2 proving regime
- text baseline is the canonical parity reference
- VL smoke is a fixed `5`-sample COCO artifact lane
- export is still text decode only and out of scope for this plan

- [ ] **Step 3: Reseed queue packets deterministically**

Update `scripts/setup/seed-runtime-state.sh` so reseeding does all of the following:

- materializes durable `done` packets for `source-readiness-bootstrap` and `source-readiness-verify`
- creates `ready` packets for `baseline-contract-refresh` and `baseline-qwen-dual`
- leaves `dynamic-export`, `export-parity`, and `triton-kernel-coverage` queued but not started
- moves any existing stale `baseline-qwen` packet to a blocked/stale form with a note that it was superseded by the split contract

- [ ] **Step 4: Record the harness reason for the reseed**

Update `docs/experiments/harness/scorecard.md` with a durable note that the old baseline packet was invalidated by real workload discovery and that queue reseeding itself is part of harness evidence.

- [ ] **Step 5: Verify the contract rewrite**

Run:

```bash
bash scripts/setup/seed-runtime-state.sh
find .harness/runtime/queue -maxdepth 2 -type f | sort
git status --short
```

Expected:

- `source-readiness-bootstrap` and `source-readiness-verify` are present as satisfied provenance
- `baseline-contract-refresh.md` and `baseline-qwen-dual.md` exist
- stale `baseline-qwen` no longer appears as the active task
- only the intentional doc/script files are tracked

- [ ] **Step 6: Commit**

```bash
git add README.md SUMMARY.md REQUIREMENT.md scripts/setup/seed-runtime-state.sh docs/specs/2026-03-20-qwen-export-campaign-design.md docs/plans/2026-03-21-qwen-export-campaign-phase2a-dual-baseline.md docs/experiments/harness/scorecard.md docs/experiments/eval/DIRECTORY.md
git commit -m "캠페인 2A 계약과 큐 재시드"
```

## Task 2: Execute `baseline-contract-refresh` Through the Harness

**Files:**
- Modify: `external/qwen-export-campaign/docs/experiments/eval/DIRECTORY.md`
- Modify: `external/qwen-export-campaign/docs/experiments/harness/scorecard.md`
- Modify: `external/qwen-export-campaign/README.md`
- Modify: `external/qwen-export-campaign/SUMMARY.md`
- Modify: `external/qwen-export-campaign/REQUIREMENT.md`
- Create: `external/qwen-export-campaign/docs/reviews/baseline-contract-refresh.md`

- [ ] **Step 1: Claim the queued task and open its worktree**

Run:

```bash
scripts/harness/claim-task.sh --task .harness/runtime/queue/ready/baseline-contract-refresh.md
scripts/harness/open-worktree.sh --task-id baseline-contract-refresh --branch baseline-contract-refresh --cleanup-policy preserve
```

Expected: a preserved worktree opens under `.worktrees/baseline-contract-refresh/`.

- [ ] **Step 2: Update the durable docs to match the new contract**

Inside the worktree, update the owned docs so they explicitly capture:

- `8bit` text baseline as the canonical parity regime
- fixed `5`-sample COCO VL smoke contract
- text decode only export scope
- the rule that workload success does not close a task while harness acceptance is still open

- [ ] **Step 3: Refresh directory memory and build a review narrative**

Run:

```bash
scripts/harness/refresh-memory.sh --changed-path README.md --changed-path SUMMARY.md --changed-path REQUIREMENT.md --changed-path docs/experiments/eval/DIRECTORY.md --changed-path docs/experiments/harness/scorecard.md
scripts/harness/build-review-pack.sh --task-id baseline-contract-refresh --promote-to docs/reviews/baseline-contract-refresh.md
```

Expected: the review pack explains why the old single-lane baseline contract was rejected.

- [ ] **Step 4: Run QA receipts and close the task**

Run the canonical review stages, write review receipts, and finish the worktree:

```bash
scripts/harness/run-qa.sh --stage rules-lint
scripts/harness/run-qa.sh --stage adversarial-regression
scripts/harness/write-review-result.sh --task-id baseline-contract-refresh --stage spec_scope_review --status passed --summary "Contract refresh matches approved spec"
scripts/harness/write-review-result.sh --task-id baseline-contract-refresh --stage rules_lint_review --status passed --summary "Docs and packets are coherent"
scripts/harness/write-review-result.sh --task-id baseline-contract-refresh --stage adversarial_regression_review --status passed --summary "Stale baseline assumptions are blocked"
scripts/harness/write-review-result.sh --task-id baseline-contract-refresh --stage human_review_pack_review --status passed --summary "Human-readable review narrative promoted"
scripts/harness/close-worktree.sh --task-id baseline-contract-refresh --mode preserve --worker-status DONE
scripts/harness/finish-worktree.sh --task-id baseline-contract-refresh --target-branch main --strategy squash --cleanup preserve
```

Expected: the task lands in `done/` and registry metadata records the preserved merge.

## Task 3: Implement the Shared `8bit` Loader and Text Baseline With TDD

**Files:**
- Modify: `external/qwen-export-campaign/src/baseline/config.py`
- Create: `external/qwen-export-campaign/src/baseline/loader.py`
- Modify: `external/qwen-export-campaign/src/baseline/wikitext2_eval.py`
- Create: `external/qwen-export-campaign/src/baseline/run_text_baseline.py`
- Create: `external/qwen-export-campaign/scripts/eval/run-baseline-wikitext2.sh`
- Create: `external/qwen-export-campaign/tests/baseline/test_loader.py`
- Modify: `external/qwen-export-campaign/tests/baseline/test_config.py`
- Modify: `external/qwen-export-campaign/tests/baseline/test_wikitext2_eval.py`
- Create: `external/qwen-export-campaign/tests/baseline/test_run_text_baseline.py`
- Modify: `external/qwen-export-campaign/docs/experiments/eval/baseline-wikitext2.md`
- Modify: `external/qwen-export-campaign/src/baseline/DIRECTORY.md`
- Modify: `external/qwen-export-campaign/tests/baseline/DIRECTORY.md`

- [ ] **Step 1: Write failing config and loader tests**

Add tests for:

```python
def test_text_baseline_defaults_to_8bit_single_regime() -> None: ...
def test_loader_builds_text_lane_with_text_config_and_8bit_policy() -> None: ...
def test_loader_rejects_mixed_regime_parity_request() -> None: ...
```

- [ ] **Step 2: Run the targeted tests to watch them fail**

Run:

```bash
python3 -m unittest discover -s tests/baseline -p 'test_config.py' -v
python3 -m unittest discover -s tests/baseline -p 'test_loader.py' -v
```

Expected: import or assertion failures for the missing loader behavior.

- [ ] **Step 3: Implement the minimal config and loader surface**

Implement:

- `config.py` for text/VL mode settings, output roots, and COCO manifest path
- `loader.py` for `Qwen3_5ForCausalLM` + `text_config` + `8bit` policy
- explicit rejection of mixed-regime parity requests

- [ ] **Step 4: Add failing text-runner tests**

Add tests for:

```python
def test_text_runner_writes_expected_metric_payload() -> None: ...
def test_text_wrapper_uses_run_text_baseline_entrypoint() -> None: ...
```

- [ ] **Step 5: Run the new text-runner tests to verify the red phase**

Run:

```bash
python3 -m unittest discover -s tests/baseline -p 'test_run_text_baseline.py' -v
```

Expected: failures for the missing runner and wrapper behavior.

- [ ] **Step 6: Implement the minimal text runner and wrapper**

Create `run_text_baseline.py` and `scripts/eval/run-baseline-wikitext2.sh` so they:

- load the text lane through `loader.py`
- evaluate `WikiText2`
- write a durable metric artifact
- update `docs/experiments/eval/baseline-wikitext2.md`

- [ ] **Step 7: Run the baseline unit suite**

Run:

```bash
python3 -m unittest discover -s tests/baseline -p 'test_*.py' -v
```

Expected: all baseline tests pass.

- [ ] **Step 8: Execute the real text baseline**

Run:

```bash
bash scripts/eval/run-baseline-wikitext2.sh
```

Expected:

- a durable text-baseline JSON artifact exists under `artifacts/`
- `docs/experiments/eval/baseline-wikitext2.md` records the real `8bit` run
- the run either succeeds or leaves explicit blocked-state evidence tied to the quantization regime

- [ ] **Step 9: Commit**

```bash
git add src/baseline/config.py src/baseline/loader.py src/baseline/wikitext2_eval.py src/baseline/run_text_baseline.py scripts/eval/run-baseline-wikitext2.sh tests/baseline/test_config.py tests/baseline/test_loader.py tests/baseline/test_wikitext2_eval.py tests/baseline/test_run_text_baseline.py docs/experiments/eval/baseline-wikitext2.md src/baseline/DIRECTORY.md tests/baseline/DIRECTORY.md
git commit -m "8비트 텍스트 베이스라인 로더 추가"
```

## Task 4: Add the Fixed-Sample COCO VL Smoke Lane With TDD

**Files:**
- Create: `external/qwen-export-campaign/third_party/coco-smoke-samples.json`
- Create: `external/qwen-export-campaign/src/baseline/coco_smoke.py`
- Create: `external/qwen-export-campaign/src/baseline/run_vl_smoke.py`
- Create: `external/qwen-export-campaign/scripts/eval/run-vl-coco-smoke.sh`
- Create: `external/qwen-export-campaign/tests/baseline/test_coco_smoke.py`
- Create: `external/qwen-export-campaign/tests/baseline/test_run_vl_smoke.py`
- Create: `external/qwen-export-campaign/docs/experiments/eval/baseline-coco-vl-smoke.md`
- Modify: `external/qwen-export-campaign/src/baseline/DIRECTORY.md`
- Modify: `external/qwen-export-campaign/tests/baseline/DIRECTORY.md`

- [ ] **Step 1: Write the failing VL smoke tests**

Add tests for:

```python
def test_coco_smoke_manifest_requires_exactly_five_samples() -> None: ...
def test_vl_smoke_payload_requires_non_empty_generated_caption() -> None: ...
def test_vl_wrapper_points_to_run_vl_smoke_entrypoint() -> None: ...
```

- [ ] **Step 2: Run the targeted VL tests to verify they fail**

Run:

```bash
python3 -m unittest discover -s tests/baseline -p 'test_coco_smoke.py' -v
python3 -m unittest discover -s tests/baseline -p 'test_run_vl_smoke.py' -v
```

Expected: missing module/function failures.

- [ ] **Step 3: Implement the fixed manifest and helpers**

Create the committed `5`-sample manifest plus helper code that:

- loads the exact sample ids
- materializes prompts deterministically
- validates non-empty generated captions
- writes a stable artifact payload per sample

- [ ] **Step 4: Implement the real VL smoke runner and wrapper**

Create `run_vl_smoke.py` and `run-vl-coco-smoke.sh` so they:

- load `Qwen3_5ForConditionalGeneration` through the shared `8bit` loader surface
- iterate over the fixed `5` samples
- write durable artifacts
- update `docs/experiments/eval/baseline-coco-vl-smoke.md`

- [ ] **Step 5: Run the baseline suite again**

Run:

```bash
python3 -m unittest discover -s tests/baseline -p 'test_*.py' -v
```

Expected: the new VL tests and the existing text tests all pass together.

- [ ] **Step 6: Execute the real VL smoke run**

Run:

```bash
bash scripts/eval/run-vl-coco-smoke.sh
```

Expected:

- exactly `5` durable sample artifacts are written
- each artifact has a non-empty caption
- `docs/experiments/eval/baseline-coco-vl-smoke.md` records the prompt/image/caption triplets

- [ ] **Step 7: Commit**

```bash
git add third_party/coco-smoke-samples.json src/baseline/coco_smoke.py src/baseline/run_vl_smoke.py scripts/eval/run-vl-coco-smoke.sh tests/baseline/test_coco_smoke.py tests/baseline/test_run_vl_smoke.py docs/experiments/eval/baseline-coco-vl-smoke.md src/baseline/DIRECTORY.md tests/baseline/DIRECTORY.md
git commit -m "큐웬 VL 스모크 레인 추가"
```

## Task 5: Execute `baseline-qwen-dual` Through the Harness

**Files:**
- Modify: `external/qwen-export-campaign/docs/experiments/harness/scorecard.md`
- Create: `external/qwen-export-campaign/docs/reviews/baseline-qwen-dual.md`
- Modify: `external/qwen-export-campaign/docs/experiments/eval/baseline-wikitext2.md`
- Modify: `external/qwen-export-campaign/docs/experiments/eval/baseline-coco-vl-smoke.md`

- [ ] **Step 1: Claim the queued task and open its worktree**

Run:

```bash
scripts/harness/claim-task.sh --task .harness/runtime/queue/ready/baseline-qwen-dual.md
scripts/harness/open-worktree.sh --task-id baseline-qwen-dual --branch baseline-qwen-dual --cleanup-policy preserve
```

- [ ] **Step 2: Run both real baseline wrappers inside the task worktree**

Run:

```bash
bash scripts/eval/run-baseline-wikitext2.sh
bash scripts/eval/run-vl-coco-smoke.sh
```

Expected: the task produces both text and VL durable artifacts or lands in an explicit blocked state with evidence.

- [ ] **Step 3: Update the harness scorecard from the task outcome**

Record:

- whether the dual-lane evidence format was sufficient
- whether the queue split reduced confusion versus the old `baseline-qwen`
- whether review receipts and review packs were still usable for a mixed ML/VL task

- [ ] **Step 4: Build review artifacts and finish the worktree**

Run:

```bash
scripts/harness/refresh-memory.sh --changed-path docs/experiments/eval/baseline-wikitext2.md --changed-path docs/experiments/eval/baseline-coco-vl-smoke.md --changed-path docs/experiments/harness/scorecard.md
scripts/harness/build-review-pack.sh --task-id baseline-qwen-dual --promote-to docs/reviews/baseline-qwen-dual.md
scripts/harness/run-qa.sh --stage rules-lint
scripts/harness/run-qa.sh --stage adversarial-regression
scripts/harness/write-review-result.sh --task-id baseline-qwen-dual --stage spec_scope_review --status passed --summary "Dual baseline matches approved phase-2A contract"
scripts/harness/write-review-result.sh --task-id baseline-qwen-dual --stage rules_lint_review --status passed --summary "Artifacts and docs are coherent"
scripts/harness/write-review-result.sh --task-id baseline-qwen-dual --stage adversarial_regression_review --status passed --summary "Text/VL acceptance recorded separately"
scripts/harness/write-review-result.sh --task-id baseline-qwen-dual --stage human_review_pack_review --status passed --summary "Review narrative promoted"
scripts/harness/close-worktree.sh --task-id baseline-qwen-dual --mode preserve --worker-status DONE
scripts/harness/finish-worktree.sh --task-id baseline-qwen-dual --target-branch main --strategy squash --cleanup preserve
```

Expected: both workload and harness acceptance are captured before the task transitions to `done`.

## Execution Handoff

After this plan lands, the next plan should cover `dynamic-export`, `export-parity`, and the single-regime text-lane export contract. Do not resume export work from the stale pre-split packets.
