# Review of `workflows.md`, and config v13 → v14

## First, a correction to my own earlier finding

In the v12 review I filed **F-01** claiming `simple` and `review_fix` were a defect
because their flows are byte-identical, and I changed `review_fix` to a QC-first
shape. `workflows.md` shows that was wrong on intent:

> Use for code-review/fix-bug work when the defect and expected behavior are already
> clear enough that separate BA analysis would duplicate context.

`review_fix` is deliberately the BA-skipped shape. I had inferred "review" meant "QC
reviews first" when it means "the work is a code review or a fix". **Reverted in
v14.**

The underlying observation still holds, though — two modes with one flow need
*something* distinguishing them, or Lead's choice between them is arbitrary. The right
resolution is not a different sequence but explicit differentiators, which v14 adds:
`entry_condition` and `qc_emphasis`. `simple` is entered on "requirement explicit and
confirmed"; `review_fix` on "defect and expected behavior already clear", with QC
weighted toward regression and missing-change-surface detection. Same shape, different
gates, and now a stated basis for picking.

Worth flagging the failure mode generally: I reasoned from the mode's *name* rather
than its stated entry condition. Naming an entry condition in the config, as v14 now
does for every mode, is what stops that.

---

## Four controls I did not have

### W-01 · The Lead authority boundary

The strongest thing in `workflows.md`, and I had nothing equivalent:

> Lead MUST NOT run tests, lint, typecheck, diff validation, code review, browser
> checks, API checks, or any other QC validation as a substitute for QC. […] That
> inspection is not a second QC pass and must not produce an independent Pass/Fail
> conclusion. No QC `worker_done` => no QC conclusion.

My v13 said Lead must not *write code*. That misses the actual failure mode. A
coordinator does not usually erode by implementing — it erodes by *checking*. Lead is
impatient, the dispatch is slow, running the suite takes four seconds, and now the pod
has an unrecorded verification by the role least equipped to be independent.

**Added:** `lead_authority_boundary`, with the forbidden list per owning phase (QC,
BA, Dev), the permitted inspection, and the two clauses that give it teeth —
`inspection_is_a_second_pass: false` and
`inspection_may_produce_an_independent_pass_fail: false`. Also written into
`orca-lead` as step 7 and into `orca-qc` as "your authority is exclusive", because QC
needs to know that reporting `blocked` is legitimate rather than a failure someone
else will quietly cover.

### W-02 · The wait loop, and two state machines

`coordinator_continuity` in v13 had `timeout_is_checkpoint_not_completion: true` as a
property. `workflows.md` has it as *mechanics*: blocking `check --wait`, process the
whole Delivery before acknowledging, inspect on timeout and re-enter the wait, no
rapid polling, no self-completion, reuse-or-release the terminal after acceptance.

Reviewing it exposed a conflation in my own v13: `return_envelope.status_values`
(`complete`/`partial`/`blocked`/`escalated`) describes whether the **work** is done,
while `ready`/`dispatched`/running/unsettled describes whether the **exchange** is
settled. I had only the first and was implicitly using it for both. A `partial` report
on a `terminal` dispatch is normal and coherent; collapsing the two is precisely how a
timeout gets read as a success.

**Added:** `dispatch_lifecycle` with `states`, `unsettled_states`, `events`,
`terminal_reached_only_by`, the full `wait_loop`, and
`on_worker_crash_or_no_worker_done`.

### W-03 · Resume as an ordered procedure

