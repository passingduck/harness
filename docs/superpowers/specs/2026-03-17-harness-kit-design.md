# Harness Kit Design

**Date:** 2026-03-17

**Goal:** Design a repo-native harness kit for Codex-centered, subagent-heavy software development that can also be adapted to Claude Code and GitHub Copilot CLI.

**Architecture:** The harness is markdown-first and repo-native. Canonical operating knowledge lives in `AGENTS.md`, `DIRECTORY.md`, specs, plans, promoted review narratives, and harness policy files. Live execution state is kept in a runtime layer that is not the long-term source of truth. Cross-agent support is handled with thin adapters generated from canonical files.

**Tech Stack:** Markdown, shell, minimal Python, Git worktrees, repo-local skills, Codex subagents, generated adapters for Claude Code and GitHub Copilot CLI.

---

## 1. Background

This design is driven by four operating assumptions:

1. In an agent-first workflow, the human bottleneck shifts from writing code to shaping context, constraints, review criteria, and evidence requirements.
2. Large language model workers perform better when they receive a small curated payload instead of full conversation history or broad repository spelunking.
3. Review should prioritize scope compliance, risk, and evidence over line-by-line style commentary.
4. The harness must work as a repo-native system first, with room for a future local daemon or richer control plane to read the same contracts.

The design also assumes:

- Codex is the primary execution environment.
- `gpt-5.4` is the default model for meaningful planning, implementation, and review.
- Documentation and prompt-like markdown should be written in English.
- Git commit messages should be written in Korean.
- Graph DB is explicitly out of scope for day 1.

## 2. Desired Outcomes

The harness kit should make the following default:

- Every meaningful task starts from a spec and plan.
- Every meaningful directory has a short memory document near the code.
- Subagents work from curated context packs rather than raw session history.
- Parallel work uses isolated worktrees with explicit ownership.
- PRs are gated on documentation refresh, rules/lint checks, adversarial regression checks, and a human-readable review pack.
- The canonical repository structure can be adapted to Codex, Claude Code, and Copilot CLI without splitting the real source of truth into three separate systems.

## 2.1 Implementation Target for This Planning Pass

The implementation plan that follows this spec is for building the `harness-kit` distribution repository in the current workspace.

This planning pass is **not** for:

- adopting the harness into a separate product repository
- implementing all future adapters
- shipping every end-state phase in one milestone

The harness-enabled project repo described later in this spec is a generated output of `harness-kit`, not a second independent implementation target for phase 1.

## 3. Scope and Non-Goals

### In Scope

- Canonical repository structure for a harness-enabled project
- Canonical documentation contract
- Queue, context, evidence, and review-pack formats
- Subagent orchestration concepts
- Model routing policy
- Cross-agent adapter strategy
- Git and PR gating policy

### Out of Scope

- Building a local daemon or dashboard in phase 1
- Designing a Graph DB schema
- Defining language-specific lint/test adapters in detail
- Implementing the harness in this document
- Supporting every coding agent identically without adapters

## 4. Design Principles

### 4.1 Repo-Native First

The repository itself is the control plane. The harness must remain understandable from files in git, not from hidden process state.

### 4.2 Markdown-First Source of Truth

Human-readable markdown is the primary memory layer. Machine-readable metadata may appear where needed for queue items or routing, but canonical operating knowledge stays in markdown.

### 4.3 Thin Metadata, Strong Bodies

Borrowing from strong skill-design patterns, metadata should stay small and discovery-oriented, while the body of each document carries the actual rules and workflow. Summaries should not replace the real document.

### 4.4 Curated Context, Not Session Dumps

Controllers prepare a small context packet per worker. Workers and reviewers should not be expected to reconstruct intent from full chat history.

### 4.5 Ordered Review Stages

“Did we build the requested thing?” must be separated from “Is it well built?” The harness extends this pattern with rules and adversarial regression gates.

### 4.6 Evidence Before Claims

No completion claim, QA pass, or PR readiness claim is valid without fresh verification evidence.

### 4.7 Cross-Agent Canonical Core

Canonical rules live once. Tool-specific instruction files, commands, hooks, and skill locations are generated adapters.

## 5. Canonical Architecture

