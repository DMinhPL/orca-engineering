# Changelog — `references/agents-models.yaml`

Version history for the config. Newest first.

`schema_version` changes when the structure changes in a way a consumer must handle.
`config_version` changes on any edit, structural or not. They were a single `version`
integer until v13, which is why a consumer could not tell a model-default tweak from a
new policy block.

Rationale for the v13 additions is in [`REVIEW.md`](REVIEW.md); for the v14 workflow
changes, [`REVIEW-workflows.md`](REVIEW-workflows.md).

Legend: `+` added · `~` changed · `-` removed

---

## v25 — project overlay is a directory of files, not one file

v24 shipped as a single `.orca/{role}.md` file. In practice a project has several
unrelated things to add to a role — one domain convention, one guardrail, one
style note — and forcing them into one file means every unrelated addition or
removal touches the same file, which is the merge-conflict and review-noise
problem the overlay was supposed to avoid.

- `~ project_overlay.directory_pattern` — `{project_root}/.orca/{role}.md` (a
  file) → `{project_root}/extra-skills/{role}/*.md` (a directory). Any number of
  markdown files, each independent, each an additional skill on its own topic.
  An empty or absent directory is still silently ignored — the common case is
  unchanged, only the shape of the uncommon case is.
- `+ project_overlay.precedence.on_conflict_between_overlay_files` — two overlay
  files disagreeing is now a real possibility once there can be more than one;
  it is reported to Lead to arbitrate, never resolved by filename order.
- `~ references/handoff-protocol.md`, `~ skills/orca-{lead,ba,dev,qc}/SKILL.md`,
  `~ SKILL.md` — updated for the directory/file-list shape.
- `~ examples/project-overlay/` — the single-file example split into
  `examples/extra-skills/dev/` with two files, demonstrating the intended use:
  one file per concern.

**Considered and rejected:** keeping the single file and telling projects to use
headings for separate concerns — that still forces one shared file for
unrelated additions, which is exactly what a directory of independent files
avoids at no extra cost.

---

## v24 — optional per-project overlay for each role

Every role's defaults live in this shared package, used across projects. There was
no way for one project to tailor a role — house conventions, an extra guardrail,
which engineering principle it cares about most — without editing the package
itself, which would leak into every other project using it.

- `+ project_overlay` — an optional, per-project markdown file at
  `{project_root}/.orca/{role}.md` for `lead`, `ba`, `dev`, `qc`. Lead detects
  presence once per task at classification (same rhythm as `knowledge_sources`)
  and states it in the dispatch envelope; a missing file is the expected default
  state, not a fallback worth logging. Additive/tightening only — it can name
  conventions, add checks, narrow an allowlist further, or point at project
  references, but it cannot loosen a prohibition, change a tier or gate, widen an
  allowlist, or override any other value in this file. On conflict with the
  default skill or this file, the default wins and the overlay is the bug — the
  same shape as the existing YAML-wins rule.
- `~ references/handoff-protocol.md` — dispatch envelope example gets an optional
  `project_overlay` field alongside `knowledge_sources`.
- `~ skills/orca-{lead,ba,dev,qc}/SKILL.md` — each gets a short "Project overlay"
  note: check for the file, read it after the default skill, apply it as an
  additional layer, never a substitute.

**Considered and rejected:** storing the overlay inside this package (e.g. a
`projects/{name}/` subtree) — that would require editing the shared package per
project and defeats the purpose; the whole point is that it lives with the
project it tailors and this package never needs to change for it to exist.

---

## v23 — engineering design principles for Dev

`execution_policy` said *how much* to build (scope-bounded, no broad scan) but never
said anything about the *shape* of the code once written — that was left implicit,
so it varied by whichever model happened to be dispatched.

- `+ agents.dev.engineering_principles` — DRY, KISS, YAGNI, Law of Demeter, Defensive
  Programming, Principle of Least Surprise, Separation of Concerns, Composition over
  Inheritance, Fail Fast. Heuristics, not gates: applied with judgment, deferring to
  the codebase's existing idiom, and never license to widen the allowlist or
  `scope_bounded`.
- `~ skills/orca-dev/SKILL.md` — new "Engineering principles" section under
  Execution policy.

**Considered and rejected:** a separate scored checklist (like `d1`–`d6` complexity
dimensions) for principle adherence, and a new QC checklist item for it — these are
Dev's own design judgment while writing, not measurable signals Lead can gate on or
QC can verify against.

---

## v22 — worktree pool reuse is mandatory, not just permitted

`primary_session_policy.worktree_reuse_allowed` already existed, but nothing forced
Lead to inventory the pool first — reuse was optional, so a fresh worktree got
created by default on most M2+ tasks even when a clean one already existed, and only
`cross_branch_review` had an explicit reuse-first procedure.

