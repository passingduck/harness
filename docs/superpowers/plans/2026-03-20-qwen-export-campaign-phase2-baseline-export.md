# Qwen Export Campaign Phase 2 Baseline and Export Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove the first real ML slice of the campaign in `external/qwen-export-campaign/`: hardware-aware setup, quantized baseline evaluation, dynamic `torch.export` with static cache and dynamic prompt-length coverage, and baseline-vs-export PPL comparison.

**Architecture:** Treat the campaign repo as the execution surface and keep the source `harness/` repo out of the hot path unless a harness gap is discovered. Split the ML work into a narrow decode/eval contract so hardware profiling, baseline runtime, export capture, and parity comparison each produce their own durable evidence and can fail independently. Keep large artifacts local-only under `artifacts/` while durable findings live in `docs/experiments/*` and updated `DIRECTORY.md` files.

**Tech Stack:** Python 3, PyTorch, Transformers, Datasets, Accelerate, BitsAndBytes for weight-only quantization, Triton allowed but not used yet, shell wrappers, markdown task packets, git worktrees.

---

## Scope Check

This phase covers only the first ML slice after readiness:

- included: external repo execution contract alignment, environment bootstrap, hardware profile capture, quantized baseline WikiText2 runner, dynamic export lane, exported ATen inventory, baseline-vs-export PPL comparison
- excluded: Triton kernel implementation, interpreter path, custom-kernel parity, PR publication as a required gate

Commands below assume the worker is operating inside the relevant worktree under `external/qwen-export-campaign/.worktrees/<task-id>`.

## File Structure

- Create: `external/qwen-export-campaign/requirements.txt`
  - Minimal dependency manifest for the baseline/export slice.
- Modify: `external/qwen-export-campaign/.gitignore`
  - Ignore `.venv/`, `artifacts/`, and other local-only ML outputs.
- Create: `external/qwen-export-campaign/docs/specs/2026-03-20-qwen-export-campaign-design.md`
  - Durable campaign-spec mirror referenced by queue items inside the proving repo.
- Create: `external/qwen-export-campaign/docs/plans/2026-03-20-qwen-export-campaign-phase2-baseline-export.md`
  - Durable campaign-plan mirror referenced by queue items inside the proving repo.
- Modify: `external/qwen-export-campaign/README.md`
  - Add phase-2 setup and execution commands.
- Modify: `external/qwen-export-campaign/SUMMARY.md`
  - Add the current baseline/export runtime map and artifact locations.
- Modify: `external/qwen-export-campaign/REQUIREMENT.md`
  - Record the environment, model-id contract, and artifact rules for this phase.
- Modify: `external/qwen-export-campaign/scripts/setup/seed-runtime-state.sh`
  - Point queue packets at real spec/plan docs and add the `export-parity` task packet.
- Create: `external/qwen-export-campaign/scripts/setup/bootstrap-env.sh`
  - Create `.venv`, install requirements, and print follow-up commands.
- Create: `external/qwen-export-campaign/scripts/experiments/profile-hardware.sh`
  - Real-machine hardware probe wrapper.
- Create: `external/qwen-export-campaign/scripts/eval/run-baseline-wikitext2.sh`
  - Baseline PPL wrapper.
- Create: `external/qwen-export-campaign/scripts/experiments/export-dynamic.sh`
  - Dynamic export + ATen inventory wrapper.
- Create: `external/qwen-export-campaign/scripts/eval/compare-ppl.sh`
  - Baseline vs export parity wrapper.
- Create: `external/qwen-export-campaign/src/__init__.py`
  - Enable `src.*` imports.
- Create: `external/qwen-export-campaign/src/analysis/__init__.py`
  - Analysis package marker.
- Create: `external/qwen-export-campaign/src/analysis/hardware_profile.py`
  - Probe, normalize, and persist the GPU/CUDA profile.
- Create: `external/qwen-export-campaign/src/analysis/ppl_report.py`
  - Compare baseline/export metrics and enforce the relative-delta contract.
- Create: `external/qwen-export-campaign/src/baseline/__init__.py`
  - Baseline package marker.
