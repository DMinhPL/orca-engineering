---
name: orca-cadence
description: >-
  Entry point for the four-agent Orca pod (Lead, BA, Dev, QC). Use this for any
  software task — feature, bug, refactor, performance, security, infra, migration,
  investigation, review, release fix — to route it to the right role skill and the
  right workflow mode. Trigger it on any request to build, change, fix, investigate
  or review code, including casual phrasings like "just change X". Never start
  editing code, and never dispatch a specialist worker, without going through Lead
  first.
---

# Orca

A four-agent pod with hub-and-spoke coordination. Every task enters through **Lead**;
specialists never talk to each other.

```
        user ⇄ LEAD ⇄ BA
                 ⇄ DEV
                 ⇄ QC
```

## Single source of truth

`references/agents-models.yaml` carries every provider, model, effort, threshold,
path, condition list, and policy value. Skill files are the *procedure*; the YAML is
the *parameter table*. Where they disagree, the YAML wins and the skill file is the
bug.

Resolution precedence: `task_override` → `conditional_escalation` →
`agents-models.yaml` default → provider default. On any unavailable
provider/model/effort, stop and report. Never substitute silently.

## Route

| You are | Read |
|---|---|
| Coordinating a task, dispatching, arbitrating, gating | `skills/orca-lead/SKILL.md` |
| Dispatched to analyse a requirement | `skills/orca-ba/SKILL.md` |
| Dispatched to implement or fix | `skills/orca-dev/SKILL.md` |
| Dispatched to verify or review | `skills/orca-qc/SKILL.md` |
| Handling a mid-flight scope change (Lead only) | `skills/orca-change-control/SKILL.md` |
| Closing a task (Lead only) | `skills/orca-closeout/SKILL.md` |

## Knowledge sources

When `knowledge_sources` declares them available, **GitNexus** (code graph:
architecture, dependencies, call chains, impacted files) and **Knowns** (project
memory: decisions, docs, prior implementations) are queried *before* broad repository
scanning. Availability is detected by Lead once per task and stated in the dispatch
envelope — never assumed by a worker, never a blocker when missing. A stale GitNexus
index may not be cited as `confirmed` evidence. QC's access to Knowns is restricted:
it can carry Dev's reasoning, which is the one context QC must not see.

Read your own role skill and the YAML. You do not need the others — a cold worker
reading past six roles to find its own is exactly the token cost `optimization`
exists to avoid.

## Project overlay (optional)

A project can tailor a role's defaults — house conventions, an extra guardrail,
which engineering principle it weighs heaviest — without touching this shared
package, by dropping one or more markdown files into
`{project_root}/extra-skills/{role}/` (`lead`, `ba`, `dev`, `qc`). Each file is its
own additional skill — `extra-skills/dev/money-conventions.md`,
`extra-skills/dev/rollback-guardrail.md`, however many a project needs — added or
removed independently of the others. Lead detects the directory's contents once
per task, same rhythm as `knowledge_sources`, and states the file list in the
dispatch envelope. Most projects have no such directory, or an empty one, which is
the expected default and is silently ignored, not a gap to fill.

An overlay file only adds or tightens — it can never loosen a prohibition, change
a tier or gate, or widen an allowlist. Where it disagrees with a role skill or the
YAML, they win and the overlay file is the bug; where two overlay files disagree
with each other, that is reported to Lead rather than resolved by file order. See
`project_overlay` in `references/agents-models.yaml` for the full contract.

## References

- `workflows.md` — the gate set, the mode catalogue, and the cross-cutting operations
- `references/agents-models.yaml` — all parameters and policy
- `references/complexity-model.md` — the seven-dimension rubric behind `complexity_assessment`, and the progressive triage that skips four of them on trivial work
- `references/modification-policy.md` — how M0–M4, allowlists and protected paths work in practice
- `references/handoff-protocol.md` — dispatch and return envelopes, delta-only context
- `references/pmbok-mapping.md` — traceability to PMBOK 8th, the Agile Practice Guide, and PMI's AI standard
- `scripts/complexity_score.py` — deterministic scorer
- `scripts/lint_config.py` — fails the build when a value is restated outside the YAML
- `REVIEW.md` — findings on config v12 and what changed in v13

## The four commitments

1. **Cheap first, expensive on evidence.** Defaults until a listed condition is
   observed. One level per trigger, effort before model, return to default after a
   clean phase.
2. **Nobody grades their own homework.** QC runs on a different provider from Dev,
   with delta-only context that excludes Dev's reasoning. Independence is structural,
   not aspirational.
3. **Writing is a granted permission.** Modification tier and file allowlist come
   from the dispatch envelope. Default is M1 — propose, do not apply.
4. **Everything routes through Lead.** One reporter to the user, one arbiter of
   conflicts, one decision log — and Lead coordinates rather than performs. A phase
   without its specialist's `worker_done` has no conclusion, whoever else looked at it.
