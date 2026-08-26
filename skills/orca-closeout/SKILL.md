---
name: orca-closeout
description: >-
  Closing an Orca task, owned by Lead. Use this before reporting a final result to
  the user: it checks the documentation status gate, validates traceability,
  closes risks, runs the per-task retrospective that calibrates the complexity
  rubric, and releases workers. Trigger it when a task is verified and about to be
  reported complete, and when a batch of tasks warrants reviewing whether the
  pod's sizing and escalation rates are healthy.
---

# Closeout

Owner: **Lead**. Parameters: `documentation.status_gate`, `retrospective`,
`cleanup_policy` in `references/agents-models.yaml`.

Short phase, and the only mechanism the pod has for getting better rather than merely
faster.

## 1. Status gate

`documentation.status_gate` — all must hold before status becomes implemented:

- ☐ QC worker done (verified, not timed out — a timeout is a checkpoint)
- ☐ No open critical review issues
- ☐ All P0 defects pass
- ☐ No allowlist violations
- ☐ Traceability complete, from band M

Also `coordinator_continuity.no_final_while_required_dispatch_unsettled`: no final
report while any required dispatch is unsettled.

## 2. Traceability validation

Walk `traceability.csv` against the two obligations:

- **Coverage** — every acceptance criterion has a test. A gap here is a P1.
- **Justification** — every changed file traces to a requirement. An unmatched file
  is scope creep that got through; record where it entered, because that tells you
  which control failed.

Any requirement not delivered becomes an explicit carry-forward task, not a footnote.

## 3. Risk closure

Each risk: `did_not_occur` · `occurred_response_worked` · `occurred_response_failed` ·
`carried_forward` · `superseded`.

The last three are the interesting ones. A response that failed is a lesson about the
response. A risk that materialised through a path nobody considered is a lesson about
the BA probe list, and it should end up *in* that list. A risk carried forward to
nobody is just closed with extra words — give it an owner outside the task.

## 4. Retrospective — the part that compounds

`retrospective.per_task`, required from band M:

```
band_at_intake        L (14)
band_final            L (15)
escalations_used      1 of 2      dispatches: ba 1, dev 3, qc 2
change_requests       2  (1 allowlist amendment, 1 scope addition from QC)
mis_scored_dimensions d5 — scored 2, actually 3

generalizable_probe   "How many ways can the entity under change come into
                       existence?"  BA looked at the auth module but never at
                       account creation paths. This generalises well beyond auth.
```

The `generalizable_probe` is the deliverable. A note about this particular auth bug
helps nobody; a question that catches the same *class* of miss on an unrelated task
is worth the five minutes.

If a lesson should change a skill file or a YAML condition list, **change it**. A
lesson recorded and never applied is the commonest form of organisational amnesia.

## 5. Worker cleanup

`cleanup_policy`. Release each worker after verified done, and record the outcome:
`RELEASED`, `RETAINED_USER_OWNED`, `RELEASE_NOT_VERIFIED`, `RELEASE_FAILED_ACTIVE`.
An accepted worker-done result is immutable during cleanup — cleanup never revises a
verified result. Report any unreleased terminal handle as a blocker.

## 6. Final report

One report, from Lead only. State what was delivered against the requirement, what
was not and why, defects outstanding with severity, risks carried, and the rollback
mechanism.

## Batch retrospective

Every `retrospective.batch.every_n_tasks` (default 15), read across tasks:

- **Which dimension is systematically mis-scored?** Adjust the rubric, not individual
  estimates. It is usually d5, verification difficulty.
- **Escalation rate** — target band 0.15–0.35. Near zero means the defaults are too
  generous and you are over-spending by default. Near one means they are too thin and
  every task pays a re-dispatch tax.
- **Where do change requests originate?** Mostly from QC means BA analysis is running
  thin. Mostly from Dev means blast-radius work is weak.
- **Did QC independence hold?** Check the provider split and the delta-only context
  actually applied. Under time pressure this is the first control to erode and the
  one most worth defending.
- **Cost share by band.** If XS and S tasks consume a disproportionate share, the mode
  downgrade rule or the defaults are wrong.
