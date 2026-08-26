# Glossary

Terms and acronyms used across the skill files, in one place. Definitions here are
descriptive; the normative values (bands, tiers, gate conditions) live in
`agents-models.yaml` and the files listed under "See also."

## Roles

- **Lead** — the coordinator. Every task enters through Lead; Lead scores complexity,
  chooses the workflow mode, dispatches specialists, arbitrates, and is the only role
  that reports to the user.
- **BA** — Business Analyst. Dispatched to turn a request into acceptance criteria,
  risk analysis, and blast-radius analysis.
- **Dev** — Developer. Dispatched to implement, bounded by modification tier and file
  allowlist.
- **QC** — Quality Control. Dispatched to verify independently — different provider
  from Dev, delta-only context, one substantive attempt per dispatch.

## Sizing

- **CAS** — Complexity Assessment Score (also "the CAS rubric" / "the CAS band"). The
  seven-dimension scoring system that produces a task's band and drives which
  workflow mode and modification tier apply. See `complexity-model.md`.
- **d1–d7** — the seven CAS dimensions: scope breadth, requirement ambiguity, blast
  radius, integration surface, verification difficulty, novelty, reversibility. Each
  scored 0–3.
- **Triage triple** — d2, d3, d7: the three CAS dimensions carrying the safety signal,
  scored first under progressive scoring. See `complexity-model.md`.
- **Fast path** — when the triage triple is all zero and no hard override matched, the
  task is banded XS without scoring d1/d4/d5/d6. Recorded as `fast-path` in the
  decision log so it stays auditable.
- **XS / S / M / L / XL** — the five complexity bands the CAS total maps to, from a
  four-sentence trivial change (XS) to a task that must be decomposed before it can
  run at all (XL). See `complexity-model.md`.

## Modification and gates

- **M0–M4** — the modification tiers, in order of increasing write authority:
  - **M0** read-only (investigation, `research_only`/`qc_only` modes)
  - **M1** produce a diff without applying it — the default
  - **M2** apply edits to allowlisted files, with a rollback note
  - **M3** structural changes (new/moved files, new dependency), adds a decision record
  - **M4** baseline changes (schema, public API, security config, infra) — requires
    human approval before any write
  See `modification-policy.md`.
- **G1–G6** — the human gates, each blocking a specific phase until a person acts:
  - **G1** scope approval — band L/XL or a hard override matched, before Dev
  - **G2** write authorization — tier M4, or M3 on a protected path, or a new
    third-party dependency, before Dev
  - **G3** ambiguity resolution — a blocking open question survives one BA pass,
    before Dev
  - **G4** escalation ceiling — the same failure repeats, or a budget/escalation
    chain is exhausted, before any phase
  - **G5** acceptance — band M or above, before the final report
  - **G6** release — merging to a protected branch, or high release risk, before the
    final report
  See `agents-models.yaml` → `human_gates`.
- **AC** — Acceptance Criterion. Referenced by ID (e.g. `AC-01`), never by prose, so
  the requirement document stays the single authoritative statement.
- **Allowlist** — the set of files a Dev dispatch may write, proposed by BA from
  blast-radius analysis and granted by Lead in the dispatch envelope. Required from
  M2 upward.
- **Protected paths** — files or directories that always force at least a hard
  override (band ≥ L) and gate G2 if they're in the change surface. Set per-repo in
  `agents-models.yaml`.
- **Branch category** — the `feat` / `fix` / `update` / `concept` prefix on a work
  branch (`feat/auth-role-mechanism-101147`). Derived from the task type rather than
  chosen freely, decided by Lead at classification. See `modification-policy.md`.

## Workflow

- **Hard override** — a condition (security boundary, secrets, PII, production
  schema, public API, infra, protected path, irreversibility) that forces band ≥ L
  and gate G1 regardless of the CAS arithmetic.
- **Soft override** — the opposite case: work that is wide but low-risk and
  low-ambiguity (e.g. a mechanical rename across many files) is scored as merely
  voluminous, not complex.
- **Dispatch envelope** — the JSON/structured contract Lead sends a fresh worker:
  mission, modification tier, allowlist, acceptance criteria, allowed context, and
  escalation conditions. See `handoff-protocol.md`.
- **Return envelope** (`worker_done`) — the structured report a worker sends back:
  status, criteria status, files changed, evidence levels, open questions.
- **Delta-only context** — QC receives only the diff, relevant requirement/dev
  document sections, and acceptance criteria — never Dev's implementation reasoning
  or full transcript. The mechanism that keeps verification independent.
- **Rework loop** — the cycle when QC returns Fail/Blocked: Lead classifies the
  finding (technical fix, requirement gap, business decision, or invalid), routes it,
  and re-dispatches QC fresh after the fix — never as a continuation.

## External standards referenced

- **PMBOK** — *Project Management Body of Knowledge* (PMI). Orca's phase and gate
  structure is a tailoring of PMBOK 8th/7th edition practice. See `pmbok-mapping.md`.
- **PMI** — Project Management Institute, publisher of PMBOK and *The Standard for
  Artificial Intelligence in PPPM*.
- **PPPM** — Portfolio, Program, and Project Management.
- **HITL** — Human-in-the-loop. The principle behind gates G1–G6: humans retain the
  ability to hold, revise, or reverse a decision at any point.
- **RACI** — Responsible, Accountable, Consulted, Informed. PMBOK's influence model;
  Orca uses a stricter enumerated allow/deny communication matrix instead (see
  `SKILL.md`'s hub-and-spoke diagram).
- **WBS** — Work Breakdown Structure. Referenced in the PMBOK mapping for how P3
  planning decomposes scope into tasks.
- **RTM** — Requirements Traceability Matrix. The `traceability.csv` artifact that
  links acceptance criteria to tests and changed files.

## See also

- `references/complexity-model.md` — CAS scoring in full, with worked examples
- `references/modification-policy.md` — M0–M4 and allowlists in practice
- `references/handoff-protocol.md` — dispatch/return envelope field-by-field
- `references/pmbok-mapping.md` — the full standards traceability
- `references/agents-models.yaml` — normative values for every term above
