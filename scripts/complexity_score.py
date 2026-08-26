#!/usr/bin/env python3
"""
Orca — Complexity Assessment Score

Mirrors complexity_assessment in references/agents-models.yaml.
The YAML is normative; if they disagree, the YAML wins.

Deterministic scorer so two agents sizing the same request land in the same band.
Scoring rubric lives in references/complexity-model.md.

Usage:
    python complexity_score.py --triage --d2 0 --d3 0 --d7 0
    python complexity_score.py --d1 2 --d2 1 --d3 3 --d4 2 --d5 2 --d6 1 --d7 2
    python complexity_score.py --d1 2 ... --override security_boundary_change
    python complexity_score.py --interactive
    python complexity_score.py --json --d1 0 --d2 0 --d3 0 --d4 0 --d5 0 --d6 0 --d7 0
"""

import argparse
import json
import sys

DIMENSIONS = {
    "d1": ("Scope breadth", "files/modules touched"),
    "d2": ("Requirement ambiguity", "how much we don't know about the WHAT"),
    "d3": ("Blast radius / criticality", "what breaks if this is wrong"),
    "d4": ("Integration surface", "external parties that must agree"),
    "d5": ("Verification difficulty", "how hard to PROVE it works"),
    "d6": ("Novelty / unknowns", "precedent in this repo"),
    "d7": ("Reversibility", "cost of undo"),
}

BANDS = [
    (0, 3, "XS", "low", "M2", False),
    (4, 7, "S", "low", "M2", False),
    (8, 12, "M", "medium", "M3", "on_M3"),
    (13, 16, "L", "high", "M3", True),
    (17, 21, "XL", "high", "M4", True),
]

HARD_OVERRIDES = [
    "irreversible_or_destructive",
    "security_boundary_change",
    "secrets_or_credentials",
    "pii_or_regulated_data",
    "production_schema_change",
    "public_api_contract_change",
    "infrastructure_or_deployment",
    "licensing_or_compliance",
    "protected_path_in_diff",
]

# Mirrors complexity_assessment.bands in references/agents-models.yaml.
MODE = {
    "XS": ("simple",   "simple",  "M2"),
    "S":  ("simple",   "simple",  "M2"),
    "M":  ("standard", "normal",  "M3"),
    "L":  ("standard", "complex", "M3"),
    "XL": ("standard", "complex", "M4"),
}
ACTION = {"XL": "DECOMPOSE into child tasks and re-score each"}


# Mirrors complexity_assessment.triage. The three dimensions that carry the safety
# signal; d1/d4/d5/d6 tune profile and effort and are skipped when these are clean.
TRIAGE_DIMS = ["d2", "d3", "d7"]


def band_for(total):
    for lo, hi, name, tier, mod, gate in BANDS:
        if lo <= total <= hi:
            return {"size": name, "effort_floor": tier, "max_mod_tier": mod, "human_gate": gate}
    raise ValueError(f"total {total} out of range 0-21")


def triage(scores, overrides=None):
    """Progressive scoring gate — complexity_assessment.triage.

    Hard overrides are checked first and unconditionally: they are a path/keyword
    match, not a judgement, and they are what stops a two-line auth change from
    taking the fast path. The fast path fires only on unanimous zero.
    """
    overrides = overrides or []
    for k in TRIAGE_DIMS:
        v = scores.get(k)
        if v is None or not 0 <= v <= 3:
            raise ValueError(f"{k}={v} out of range 0-3")

    if overrides:
        return {
            "fast_path": False,
            "reason": f"hard override matched: {', '.join(overrides)}",
            "next": "score all seven dimensions",
            "triage_dimensions": {k: scores[k] for k in TRIAGE_DIMS},
            "overrides": list(overrides),
        }

    nonzero = [f"{k}={scores[k]}" for k in TRIAGE_DIMS if scores[k]]
    if nonzero:
        return {
            "fast_path": False,
            "reason": f"triage dimension non-zero: {', '.join(nonzero)}",
            "next": "score all seven dimensions",
            "triage_dimensions": {k: scores[k] for k in TRIAGE_DIMS},
        }

    mode, profile, cap = MODE["XS"]
    r = band_for(0)
    r.update({
        "fast_path": True,
        "total": 0,
        "recorded_as": "fast-path (d2/d3/d7 = 0, no hard override)",
        "triage_dimensions": dict.fromkeys(TRIAGE_DIMS, 0),
        "dimensions_not_scored": ["d1", "d4", "d5", "d6"],
        "max_mod_tier": cap,
        "workflow_mode": mode,
        "complexity_profile": profile,
        "notes": ["d1/d4/d5/d6 deliberately not scored; d5 omission is valid only "
                  "because d3 = 0"],
    })
    return r


