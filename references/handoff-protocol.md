# Dispatch and Return Envelopes

Field lists are normative in `agents-models.yaml` →
`orchestration.dispatch_envelope` and `orchestration.return_envelope`. This file
explains how to fill them well.

## Why the envelope is the contract

`primary_session_policy.fresh_supervised_worker_for_every_specialist_phase: true`
means every worker boots cold. It has no conversation history and no memory of the
task. Whatever is not in the envelope did not reach it.

The envelope does a second, less obvious job: it *bounds* context. A worker given
only what it needs is cheaper, faster, and less likely to helpfully solve a problem
nobody asked about. That is why `allowed_context` is a required field rather than an
optimisation.

## Dispatch

```json
{
  "task_id": "TASK-0142",
  "role": "dev",
  "provider": "codex",
  "model": "gpt-5.6-luna",
  "effort": "medium",

  "mission": "Implement third-party sign-in per the approved requirement. Do not modify the session model.",

  "modification_tier": "M3",
  "file_allowlist": [
    {"path": "src/auth/providers/google.ts", "change_kind": "new"},
    {"path": "src/auth/link_account.ts",     "change_kind": "new"},
    {"path": "src/auth/index.ts",            "change_kind": "modify — register provider only"},
    {"path": "src/routes/auth.ts",           "change_kind": "modify — add two routes"}
  ],

  "acceptance_criteria": ["AC-01", "AC-02", "AC-03", "AC-05"],
  "definition_of_done": [
    "each listed AC satisfied with named evidence",
    "no file changed outside the allowlist",
    "rollback note written before apply",
    "self-check reports evidence, not narrative"
  ],

  "allowed_context": [
    ".docs/features/2026-08-25_third-party-signin/ba/requirement.md",
    "git diff",
    "tests/auth/**"
  ],

  "escalate_to_lead_when": [
    "a needed change falls outside the allowlist",
    "the same material failure occurs twice",
    "an acceptance criterion appears untestable or contradictory"
  ],

  "return_artifacts": ["dev/development.md", "branch orca/TASK-0142-third-party-signin"]
}
```

### Field notes

- **`mission`** — one sentence, imperative, plus the most important *negative*
  instruction. The negative is usually what prevents the expensive mistake.
- **`allowed_context`** — paths and patterns, not pasted content. Pasting defeats the
  purpose. For QC this field is load-bearing: `qc_policy.context_mode: delta_only`
  and the forbidden list are what keep verification independent, and the envelope is
  where that is actually enforced.
- **`acceptance_criteria`** — IDs, not prose. Prose drifts between copies; an ID
  points at one authoritative statement in the requirement document.
- **`escalate_to_lead_when`** — pre-authorisation. Workers under-escalate because
  escalating feels like failing; naming the conditions in advance reframes it as
  following the protocol.
- **`file_allowlist`** — annotate every entry with `change_kind`. "modify — register
  provider only" constrains far more than "modify", and constraint is the point.

### Rejecting an incomplete envelope

`reject_incomplete_envelope: true`. A worker returns the envelope without starting
when required fields are missing, when the tier is M2+ with an empty allowlist, when
a blocking open question is unresolved, or when the mission and the criteria
disagree. Filling those gaps by inference is the most expensive habit a worker can
have, because the inference is invisible until QC.

## Minimal form for small tasks

Full JSON for a two-line change is exactly the ceremony `optimization` exists to
avoid. Five lines carry the same contract:

```
→ DEV · codex/gpt-5.6-luna/medium · TASK-0187 · tier M2
  MISSION   replace the hardcoded year in src/components/Footer.tsx with the current year
  ALLOWLIST src/components/Footer.tsx (modify), Footer.test.tsx (modify — snapshot)
  DONE      renders current year; snapshot updated; no other file touched
  ESCALATE  if the literal appears anywhere else
```

## Return

```json
{
  "task_id": "TASK-0142",
  "role": "dev",
  "status": "partial",
  "criteria_status": {
    "AC-01": "satisfied — tests/auth/google.spec.ts:12",
    "AC-02": "satisfied — tests/auth/google.spec.ts:34; decline path :58",
    "AC-03": "satisfied — manual behind flag; token redacted src/auth/log.ts:22",
    "AC-05": "not_satisfied — see open_questions"
  },
  "files_changed": ["src/auth/providers/google.ts", "src/auth/link_account.ts",
                    "src/auth/index.ts", "src/routes/auth.ts"],
  "allowlist_violations": [],
  "evidence_levels": {
    "root_cause_of_AC05_conflict": "hypothesis — verification step: enumerate account creation paths"
  },
  "open_questions": [
    "AC-05 requires automatic linking. Every automatic path I can construct is an account-takeover vector. Needs a decision."
  ],
  "recommended_next_action": "raise change request; AC-05 is a requirement gap, not an implementation defect"
}
```

`status` is `complete` · `partial` · `blocked` · `escalated`.

A `partial` with honest `criteria_status` is worth far more than a `complete` that
quietly redefined a criterion. The reinterpreted-criterion failure is the one
independent verification exists to catch, and declaring it yourself is cheaper for
everyone than making QC find it.

`evidence_levels` are required where
`engineering_policy.evidence_policy.tag_required_on` says so. An unconfirmed claim
cannot justify a tier above M1, close a human gate, or satisfy an acceptance
criterion — so tagging honestly is what keeps the downstream gates meaningful.

## Rules

1. **No verbal handoffs.** Not in the envelope, not received.
2. **The receiver validates before starting.** Bounce, do not infer.
3. **The receiver does not expand the mission.** Adjacent improvements go in the
   report as follow-ups, never into the diff.
4. **Lead passes summaries, not transcripts.**
   `optimization.rules.pass_concise_handoff_summaries_and_required_artifacts_instead_of_full_transcripts_when_possible`
   — and for QC, passing the Dev transcript is not merely wasteful, it is a forbidden
   context that destroys the independence the provider split was designed to create.
5. **Every envelope is a line in `decisions.jsonl`.** The envelope sequence is the
   audit trail of who was asked to do what, on what basis.
