# Workflow Modes and Gates

The procedural rulebook: how a supervised task actually flows through
Lead → BA/Dev/QC. One layer below `SKILL.md`, one layer above the role skills.

**Parameter authority.** Every provider, model, effort, threshold, state name,
condition list and enumerated value in this document is defined in
`references/agents-models.yaml`. This file states *procedure and sequence*; the YAML
states *values*. Where they disagree, the YAML wins and this file is the bug.
`scripts/lint_config.py` enforces that mechanically — it fails if a model identifier,
an effort default, or a mode flow is restated here in prose.

---

# Part 1 — Gates that apply to every mode

Non-negotiable regardless of which mode is selected.

## 1.1 Primary coordinator-only gate

`primary_session_policy`. Primary coordinates only. Every BA/Dev/QC phase runs as a
**fresh supervised worker** started through Orca.

- Reusing a worktree does not authorize reusing Primary or an ordinary chat session
  as the worker. Worktree reuse and session reuse are separate permissions.
- If worker creation fails: stop, recover, report. Never fall back to direct
  specialist execution in Primary, and never to a generic subagent —
  `orchestration.forbidden_fallbacks` names the ones most likely to be reached for.
- For work or review on another branch, Primary stays on its branch and the target
  branch runs in a separate worktree. See mode `cross_branch_review`.

## 1.2 Coordinator resume / recovery gate

`coordinator_resume`. Applies when the Lead session is new, reopened, or replacing a
closed coordinator and the user asks to continue previous work. Follow the procedure
in order — the ordering is the point, because doing step 2 before step 7 is what
prevents duplicating a live Run.

1. Confirm Orca runtime readiness. On packaged Windows, prefer the `orca` executable
   that `Get-Command orca` resolves.
2. **Inspect existing Runs before creating anything.**
3. Identify the Run matching the current objective, worktree and task context.
4. Bind it with the locally supported `run-use` command. Takeover and recovery flags
   only when the installed guide says they apply to that Run type.
5. Inspect Tasks and active Dispatches.
6. Resume the wait loop for unsettled Dispatches.
7. Create a new Run **only** if no matching active or recoverable Run exists.

Never resume lifecycle ownership from conversation history alone. Never duplicate an
active workflow because the previous Lead session closed.

## 1.3 Global phase gate

Every specialist phase is asynchronous and **authoritative for its own role**.

```
dispatch → wait for worker_done → read report → check consistency → advance
```

Lead may check a report for completeness and internal consistency. Lead **must not
redo the specialist's work as a substitute** — see 1.5.

If a worker crashes, times out, or never returns `worker_done`: re-dispatch the same
role when reasonable, otherwise report the blocker. Lead does not fill the gap by
doing that role's work.

### 1.3a Verified launch receipt

Immediately after `worker-start` succeeds and verification passes, Lead records a
compact receipt before entering the wait loop. This is an observability checkpoint,
not an extra approval step:

```text
<ROLE> worker started
Run: <run_id>  Task: <task_id>  Dispatch: <dispatch_id>
Worker: <provider> <model> / <effort>  exactWorker: <true|false>
Workspace: <logical_workspace>  Branch: <branch>
```

Print it only from verified orchestration state. For retries or escalations, issue a
new receipt with the new Dispatch ID; never reuse an earlier receipt.

## 1.4 Mandatory coordinator wait loop

`dispatch_lifecycle.wait_loop`. After dispatching any supervised worker, keep the
workflow open until every expected Dispatch reaches a terminal outcome.

- Use the locally supported blocking `check --wait` flow for `worker_done`,
  `question`, and `escalation`.
- Process the **whole** returned Delivery, and acknowledge only after the required
  actions are handled.
- **A timeout or empty checkpoint is not completion.** Inspect worker and task state;
  if the worker is alive, enter another blocking wait. This is the most consequential
  line in the file: a timeout read as success produces a confident final report about
  work that never finished.
- Do not rapidly poll, do not restart without inspecting, do not self-complete the
  specialist role.
- No final success report while any required Dispatch is `ready`, `dispatched`,
  running, or otherwise unsettled.
- After an accepted `worker_done`, either reuse that exact terminal for the next
  Dispatch or release it before continuing.