- Create: `external/qwen-export-campaign/src/baseline/config.py`
  - Typed baseline configuration from env/CLI defaults.
- Create: `external/qwen-export-campaign/src/baseline/wikitext2_eval.py`
  - Dataset windowing and perplexity aggregation helpers.
- Create: `external/qwen-export-campaign/src/baseline/run_baseline.py`
  - Quantized baseline runner that emits durable metric artifacts.
- Create: `external/qwen-export-campaign/src/export_pt2/__init__.py`
  - Export package marker.
- Create: `external/qwen-export-campaign/src/export_pt2/config.py`
  - Export-case definitions, prompt-length coverage, and artifact paths.
- Create: `external/qwen-export-campaign/src/export_pt2/export_decode.py`
  - Decode-step export entrypoint with static cache and dynamic prompt-length support.
- Create: `external/qwen-export-campaign/src/export_pt2/aten_inventory.py`
  - Extract and summarize exported ATen coverage.
- Create: `external/qwen-export-campaign/tests/baseline/test_hardware_profile.py`
  - Parser and serializer tests for the hardware probe.
- Create: `external/qwen-export-campaign/tests/baseline/test_config.py`
  - Baseline config defaults and quantization-policy tests.
- Create: `external/qwen-export-campaign/tests/baseline/test_wikitext2_eval.py`
  - Windowing and perplexity aggregation tests.
- Create: `external/qwen-export-campaign/tests/export/test_export_config.py`
  - Dynamic prompt-length case and artifact-path tests.
- Create: `external/qwen-export-campaign/tests/export/test_aten_inventory.py`
  - ATen inventory extraction tests using small synthetic FX/export graphs.
- Create: `external/qwen-export-campaign/tests/integration/test_ppl_report.py`
  - Relative-delta gate tests.
- Create: `external/qwen-export-campaign/docs/experiments/hardware/rtx-4070-ti-super.md`
  - Durable machine-specific hardware notes.
- Create: `external/qwen-export-campaign/docs/experiments/eval/baseline-wikitext2.md`
  - Durable baseline-run report.
- Create: `external/qwen-export-campaign/docs/experiments/export/dynamic-export.md`
  - Durable export-run report and ATen inventory summary.
- Create: `external/qwen-export-campaign/docs/experiments/eval/export-parity.md`
  - Durable baseline-vs-export parity report.
- Modify: `external/qwen-export-campaign/docs/experiments/hardware/DIRECTORY.md`
- Modify: `external/qwen-export-campaign/docs/experiments/eval/DIRECTORY.md`
- Modify: `external/qwen-export-campaign/docs/experiments/export/DIRECTORY.md`
- Modify: `external/qwen-export-campaign/src/baseline/DIRECTORY.md`
- Modify: `external/qwen-export-campaign/src/export_pt2/DIRECTORY.md`
- Modify: `external/qwen-export-campaign/src/analysis/DIRECTORY.md`
- Modify: `external/qwen-export-campaign/tests/baseline/DIRECTORY.md`
- Modify: `external/qwen-export-campaign/tests/export/DIRECTORY.md`
- Modify: `external/qwen-export-campaign/tests/integration/DIRECTORY.md`
- Modify: `external/qwen-export-campaign/docs/experiments/harness/scorecard.md`
  - Keep/improve/remove notes for the first real ML slice.

## Task 1: Align the External Repo Contract for Phase 2

**Files:**
- Create: `external/qwen-export-campaign/requirements.txt`
- Create: `external/qwen-export-campaign/docs/specs/2026-03-20-qwen-export-campaign-design.md`
- Create: `external/qwen-export-campaign/docs/plans/2026-03-20-qwen-export-campaign-phase2-baseline-export.md`
- Create: `external/qwen-export-campaign/scripts/setup/bootstrap-env.sh`
- Modify: `external/qwen-export-campaign/.gitignore`
- Modify: `external/qwen-export-campaign/README.md`
- Modify: `external/qwen-export-campaign/SUMMARY.md`
- Modify: `external/qwen-export-campaign/REQUIREMENT.md`
- Modify: `external/qwen-export-campaign/scripts/setup/seed-runtime-state.sh`
- Modify: `external/qwen-export-campaign/scripts/setup/DIRECTORY.md`
- Modify: `external/qwen-export-campaign/docs/experiments/harness/scorecard.md`