v13's `coordinator_continuity` states properties (`resume_inspects_existing_runs_first:
true`). Properties do not tell a reopened session what to do in what order, and the
order is the entire control — inspecting Runs *before* creating one is what prevents
duplicating a live workflow.

**Added:** `coordinator_resume` with the seven steps as an ordered list, the
takeover-flag caveat, and the two prohibitions (resume from conversation history,
duplicate an active Run).

### W-04 · Document status was another dangling reference

Exactly the defect class as the `p0` finding in the v12 review. `research_only` says
the development document must "remain Draft/Confirmed, never Implemented", and
`documentation.status_gate` is named for a status that is enumerated nowhere.

**Added:** `document_status` with three values, transition preconditions,
per-mode ceilings, and one rule that was implied but never stated —
`a_document_may_not_be_marked_implemented_by_the_role_that_authored_the_change`.

---

## Three smaller gaps

**W-05 · `defect_triage` (new mode).** A defect whose expected behaviour is *not* yet
established has nowhere to go. `review_fix` requires clarity you do not have;
`standard` sends BA to characterize the defect, which is QC's work — establishing what
the code actually does is quality validation, not requirement analysis. The new mode
runs QC first for characterization only (observed vs expected, evidence levels, no fix,
no test authoring), then Lead, Dev, QC. Lead may route to BA afterwards if "expected"
turns out to be a business decision.

**W-06 · `cross_branch_review` (new mode).** `workflows.md` describes it; the YAML
had only `separate_worktree_for_other_branch: true`. Without a named mode this runs as
`qc_only` with an ad hoc worktree and the "never checkout inside Primary" rule lives
only in prose.

**W-07 · The `simple` mode escape valve.** "Lead may persist the user's
already-confirmed requirement into `ba/requirement.md`, but must not invent or derive
new business rules in place of BA." This is the precise line between an efficiency and
a shadow BA, and it was missing. Now `workflow_modes.simple.ba_substitution`, with
`on_new_business_rule_needed: switch_to_standard_and_dispatch_ba`.

Also folded in: the `rework_loop` as a named construct with Lead's four-way
classification (technical fix / requirement gap / business decision / invalid),
`cleanup_policy.future_work_after_non_released_outcome_requires_fresh_worker`, and the
`research_only` / `qc_only` documentation rules.

---

## The duplication problem, solved mechanically

You identified it precisely: the token-optimized profile restates model defaults and
escalation staging that `agents-models.yaml` owns. Three files now describe the same
system, and a convention that says "don't duplicate" fails silently the first time
someone is in a hurry.

**`scripts/lint_config.py`** makes it fail loudly instead. Six checks:

| | Catches |
|---|---|
| C1 | model identifiers restated outside the YAML — including bare family names paired with an effort, e.g. `Terra` + `high`, which a naive grep misses |
| C2 | effort defaults restated in prose (`QC default … medium`) |
| C3 | workflow flows written out as `User -> Lead -> …` |
| C4 | dotted YAML references in prose that do not resolve |
| C5 | vocabulary used in prose but never defined in the YAML — the `p0` and `Draft` defect class, caught automatically from now on |
| C6 | YAML integrity: contiguous bands, every task type mapped to a defined mode, no undefined gate references, and **no specialist-to-specialist edge in any flow** (a mode that violates `communication.deny` by construction) |

Run against your original `workflows.md` it reports **8 errors** — the six model
restatements plus the QC effort default. It also caught one I had introduced myself in
`orca-change-control` ("qc effort high"), and a broken reference,
"budgets.by_profile.qc_dispatches" (missing the profile level), which needs a profile name in the middle. Both
fixed; the resolver now supports `*` wildcards for that pattern.

Wire it into CI or a pre-commit hook. The revised `workflows.md` in this package passes
with `--strict`.

```bash
python scripts/lint_config.py --root . --strict
```

---

## What I did not adopt

- **The `.docs/features` two-file package as the only artifact set.** v14 keeps the
  expanded set (`qc/verification.md`, `decisions.jsonl`, `traceability.csv`) behind
  `documentation.files_by_band`, so XS tasks still produce one file. If your volume is
  mostly small tasks, verify that before enabling the full set.
- **Restating the wait-loop mechanics in every role skill.** Only Lead runs the wait
  loop; putting it in BA/Dev/QC would be the same duplication in a different file.
- **The prose flow diagrams.** They are readable, and they are C3 lint errors. The
  mode catalogue in the revised `workflows.md` describes entry conditions and gate
  emphasis instead, and points at `workflow_modes` for the sequence.

## One thing still worth deciding

`workflows.md` says QC "does not retry until success", and v13 added a narrow
`transient_reattempt` carve-out for declared flaky signatures. These are in tension by
design: the carve-out saves a Lead round trip on a port collision, at the cost of one
place where "retry" is permitted. It is guarded — one re-run, signature must match,
must be recorded, must be reported even when the second attempt passes — but if you
would rather keep the absolute rule, set
`qc_policy.testing.transient_reattempt.allowed: false` and nothing else changes.
