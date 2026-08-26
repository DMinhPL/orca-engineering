---
name: orca-change-control
description: >-
  Integrated change control for the Orca pod, owned by Lead. Use this whenever
  work must change mid-flight: Dev needs a file outside the allowlist, QC finds a
  requirement gap rather than a defect, the user asks for "just one more thing",
  the design does not survive contact with the code, or a new constraint appears.
  Trigger it instead of quietly widening a diff or amending a requirement in
  place, and always before accepting a scope addition to an in-progress task.
---

# Integrated Change Control

Owner: **Lead**. Raisable by BA, Dev, QC, or the user — always via Lead.
Parameters: `change_control` in `references/agents-models.yaml`.

Change is not the problem; *unrecorded* change is. A pod that absorbs changes
silently produces work that no longer matches its requirement, its tests, or its
traceability, and nobody notices until the status gate fails. The goal is to make
recording a change take about ninety seconds so that doing it properly is easier
than not.

## Step 1 — the deciding question

**Does the current acceptance criteria set fail without this change?**

- **No** → `if_not_required: log_as_followup_and_continue`. The refactor Dev noticed
  is real and it is not this task. Adjacent-but-tempting work is the largest source
  of diff inflation in agent pods, precisely because the agents are helpful.
- **Yes** → classify and proceed.

## Step 2 — classify

`change_control.classes` gives five, with their authority:

| Class | Authority | Artifact |
|---|---|---|
| `clarification` — ambiguity resolved, scope unmoved | Lead | amend requirement |
| `allowlist_amendment` — necessary file missing, no new requirement | Lead | recorded amendment |
| `scope_addition` — new requirement or criterion | Lead if band unchanged, else G1 | change request |
| `design_change` — the approach fails | Lead proposes, user approves from band L | CR + decision record |
| `baseline_change` — schema, public API, security, infra, dependency, licensing | **user, gate G2** | change request |

For `baseline_change`, `writes_before_approval: forbidden`. No exceptions. "It's a
small schema change" is the sentence that precedes the incident report.

Getting the classification right is most of the work. The common error is treating a
scope addition as an allowlist amendment because it feels small.

## Step 3 — fast path (allowlist amendment)

```
CR-01  allowlist_amendment  ·  TASK-0142  ·  raised by dev
  ADD      src/auth/invite.go   modify — add ownership check
  WHY      invite-created accounts have no password row, so AC-02's confirmation
           step cannot execute; AC-02 cannot be satisfied without this
  IMPACT   scope none new · +1 subtask · risk: closes the R-03 gap
           protected path: no · tier unchanged M2
  DECIDE   lead — approved
```

One exchange, recorded in `decisions.jsonl`, allowlist updated, Dev resumes.

`promote_to_formal_when: exceeds_two_files_or_reveals_missed_requirement`. And note
the meta-signal: two or three amendments on one task means BA's blast-radius analysis
was wrong. Say that out loud rather than accumulating them quietly — it is a
`rescore_trigger`.

## Step 4 — formal path

Assess impact across every field in `change_control.impact_assessment_fields`. This
is the part that gets skipped and the part that makes the decision real:

```
  SCOPE       +REQ-04, +AC-06. No existing requirement invalidated.
  SCHEDULE    +1 design decision, +2 subtasks, +2 test cases, one Dev/QC cycle.
  COST        1 of 2 budgeted escalations used; within budget.
  RESOURCES   dev at default; qc escalated (security_sensitive condition matched).
  RISK        Closes R-03 residual. Adds R-06: email-based ownership proof is
              weaker than password — mitigate with a signed, time-limited link.
  QUALITY     TC-05 needs an invite-account variant.
  RESCORE     band L, 14 → 15. d5 1→2. Band unchanged, profile unchanged.
```

Disposition is one of `approved` · `rejected` · `deferred` ·
`more_information_needed`.

## Step 5 — propagate

An approved change is not done when it is approved. Walk
`change_control.propagation_checklist` in order:

1. requirement document
2. **traceability matrix** — skipping this is how a change ends up implemented but
   untraceable, which is indistinguishable from scope creep at the status gate
3. risk section
4. file allowlist
5. definition of done
6. budget
7. decision log
8. **reissue the dispatch envelope** — the worker is cold and holds no memory of the
   amendment

## When QC raises one

`qc_policy.authority.may_raise_change_request_to_lead: true` exists because a
requirement gap found during verification is not a defect. Fixing it as a bug leaves
the requirement wrong, the traceability broken, and the same gap available to the
next task in that area. Route it here, add the REQ, then fix.

## The rejection worth making

Sometimes the best output is "no, not in this task". A change rejected with a
recorded reason and a follow-up item beats one absorbed silently: the work still gets
considered, the current task still ships, and the reasoning survives.