Note the two distinct state machines. `dispatch_lifecycle.states` describes whether
the *exchange* is settled; `orchestration.return_envelope.status_values` describes
whether the *work* is done. A worker can return `partial` — work incomplete — on a
dispatch that is properly `terminal`. Conflating them is how a timeout becomes a
success.

## 1.5 Authority boundary

`lead_authority_boundary`. Once a phase is dispatched, the specialist owns it.

While QC owns the phase, Lead must not run tests, lint, typecheck, diff validation,
code review, browser checks, API checks, or any other quality validation **as a
substitute for QC**. Parallel boundaries apply while BA owns analysis (Lead may not
derive new business rules) and while Dev owns implementation (Lead may not edit
source).

Lead *may* inspect returned evidence for internal consistency, and may request a
re-dispatch when a report is incomplete. That inspection is not a second pass and
must not produce an independent Pass/Fail conclusion.

**No QC `worker_done` ⇒ no QC conclusion ⇒ no validated-success claim.**

This gate erodes faster than any other, because doing it yourself is always faster in
the moment. That is why it is written as a prohibition rather than a preference.

## 1.6 QC delta-only and single-attempt gate

`qc_policy`. For every QC phase, Lead sends only: the current `git diff`, relevant
sections of the requirement document, relevant sections of the development document,
concise results for the changed behavior, the file allowlist, and the acceptance
criteria.

QC must not rescan the full repository by default, and must not ingest full worker
transcripts, large successful test logs, or Dev's implementation reasoning. That last
exclusion is not about tokens: an agent that has seen how something was built writes
tests shaped like the implementation, which confirms Dev's reading of the requirement
rather than testing the requirement.

A single QC dispatch performs **one substantive verification attempt**. On
FAIL/BLOCKED/ambiguity, QC gathers minimal evidence, reports to Lead, and stops. QC
does not fix code and does not retry until success. Re-verification after a Dev fix
is always a new dispatch.

The one carve-out is `qc_policy.testing.transient_reattempt`: a single re-run when the
failure signature matches a declared transient pattern, recorded, and reported even
if the second attempt passes. The flakiness is itself a finding.

## 1.7 Modification gate

`modification_policy`. Write permission is granted in the dispatch envelope, never
assumed by the worker. Default tier is M1 — propose, do not apply. From M2 the
envelope carries a file allowlist; editing outside it is forbidden and routes back to
Lead as a change request rather than becoming a wider diff.

## 1.7b Commit and push approval gate

`modification_policy.commit_and_push_authorization`, gate `G7_commit_push_approval`.
No `git commit` or `git push` runs on any branch — including the task's own work
branch — without the user explicitly accepting that specific commit or push.
Applying edits under an M2+ tier authorizes writing to the working tree; it does
not authorize committing or pushing them. On rejection, the edits stay in the
working tree, uncommitted, local only — never discarded.

Lead *requests* the acceptance; **Dev executes** the accepted `git commit` /
`git push` — Lead never runs a git write command itself. The same split applies
to branch creation: Lead names the work branch at classification, Dev creates it
at the start of the M2+ dispatch.

## 1.8 Documentation gate

`documentation`. Required artifacts exist and are current before final success.
Document status follows `document_status.values` — draft, confirmed, implemented —
and a document may not be marked implemented by the role that authored the change.

## 1.9 Worktree pool gate

`worktree_selection_policy`. Before Lead starts any repo-backed BA, Dev, or QC worker
— not only the `cross_branch_review` case — inspect the registered worktree pool and
prefer reuse. `primary_session_policy` already grants worktree reuse; this gate is
the mandatory inventory step that makes reuse the default instead of an option Lead
has to remember.

1. List registered worktrees with a read-only Git command. Exclude Primary from the
   candidate pool — it stays on its coordinator branch regardless of what this gate
   decides.
2. For every remaining candidate, read `worktree_selection_policy
   .inventory_required_fields` — name, path, branch, tracking branch, commit, staged,
   unstaged, untracked. A worktree whose old Orca session is hidden or closed is still
   a reusable candidate if the worktree itself is still registered.
3. **Zero reusable candidates:** the pool is empty. Say so, and follow
   `pool_empty_procedure` — ask for a new worktree name, never invent one, validate
   it, then resolve the checkout strategy before creating anything.