The harness is composed of six primitives.

### 5.1 ContextPack

A curated packet assembled by the controller for a worker or reviewer.

Required fields:

- task text
- why this task exists
- owned paths
- required reads
- disallowed edits
- constraints
- verification commands
- expected report schema

### 5.2 ReviewStage

A typed gate in the lifecycle. Recommended standard stages:

1. Spec/scope review
2. Rules/lint review
3. Adversarial regression review
4. Human review pack review

Each stage returns a typed verdict and can trigger fix-and-rereview.

Required verdict enum:

- `APPROVED`
- `CHANGES_REQUIRED`
- `ESCALATE`

Required review result fields:

- `stage`
- `verdict`
- `blocking_issues`
- `advisory_notes`
- `evidence_refs`
- `next_action`

### 5.3 WorkerStatus

Workers report one of:

- `DONE`
- `DONE_WITH_CONCERNS`
- `NEEDS_CONTEXT`
- `BLOCKED`

This lets the controller respond mechanically instead of interpreting free-form prose.

### 5.4 EvidencePack

A compact record of commands, outputs, artifacts, and reviewer verdicts that justify a claim.

### 5.5 WorkspaceProvider

A lifecycle abstraction for isolated execution environments.

Required lifecycle:

- provision
- baseline verify
- attach
- cleanup or preserve

Phase 1 uses Git worktrees as the default provider.

### 5.6 ModelRoutingPolicy

A canonical mapping from role class to actual model name. This prevents accidental drift toward low-capability models for high-judgment roles.

## 6. Repository Structure

There are two related repositories in the ecosystem:

1. `harness-kit` distribution repo
2. a harness-enabled project repo

### 6.1 Harness Kit Distribution Repo

```text
harness-kit/
  README.md
  skills/
    orchestrate-queue/
    refresh-memory/
    lint-rules-qa/
    adversarial-regression/
    prepare-review-pack/
  templates/
    project/
      AGENTS.md
      README.md
      SUMMARY.md
      REQUIREMENT.md
      DIRECTORY.md
      .harness/
      docs/
      scripts/
  adapters/
    codex/
    claude/
    copilot/
  install/
    init-project.sh
    adopt-project.sh
    upgrade-project.sh
```

### 6.2 Harness-Enabled Project Repo

```text
project-repo/
  AGENTS.md
  README.md
  SUMMARY.md
  REQUIREMENT.md
  DIRECTORY.md

  docs/
    specs/
    plans/
    reviews/

  .harness/
    policies/
      model-routing.yaml
      review-stages.yaml
      qa-rules.md
      doc-update-policy.md
    templates/
      task.md
      context-pack.md
      evidence-pack.md
      commit-pack.md
      pr-pack.md
    runtime/
      queue/
        backlog/
        ready/
        in_progress/
        blocked/
        review/
        done/
      context-packs/
      evidence/
        raw/
      review-packs/
        drafts/
      agent-runs/
      worktree-registry/

  skills/
    orchestrate-queue/
    refresh-memory/
    lint-rules-qa/
    adversarial-regression/
    prepare-review-pack/

  scripts/
    harness/
      init.sh
      claim-task.sh
      open-worktree.sh
      close-worktree.sh
      refresh-memory.sh
      run-qa.sh
      build-review-pack.sh

  .worktrees/

  src/
    DIRECTORY.md
  tests/
    DIRECTORY.md
  infra/
    DIRECTORY.md
```

## 7. Canonical Document Contracts

### 7.1 `AGENTS.md`

`AGENTS.md` is the repo constitution. It must stay short and stable.

It should define:

- mission
- instruction priority
- required reads
- default workflow
- model routing default
- documentation gate
- QA gate
- worktree rule
- output convention

It should not hold deep directory knowledge or long operational history.

### 7.2 `DIRECTORY.md`

`DIRECTORY.md` is the standard directory-local memory file.

It should define:

- directory purpose
- owned paths
- public interfaces
- domain knowledge
- dependencies
- invariants and gotchas
- change checklist
- update triggers
- related docs

This is the main mechanism for keeping local context near the code while keeping the root prompt short.

### 7.3 `SUMMARY.md`