def score(scores, overrides=None):
    overrides = overrides or []
    for k, v in scores.items():
        if not 0 <= v <= 3:
            raise ValueError(f"{k}={v} out of range 0-3")

    total = sum(scores.values())
    result = band_for(total)
    result.update({"total": total, "dimensions": dict(scores), "notes": []})

    # Implicit hard overrides from the dimension scores themselves
    implicit = []
    if scores["d3"] == 3:
        implicit.append("d3=3 (critical blast radius)")
    if scores["d7"] == 3:
        implicit.append("d7=3 (irreversible)")

    all_overrides = list(overrides) + implicit

    if all_overrides:
        order = ["XS", "S", "M", "L", "XL"]
        if order.index(result["size"]) < order.index("L"):
            result["notes"].append(
                f"HARD OVERRIDE raised size {result['size']} -> L: {', '.join(all_overrides)}"
            )
            result.update({"size": "L", "effort_floor": "high", "max_mod_tier": "M3"})
        else:
            result["notes"].append(f"hard override active: {', '.join(all_overrides)}")
        result["human_gate"] = True
        result["overrides"] = all_overrides

    # Soft downward override: wide but perfectly specified and precedented
    elif scores["d2"] == 0 and scores["d6"] == 0 and scores["d3"] <= 1 and scores["d7"] <= 1:
        driven_by_breadth = scores["d1"] >= 2 and (total - scores["d1"]) <= 4
        if driven_by_breadth:
            order = ["XS", "S", "M", "L", "XL"]
            i = order.index(result["size"])
            if i > 0:
                smaller = order[i - 1]
                result["notes"].append(
                    f"SOFT OVERRIDE {result['size']} -> {smaller}: voluminous but "
                    "fully specified and precedented; route to a code-generation agent "
                    "at low tier with a tight allowlist"
                )
                result.update(band_for({"XS": 2, "S": 5, "M": 10, "L": 14}[smaller]))
                result["total"] = total
                result["dimensions"] = dict(scores)

    mode, profile, cap = MODE[result["size"]]
    result["workflow_mode"] = mode
    result["complexity_profile"] = profile
    if _tier_index(cap) < _tier_index(result["max_mod_tier"]):
        result["max_mod_tier"] = cap
    if result["size"] in ACTION:
        result["notes"].append(ACTION[result["size"]])
    return result


def _tier_index(t):
    return ["M0", "M1", "M2", "M3", "M4"].index(t)


def render(r):
    lines = []
    lines.append("┌─ CAS ─────────────────────────────────────────────")
    for k, (label, _) in DIMENSIONS.items():
        v = r["dimensions"][k]
        bar = "█" * v + "·" * (3 - v)
        lines.append(f"│ {k.upper()} {bar}  {v}  {label}")
    lines.append("├───────────────────────────────────────────────────")
    lines.append(f"│ TOTAL        {r['total']}/21")
    lines.append(f"│ SIZE         {r['size']}")
    lines.append(f"│ EFFORT FLOOR {r['effort_floor']}")
    lines.append(f"│ MAX MOD TIER {r['max_mod_tier']}")
    lines.append(f"│ HUMAN GATE   {r['human_gate']}")
    lines.append(f"│ WORKFLOW     {r['workflow_mode']}  ·  profile {r['complexity_profile']}")
    for n in r["notes"]:
        lines.append(f"│ ! {n}")
    lines.append("└───────────────────────────────────────────────────")
    return "\n".join(lines)