- [ ] **Step 1: Create the external durable spec/plan mirror and artifact policy**

Write the approved campaign spec and this phase-2 plan into the external repo, then update `seed-runtime-state.sh` so `parent_spec` and `parent_plan` reference those exact files instead of placeholders. Add a new ready-state packet for `export-parity` with owned paths under `src/analysis/`, `docs/experiments/eval/`, and `tests/integration/`.

- [ ] **Step 2: Add the environment bootstrap surface**

Create `requirements.txt` with the minimal phase-2 dependency set and `scripts/setup/bootstrap-env.sh` with a flow like:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Also update `.gitignore` to keep `.venv/` and `artifacts/` local-only.

- [ ] **Step 3: Refresh operator-facing docs**

Update `README.md`, `SUMMARY.md`, `REQUIREMENT.md`, and `scripts/setup/DIRECTORY.md` so they explain:

- how to bootstrap the environment
- where large local artifacts live
- which env vars define the model id and output roots
- that phase 2 still excludes Triton/interpreter work

- [ ] **Step 4: Verify the contract changes**

Run:

```bash
bash scripts/setup/bootstrap-env.sh
bash scripts/setup/seed-runtime-state.sh
git status --short
```

Expected:

- `.venv/` exists locally but stays ignored
- queue packets still exist for the current unfinished tasks
- `export-parity.md` appears in `ready/` if it was not already present
- no unexpected tracked files are produced outside the intentional doc/script changes

- [ ] **Step 5: Commit**

```bash
git add .gitignore README.md SUMMARY.md REQUIREMENT.md requirements.txt scripts/setup/bootstrap-env.sh scripts/setup/seed-runtime-state.sh scripts/setup/DIRECTORY.md docs/specs/2026-03-20-qwen-export-campaign-design.md docs/plans/2026-03-20-qwen-export-campaign-phase2-baseline-export.md docs/experiments/harness/scorecard.md
git commit -m "캠페인 2단계 실행 계약 정렬"
```

## Task 2: Capture the Real Hardware Profile and Budget

**Files:**
- Create: `external/qwen-export-campaign/src/analysis/__init__.py`
- Create: `external/qwen-export-campaign/src/analysis/hardware_profile.py`
- Create: `external/qwen-export-campaign/scripts/experiments/profile-hardware.sh`
- Create: `external/qwen-export-campaign/tests/baseline/test_hardware_profile.py`
- Create: `external/qwen-export-campaign/docs/experiments/hardware/rtx-4070-ti-super.md`
- Modify: `external/qwen-export-campaign/docs/experiments/hardware/DIRECTORY.md`
- Modify: `external/qwen-export-campaign/src/analysis/DIRECTORY.md`
- Modify: `external/qwen-export-campaign/tests/baseline/DIRECTORY.md`
- Modify: `external/qwen-export-campaign/docs/experiments/harness/scorecard.md`

- [ ] **Step 1: Write the failing hardware-profile tests**

Add tests for:

```python
def test_normalize_cuda_probe_emits_vram_and_compute_fields() -> None: ...
def test_missing_nvidia_smi_is_recorded_without_crashing() -> None: ...
def test_budget_summary_marks_weight_only_quantization_as_required() -> None: ...
```

- [ ] **Step 2: Run the targeted tests to verify they fail**

Run:

```bash
python3 -m unittest discover -s tests/baseline -p 'test_hardware_profile.py' -v
```

Expected: `ImportError` / failing assertions for the missing probe helpers.

- [ ] **Step 3: Implement the hardware probe and durable report writer**

Build `src/analysis/hardware_profile.py` so it:

- reads `torch.cuda.get_device_properties()` when available
- optionally shells out to `nvidia-smi --query-gpu=... --format=csv,noheader,nounits`
- normalizes a JSON-serializable summary
- writes a small machine-profile artifact under `artifacts/hardware/`
- derives a durable budget summary for cache length, prompt-length cases, and quantization policy