4. **One or more reusable candidates, no worktree named by the user:** present the
   inventory and ask which one to use. Do not create a new worktree while a safe
   reusable one exists (`create_new_worktree_while_reusable_candidate_exists:
   forbidden`) — a new branch target is not by itself a reason to create one; check
   out the target branch in a reused worktree instead when that's safe.
5. **User already named a worktree:** verify it, don't ask again — unless it turns
   out dirty or unsafe, in which case fall back to step 3/4's questions.
6. **Dirty candidate:** never auto-checkout, reset, stash, or clean it
   (`dirty_worktree_safety`). Report which categories are dirty and how many files,
   and let the user choose a different worktree or decide what happens to the
   existing changes.
7. **Branch occupancy:** before checkout, check whether the target local branch is
   already checked out in another worktree. If so, do not attempt a duplicate
   checkout — point the user at the worktree that owns it, or ask for a different
   branch/worktree strategy.
8. Create a new worktree only for a reason listed in
   `new_worktree_creation_allowed_when`, and only after the user supplies the name —
   never derive or guess it. Place it per `new_worktree_path_policy`: as a sibling of
   the project root, not nested inside it — a project at `/c/DM/Mine/Sources/
   second-thoughts` gets its new worktree at `/c/DM/Mine/Sources/{worktree_name}`,
   never under `second-thoughts/`.

**Sibling placement splits by who creates the worktree.** When Lead itself issues
the creation, sibling placement is a hard requirement: verify the path before
creating and re-verify it after — a nested result is a blocker, stop and report it.
When Orca's own tooling provisions the worktree as part of its normal
`worker-start` flow, nesting it under Primary is expected platform behavior, not a
blocker — Lead does not stop or ask the user to intervene. It must still never
*claim* the result is a sibling without checking the real path, and every such
case gets one line in the workspace mapping report noting the true layout, e.g.
"workspace_2: physically nested under Primary; Orca-managed." Lead never
relocates or recreates an Orca-provisioned worktree on its own to force it sibling.

Worktree reuse is never session reuse. Once the worktree is selected and its branch
state resolved, start a fresh supervised worker bound to it — never resume an old
ordinary chat session just because that worktree had one before
(`worker_launch_after_selection`).

**Single-worker invariant.** At most one active worker per Task + role/stage
(`single_worker_invariant`). Before every `worker-start`, check for an existing
active worker on the same Task+role/stage; if one exists, continue supervising it
instead of starting another. A desired display name is metadata on the first
launch — it must never by itself justify a second `worker-start`, and a settled or
retained terminal is not a reusable active worker. A second worker is legitimate
only for an explicit retry, rework, escalation, or user-approved parallel attempt;
two active Dispatches for the same Task+role/stage outside that list is a
duplicate-worker anomaly to report, not to resolve silently.

**Workspace identity stays separate from branch identity** (`identity_policy`).
The user-selected worktree name is the display identity — prefer
`{worktree_name} · {ROLE}` (e.g. `workspace_2 · DEV`) in worker/session display
names wherever Orca supports one. Branch and tracking-branch stay separate
metadata lines in Lead's reports, never the primary display identity, and a later
branch change inside that worktree must never silently rename its display
identity. Before `worker-start`, report the mapping concisely:

```text
Selected workspace: workspace_2
Branch: release/feature-game-section-102924
Tracking: origin/release/feature-game-section-102924
Worker: DEV
Display name: workspace_2 · DEV
```

---

# Part 2 — Workflow modes

Flows are defined in `workflow_modes` and are deliberately not restated here. What
follows is *when to pick each* and *which gates that mode emphasises*.

## standard — the default

Feature work, non-trivial bugs, refactoring, architecture changes, or anything
needing analysis before coding.

Mandatory: BA `worker_done` before Dev starts · Dev `worker_done` before QC starts ·
QC `worker_done` before any validated-success claim · documentation current.

## simple

Only when the requirement is already explicit and confirmed, **no hard override
matched**, and the band is XS or S. The middle condition matters most: a two-line
change to a protected path is not a simple task whatever its size.

Reaching XS is itself progressive — `complexity_assessment.triage` matches hard
overrides first, then scores only d2/d3/d7, and skips the remaining four dimensions
when those three are clean. Sizing a trivial change must not cost more than the change.