- `+ worktree_selection_policy` — mandatory pre-dispatch inventory (name, path,
  branch, tracking, commit, staged/unstaged/untracked) for every repo-backed BA/Dev/QC
  dispatch, not only `cross_branch_review`. Reuse-first by default
  (`create_new_worktree_while_reusable_candidate_exists: forbidden`), an explicit
  pool-empty procedure that asks the user for a name rather than inventing one, dirty-
  worktree and branch-occupancy safety rules, and confirmation that worktree reuse is
  never session reuse.
- `+ worktree_selection_policy.new_worktree_path_policy` — new worktrees are created
  as a sibling of the project root, never nested inside it (project at
  `/c/DM/Mine/Sources/second-thoughts` → new worktree at
  `/c/DM/Mine/Sources/{worktree_name}`).
- `+ workflows.md` §1.9 Worktree pool gate — the procedure; `cross_branch_review`
  updated to note it is the branch-B-specific case of this general gate rather than a
  separate mechanism.
- `+ glossary.md` — **Worktree** was used throughout the config but never defined.

**Considered and rejected:** a separate "workspace" vocabulary distinct from
"worktree," and a standalone `references/shared/` policy file outside the existing
flat `references/` layout. Both were proposed externally; both would have created a
second name and a second source of truth for something `primary_session_policy` and
`cross_branch_review` already governed. Extending the existing block keeps
`worktree` as the one term and the YAML as the one place its values live.

## v21 — specialists can challenge the band

Lead still owns CAS. What changes is that the pod no longer has to wait for a
mis-scoring to cause damage before hearing about it.

- `+ complexity_assessment.rescore_triggers.specialist_reports_band_materially_wrong_on_first_read`
  — the other four triggers all require the error to have already cost something: an
  allowlist overrun, a repeated failure, a blocked question. Lead scores from the
  request text before anyone has read the code; the specialist is the first to read it.
- `+ complexity_assessment.band_challenge` — how it is raised. Deliberately **evidence,
  not a vote**: the specialist whose tier, effort and gates the band determines does not
  get to set it. Raisable by BA, Dev and QC on first read, with observed band,
  dimensions moved, evidence and evidence level. Lead must re-score or record why not.
  A challenge reaching L/XL or matching a hard override implies G1 should have fired
  before that phase, so the worker stops rather than writing past an ungated gate;
  every other case continues under the granted tier, which is the conservative
  direction.
- `+ orchestration.return_envelope.optional_fields` — `band_challenge` is optional, not
  required. A field every worker must fill even when empty becomes noise, and noise is
  how a real challenge gets skimmed past.

**Considered and rejected:** having Dev participate in the initial CAS scoring. It is
circular — the band sets Dev's own model, effort and tier, so Dev would be dispatched
to decide how Dev should be dispatched — and `G1_scope_approval` fires `before_phase:
dev` precisely to put a human between scoping and Dev starting. An M0 scoping dispatch
would also add a cold-boot worker to every task including XS fast-path ones.

## v20 — provider rebalance

`schema_version: 3`

- `~ agents.ba` — `codex/gpt-5.5` → `claude/claude-sonnet-5`. The pod was 3:1 on codex
  (lead, ba, dev) against claude (qc alone), and qc is the role deliberately kept
  lightest by `context_mode: delta_only`. BA is the second-heaviest consumer and the
  only heavy role with no independence constraint. Now 2:2 by role.
  **This is a partial rebalance, not a fix** — Dev remains the dominant codex consumer
  by token weight. If codex is still the binding constraint, the next lever is reducing
  Dev's consumption, not moving Dev.
- `~ agents.ba.escalation.model_escalation` — preferred is now cross-family
  (`codex/gpt-5.6-terra`); the old alternative had become the default. Alternative is
  `claude-opus-5`. Cross-family escalation suits a hard architecture question and keeps
  BA working when one provider is down.
- `+ qc_policy.independence` — BA and QC now share a provider and model. Recorded as
  deliberate, with the reasoning and a `revisit_if` condition.

## v19 — dev routing, quota-first and evidence-based

- `~ agents.dev.escalation_chain` — 3 rungs → 5, and Codex-only.
  - `+ broader_capability` (terra @ medium) buys capability without also buying effort.
    Sibling of `scoped_deeper_reasoning` (luna @ high), not sequential — Lead picks by
    which deficit was observed.
  - `~ very_hard` is now sol @ xhigh; the chain previously plateaued at high.
  - `-` **Removed the `claude-sonnet-5` / `claude-opus-5` alternatives.** QC is always
    claude, so both collided with `qc_provider_must_differ_from_dev_provider` and
    tripped `on_independence_unavailable` → Dev capped at M1 (propose-only) at the
    hardest moment. They were dead options, not fallbacks.
- `+ agents.dev.escalation_policy` — carry findings across escalation. Dev→Dev only;
  never into a QC dispatch, which stays `delta_only`.
- `~ optimization.rules` — `escalate_effort_before_escalating_model` was unconditional.
  Now: diagnose the deficit first — effort for reasoning on a known scope, model for
  missing context or capability.
- `+ retrospective.batch.dev_model_distribution_target` — a measurable target.

