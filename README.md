# orca-cadence

A Claude Code skill that runs a four-agent engineering pod — **Lead, BA, Dev, QC** —
in hub-and-spoke coordination. Every task enters through Lead; specialists never talk
to each other, and no specialist grades its own work.

```
        user ⇄ LEAD ⇄ BA
                 ⇄ DEV
                 ⇄ QC
```

## Why

Letting one agent analyse, implement, and verify its own change collapses the one
control that catches its own mistakes: independent review. Orca enforces four
non-negotiable commitments instead:

1. **Cheap first, expensive on evidence.** Default model/effort until a defined
   condition is observed; one escalation step per trigger; de-escalate after a clean
   phase.
2. **Nobody grades their own homework.** QC runs on a different provider from Dev,
   with delta-only context that excludes Dev's implementation reasoning.
3. **Writing is a granted permission.** Modification tier and file allowlist are set
   in the dispatch envelope, not assumed by the worker. Default is M1 — propose, do
   not apply.
4. **Everything routes through Lead.** One reporter to the user, one arbiter of
   conflicts, one decision log.

The workflow is a deliberate tailoring of PMBOK 8th/7th, the Agile Practice Guide,
and PMI's AI standard to small, high-frequency software tasks — see
[`references/pmbok-mapping.md`](references/pmbok-mapping.md) for the traceability.

## How it works

1. **Every task enters through `SKILL.md`**, which routes by role to the matching
   skill file and reads `references/agents-models.yaml` for parameters.
2. **Lead** scores task complexity into a band (XS–XL) using a progressive rubric —
   hard overrides first, then three safety dimensions, then the remaining four only
   if needed (see [`references/complexity-model.md`](references/complexity-model.md))
   — picks a workflow mode, and dispatches specialists as fresh, cold-boot supervised
   workers.
3. **BA, Dev, QC** each read only their own role skill plus the YAML — never the
   whole lifecycle — do their phase, and return a `worker_done` report to Lead.
4. **Lead** waits for each dispatch to reach a terminal state, checks reports for
   internal consistency (never redoing the specialist's work), and advances or loops
   back per [`workflows.md`](workflows.md).

```
skills/
├── orca-lead/               dispatch procedure, arbitration, gates, escalation
├── orca-ba/                 requirements, acceptance criteria, risk, blast radius
├── orca-dev/                implementation bounded by modification tier, allowlist, and design heuristics (DRY, KISS, YAGNI, ...)
├── orca-qc/                 delta-only independent verification and review
├── orca-change-control/     Lead-owned — mid-flight scope changes
└── orca-closeout/           Lead-owned — status gate and retrospective
```

## Single source of truth

[`references/agents-models.yaml`](references/agents-models.yaml) carries every
provider, model, effort, threshold, path, condition list, and policy value. Skill
files are the *procedure*; the YAML is the *parameter table*. Where they disagree,
the YAML wins and the skill file is the bug —
[`scripts/lint_config.py`](scripts/lint_config.py) enforces this mechanically.

## Repository layout

| Path | Purpose |
|---|---|
| `SKILL.md` | Entry point and role router |
| `workflows.md` | The gate set, workflow-mode catalogue, and cross-cutting operations |
| `skills/orca-*/SKILL.md` | Role-scoped procedures (Lead, BA, Dev, QC, change control, closeout) |
| `references/agents-models.yaml` | All providers, models, efforts, thresholds, and policy |
| `references/glossary.md` | Definitions for the acronyms and abbreviations used throughout (CAS, M0–M4, G1–G6, PMBOK, etc.) |
| `references/complexity-model.md` | The seven-dimension sizing rubric |
| `references/modification-policy.md` | How write tiers M0–M4, allowlists, and protected paths work |
| `references/handoff-protocol.md` | Dispatch/return envelopes and delta-only context |
| `references/pmbok-mapping.md` | Traceability to PMBOK 8th, the Agile Practice Guide, and PMI's AI standard |
| `scripts/complexity_score.py` | Deterministic complexity scorer |
| `scripts/lint_config.py` | Fails the build when a value is restated outside the YAML, or the changelog drifts from the config |
| `scripts/retro_report.py` | Aggregates `decisions.jsonl` across tasks — escalation rate, allowlist amendments, requirement-gap change requests, upward re-scores |
| `CHANGELOG.md` | Version history for `agents-models.yaml` |
| `REVIEW.md` / `REVIEW-workflows.md` | Design review findings behind the v13 and v14 changes |
| `examples/extra-skills/` | Worked example of a project overlay (see below) |

## Workflow modes

Six modes cover the shape of the work — see [`workflows.md`](workflows.md) for full
detail on when each applies and which gates it emphasises:

- **standard** — the default: analysis, build, verify
- **simple** — explicit, confirmed, XS/S work with no hard override
- **review_fix** — defect and expected behavior already clear; QC leads, then Dev fixes, then QC re-verifies
- **defect_triage** — root cause not yet established; QC characterizes first
- **research_only** — analysis or documentation, no code changes (tier M0)
- **qc_only** — verification of existing changes, no new implementation (tier M0)
- **cross_branch_review** — reviewing another branch while Primary stays on its own

## Project overlay (optional)

This package is shared across projects, so its defaults are generic. A single
project can tailor a role — a domain convention, an extra guardrail, which
engineering principle to weigh heaviest — without editing the package itself, by
dropping markdown files into its own repository:

```
your-project/
  extra-skills/
    lead/
    ba/
    dev/
      01-money-conventions.md
      02-ledger-guardrails.md
    qc/
```

Each file under `extra-skills/{role}/` is an independent additional skill for
that role, read after the role's default `SKILL.md`, in filename order. An empty
or absent folder for a role is the common case and is silently ignored — nothing
to set up if you don't need it. Lead detects what exists once per task and hands
the file list to the dispatched worker, the same way it hands over
`knowledge_sources`.

An overlay file may only add or tighten — name conventions, add checks, narrow an
already-granted allowlist, point at project docs. It may never loosen a
prohibition, change a modification tier or gate, or widen an allowlist: where an
overlay disagrees with the role's default skill or `agents-models.yaml`, the
default wins and the overlay is the bug. Two overlay files disagreeing with each
other is reported to Lead, never resolved by file order.

See [`references/agents-models.yaml`](references/agents-models.yaml) →
`project_overlay` for the full contract, and
[`examples/extra-skills/dev/`](examples/extra-skills/dev/) for a worked example.

## Getting started

1. Read [`SKILL.md`](SKILL.md) to understand the router and the four commitments.
2. Set `protected_paths` in `references/agents-models.yaml` for your own repository —
   the shipped defaults are generic placeholders.
3. Run a handful of tasks with Lead scoring complexity in shadow mode before letting
   the score drive `workflow_mode` selection automatically (see
   `references/complexity-model.md`).
4. Run `python scripts/lint_config.py` whenever `agents-models.yaml` changes, to keep
   procedure files honest about where values actually live.

## Status

Config `schema_version: 3`, `config_version: 25` — see [`CHANGELOG.md`](CHANGELOG.md)
for the version history, and [`REVIEW.md`](REVIEW.md) /
[`REVIEW-workflows.md`](REVIEW-workflows.md) for the design review findings behind it.