Keep the module resilient when CUDA tooling is partially unavailable.

- [ ] **Step 4: Add the real-machine wrapper and durable docs**

Create `scripts/experiments/profile-hardware.sh` to run the probe, save the local JSON artifact, and update `docs/experiments/hardware/rtx-4070-ti-super.md` with the actual machine findings plus explicit decisions for:

- baseline quantization mode
- export prompt-length case set
- max sequence/cache budget to try first

- [ ] **Step 5: Re-run tests and execute the probe**

Run:

```bash
python3 -m unittest discover -s tests/baseline -p 'test_hardware_profile.py' -v
bash scripts/experiments/profile-hardware.sh
```

Expected:

- unit tests PASS
- hardware artifact JSON exists under `artifacts/hardware/`
- `docs/experiments/hardware/rtx-4070-ti-super.md` contains measured values and chosen budgets

- [ ] **Step 6: Commit**

```bash
git add src/analysis/__init__.py src/analysis/hardware_profile.py scripts/experiments/profile-hardware.sh tests/baseline/test_hardware_profile.py docs/experiments/hardware/rtx-4070-ti-super.md docs/experiments/hardware/DIRECTORY.md src/analysis/DIRECTORY.md tests/baseline/DIRECTORY.md docs/experiments/harness/scorecard.md
git commit -m "하드웨어 프로파일과 예산 기록 추가"
```

## Task 3: Implement the Quantized Baseline WikiText2 Lane

**Files:**
- Create: `external/qwen-export-campaign/src/baseline/__init__.py`
- Create: `external/qwen-export-campaign/src/baseline/config.py`
- Create: `external/qwen-export-campaign/src/baseline/wikitext2_eval.py`
- Create: `external/qwen-export-campaign/src/baseline/run_baseline.py`
- Create: `external/qwen-export-campaign/scripts/eval/run-baseline-wikitext2.sh`
- Create: `external/qwen-export-campaign/tests/baseline/test_config.py`
- Create: `external/qwen-export-campaign/tests/baseline/test_wikitext2_eval.py`
- Create: `external/qwen-export-campaign/docs/experiments/eval/baseline-wikitext2.md`
- Modify: `external/qwen-export-campaign/docs/experiments/eval/DIRECTORY.md`
- Modify: `external/qwen-export-campaign/src/baseline/DIRECTORY.md`
- Modify: `external/qwen-export-campaign/tests/baseline/DIRECTORY.md`
- Modify: `external/qwen-export-campaign/docs/experiments/harness/scorecard.md`

- [ ] **Step 1: Write the failing baseline helper tests**

Add tests for:

```python
def test_baseline_config_defaults_to_weight_only_quantization() -> None: ...
def test_wikitext2_window_builder_preserves_stride_and_context_limit() -> None: ...
def test_ppl_aggregator_ignores_padding_tokens() -> None: ...
```

- [ ] **Step 2: Run the targeted tests to verify they fail**

Run:

```bash
python3 -m unittest discover -s tests/baseline -p 'test_*.py' -v
```

Expected: failing imports or missing-function failures.

- [ ] **Step 3: Implement the baseline config and evaluation helpers**

Build:

- `config.py` for `MODEL_ID`, quantization mode, context length, stride, and artifact roots
- `wikitext2_eval.py` for dataset loading, token-window building, and perplexity aggregation
- `run_baseline.py` for the real model run that writes local metric JSON under `artifacts/eval/`

Keep the actual model-id configurable through env so the repo does not hardcode a potentially moving upstream identifier.

- [ ] **Step 4: Add the baseline shell wrapper and durable report**

Create `scripts/eval/run-baseline-wikitext2.sh` that:

- activates `.venv`
- runs `python -m src.baseline.run_baseline`
- writes a local JSON artifact such as `artifacts/eval/baseline-wikitext2.json`
- updates `docs/experiments/eval/baseline-wikitext2.md` with the chosen model id, quantization mode, token-budget, and measured PPL

- [ ] **Step 5: Re-run tests and execute the baseline runner**