Repo-wide architecture and operations snapshot for humans and controllers.

### 7.4 `REQUIREMENT.md`

Environment constraints, versions, dependency constraints, and non-negotiable operating assumptions.

### 7.5 Specs, Plans, Reviews

- `docs/specs/` contains approved design docs
- `docs/plans/` contains approved implementation plans
- `docs/reviews/` contains durable promoted PR review narratives and change summaries worth keeping in git

## 8. Queue, Context, Evidence, and Review Formats

### 8.1 Queue Item

Queue items live under `.harness/runtime/queue/<state>/`.

They are markdown-first with machine-readable frontmatter.

Required metadata:

- `id`
- `title`
- `status`
- `priority`
- `owner_role`
- `model_hint`
- `worktree` (nullable until task claim time)
- `parent_spec`
- `parent_plan`
- `owned_paths`
- `required_reads`
- `docs_to_update`
- `verification_commands`
- `review_stages`
- `dependencies`

The body contains:

- task text
- acceptance criteria
- non-goals

### 8.2 Context Pack

Context packs live in `.harness/runtime/context-packs/`.

They must contain:

- verbatim task text
- short reason this task exists
- files to read first
- files not to edit
- constraints
- verification instructions
- expected report schema

### 8.3 Evidence Pack

Evidence packs live in `.harness/runtime/evidence/raw/` during execution.

Raw evidence is always runtime-only. If a task or PR needs durable retention, the controller promotes a markdown summary into `docs/reviews/`.

They must contain:

- claim being justified
- commands run
- exit codes
- key output
- files verified
- regression checks
- related artifacts
- reviewer notes

### 8.4 Review Pack

Human-facing review packs summarize:

- what changed
- why it changed
- intended scope
- major risks
- verification evidence
- documentation updates
- deferred questions

Draft review packs live in `.harness/runtime/review-packs/drafts/`.

There should be both commit-level and PR-level templates.

Retention policy:

- commit-level review packs are runtime-only and are not committed
- PR-level review packs are promoted into `docs/reviews/` only when the merged change materially alters behavior, interfaces, operations, or incident learnings

### 8.5 Artifact Matrix

The canonical storage model is:

| Artifact | Path | In Git? | Producer | Primary Consumer | Retention |
|----------|------|---------|----------|------------------|-----------|
| Queue item | `.harness/runtime/queue/<state>/<id>.md` | No | controller | controller, worker, reviewers | until branch finish |
| Context pack | `.harness/runtime/context-packs/<id>.md` | No | controller | worker, reviewers | until task completion |
| Raw evidence | `.harness/runtime/evidence/raw/<id>/` | No | worker, reviewers | controller | until branch finish |
| Draft review pack | `.harness/runtime/review-packs/drafts/<id>.md` | No | controller or review-pack builder | human reviewer, controller | until branch finish |
| Final review narrative | `docs/reviews/<id>.md` | Yes | controller promotion step | humans, future agents | durable when retention criteria are met |

There is no committed runtime evidence directory in phase 1. Durable evidence lives only as summarized narrative inside a promoted PR review document.

### 8.6 Queue State Machine

Queue item states are:

- `backlog`
- `ready`
- `in_progress`
- `review`
- `blocked`
- `done`

Allowed transitions:

- `backlog -> ready` when dependencies and prerequisites are satisfied
- `ready -> in_progress` when claimed; worktree may be assigned at this moment
- `in_progress -> review` when worker reports `DONE` or `DONE_WITH_CONCERNS`
- `in_progress -> blocked` when worker reports `BLOCKED`
- `in_progress -> ready` when worker reports `NEEDS_CONTEXT` and the controller enriches the task packet
- `review -> in_progress` when any required review stage returns changes required
- `review -> done` when all required review stages pass and required doc updates are complete
- `blocked -> ready` when the blocker is explicitly resolved

Reviewer verdicts are:

- `approved`
- `changes_required`
- `escalate`

Loop policy:

- same worker repairs `changes_required`
- each review stage may loop twice before automatic human escalation

## 9. Subagent and Prompt Architecture

The harness should borrow strong prompt architecture patterns from proven skill systems without copying tool-specific assumptions.

### 9.1 Controller/Worker Split

