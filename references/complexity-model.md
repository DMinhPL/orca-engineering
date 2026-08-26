# Complexity Assessment — the rubric behind `complexity_assessment`

Bands, ranges, overrides and mode/profile mappings are normative in
`agents-models.yaml`. This file is the scoring guidance Lead uses to produce the
numbers.

## Why a rubric

"This looks hard" cannot be audited, reproduced, or argued with. Without one,
`lead.choose_complexity_profile` and `lead.choose_workflow_mode` are intuition, and
two Leads route the same request differently.

Seven cheap questions, scored 0–3, total 0–21. Scoring happens at classification, at
**default effort** — `optimization.rules` forbids scoring at escalated effort, because
sizing must never be the expensive step. You score from the request text and a shallow
look at the repo, not from an analysis pass. The score is provisional;
`rescore_triggers` exists because it will sometimes be wrong.

## The dimensions

**d1 · Scope breadth** — 0 one function · 1 two to five files in one module ·
2 multiple modules or a new component · 3 cross-cutting or a new dependency/service

**d2 · Requirement ambiguity** — 0 acceptance criteria are obvious from the request ·
1 one or two non-blocking clarifications · 2 real gaps; success is describable but not
described · 3 the problem itself is contested

**d3 · Blast radius** — 0 cosmetic or dev-only · 1 one feature degrades, nothing lost ·
2 shared path: auth, billing, core domain, background jobs · 3 data integrity,
security boundary, money, public API, compliance

**d4 · Integration surface** — 0 self-contained · 1 one internal interface ·
2 external API or another team's contract · 3 multiple parties, or a versioned
contract with live consumers

**d5 · Verification difficulty** — 0 existing tests cover it · 1 straightforward new
unit tests · 2 integration tests, fixtures, seeded state, async · 3 concurrency,
performance targets, visual, ML output quality, production-only conditions

**d6 · Novelty** — 0 direct precedent in the repo · 1 familiar pattern, unfamiliar
corner · 2 new library, new pattern, thin domain knowledge · 3 the approach itself is
unknown

**d7 · Reversibility** — 0 revert the commit · 1 revert plus redeploy ·
2 needs a compensating change: cache invalidation, flag unwind, coordinated release ·
3 irreversible: destructive migration, deleted data, published API, sent messages

## Bands → mode and profile

Ranges and mappings live in `complexity_assessment.bands`. In summary: XS and S route
to `simple` mode and the `simple` profile; M routes to `standard` and `normal`; L
routes to `standard` and `complex`; XL is not executed — it decomposes into child
tasks that each re-score.

## Overrides

`hard_overrides` are **matched, not calculated**, and they beat the arithmetic:
minimum band L, complex profile, gate G1. Security boundary, secrets, PII, production
schema, public API, infra, licensing, irreversibility, protected paths. Note that
`mode_downgrade_forbidden_when: hard_override_matched` — a two-line change to an auth
file is not a simple task, whatever the total says.

`soft_override` runs the other way: when d2 and d6 are both 0 and blast radius and
reversibility are low, work that is wide is merely voluminous, not complex. A rename
across forty files goes to Dev at default effort with a tight allowlist.

## Worked examples

**"Footer copyright year is hardcoded."**
0·0·0·0·0·0·0 = **0, XS.** Simple mode, tier M2, one-file allowlist. About four
sentences of process. Anything more is waste.

**"Add CSV export to the reports page."**
2·1·1·0·2·1·0 = **7, S.** Simple mode is permissible if the requirement is explicit —
but d5=2 says verification is not trivial, so confirm the boundary behaviours
(delimiter, encoding, large files, permissions) are stated before skipping BA. If
"large file" turns into streaming, that is a `rescore_trigger`.

**"Let users sign in with Google."**
2·2·3·2·2·1·2 = **14, L** — and `security_boundary_change` matches, so the override
would have forced L regardless. Standard mode, complex profile, tier M3, gates G1 and
G2. BA at `high` with model escalation available on `security_boundary_analysis`.

**"Split the billing module into a service."**
3·2·3·3·3·2·3 = **19, XL.** Not executed. Decompose — preferably by risk first, so the
irreversible part is isolated and gated while the rest moves: (1) spike on boundary
definition, (2) extract domain interfaces in place, (3) strangler proxy, (4) data
ownership migration, (5) cutover. Each child re-scores. If a child still lands XL,
split again.

## Re-scoring

On any `rescore_trigger`, record both scores and the dimensions that moved:

```
14 (L) → 15 (L)   d5 2→3   reason: alternate account creation path found in QC
```

`retrospective.per_task.fields.mis_scored_dimensions` feeds the batch review. The dimension
most commonly under-scored across pods is **d5** — verification difficulty is almost
always worse than it looks from the outside. If your retrospectives keep landing
there, adjust the rubric rather than individual estimates.

## Deterministic scoring

`scripts/complexity_score.py` implements the bands, the hard overrides and the soft
override, so two Leads scoring the same dimensions get the same band.

```
python scripts/complexity_score.py --d1 2 --d2 2 --d3 3 --d4 2 --d5 2 --d6 1 --d7 2
python scripts/complexity_score.py --interactive
python scripts/complexity_score.py --json ...     # for decisions.jsonl
```
