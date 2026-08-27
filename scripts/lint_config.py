#!/usr/bin/env python3
"""
Orca — config lint.

The staleness risk in a multi-file rulebook is that a number gets restated in prose
and then the YAML changes underneath it. Conventions do not prevent that; a check
that runs does. Wire this into CI or a pre-commit hook.

Checks:
  C1  model identifiers restated outside the YAML
  C2  effort levels restated outside the YAML
  C3  workflow-mode flows restated outside the YAML
  C4  dotted YAML paths referenced in prose that do not resolve
  C5  enumerated vocabulary used in prose but never defined in the YAML
  C6  YAML internal integrity (band coverage, mode/type mapping, gate references)
  C7  config_version has a matching CHANGELOG.md entry

Usage:
    python scripts/lint_config.py                 # lint the whole skillset
    python scripts/lint_config.py --root . --strict
"""

import argparse
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("lint: pyyaml required (pip install pyyaml)", file=sys.stderr)
    sys.exit(2)

YAML_REL = "references/agents-models.yaml"

# Files allowed to name a model: the YAML itself, the review (which discusses the
# config), and envelope examples that must show a concrete dispatch to be useful.
CHANGELOG_REL = "CHANGELOG.md"

MODEL_EXEMPT = {YAML_REL, CHANGELOG_REL, "REVIEW.md", "REVIEW-workflows.md",
                "references/handoff-protocol.md"}
FLOW_EXEMPT = {YAML_REL, CHANGELOG_REL, "REVIEW.md", "REVIEW-workflows.md", "workflows.md"}

EFFORTS = ["low", "medium", "high", "xhigh"]