The controller:

- reads the spec and plan
- breaks work into queue items
- prepares context packs
- assigns ownership at queue creation time
- assigns worktrees when a task is claimed for isolated execution
- routes to the correct model
- dispatches the correct review stages

The worker:

- receives a curated task packet
- asks for clarification if needed
- implements within declared boundaries
- verifies changes
- reports using the typed status schema

The reviewer:

- receives requirements and concrete artifacts to inspect
- does not trust worker reports
- verifies independently
- returns a typed review result

### 9.2 Adversarial Review Framing

Reviewer prompts should explicitly distrust optimistic worker summaries and inspect the actual code, diff, or evidence. This pattern is especially important for:

- spec compliance
- rules/lint QA
- adversarial regression review
- final PR pack preparation

### 9.3 Repair Ownership

When a reviewer finds issues, the original worker should normally repair them. This keeps task context localized and preserves the controller’s orchestration role.

### 9.4 Retry and Escalation

The controller should react to typed statuses deterministically:

- `NEEDS_CONTEXT` -> add missing context and redispatch
- `BLOCKED` -> provide stronger context, route to a stronger model, split the task, or escalate
- review issues -> fix and rereview

The design should cap review loops and surface repeated disagreement to a human.

## 10. Model Routing Policy

The default policy is:

```yaml
default: gpt-5.4
planner: gpt-5.4
implementer: gpt-5.4
spec_reviewer: gpt-5.4
quality_reviewer: gpt-5.4
adversarial_regression_reviewer: gpt-5.4
inventory_only:
  model: gpt-5.1-codex-mini
  allowed_for:
    - shallow file inventory
    - grep-style indexing
```

Policy intent:

- Use `gpt-5.4` for all roles requiring judgment, architecture, verification, or adversarial review.
- Use smaller models only for narrow, low-risk indexing or inventory tasks.
- Do not let low-capability model defaults silently drive important work.

## 11. Workflow Lifecycle

The intended lifecycle is:

1. discover
2. spec
3. spec review
4. plan
5. plan review
6. queue creation
7. isolated execution
8. staged review
9. evidence assembly
10. human review
11. branch finishing

Recommended execution path:

1. Create or approve a spec.
2. Create an implementation plan.
3. Decompose the plan into queue items.
4. Claim a queue item and provision a worktree if the task needs isolated write access.
5. Generate the task-specific context pack.
6. Dispatch subagents against that context pack.
7. Run ordered review stages.
8. Update directory memory and repo summaries.
9. Assemble raw evidence and draft review packs in runtime directories.
10. Promote durable PR review summaries into `docs/reviews/` when retention criteria are met.
11. Present the result for human approval.

## 12. Git and Runtime Policy

### 12.1 Commit to Git

Keep these in git:

- `AGENTS.md`
- `README.md`
- `SUMMARY.md`
- `REQUIREMENT.md`
- repo and directory `DIRECTORY.md`
- `docs/specs/*`
- `docs/plans/*`
- `docs/reviews/*`
- `.harness/policies/*`
- `.harness/templates/*`
- `skills/*`
- `scripts/harness/*`
- durable generated adapters

### 12.2 Ignore from Git

Ignore these by default:

- `.harness/runtime/queue/*`
- `.harness/runtime/context-packs/*`
- `.harness/runtime/evidence/*`
- `.harness/runtime/review-packs/*`
- `.harness/runtime/agent-runs/*`
- `.harness/runtime/worktree-registry/*`
- `.worktrees/*`
- temporary logs and local artifacts

The rule is simple: persistent knowledge and reusable policy belong in git; volatile execution state does not.

## 13. PR Gate and Human Review Mode

No PR should be considered ready unless all of the following are true:

1. an active spec exists
2. an active plan exists
3. touched directories have updated `DIRECTORY.md` files if their local knowledge changed
4. rules/lint QA passed
5. adversarial regression test cases were generated and checked
6. a human-readable PR review pack exists

Human review is narrative-first, not diff-first.

The primary human inputs should be:

- why this change exists
- which boundaries it intentionally changed
- what risks remain
- how it was verified
- which docs were updated
- what was intentionally deferred

The reviewer may inspect the raw diff afterward, but the review pack is the default entry point.

