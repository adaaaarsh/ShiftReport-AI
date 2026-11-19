"""Non-LLM baseline: a rule-based extractor that writes the same report format.

It does what a conventional keyword/regex system would do: find machine references
with patterns and the registry, assign severity from keyword lists, copy times, and
list each sentence as the issue text. It has no notion of ambiguity or contradiction.
This gives the paper a classical comparator for machine-ID accuracy and fabrication.

Usage: python baseline.py   ->  outputs/reports/<scenario>_baseline_rules_r1.md
"""
import json, re
from providers import ROOT

EQ = json.loads((ROOT / "equipment.json").read_text())
LINES = {"a": "Line A", "b": "Line B", "c": "Line C"}
ALIASES = {  # registry name keywords -> candidate ids (resolved by line when possible)
    "mill": ["M-01", "M-07"], "lathe": ["M-02"], r"press\b": ["M-03"], "molder": ["M-04"], "conveyor": ["M-05"],
    "robot": ["M-06"], "weld": ["M-06"], "packag": ["M-08"], "scanner": ["M-09"], "oven": ["M-10"],
    "coolant": ["M-11"], "pump": ["M-11"], "compressor": ["M-12"], "generator": ["M-13"], "hvac": ["M-14"],
    "forklift 1": ["M-15"], "fl1": ["M-15"], "forklift 2": ["M-16"], "fl2": ["M-16"],
}
SEV = [("CRITICAL", ["interlock", "guard", "injur", "burn", "fire", "lockout", "locked out", "bypass", "near miss"]),
       ("HIGH", ["down", "stopped", "out of service", "tagged out", "leak", "overload", "tripped", "out of tolerance", "under-cured", "grind"]),
       ("MEDIUM", ["slow", "noise", "sound", "alarm", "error", "low", "flicker", "whin", "rattl", "chatter"]),
       ("LOW", [])]
BY_ID = {e["id"]: e for e in EQ}


def find_ids(sentence):
    s = sentence.lower(); ids = set()
    for m in re.finditer(r"\bm-?(\d{1,2})\b", s):
        ids.add(f"M-{int(m.group(1)):02d}")
    for m in re.finditer(r"machine\s+(\d{1,2})", s):
        ids.add(f"M-{int(m.group(1)):02d}")
    line = next((LINES[k] for k in LINES if re.search(rf"\b(line|on)\s+{k}\b", s)), None)
    for kw, cands in ALIASES.items():
        if re.search(rf"\b{kw}", s):
            in_line = [c for c in cands if line and BY_ID[c]["line"] == line]
            ids.add((in_line or cands)[0])
    return sorted(ids)


def severity(sentence):
    s = sentence.lower()
    return next(level for level, kws in SEV if not kws or any(k in s for k in kws))


def report(text):
    sentences = [x.strip() for x in re.split(r"(?<=[.!?])\s+|\n", text) if x.strip()]
    out = ["# SHIFT HANDOVER REPORT", "**Date:** Not specified", "**Shift:** Not specified", "", "## ISSUES & EVENTS"]
    n = 0
    for sent in sentences:
        for mid in find_ids(sent):
            n += 1
            e = BY_ID.get(mid, {"name": "Unknown equipment", "line": "Unknown"})
            t = re.search(r"\b\d{1,2}:\d{2}\s*(?:am|pm)?|\b\d{1,2}\s*(?:am|pm)\b", sent, re.I)
            out += [f"### {n}. {mid} — {e['name']} ({e['line']})", f"- **Issue:** {sent}",
                    f"- **Severity:** {severity(sent)}", f"- **Time Noticed:** {t.group(0) if t else 'Not specified'}", ""]
    if n == 0:
        out += ["No equipment issues identified."]
    return "\n".join(out)


def main():
    scenarios = json.loads((ROOT / "scenarios.json").read_text())["scenarios"]
    out = ROOT / "outputs" / "reports"; out.mkdir(parents=True, exist_ok=True)
    for s in scenarios:
        (out / f"{s['id']}_baseline_rules_r1.md").write_text(report(s["input"]))
    print(f"wrote {len(scenarios)} baseline reports")


if __name__ == "__main__":
    main()
