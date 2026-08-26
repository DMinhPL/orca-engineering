# Review of `agents-models.yaml` v12, and what changed in v2

## Verdict first

Your config is more mature than the placeholder I shipped in v1, in four specific
ways that I have adopted rather than argued with:

1. **Provider-level independence beats a rule.** My v1 said "the reviewer must not be
   the implementer" and hoped agents would honour it. You made Dev = Codex and QC =
   Claude. Structural separation does not erode under time pressure; a rule does.
2. **`qc_policy.context_mode: delta_only` is stronger than anything I wrote.**
   Forbidding the Dev transcript prevents QC from writing tests shaped like the
   implementation. I had the *principle* of independent verification without the
   *mechanism* that enforces it. I have added `dev_implementation_reasoning` to the
   forbidden list to close the last gap.
3. **The communication allow/deny matrix.** My v1 had a RACI, which describes
   influence. Yours enumerates permitted edges, which is enforceable. Hub-and-spoke
   through Lead is what keeps each worker's context bounded and each report
   attributable.
4. **`substitution_policy.allow_silent_substitution: false`.** My v1 had fallback
   agents, which quietly trades reproducibility for availability. Stopping and
   reporting is correct. I removed my fallback chain.

Where v1 has something you do not, it is in exactly the areas you asked me about in
the first place: sizing, write permission, and change control.

---

## Findings

### F-01 · P1 · `simple` and `review_fix` have identical flows

Both are `lead → dev → lead → qc → lead → user`. Two names, one behaviour — verified
programmatically. A review-then-fix task should *open* with the review that
establishes the defect, not with an implementation.

**Changed:** `review_fix` is now `lead → qc → lead → dev → lead → qc → lead → user`,
with the first QC dispatch marked review-only, no test execution. The second verifies
the fix and the regression surface.

### F-02 · P1 · Dangling `p0` reference

`documentation.status_gate.implemented_requires_all_p0_pass: true` is the only
occurrence of "p0" in the file. No severity scale is defined anywhere, so Lead has
nothing to check the gate against and QC has nothing to classify by.

**Changed:** added `engineering_policy.defect_severity` with P0–P3 definitions and
`gate_rule`, and added `severity` to `qc_policy.testing.failure_report_fields`.

### F-03 · P1 · No mapping from task type to workflow mode

Ten task types, five modes, no stated default between them. Lead infers, which means
two Leads route the same bug differently.

**Changed:** `default_mode_by_type` for all ten, plus explicit
`mode_downgrade_allowed_when` / `mode_downgrade_forbidden_when`. The downgrade
guard matters most: a two-line change to an auth file is not a simple task, and
without that clause "requirement is explicit and confirmed" would let it become one.

### F-04 · P0 · No modification policy at all

Zero occurrences of allowlist, protected path, or rollback. Nothing in the config
constrains *which files* Dev may write, and `execution_policy.scope_bounded: true` is
a disposition rather than a boundary. This is the gap that lets a one-file fix become
an eleven-file refactor, and it is what you originally asked for.

**Changed:** added `modification_policy` — tiers M0–M4, `tier_selection` conditions,
`file_allowlist` (BA proposes, Lead grants, Dev may not exceed), `protected_paths`,
absolute `prohibitions`, branch rules, and a `rollback_note` obligation from M2.
Wired into `agents.dev.execution_policy` with
`on_needed_file_outside_allowlist: stop_and_raise_change_request`.

### F-05 · P1 · `requirement_traceability` has no artifact

It is listed as a QC responsibility, but nothing defines an ID scheme, a matrix, or
where it lives. QC cannot verify traceability against nothing.

**Changed:** `engineering_policy.traceability` with the ID schemes, a
`traceability.csv` required from band M, and the two obligations that make it useful
— every criterion has a test, every changed file traces to a requirement.

### F-06 · P1 · `evidence_levels` is unbound

Four levels enumerated, no statement of where they apply or what an unconfirmed claim
may not do. As written it is vocabulary, not policy.

**Changed:** `evidence_policy` binds them to BA root-cause and architecture claims,
Dev root-cause and compatibility claims, and QC defect attributions. Adds the teeth:
an unconfirmed claim may not justify a tier above M1, close a human gate, or satisfy
an acceptance criterion. A hypothesis must carry a verification step.

### F-07 · P2 · `escalate_to_user` has no enumerated conditions

Lead is told to escalate to the user, but the file never says when. In practice this
means either constant interruption or none.