## 14. Cross-Agent Adapter Strategy

The canonical source of truth is:

- `AGENTS.md`
- `DIRECTORY.md`
- specs, plans, and durable review docs
- `.harness/policies/*`
- `skills/*`

Tool-specific files are adapters generated from this core.

Adapter policy for phase 1:

- adapters are deterministically generated from canonical source files
- generated adapters are not manually edited
- upgrades regenerate adapters rather than trying to merge hand edits
- any future local overlay mechanism is explicitly out of scope for phase 1

### 14.1 Codex

Codex uses `AGENTS.md` as the canonical instruction entry point.

Skill loading should support:

- preferred: repo-local `skills/`
- fallback: linked installation into the Codex skill discovery path

### 14.2 Claude Code

Generate:

- `CLAUDE.md`
- `.claude/commands/*`
- `.claude/agents/*`

These are wrappers around canonical rules and roles, not new sources of truth.

### 14.3 GitHub Copilot CLI

Generate:

- `.github/copilot-instructions.md`
- `.github/instructions/**/*.instructions.md`
- `.github/skills/*`
- `.github/agents/*`
- `.github/hooks/*`

Again, these are adapters around the canonical operating model.

### 14.4 Minimum Mapping Rules

Future adapter generators must follow these minimum mappings:

- canonical `AGENTS.md` -> generated root instruction files such as `CLAUDE.md` and `.github/copilot-instructions.md`
- canonical `DIRECTORY.md` stays canonical and is not duplicated into tool-specific directory docs
- canonical `skills/*` -> copied or linked into tool-native skill locations without semantic rewrite
- canonical `.harness/policies/review-stages.yaml` -> generated reviewer wrappers, commands, or hooks as needed by each tool
- generated hooks may call only documented scripts under `scripts/harness/`

These mapping rules are enough to keep future adapter generation deterministic without forcing phase 1 to implement every adapter.

## 15. Packaging and Adoption Strategy

End-state `harness-kit` should support three modes:

- `init`: start a new repository from the harness scaffold
- `adopt`: inject the harness into an existing repository
- `upgrade`: sync new policies, templates, skills, and deterministically regenerated adapters into a repository already using the harness

This should behave like a versioned starter kit, not a one-time copy-paste boilerplate dump.

Planning pass 1 does not implement all three. It implements:

- `init` for new Codex-first repositories
- deterministic Codex adapter installation

`adopt`, `upgrade`, and non-Codex adapters are follow-on phases.

## 16. Phase 1 Deliverables

Phase 1 is explicitly limited to a Codex-first core:

- canonical project scaffold
- canonical document templates
- queue/context/evidence/review-pack contracts
- queue state machine
- model routing policy
- worktree policy
- Codex adapter
- `init` installer for new repositories
- first-pass core automation:
  - queue orchestration
  - memory refresh
  - review-pack assembly

Phase 2 extends the core with:

- Claude Code adapter
- Copilot CLI adapter
- `adopt` support for existing repositories
- `upgrade` support for deterministic adapter regeneration

Phase 3 extends the QA layer with:

- reusable `lint-rules-qa` skill packaging
- reusable `adversarial-regression` skill packaging
- language-specific lint/test adapter packs

## 17. Open Questions

These do not block planning but should be made explicit:

- What is the minimum cross-platform installer surface for Codex, Claude Code, and Copilot CLI?
- Which language-specific lint/test adapter packs should ship first?

## 18. Recommendation

Build phase 1 as a repo-native, markdown-first harness with canonical docs, generated adapters, worktree-based isolation, typed context and review contracts, and `gpt-5.4` as the default meaningful-work model.

Do not start with a daemon or Graph DB.

Design the file contracts so a future daemon can consume them without changing the canonical repository structure.

## 19. Sources

- OpenAI, “Harness engineering” and Codex-related guidance on `AGENTS.md` and repository-embedded skills
- Anthropic Claude Code documentation on project instructions, commands, agents, and skills
- GitHub Copilot CLI documentation on instructions, skills, agents, and hooks
- Local inspection of the installed `superpowers` skill library for prompt architecture, review loops, verification gates, and skill authoring patterns