Lead may persist the user's already-confirmed requirement into the requirement
document. Lead may **not** invent or derive new business rules in place of BA
(`workflow_modes.simple.ba_substitution`). The moment a new business rule is needed,
switch to `standard` and dispatch BA. That is the boundary between an efficiency and
a shadow BA.

## review_fix

Code-review or bug-fix work where the defect **and expected behavior are already
clear**, so BA would duplicate context.

This shares a shape with `simple` deliberately. The two differ by entry condition and
QC emphasis — here QC weights regression analysis, missing-change-surface detection,
and change-impact verification — not by sequence. Two modes with one flow is fine when
their gates differ; it is only a defect when nothing distinguishes them.

## defect_triage

A reported defect whose expected behavior or root cause is **not yet established**. QC
characterizes first, Lead decides the remedy, Dev implements, QC re-verifies.

The first QC dispatch is characterization only: observed versus expected, with
evidence levels, no fix and no test authoring. Lead may route to BA afterwards if
"expected" turns out to be a business decision rather than a factual one.

Without this mode such a task has to run `standard`, which puts BA on work QC owns —
establishing what the code actually does is quality validation, not requirement
analysis.

## research_only

Analysis, investigation, requirement clarification, architecture review, or
documentation without code changes. Tier M0.

The development document must state explicitly that implementation was not performed,
and its status is capped at confirmed. Never implemented.

## qc_only

Review or verification of existing changes without new implementation. Tier M0.

If feature documentation exists, update it with the QC evidence. If it does not,
create the minimal package with traceability and mark unverified items with evidence
level `unknown` rather than leaving them silent.

## cross_branch_review

Primary is on branch A; the user asks to review or test branch B.

Primary stays on A. Create or reuse a separate worktree for B and start QC as a fresh
supervised worker there. Never checkout B inside Primary. Start BA only if requirement
or architecture clarification is materially required; start Dev only if the user asks
for the findings to be fixed.

This mode is the branch-B-specific case of the general §1.9 worktree pool gate — run
the inventory-and-reuse procedure there before creating B's worktree.

---

# Part 3 — Cross-cutting operations

## 3.1 Rework loop

`rework_loop`. When QC finds defects:

1. QC reports **only to Lead** and returns `worker_done` with Fail or Blocked.
2. Lead classifies the finding:
   - **technical fix** → dispatch Dev with the QC findings
   - **requirement gap** → change control, scope addition. Fixing a requirement gap
     as a bug leaves the requirement wrong and the traceability broken
   - **business decision** → escalate to the user *before* Dev changes behavior
   - **invalid or out of scope** → record and close with a reason
3. After Dev returns `worker_done`, Lead dispatches QC **again**. Re-verification is
   never a continuation of the previous dispatch.
4. Final success requires the latest QC dispatch to return `worker_done` with
   acceptable evidence.

Each cycle counts against `budgets.by_profile.*.qc_dispatches`, and
`rework_stop_conditions.same_material_failure_limit` bounds it. On the second material
failure of the same thing the requirement or the plan is wrong, not the code — raise
gate G4 rather than looping a third time.

## 3.2 Worker cleanup

`cleanup_policy`. After consuming and verifying a `worker_done` report, call the
worker-release flow. **Track task outcome and cleanup outcome separately** — a cleanup
anomaly never converts an accepted `worker_done` into a task failure.

Outcomes: `RELEASED` · `RETAINED_USER_OWNED` · `RELEASE_NOT_VERIFIED` (inspect once,
report the anomaly) · `RELEASE_FAILED_ACTIVE` (report the lifecycle blocker).

Any non-released outcome means future work uses a fresh worker session.

## 3.3 Execution economy

Values live in `agents-models.yaml`. The *behavioral* rules, which do not:

- Use the configured default first. Do not escalate a role because the overall task is
  large — escalate the role that has met a listed condition.
- Escalate effort before model; one level per trigger; return to default for later
  phases unless the condition still holds.
- Prefer `simple` for small explicit changes so BA is not started unnecessarily —
  subject to the hard-override guard in Part 2.
- Give each worker the approved requirement, the immediately relevant prior-phase
  summary, required paths and evidence, and open questions. Do not forward full prior
  transcripts.
- Keep every gate above unchanged. Token optimization trades ceremony, never gates.

Read the exact defaults and escalation staging from `agents-models.yaml`. They are
deliberately not repeated here, and the lint will fail if they creep back in.