**Changed:** `human_gates` G1–G6 with conditions and the phase each blocks, plus a
five-part request format. Blocking semantics are explicit: non-dependent analysis may
continue, the governed writes may not.

### F-08 · P2 · BA escalates effort but not model

BA owns `architecture_analysis` and `cross_system_change` is an escalation condition,
yet BA can only go from `high` to `xhigh` on `gpt-5.5` while Dev gets a three-model
staircase. If architecture analysis is genuinely the hard part, the effort knob alone
may not reach.

**Changed:** added `model_escalation` to BA (preferred `gpt-5.6-terra`, alternative
`claude-sonnet-5`, Lead selects and records) gated on architecture complexity,
cross-system change, and security boundary analysis. Same pattern added to QC for
security-critical releases and repeated root-cause disputes.

### F-09 · P2 · `optimization.objective` has no measurable ceiling

"Minimize token usage" with nothing to exceed. `same_material_failure_limit: 2` is
the only real guard, and it is per-failure rather than per-task.

**Changed:** `budgets` by profile — dispatch counts and escalation counts — with
`on_exhaustion: stop_and_report_to_user_via_lead`. Exhaustion produces a report
stating what was attempted, what was learned, the revised band, and the options.
Never a silent purchase of more compute.

### F-10 · P2 · No sizing input to `choose_complexity_profile`

Lead is told to choose a profile but given no rubric, so profile selection is
intuition. That is the same problem the modification policy has: a disposition where
a decision procedure is needed.

**Changed:** `complexity_assessment` — seven dimensions scored 0–3, bands XS–XL each
mapping to a `workflow_mode` and a `complexity_profile`, `hard_overrides` that
bypass the arithmetic, a `soft_override` for work that is voluminous but precedented,
and `rescore_triggers`. Scoring is explicitly required at default effort — sizing
must never be the expensive step.

### F-11 · P2 · QC's one-attempt rule is costly on flaky suites

`max_attempts_per_dispatch: 1` + `allow_transient_retry_without_lead: false` means a
port collision costs a full Lead round trip. The rule is *correct* — it surfaces
flakiness instead of hiding it — but the cost is real and it works against your token
objective.

**Changed:** a deliberately narrow `transient_reattempt` carve-out: one re-run, only
on a signature in `transient_failure_signatures`, must be recorded, and **must be
reported even if the second attempt passes**. The flakiness stays visible. This is
not a general retry licence and using it on a genuine failure defeats the rule.

### F-12 · P2 · QC can find a requirement gap and has nowhere to put it

`may_change_requirements: false` and `may_contact_ba_directly: false` are right, but
with no change-request path a requirement gap discovered in verification gets
reported as a defect. It then gets fixed as a bug, leaving the requirement wrong and
the traceability broken.

**Changed:** `may_raise_change_request_to_lead: true`, plus a `change_control` block
defining classes, authority, impact fields, dispositions, and a propagation
checklist.

### F-13 · P3 · No QC artifact and no decision log

`documentation.files` has BA and Dev outputs only. QC produces findings with nowhere
to persist them. Separately, the config demands a recorded reason in five places
(`escalate_with_recorded_reason`, `lead_selects_one_and_records_reason` ×3,
`silent_material_assumptions: false`) with no file to record into.

**Changed:** added `qc/verification.md`, `decisions.jsonl`, `traceability.csv`, plus
`files_by_band` so XS tasks still only get the decision log. `documentation
.decision_log` names the required events and line fields.

### F-14 · P3 · A cold worker cannot infer its contract

`primary_session_policy.fresh_supervised_worker_for_every_specialist_phase: true` is
the right design, but `orchestration.verification` only checks provider, model and
effort. Nothing verifies the worker was told what it may write or what "done" means.

**Changed:** `orchestration.dispatch_envelope` and `return_envelope` with required
fields, `reject_incomplete_envelope: true`, and a verification line for envelope
completeness.

### F-15 · P3 · `version: 12` conflates schema and content

Changing a model default and adding a policy block bump the same integer, so a
consumer cannot tell a compatible edit from a structural one.

**Changed:** `schema_version: 2`, `config_version: 13`.

---

## What I removed from my v1

Being direct about the redundancy, since it was substantial:

| v1 construct | Why it went |
|---|---|
| **9 roles** (Orca, Scout, Keel, Sonar, Fluke, Echo, Breach, Pod, Human) | Your 4 are the dispatchable units. Keel and Sonar are already BA responsibilities (`architecture_analysis`, `risk_analysis`); Breach is already QC (`risk_based_review`, `review_changed_behavior`); Pod is Dev's `development_document` plus your `documentation` block. Nine roles across four runtimes is nomenclature, not division of labour. |
| **8 phase-scoped skills** | Wrong shape for your architecture. A fresh worker boots cold and needs *its role contract*, not the whole lifecycle. Phase-scoped skills force every worker to read past the seven phases that are not theirs. |
| **Agent fallback chains** | Contradicts `allow_silent_substitution: false`. Yours is stricter and better for reproducibility. |
| **`.orca/work-items/` layout** | You already have `.docs/features/{date}_{slug}`. Two conventions is one too many. |
| **The `orca.config.yaml` I invented** | Superseded entirely. `agents-models.yaml` is the single source of truth; everything I added went into it in your style. |
| **Sea-mammal codenames** | They were fun and they were noise. Lead/BA/Dev/QC is what your config says and what your team will say. |

**Kept, because you asked for it and the config lacked it:** the CAS rubric, the M0–M4
tiers with allowlist and protected paths, the human gates, change control,
traceability, and the retrospective loop. All now expressed as YAML blocks rather
than prose in a skill file.

---

## On sub-skills per role — yes, and this is the structural change

You asked whether to add sub-skills for each role. Your architecture makes that the
*right* decomposition rather than an optional extra, for one reason:
`fresh_supervised_worker_for_every_specialist_phase: true`.

A worker that boots cold has no conversation history and no memory of the lifecycle.
What it needs is a self-contained contract for its own role: what it may read, what it
may write, when it escalates, what it must return. A phase-scoped skill makes it read
the whole workflow to find its part. A role-scoped skill *is* its part.

So v2 ships four role skills and two Lead-owned cross-cutting skills:

```
skills/
├── orca-lead/               dispatch procedure, arbitration, gates, escalation
├── orca-ba/                 requirements, AC, risk, blast radius, allowlist proposal
├── orca-dev/                implementation bounded by tier and allowlist
├── orca-qc/                 delta-only independent verification and review
├── orca-change-control/     Lead-owned, invoked from any phase
└── orca-closeout/           Lead-owned, status gate and retrospective
```

Two design rules held throughout:

- **Every skill defers to the YAML.** No provider, model, effort, threshold, path, or
  condition list is hardcoded in a skill file. Where a skill and the YAML disagree,
  the YAML wins and the skill is the bug. Each skill says so in its opening lines.
- **Each role skill is readable standalone.** A cold BA worker reads `orca-ba` and
  the YAML and needs nothing else. It does not need to know Dev's escalation chain.

I did **not** add skills for Keel/Sonar/Pod as separate roles. Splitting BA into
architect-and-risk would create two dispatches where your config has one, doubling
worker spin-up against your token objective for no separation-of-duties gain — BA
already owns both responsibilities and neither verifies the other.

---

## Migration

1. **Diff the YAML.** Every v13 addition is commented with `# v13` at the block or
   line. Nothing from v12 was removed except `version`, which split into
   `schema_version` / `config_version`.
2. **Set `protected_paths` for your repo first.** The defaults are generic. This is
   the single highest-value edit in the file.
3. **Decide on `transient_reattempt`.** If you would rather keep the absolute
   one-attempt rule, set `allowed: false` — the rest of `qc_policy` is unchanged.
4. **Adopt `complexity_assessment` in shadow mode for ~10 tasks.** Have Lead score and
   record, but keep choosing the mode as you do now. Compare. Then switch the band to
   drive `workflow_mode` once the bands match your judgement.
5. **`documentation.files_by_band`** keeps XS tasks at one file. If your current
   volume is mostly small tasks, verify that before turning on the full artifact set.

## Two things I would still question

- **`ba: skipped_when_allowed` in the simple profile.** Combined with the mode
  downgrade rule this is safe, but it puts a lot of weight on Lead correctly judging
  "explicit and confirmed". If your retrospectives show change requests clustering at
  QC on simple-mode tasks, that is the control failing, and the fix is to tighten the
  downgrade condition rather than to add BA back everywhere.
- **Lead runs `gpt-5.6-luna` at medium while BA runs `gpt-5.5` at high.** Lead makes
  the routing, tier, gate and escalation decisions — arguably the highest-leverage
  judgement in the pod — on the cheaper setting. The v13 escalation condition
  `complexity_band_is_L_or_XL` partly addresses this, but you may want Lead's default
  effort at high for tasks above band S regardless of the other conditions. Worth
  measuring rather than assuming.