def render_triage(r):
    lines = ["┌─ CAS triage ──────────────────────────────────────"]
    for k in TRIAGE_DIMS:
        v = r["triage_dimensions"][k]
        label = DIMENSIONS[k][0]
        lines.append(f"│ {k.upper()} {'█' * v}{'·' * (3 - v)}  {v}  {label}")
    lines.append("├───────────────────────────────────────────────────")
    if r["fast_path"]:
        lines.append("│ FAST PATH    yes")
        lines.append(f"│ SIZE         {r['size']}  (recorded as fast-path)")
        lines.append(f"│ MAX MOD TIER {r['max_mod_tier']}")
        lines.append(f"│ WORKFLOW     {r['workflow_mode']}  ·  profile {r['complexity_profile']}")
        lines.append(f"│ NOT SCORED   {', '.join(r['dimensions_not_scored'])}")
        for n in r["notes"]:
            lines.append(f"│ ! {n}")
    else:
        lines.append("│ FAST PATH    no")
        lines.append(f"│ REASON       {r['reason']}")
        lines.append(f"│ NEXT         {r['next']}")
    lines.append("└───────────────────────────────────────────────────")
    return "\n".join(lines)


def interactive():
    print("Score each dimension 0-3. See references/complexity-model.md for the rubric.\n")
    s = {}
    for k, (label, hint) in DIMENSIONS.items():
        while True:
            try:
                raw = input(f"  {k.upper()} {label} ({hint}): ").strip()
                v = int(raw)
                if 0 <= v <= 3:
                    s[k] = v
                    break
            except (ValueError, EOFError):
                pass
            print("     -> enter 0, 1, 2, or 3")
    print("\nHard overrides (comma-separated, blank for none):")
    print("  " + ", ".join(HARD_OVERRIDES))
    raw = input("  > ").strip()
    ov = [x.strip() for x in raw.split(",") if x.strip()]
    return s, ov


def main():
    p = argparse.ArgumentParser(description="Orca CAS complexity scorer")
    for k, (label, _) in DIMENSIONS.items():
        p.add_argument(f"--{k}", type=int, help=f"{label} (0-3)")
    p.add_argument("--override", action="append", default=[], choices=HARD_OVERRIDES,
                   help="hard override flag; repeatable")
    p.add_argument("--interactive", action="store_true")
    p.add_argument("--triage", action="store_true",
                   help="progressive gate: score d2/d3/d7 only and report whether "
                        "the XS fast path applies")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    a = p.parse_args()

    if a.triage:
        s = {k: getattr(a, k) for k in TRIAGE_DIMS}
        missing = [k for k, v in s.items() if v is None]
        if missing:
            p.error(f"--triage needs: {', '.join('--' + m for m in missing)}")
        try:
            r = triage(s, a.override)
        except ValueError as e:
            print(f"error: {e}", file=sys.stderr)
            return 1
        print(json.dumps(r, indent=2) if a.json else render_triage(r))
        return 0

    if a.interactive:
        s, ov = interactive()
    else:
        s = {k: getattr(a, k) for k in DIMENSIONS}
        missing = [k for k, v in s.items() if v is None]
        if missing:
            p.error(f"missing dimensions: {', '.join(missing)} (or use --interactive)")
        ov = a.override

    try:
        r = score(s, ov)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    print(json.dumps(r, indent=2) if a.json else render(r))
    return 0


if __name__ == "__main__":
    sys.exit(main())
