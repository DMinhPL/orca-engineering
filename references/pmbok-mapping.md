# Standards Traceability

This file exists so that anyone auditing the pod can see that the workflow is a
tailoring of recognised practice rather than an invented process — and so that when
someone asks "why do we do a gate here", the answer is a citation rather than a
preference.

Sources: *PMBOK® Guide* 8th edition (performance domains and processes), *PMBOK®
Guide* 7th edition (principles, tailoring), *Agile Practice Guide* (adaptive
delivery), and *The Standard for Artificial Intelligence in PPPM* (HITL, AI
governance).

## Tailoring statement

PMBOK is explicit that tailoring — deliberately adapting approach, governance and
processes to the work at hand — is expected, and the 8th edition adds tailoring
considerations per performance domain. Orca is a tailoring for **small, high-frequency
software tasks executed by a four-agent pod (Lead, BA, Dev, QC)**. The adaptations are:

1. **The "project" is a work item.** Charter, plan, and closeout are compressed to
   fit a unit of work measured in hours, not months.
2. **Resources are agents.** The Resources domain is applied to model capacity and
   role assignment rather than to people and equipment.
3. **Finance is compute.** Token and quota consumption is the cost baseline; the
   reasoning tier is the resource-levelling decision. Budget guards are reserve
   analysis.
4. **Ceremony scales with the CAS band.** PMBOK's tailoring consideration "project
   size and complexity — determine if complexity necessitates a more detailed
   approach or if a simplified process suffices" is operationalised as the size table.