class Lint:
    def __init__(self, root: Path, strict: bool):
        self.root, self.strict = root, strict
        self.findings = []
        self.ypath = root / YAML_REL
        self.ytext = self.ypath.read_text(encoding="utf-8")
        self.y = yaml.safe_load(self.ytext)

    def add(self, sev, code, where, msg):
        self.findings.append((sev, code, where, msg))

    def files(self):
        for p in sorted(self.root.rglob("*.md")):
            if ".git" in p.parts:
                continue
            yield p, p.relative_to(self.root).as_posix()

    # C1 — model identifiers
    def c1(self):
        models = sorted(set(re.findall(
            r"\bgpt-[0-9]+\.[0-9]+(?:-[a-z]+)?\b|\bclaude-(?:sonnet|opus|haiku)-[0-9]+\b",
            self.ytext)))
        # Bare capitalised family names are the sneakier duplication: "Terra `high`"
        families = sorted({m.split("-")[-1].capitalize() for m in models if "-" in m}
                          - {"5", "5.5", "5.6"})
        for p, rel in self.files():
            if rel in MODEL_EXEMPT:
                continue
            txt = p.read_text(encoding="utf-8")
            for m in models:
                if m in txt:
                    self.add("ERROR", "C1", rel,
                             f"model identifier '{m}' restated outside the YAML; "
                             f"reference the config key instead")
            for f in families:
                if re.search(rf"\b{f}\b\s+`?(?:{'|'.join(EFFORTS)})`?", txt):
                    self.add("ERROR", "C1", rel,
                             f"model family '{f}' paired with an effort level outside "
                             f"the YAML; this is the same number in prose form")

    # C2 — effort defaults restated
    def c2(self):
        pat = re.compile(
            rf"\b(Lead|BA|Dev|QC)\b[^.\n]{{0,40}}\b(?:default)\b[^.\n]{{0,40}}\b({'|'.join(EFFORTS)})\b",
            re.I)
        for p, rel in self.files():
            if rel in MODEL_EXEMPT:
                continue
            for role, eff in pat.findall(p.read_text(encoding="utf-8")):
                self.add("ERROR", "C2", rel,
                         f"'{role} default ... {eff}' restates agents.{role.lower()}.effort")

    # C3 — flows restated
    def c3(self):
        flows = {m: " -> ".join(v["flow"]) for m, v in self.y["workflow_modes"].items()}
        arrow = re.compile(r"(?:User|user)\s*(?:->|→)\s*(?:Lead|lead)[^\n]*")
        for p, rel in self.files():
            if rel in FLOW_EXEMPT:
                continue
            for line in arrow.findall(p.read_text(encoding="utf-8")):
                norm = re.sub(r"\s+", " ", line.lower().replace("→", "->")).strip()
                for m, f in flows.items():
                    if norm.startswith("user -> " + f.split(" -> ", 0)[0]) and norm.count("->") >= 2:
                        self.add("WARN", "C3", rel,
                                 f"workflow flow written out in prose; "
                                 f"workflow_modes.{m}.flow is authoritative")
                        break

    # C4 — dotted references resolve
    def c4(self):
        def resolve(path, cur=None):
            cur = self.y if cur is None else cur
            parts = path.split(".")
            for i, part in enumerate(parts):
                if part == "*":                       # any key at this level must match the rest
                    rest = ".".join(parts[i + 1:])
                    if not isinstance(cur, dict):
                        return False
                    return any(resolve(rest, v) for v in cur.values()) if rest else True
                if isinstance(cur, dict) and part in cur:
                    cur = cur[part]
                elif isinstance(cur, list) and part in [str(i) for i in cur if isinstance(i, str)]:
                    return True
                else:
                    return False
            return True

        for p, rel in self.files():
            for ref in set(re.findall(r"`([a-z_]+(?:\.[a-z_0-9\*\[\]]+)+)`", p.read_text(encoding="utf-8"))):
                head = ref.split(".")[0]
                if head not in self.y:
                    continue
                if not resolve(ref.replace("[", ".").replace("]", "")):
                    self.add("WARN", "C4", rel, f"reference '{ref}' does not resolve in the YAML")

    # C5 — vocabulary used but undefined
    def c5(self):
        defined = self.ytext
        vocab = {
            "worker_done": "dispatch_lifecycle.events",
            "run-use": "coordinator_resume.procedure",
            "check --wait": "dispatch_lifecycle.wait_loop.mechanism",
            "Draft": "document_status.values",
            "Implemented": "document_status.values",
            "P0": "engineering_policy.defect_severity",
        }
        for p, rel in self.files():
            txt = p.read_text(encoding="utf-8")
            for term, home in vocab.items():
                key = term.lower().replace(" ", "_").replace("--", "").replace("-", "_")
                if term in txt and key not in defined.lower():
                    self.add("ERROR", "C5", rel,
                             f"'{term}' used in prose but not defined in the YAML "
                             f"(expected under {home})")

    # C6 — YAML internal integrity
    def c6(self):
        rel = YAML_REL
        ca = self.y.get("complexity_assessment", {})
        bands = [v["range"] for v in ca.get("bands", {}).values()]
        if bands:
            ok = bands[0][0] == 0 and bands[-1][1] == 21 and all(
                bands[i][1] + 1 == bands[i + 1][0] for i in range(len(bands) - 1))
            if not ok:
                self.add("ERROR", "C6", rel, "complexity bands are not contiguous over 0-21")

        modes = set(self.y["workflow_modes"])
        tc = self.y["engineering_policy"]["task_classification"]
        types, m = set(tc["types"]), tc.get("default_mode_by_type", {})
        if types - set(m):
            self.add("ERROR", "C6", rel, f"task types with no default mode: {sorted(types - set(m))}")
        if set(m.values()) - modes:
            self.add("ERROR", "C6", rel, f"modes referenced but undefined: {sorted(set(m.values()) - modes)}")

        # Branch category must cover every task type, and name a defined category.
        bn = self.y.get("modification_policy", {}).get("branch_naming", {})
        if bn:
            cats, by_type = set(bn.get("categories", {})), bn.get("category_by_task_type", {})
            if types - set(by_type):
                self.add("ERROR", "C6", rel,
                         f"task types with no branch category: {sorted(types - set(by_type))}")
            unknown = set(by_type.values()) - cats
            if unknown:
                self.add("ERROR", "C6", rel,
                         f"branch categories used but undefined: {sorted(unknown)}")

        gates = {g.split("_")[0] for g in self.y.get("human_gates", {}).get("gates", {})}
        refd = set(re.findall(r"\bG[1-9]\b", self.ytext))
        if refd - gates:
            self.add("ERROR", "C6", rel, f"gates referenced but undefined: {sorted(refd - gates)}")

        for mode, spec in self.y["workflow_modes"].items():
            flow = spec["flow"]
            if flow[0] != "lead" or flow[-1] != "user":
                self.add("ERROR", "C6", rel, f"mode '{mode}' does not start at lead and end at user")
            for i in range(len(flow) - 1):
                if flow[i] not in ("lead", "user") and flow[i + 1] not in ("lead", "user"):
                    self.add("ERROR", "C6", rel,
                             f"mode '{mode}': {flow[i]} -> {flow[i+1]} is a specialist-to-specialist "
                             f"edge, forbidden by communication.deny")

    # C7 — the changelog tracks the config
    def c7(self):
        cur = self.y.get("config_version")
        path = self.root / CHANGELOG_REL
        if not path.exists():
            self.add("ERROR", "C7", CHANGELOG_REL,
                     f"missing; config_version {cur} has nowhere to be recorded")
            return

        text = path.read_text(encoding="utf-8")
        versions = {int(m) for m in re.findall(r"^##\s*v(\d+)\b", text, re.M)}
        if cur not in versions:
            self.add("ERROR", "C7", CHANGELOG_REL,
                     f"no '## v{cur}' entry for config_version {cur}; "
                     f"bumping the version without recording the change is how the "
                     f"history stops being trustworthy")
        # A version documented but never shipped is the same drift in reverse.
        ahead = {v for v in versions if isinstance(cur, int) and v > cur}
        if ahead:
            self.add("WARN", "C7", CHANGELOG_REL,
                     f"entries ahead of config_version {cur}: {sorted(ahead)}")

    def run(self):
        for c in (self.c1, self.c2, self.c3, self.c4, self.c5, self.c6, self.c7):
            c()
        return self.findings


def main():
    ap = argparse.ArgumentParser(description="Orca config lint")
    ap.add_argument("--root", default=".")
    ap.add_argument("--strict", action="store_true", help="treat WARN as failure")
    a = ap.parse_args()

    root = Path(a.root).resolve()
    if not (root / YAML_REL).exists():
        print(f"lint: {YAML_REL} not found under {root}", file=sys.stderr)
        return 2

    findings = Lint(root, a.strict).run()
    errors = [f for f in findings if f[0] == "ERROR"]
    warns = [f for f in findings if f[0] == "WARN"]

    for sev, code, where, msg in sorted(findings):
        print(f"{sev:5s} {code}  {where}\n        {msg}")

    print(f"\n{len(errors)} error(s), {len(warns)} warning(s)")
    if errors or (a.strict and warns):
        return 1
    print("config is single-sourced")
    return 0


if __name__ == "__main__":
    sys.exit(main())
