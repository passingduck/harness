# Qwen Export Campaign Design

## Goal

Validate the harness boilerplate on a real, high-friction ML systems campaign rather than a toy repo. The campaign must exercise queue orchestration, worktree isolation, review gates, directory memory, review narratives, and merge/publish flow while attempting a concrete technical goal:

- run `Qwen/Qwen3.5-9B` on a real `RTX 4070 Ti SUPER 16GB`
- export a dynamic-prompt-length PT2 graph with static cache and dynamic `SymInt`
- compare `WikiText2` perplexity against a baseline and keep relative delta within `3%`
- replace exported `ATen` coverage with Triton kernels where feasible
- run an interpreter path over the exported PT2 using those custom kernels
- compare baseline/export/custom-kernel perplexity again

The primary success condition is not merely model execution. It is proving which harness features help, which require improvement, and which should be removed when applied to a difficult real-world workflow.

## Problem

Phase 1 of `harness-kit` proves queue, worktree, memory refresh, and review-pack scaffolding in controlled tests, but it has not yet been pressure-tested on:

- GPU-bound experiments
- heavy external dependencies
- model export workflows with dynamic shapes
- repeated review loops driven by real failures such as OOM, export graph instability, or parity regressions
- end-to-end branch finishing and publication under actual project churn

Without a real campaign, the harness risks optimizing for synthetic cleanliness rather than useful operational behavior.

## Design Summary

Use a `hybrid campaign` design with two repositories:

- `harness/` remains the source repo for boilerplate, runtime, and skill improvements
- `external/qwen-export-campaign/` is initialized from the harness boilerplate and becomes the real proving ground

The campaign repo will use the harness runtime and markdown contracts as intended:

- task queue drives execution
- worktrees isolate meaningful changes
- `DIRECTORY.md` files accumulate domain-local knowledge
- review-result receipts gate `review -> done`
- review narratives summarize each meaningful step for humans
- merge/publish flow is used for campaign closeout rather than simulated

The campaign is decomposed into staged tasks so harness failures and ML failures can be distinguished cleanly.

## Scope

### Included

- create a real harness-enabled campaign repo under `external/`
- model the campaign as queue-driven work rather than ad-hoc scripts
- dynamic prompt length coverage across multiple export cases
- weight-only quantization as an allowed memory strategy
- Triton as the allowed custom kernel mechanism
- `WikiText2` perplexity parity checks
- explicit hardware-aware documentation for `RTX 4070 Ti SUPER 16GB`
- closeout review documenting `keep`, `improve`, and `remove` recommendations for the harness

### Excluded

- guaranteeing full success of every ML subgoal in the first implementation pass
- non-Triton custom CUDA extension work as a required first implementation path
- multi-GPU or distributed execution
- production serving or packaging beyond campaign validation needs

## Campaign Architecture

### Repository Split

- `harness/`
  - owns boilerplate, runtime, tests, skills, and any improvements discovered during the campaign
- `external/qwen-export-campaign/`
  - owns the actual model/export/kernel/eval work
  - is initialized from `harness-kit` and operated through queue/worktree/review flows

### Validation Layers

The campaign validates three layers at once.

1. `ML correctness`
   - baseline Qwen inference must run under the real hardware constraint
   - PT2 export with static cache and dynamic `SymInt` must succeed for multiple prompt-length cases
   - exported inference must preserve `WikiText2` perplexity within the agreed threshold
2. `Kernel/backend correctness`
   - exported `ATen` coverage is inventoried
   - Triton replacements are added incrementally
   - an interpreter path dispatches to those kernels
   - perplexity is rechecked against the same baseline
3. `Harness correctness`
   - queue, context packs, worktree lifecycle, review receipts, memory refresh, review packs, and closeout flow are all exercised on a nontrivial project
   - discovered harness friction is promoted into explicit improvement or removal decisions

## Repository Structure

The campaign repo keeps the phase-1 boilerplate shape and adds campaign-specific directories.