Run:

```bash
python3 -m unittest discover -s tests/baseline -p 'test_*.py' -v
bash scripts/eval/run-baseline-wikitext2.sh
```

Expected:

- targeted tests PASS
- baseline metric artifact exists under `artifacts/eval/`
- durable baseline report is updated
- scorecard records whether the baseline flow fit and completed on the target GPU

- [ ] **Step 6: Commit**

```bash
git add src/baseline/__init__.py src/baseline/config.py src/baseline/wikitext2_eval.py src/baseline/run_baseline.py scripts/eval/run-baseline-wikitext2.sh tests/baseline/test_config.py tests/baseline/test_wikitext2_eval.py docs/experiments/eval/baseline-wikitext2.md docs/experiments/eval/DIRECTORY.md src/baseline/DIRECTORY.md tests/baseline/DIRECTORY.md docs/experiments/harness/scorecard.md
git commit -m "큐웬 베이스라인 위키텍스트 평가 추가"
```

## Task 4: Implement Dynamic Export and ATen Inventory

**Files:**
- Create: `external/qwen-export-campaign/src/export_pt2/__init__.py`
- Create: `external/qwen-export-campaign/src/export_pt2/config.py`
- Create: `external/qwen-export-campaign/src/export_pt2/export_decode.py`
- Create: `external/qwen-export-campaign/src/export_pt2/aten_inventory.py`
- Create: `external/qwen-export-campaign/scripts/experiments/export-dynamic.sh`
- Create: `external/qwen-export-campaign/tests/export/test_export_config.py`
- Create: `external/qwen-export-campaign/tests/export/test_aten_inventory.py`
- Create: `external/qwen-export-campaign/docs/experiments/export/dynamic-export.md`
- Modify: `external/qwen-export-campaign/docs/experiments/export/DIRECTORY.md`
- Modify: `external/qwen-export-campaign/src/export_pt2/DIRECTORY.md`
- Modify: `external/qwen-export-campaign/tests/export/DIRECTORY.md`
- Modify: `external/qwen-export-campaign/docs/experiments/harness/scorecard.md`

- [ ] **Step 1: Write the failing export tests**

Add tests for:

```python
def test_export_cases_require_multiple_prompt_lengths() -> None: ...
def test_artifact_paths_are_namespaced_by_case_id() -> None: ...
def test_aten_inventory_summarizes_unique_ops_from_graph_module() -> None: ...
```

- [ ] **Step 2: Run the targeted tests to verify they fail**

Run:

```bash
python3 -m unittest discover -s tests/export -p 'test_*.py' -v
```

Expected: failing imports or assertions because the export helpers do not exist yet.

- [ ] **Step 3: Implement the export contract and ATen inventory helpers**

Build:

- `config.py` with a case list derived from the hardware budget doc, for example short/medium/long prompt buckets
- `export_decode.py` with a narrow decode-step wrapper that isolates the static-cache + dynamic prompt-length export path
- `aten_inventory.py` that emits both machine-readable JSON and a compact markdown table for docs

If quantized modules are not directly exportable, record the chosen adapter or dequantization strategy explicitly instead of hiding it.

- [ ] **Step 4: Add the dynamic-export wrapper and durable report**

Create `scripts/experiments/export-dynamic.sh` that:

- activates `.venv`
- runs the export across all configured prompt-length cases
- writes PT2 and inventory artifacts under `artifacts/export/`
- updates `docs/experiments/export/dynamic-export.md` with prompt-length coverage, success/failure by case, and the resulting ATen families

- [ ] **Step 5: Re-run tests and execute the export lane**

Run:

```bash
python3 -m unittest discover -s tests/export -p 'test_*.py' -v
bash scripts/experiments/export-dynamic.sh
```

Expected:

- targeted tests PASS
- export artifacts exist for each attempted prompt-length case
- ATen inventory JSON/markdown is generated
- durable export report records success cases, failures, and blockers without claiming parity yet

- [ ] **Step 6: Commit**