5. **Adaptive by default, predictive at the gates.** Backlog-style change handling for
   ordinary work (per the Agile Practice Guide and PMBOK's adaptive change guidance),
   formal change requests once a baseline exists — schema, public API, security config.

## Phase → performance domain → process

| Orca phase | Performance domain | PMBOK 8th processes tailored |
|---|---|---|
| **P0 Intake** | Governance, Scope | Develop Project Charter (mini); Plan Scope Management |
| **P1 Analyse** | Scope, Stakeholders | Elicit and Analyze Requirements; Define Scope |
| **P2 Risk** | Risk | Plan Risk Management; Identify Risks; Perform Risk Analysis; Plan Risk Responses |
| **P3 Plan** | Scope, Schedule, Resources, Finance | Develop Scope Structure (WBS); Estimate Activity Resources; Acquire Resources; Determine Budget |
| **P4 Build** | Scope, Risk | Direct and Manage Project Work; Implement Risk Responses |
| **P5 Verify** | Scope (quality) | Manage Quality Assurance; Monitor and Control Scope; Validate Scope |
| **P6 Integrate** | Governance, Stakeholders | Manage Communications; Assess and Implement Changes |
| **P7 Close** | Governance | Close Project or Phase; lessons learned register |
| **Any — change control** | Governance, Scope | Assess and Implement Changes (integrated change control) |
| **Any — escalation** | Risk, Governance | Monitor Risks; escalation paths per the AI standard |

## Principle → mechanism

PMBOK 8th principles, and where each one is actually implemented in Orca rather than
merely admired:

| Principle | Orca mechanism |
|---|---|
| **Adopt a holistic view** | Blast-radius analysis (D3), contract impact statement, `follow_ups` capture of adjacent debt |
| **Focus on value** | CAS-scaled ceremony; XS items get four sentences of process, not four documents |
| **Embed quality into processes and deliverables** | Independent verification (Echo ≠ Fluke ≠ Breach); acceptance criteria written before code; tests traced to AC IDs |
| **Be an accountable leader** | Orca is accountable for every phase; accountability never rotates; decision log |
| **Integrate sustainability within all project areas** | Compute budget guards; de-escalation after clean phases; treating quota as a finite resource |
| **Build an empowered culture** | Agents are authorised to escalate by protocol, not by permission; `escalate_when` is pre-authorisation |

## Risk domain mapping

The risk sub-skill implements the six Risk processes directly:

| PMBOK process | Orca implementation |
|---|---|
| Plan Risk Management | Size band determines register depth; `orca.config.yaml` holds thresholds |
| Identify Risks | Prompt list by category (technical, data, integration, security, operational, schedule, opportunity); separates genuine risks from concerns and issues |
| Perform Risk Analysis | Probability × impact matrix; quantitative only where the item warrants it |
| Plan Risk Responses | Threat strategies (avoid, transfer, mitigate, escalate, accept) and opportunity strategies (exploit, share, enhance, escalate, accept) |
| Implement Risk Responses | Responses become WBS tasks in the execution plan with named owners |
| Monitor Risks | Trigger conditions checked at each phase gate; register updated at P5 and P7 |

PMBOK's note that risk identification is necessarily iterative and incomplete at the
outset is why Orca re-scores rather than treating the P2 register as final.

## Change control mapping

PMBOK's change flow — request → impact analysis across scope, schedule, finance,
resources, stakeholders, risk → approve / reject / defer / more information — is the
literal structure of `skills/orca-change-control/SKILL.md`. Two paths, per PMBOK's
predictive/adaptive split:

- **Adaptive path** (default): the change becomes a backlog item; prioritisation *is*
  the decision; low priority means deferred, not added means rejected.
- **Predictive path** (once a baseline exists): a formal change request with cost and
  schedule impact, dispositioned by the human acting as change control authority.

## AI standard mapping

| AI standard concept | Orca mechanism |
|---|---|
| Human-in-the-loop | Gates G1–G6; humans can hold, revise, or reverse any decision at any point |
| Defined intervention triggers | The escalation trigger table |
| Documented escalation protocols | The ladder, written in advance, not improvised |
| Traceability and auditability | Decision log, handoff trail, RTM, WI-referenced commits |
| Continuous monitoring and adaptation | Re-scoring on triggers; calibration review at P7 |
| Governance and compliance guardrails | Protected paths, absolute prohibitions, M4 tier |
| Accountability distribution | RACI; single accountable role per phase |
| Hallucination risk | Independent verification; acceptance criteria as the source of truth rather than the implementer's account of its own work |

## What Orca deliberately does not do

Honest tailoring includes naming the omissions:

- **No procurement domain.** Adding a paid dependency is handled as an M3/M4 gate, not
  a procurement process.
- **No earned value management.** Attempt counts and budget guards are the
  proportionate substitute at this scale.
- **No stakeholder register.** Collapsed to "the requester and the human approver".
  Scale this up if your pod serves multiple stakeholders with conflicting interests.
- **No formal quality audits.** The reviewer role plus the P7 calibration note
  substitutes; a monthly sample audit of closed work items is a reasonable addition
  if the pod's volume justifies it.

---

## Addendum — mapping to the four-role pod (config v13)

The phase names in the tables above correspond to roles and workflow modes as follows:

| Table phase | Role | Workflow position |
|---|---|---|
| P0 Intake | Lead | `classify_task`, `score_complexity`, `choose_workflow_mode` |
| P1 Analyse | BA | `requirement_analysis`, `acceptance_criteria` |
| P2 Risk | BA | `risk_analysis`, `blast_radius_analysis` |
| P3 Plan | Lead + BA | `grant_modification_tier`, allowlist, definition of done |
| P4 Build | Dev | `implementation` |
| P5 Verify | QC | `execute_quality_validation`, `risk_based_review` |
| P6 Integrate | Dev + Lead | `development_document`, gate G6 |
| P7 Close | Lead | `documentation.status_gate`, `retrospective` |
| Change control | Lead | `change_control` |

Risk analysis is a BA responsibility rather than a separate role, and review is a QC
responsibility rather than a separate role. PMBOK does not require one person per
process — it requires that each process has a single accountable owner, which
`communication.rules.every_specialist_reports_only_to_lead` satisfies by making Lead
accountable throughout.

### Where the v13 additions map

| v13 block | Standard |
|---|---|
| `complexity_assessment` | PMBOK tailoring: "determine if the project's size or complexity necessitates a more detailed approach or if a simplified process suffices" |
| `modification_policy` | Configuration management plan — which artifacts are under control and how changes to them are authorised |
| `human_gates` | PMI AI standard: humans retain the capability to hold, revise or reverse decisions; escalation paths defined in advance |
| `change_control` | Assess and Implement Changes — request, impact across scope/schedule/cost/resources/risk, disposition approved/rejected/deferred/more-information |
| `traceability` | Requirements traceability matrix |
| `evidence_policy` | PMI AI standard: hallucination risk and traceable links between inputs and AI-driven results |
| `budgets` | Reserve analysis, applied to compute rather than money |
| `decision_log` | Auditability and accountability distribution |
| `retrospective` | Lessons learned register; continuous monitoring and adaptation |