```text
external/qwen-export-campaign/
  AGENTS.md
  README.md
  SUMMARY.md
  REQUIREMENT.md
  DIRECTORY.md

  docs/
    specs/
    plans/
    reviews/
    experiments/
      DIRECTORY.md
      hardware/
        DIRECTORY.md
      harness/
        DIRECTORY.md
        scorecard.md
        gaps/
          DIRECTORY.md
      export/
        DIRECTORY.md
      kernels/
        DIRECTORY.md
      eval/
        DIRECTORY.md

  .harness/
    policies/
    templates/
    runtime/
      queue/
      context-packs/
      review-results/
      review-packs/
      worktree-registry/
      evidence/
      harness-gaps/

  scripts/
    harness/
    setup/
      DIRECTORY.md
    experiments/
      DIRECTORY.md
    eval/
      DIRECTORY.md

  src/
    baseline/
      DIRECTORY.md
    export_pt2/
      DIRECTORY.md
    kernels/
      DIRECTORY.md
    interpreter/
      DIRECTORY.md
    analysis/
      DIRECTORY.md

  tests/
    DIRECTORY.md
    baseline/
      DIRECTORY.md
    export/
      DIRECTORY.md
    kernels/
      DIRECTORY.md
    integration/
      DIRECTORY.md

  third_party/
    DIRECTORY.md
```

### Directory-Memory Intent

- root docs capture campaign-wide operating rules and environment requirements
- `docs/experiments/harness/*` captures harness feature scoring, friction records, and closeout evidence
- `docs/experiments/*/DIRECTORY.md` files capture hardware, export, kernel, and evaluation decisions
- `src/*/DIRECTORY.md` files capture implementation-local domain knowledge and gotchas
- `tests/*/DIRECTORY.md` files capture verification intent and residual risk

This structure is intentionally knowledge-dense. The campaign is meant to test whether directory-local memory stays useful under real churn.

## Campaign Readiness Gate

The campaign must not be judged as a harness-usability experiment until the minimum runtime surface it depends on actually exists in `harness/`.

Required readiness capabilities in the source repo:

- review-result receipt write/read/validation support
- `finish-worktree`
- `publish-pr`
- a deterministic generated-repo resync path for vendored runtime and template updates

This creates two phases:

1. `campaign bootstrap`
   - land the missing harness capabilities in `harness/`
   - verify them in source-repo tests
2. `campaign execution`
   - initialize or resync `external/qwen-export-campaign/`
   - only now begin using the repo as the proving ground

Before readiness passes, failures are classified as harness implementation debt, not campaign evidence about harness usefulness.

## Synchronization Contract

Because the campaign repo vendors runtime files, the hybrid design needs an explicit source-to-generated sync rule.

### Source Of Truth

- `harness/` remains the only authoritative source for boilerplate, vendored runtime modules, and generated wrapper scripts
- `external/qwen-export-campaign/` must never hand-edit vendored runtime files as the long-term source of truth

### Campaign Repo Provenance

The campaign repo must record:

- the source harness git remote and branch
- the source harness commit SHA used for the latest sync
- the runtime bundle manifest version or file list used for vendoring

This provenance should live in a durable repo file such as `third_party/harness-source.txt` or an equivalent generated metadata file.

If `third_party/harness-source.txt` is used, it must record at least:

- `source_remote`
- `source_branch`
- `source_commit`
- `runtime_bundle_fileset`
- `synced_at`

### Required Sync Behavior

The first implementation plan for this campaign must define and then implement a deterministic resync command. That command must:

- copy the canonical vendored runtime files from `harness/`
- copy generated wrapper updates from `harness/`
- update provenance metadata in the campaign repo
- leave campaign-owned code and docs untouched unless they directly depend on generated template changes

Manual ad hoc copying is not an acceptable long-term sync method.

## Queue Decomposition

The campaign is broken into at least eight queue tasks.

1. `campaign-setup`
   - initialize the campaign repo
   - add bootstrap scripts and baseline docs
   - verify runtime roots and commands
2. `hardware-profile`
   - document the real `RTX 4070 Ti SUPER 16GB` constraints
   - record VRAM, cache, token-budget, and toolchain policy
3. `baseline-qwen`
   - create the baseline model-loading and inference path
   - run baseline `WikiText2` perplexity
4. `dynamic-export`
   - implement multi-export coverage for dynamic prompt lengths
   - produce PT2 artifacts with static cache and dynamic `SymInt`
   - extract `ATen` inventory