**Not adopted** from the routing proposal: a separate `blast_radius` scale (duplicates
CAS d3 + `hard_overrides`; mapped instead via `escalation_chain.hard.minimum_rung_when`),
a `context_policy` block (already covered by `execution_policy` + `knowledge_sources`),
and the Fable/Claude tier mapping (collides with the QC provider split).

## v18 — BA escalation ladder

Followed from lowering `agents.ba.effort` high → medium.

- `~ agents.ba.escalation.effort` — xhigh → high. medium → xhigh skipped a rung and
  breached `one_escalation_level_per_trigger`. The ladder is now
  medium → high → model_escalation, which is also monotonic; the old path dropped
  effort from xhigh back to high at the model step. Note xhigh is no longer reachable
  for BA — model escalation covers that ceiling.
- `~ agents.ba.escalation.when` — `+ complexity_band_is_L_or_XL`. BA's other conditions
  all require a judgement call. This one is mechanical, mirroring `lead.escalation`, so
  band L/XL cannot silently run at medium.

## v17 — knowledge sources

- `+ knowledge_sources` — GitNexus (code graph) and Knowns (project memory) as
  availability-gated context providers, with per-role access, a precedence order, and a
  freshness rule that stops a stale index from being cited as confirmed evidence.
- `~ qc_policy.allowed_context` — targeted queries admitted. A graph query is not a
  `full_repository_scan`, but Knowns is restricted for QC because it can carry Dev's
  reasoning.
- `~ optimization.rules` — prefer a targeted query over a broad scan.

## v16 — branch naming

- `~ modification_policy.branch_pattern` → `modification_policy.branch_naming` —
  `{category}/{slug}[-{ticket}]`, with the category derived from the task type rather
  than chosen freely.
  **Breaking** for anyone parsing `branch_pattern`: the branch no longer carries
  `{task_id}`; commit messages still do, via `[TASK-####]`.

## v15 — progressive complexity scoring

- `+ complexity_assessment.triage` — d2/d3/d7 first, full seven only when the triple is
  non-zero. Additive and backward compatible: set `enabled: false` to restore
  unconditional seven-dimension scoring.

## v14 — workflow modes, lifecycle, and authority

Reconstructed from inline `# v14` markers; this version was never recorded in the
config header. See [`REVIEW-workflows.md`](REVIEW-workflows.md) for the findings behind
it.

- `~ workflow_modes.review_fix` — flow reverted to Dev-first. v13 had changed it to
  QC-first, misreading the intent: `review_fix` is for defects whose expected behavior
  is *already* clear.
- `+ workflow_modes.defect_triage` — new. Previously an uncharacterized defect had to
  run `standard`, which puts BA on work QC owns.
- `+ workflow_modes.cross_branch_review` — new. `primary_session_policy` already
  required a separate worktree, but no mode named the flow.
- `+ workflow_modes.simple.ba_substitution` — the escape valve that stops Lead becoming
  a shadow BA.
- `+ engineering_policy.task_classification.mode_selection_within_type` — `review_fix`
  and `defect_triage` share the `bug` type; the entry condition decides.
- `+ document_status` — `documentation.status_gate` referenced "implemented" with no
  enumeration, the same defect class as the v13 `p0` reference.
- `+ dispatch_lifecycle` — distinct from the report status in `return_envelope`. A
  worker's report says whether the *work* is done; the dispatch state says whether the
  *exchange* is settled. Conflating them is how a timeout becomes a success.
- `+ lead_authority_boundary` — the strongest control in the pod, and the one most
  likely to erode, because doing it yourself is faster.
- `+ coordinator_resume` — `coordinator_continuity` stated properties; this states the
  order. A reopened Lead session that skips step 2 duplicates a live Run.
- `+ rework_loop` — the QC-fail cycle, named and budgeted.
- `+ cleanup_policy.future_work_after_non_released_outcome_requires_fresh_worker`

## v13 — governance layer

`schema_version: 2` — split from the single `version` integer, so a compatible edit is
distinguishable from a structural one. Full rationale in [`REVIEW.md`](REVIEW.md).

- `+ complexity_assessment` — sizing rubric driving profile and mode selection
- `+ modification_policy` — write-permission tiers, allowlist, protected paths
- `+ human_gates` — enumerated user-approval points
- `+ change_control` — classes, authority, propagation
- `+ traceability` — ID scheme and RTM obligation
- `+ defect_severity` — resolves the dangling `p0` reference in
  `documentation.status_gate`
- `+ evidence_policy` — binds `engineering_policy.evidence_levels` to where they apply
- `+ budgets` — measurable ceilings behind `optimization.objective`
- `~ workflow_modes` — `review_fix` differentiated from `simple`; type→mode defaults
- `~ agents.ba.escalation` — model escalation added alongside effort
- `~ documentation.files` — QC report, decision log, risk section

## v12 and earlier

Not recorded. v12 is the baseline reviewed in [`REVIEW.md`](REVIEW.md), which enumerates
its gaps as findings F-01 through F-15.