```bash
git add src/export_pt2/__init__.py src/export_pt2/config.py src/export_pt2/export_decode.py src/export_pt2/aten_inventory.py scripts/experiments/export-dynamic.sh tests/export/test_export_config.py tests/export/test_aten_inventory.py docs/experiments/export/dynamic-export.md docs/experiments/export/DIRECTORY.md src/export_pt2/DIRECTORY.md tests/export/DIRECTORY.md docs/experiments/harness/scorecard.md
git commit -m "동적 익스포트와 아텐 인벤토리 추가"
```

## Task 5: Compare Baseline vs Export PPL and Close the Phase

**Files:**
- Create: `external/qwen-export-campaign/src/analysis/ppl_report.py`
- Create: `external/qwen-export-campaign/scripts/eval/compare-ppl.sh`
- Create: `external/qwen-export-campaign/tests/integration/test_ppl_report.py`
- Create: `external/qwen-export-campaign/docs/experiments/eval/export-parity.md`
- Modify: `external/qwen-export-campaign/docs/experiments/eval/DIRECTORY.md`
- Modify: `external/qwen-export-campaign/tests/integration/DIRECTORY.md`
- Modify: `external/qwen-export-campaign/docs/experiments/harness/scorecard.md`

- [ ] **Step 1: Write the failing parity-report tests**

Add tests for:

```python
def test_relative_delta_passes_when_within_three_percent() -> None: ...
def test_relative_delta_fails_when_export_regresses_beyond_threshold() -> None: ...
def test_report_serialization_surfaces_missing_artifacts() -> None: ...
```

- [ ] **Step 2: Run the targeted tests to verify they fail**

Run:

```bash
python3 -m unittest discover -s tests/integration -p 'test_ppl_report.py' -v
```

Expected: missing module or missing helper failures.

- [ ] **Step 3: Implement the parity report helper**

Build `src/analysis/ppl_report.py` so it:

- reads the baseline and export metric JSON artifacts
- computes absolute and relative deltas
- enforces the agreed `<= 3%` relative threshold
- writes a small comparison artifact under `artifacts/eval/`

- [ ] **Step 4: Add the comparison wrapper and durable report**

Create `scripts/eval/compare-ppl.sh` that:

- activates `.venv`
- runs the report helper
- updates `docs/experiments/eval/export-parity.md`
- records whether the phase is green or blocked, plus the exact blocker if parity fails

- [ ] **Step 5: Re-run tests and execute the parity comparison**

Run:

```bash
python3 -m unittest discover -s tests/integration -p 'test_ppl_report.py' -v
bash scripts/eval/compare-ppl.sh
git status --short
```

Expected:

- targeted tests PASS
- parity artifact exists under `artifacts/eval/`
- durable parity report states either:
  - baseline/export delta is within `3%`, or
  - the exact failure mode and next corrective action
- only intended docs/code changes are tracked

- [ ] **Step 6: Refresh directory memory, review docs, and commit**

Update the touched `DIRECTORY.md` files plus `docs/experiments/harness/scorecard.md` so they capture:

- whether the baseline lane was practical
- whether the export lane was practical
- which parts of the harness helped or created friction during the first real ML slice

Then commit:

```bash
git add src/analysis/ppl_report.py scripts/eval/compare-ppl.sh tests/integration/test_ppl_report.py docs/experiments/eval/export-parity.md docs/experiments/eval/DIRECTORY.md tests/integration/DIRECTORY.md docs/experiments/harness/scorecard.md
git commit -m "베이스라인과 익스포트 퍼플렉서티 비교 추가"
```

## Verification

Before handing execution off, re-verify the source repo is still clean after writing this plan:

```bash
git status --short
git diff --check
```

During execution, each task should re-run its targeted tests plus the real shell command listed above. After Task 5, the proving repo should additionally pass:

```bash
find .harness/runtime/review-results -maxdepth 2 -type f | sort
find docs/experiments -maxdepth 3 -type f | sort
```

## Follow-On Plan Boundary

Do not implement Triton kernels or the interpreter path in this plan. Once Task 5 is complete, write the next plan for:

- `triton-kernel-coverage`
- interpreter dispatch
- custom-kernel parity
- harness closeout with `keep / improve / remove`