5. `export-parity`
   - run exported PT2 evaluation
   - compare perplexity to baseline
6. `triton-kernel-coverage`
   - classify exported `ATen` families
   - add Triton replacements and tests
7. `interpreter-parity`
   - run the interpreter path with custom-kernel dispatch
   - compare perplexity again
8. `campaign-closeout`
   - complete review narratives
   - evaluate harness usefulness
   - produce `keep / improve / remove` recommendations

### Parallelism Policy

Some work may run in parallel when dependencies allow it:

- `hardware-profile` can proceed alongside early baseline setup
- `ATen` inventory analysis can proceed alongside exported-eval runner setup
- Triton kernel work can split across independent operator families

Parallelism is desirable because it tests whether the harness can support multi-worktree, multi-review operation rather than only linear workflows.

## Queue Item Contract

The eight campaign tasks are not merely names. Every campaign queue item must use the normal harness contract fields so the campaign actually tests context-pack usefulness.

Each queue item must explicitly declare at least:

- `owned_paths`
- `required_reads`
- `docs_to_update`
- `verification_commands`
- `review_stages`
- `dependencies`

### Meaningful Task Definition

For this campaign, a `meaningful task` is a queue item that satisfies at least one of the following:

- changes code under `src/`, `tests/`, or `scripts/`
- changes durable docs under `docs/`
- creates or updates a durable experiment artifact used by later tasks
- changes a harness policy, runtime, or wrapper relied upon by the campaign

Micro-iterations inside one active worktree do not each require separate queue items. Review receipts and review narratives are required at queue-item granularity, not for every exploratory command.

### Exemplar Queue Contracts

At minimum, the follow-up implementation plan must define concrete queue-item fields for:

- `campaign-setup`
- `baseline-qwen`
- `dynamic-export`
- `triton-kernel-coverage`

The campaign is not allowed to proceed with only human-readable task names.

## Technical Constraints

### Hardware Constraint

The real device is `RTX 4070 Ti SUPER 16GB`.

The campaign must treat this as a hard design input rather than an afterthought. Documentation and task decisions must explicitly account for:

- limited VRAM budget
- CUDA/driver compatibility
- cache-size constraints
- prompt-length tradeoffs
- kernel launch overhead and memory residency

### Model and Precision Policy

- target model: `Qwen/Qwen3.5-9B`
- prompt length is dynamic and therefore export coverage must be multi-case, not single-shape only
- full precision only is rejected as unrealistic for this card
- `weight-only quantization` is allowed
- quantization policy must be documented in the campaign repo before parity claims are accepted

### Kernel Policy

- Triton is allowed and is the required first custom-kernel path
- non-Triton C++/CUDA extensions are not required for the first campaign pass
- custom-kernel work must be driven by exported `ATen` evidence, not speculative optimization

### Evaluation Policy

Use `WikiText2` as the shared perplexity comparison dataset across all three execution paths:

- baseline
- exported PT2
- interpreter with custom kernels

Passing threshold:

- relative perplexity delta must be `<= 3%`

If a path fails this gate, the failure is recorded and the queue loops rather than silently advancing.

## Harness Measurement Contract

The campaign must produce auditable, non-anecdotal conclusions about harness usefulness.

### Scorecard

The campaign repo must maintain a durable harness scorecard at:

- `docs/experiments/harness/scorecard.md`

Each evaluated harness feature must record:

- `feature`
- `tasks_used_by`
- `times_invoked`
- `review_loops_triggered`
- `blockers_or_friction_count`
- `operator_minutes_estimate`
- `time_cost_notes`
- `evidence_refs`
- `verdict`
- `verdict_reason`

Allowed verdicts:

- `keep`
- `improve`
- `remove`

### Minimum Feature Set To Score

At minimum, the scorecard must assess:

- queue/task packet structure
- context packs
- worktree isolation
- directory memory refresh
- review-result receipts
- review packs
- finish/merge/publish flow
- campaign repo resync flow

The campaign closeout is incomplete unless every feature in that set has a verdict supported by evidence references.

## Review Gate And Evidence Model

Each task must leave behind:

- a `ContextPack`
- evidence artifacts and command summaries
- review-result receipts
- a human-readable review narrative when the task meaningfully changes behavior or understanding

Review overhead must itself be measurable. Each queue item must record at least:

- number of review loops
- whether review found a real issue, false alarm, or no issue
- whether the review stage materially changed the next action

### Required Review Stages

Every meaningful task in the campaign uses the canonical stage family:

- `spec_scope_review`
- `rules_lint_review`
- `adversarial_regression_review`
- `human_review_pack_review`

The point of this campaign is to see whether these stages remain useful under difficult real work, not merely under toy examples.

### Evidence Requirements

GPU and export tasks must record more than ordinary test output. Evidence should include, when relevant:

- commands run
- key stdout/stderr summary
- artifact locations
- `nvidia-smi` snapshots or equivalent memory evidence
- perplexity measurements
- export coverage summaries
- unsupported-operator or failure diagnostics

## Failure Loop Policy

### ML Failures Are First-Class

The following are expected and must be treated as normal review outcomes rather than process corruption:

- export failure
- out-of-memory
- perplexity regression
- unsupported exported operator coverage
- interpreter mismatch

Queue transitions on such failures remain explicit:

- `review -> in_progress` when the same task needs repair
- `review -> ready` when more context or reframing is required
- `review -> blocked` when an external blocker prevents progress

### Harness Failures Are First-Class

If the harness itself causes friction, that is a valid campaign result. Examples:

- review artifacts are hard to link deterministically to tasks
- worktree finishing flow blocks practical experiment iteration
- `DIRECTORY.md` refresh creates excessive noise
- review stages are useful in theory but too expensive in practice

Such findings must be promoted into explicit `harness-gap` issues and, when appropriate, reflected back into the `harness/` repo through new specs, plans, or implementation work.

### Harness-Gap Storage Contract

Raw runtime evidence may remain ephemeral, but each harness-gap finding that informs a final `keep / improve / remove` verdict must have a durable summary.

Required storage:

- runtime detail: `.harness/runtime/harness-gaps/<gap-id>/`
- durable summary: `docs/experiments/harness/gaps/<gap-id>.md`

Each durable harness-gap summary must include:

- `gap_id`
- `feature_area`
- `triggering_task_ids`
- `symptom`
- `impact_on_workflow`
- `evidence_refs`
- `proposed_action`
- `status`

If a harness-gap leads to work in `harness/`, the summary must also link the corresponding spec, plan, branch, or commit.

### Removal Is Allowed

The campaign is not restricted to additive improvement. If a harness feature proves repeatedly unhelpful, it may be recommended for removal.

The final closeout must classify outcomes as:

- `keep`
- `improve`
- `remove`

## Expected Harness Gaps

Before implementation starts, the most likely gaps are:

1. `review-results` runtime support is still thin relative to the spec
2. `finish-worktree` and `publish-pr` are designed but not yet implemented
3. generated-repo resync does not yet have a canonical command
4. queue-item authoring for large campaigns is likely too manual
5. evidence ergonomics for GPU tasks are likely insufficient
6. directory-memory refresh may prove too noisy for ML-heavy repos
7. toolchain bootstrap for Torch/Transformers/Triton may need repo-local conventions that phase 1 does not yet encode

These are not reasons to delay the campaign. They are reasons to start it with an explicit expectation that harness iteration will occur alongside ML work.

## Acceptance Criteria

The campaign design is satisfactory when all of the following are true:

- readiness-gate dependencies are explicit, so campaign evidence is not confused with missing harness implementation
- the hybrid repo model includes a deterministic source-to-generated sync contract
- a real harness-enabled campaign repo can be initialized under `external/`
- the campaign repo records which harness source SHA/runtime bundle it is synced from
- the campaign repo structure supports directory-local knowledge growth
- the work is decomposed into queue tasks rather than treated as a single opaque effort
- queue items are required to use the full harness task contract rather than free-form names only
- dynamic prompt length coverage is a first-class export requirement
- `weight-only quantization` is allowed and documented
- Triton is the first custom-kernel path
- `WikiText2` perplexity parity threshold is fixed at `<= 3%`
- ML failures and harness failures both feed deterministic review loops
- harness usefulness is measured through a durable feature scorecard rather than anecdotal closeout text
- harness-gap findings have durable traceable summaries
- the final campaign closeout will produce `keep / improve / remove` recommendations for the harness
