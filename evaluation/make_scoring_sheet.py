"""Build blinded Excel scoring sheets for the human raters.

Sample: one report per scenario x prompt version (30 x 4 = 120), run 1, with the
generator model rotated so each of the three models contributes 40 reports and every
version gets every model equally often. Each rater gets an independently shuffled
order; reports carry only a random code. The mapping goes to
outputs/scoring/KEY_do_not_open.csv. Raters score independently and do not open it.

The first rater scores all 120. Raters listed in --subset score a balanced 60-report
subset (see reliability_subset) used for inter-rater reliability.

Usage: python make_scoring_sheet.py --raters RaterA RaterB --subset RaterB --seed 2026
"""
import argparse, csv, json, random
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation
from providers import CONFIG, ROOT, slug

DIMS = ["Accuracy", "Completeness", "Severity", "Readability", "Uncertainty"]
VERSIONS = ["v1", "v2", "v3", "v4"]


def human_sample():
    """(scenario, version, model) triples in the human-rated sample: balanced model rotation, run 1."""
    scenarios = json.loads((ROOT / "scenarios.json").read_text())["scenarios"]
    models = [slug(g["id"]) for g in CONFIG["generators"]]
    return [(s["id"], v, models[(si + vi) % len(models)]) for si, s in enumerate(scenarios) for vi, v in enumerate(VERSIONS)]


def reliability_subset():
    """Balanced 60 of the 120: within each category, scenarios alternate between {v1,v3} and {v2,v4}.
    Gives 15 per version, 20 per model, 3 per category x version and 5 per version x model."""
    scenarios = json.loads((ROOT / "scenarios.json").read_text())["scenarios"]
    seen, keep = {}, set()
    for s in scenarios:
        ci = seen.get(s["category"], 0); seen[s["category"]] = ci + 1
        keep |= {(s["id"], v) for v in (("v1", "v3") if ci % 2 == 0 else ("v2", "v4"))}
    return [t for t in human_sample() if (t[0], t[1]) in keep]


def write_sheet(out, rater, order, rubric, note=None):
    wb = Workbook(); ins = wb.active; ins.title = "Instructions"
    ins["A1"] = (f"Scoring sheet for {rater}. Score alone: do not look at any other rater's sheet or scores, "
                 "and do not discuss any report with anyone until your sheet is complete and returned.")
    ins["A1"].font = Font(bold=True)
    if note:
        ins["A2"] = note; ins["A2"].font = Font(bold=True, color="C00000")
    for i, line in enumerate(rubric.splitlines(), start=3):
        ins.cell(row=i, column=1, value=line)
    ins.column_dimensions["A"].width = 120
    ws = wb.create_sheet("Scores")
    ws.append(["Code", "Supervisor input", "Generated report"] + DIMS + ["Fabricated detail? (Y/N)", "Comment"])
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF"); c.fill = PatternFill("solid", fgColor="1F2937")
    for it in order:
        ws.append([it["code"], it["input"], it["report"]] + [None] * 7)
    for col, wdt in zip("ABCDEFGHIJ", [10, 45, 80, 11, 13, 10, 12, 12, 14, 40]):
        ws.column_dimensions[col].width = wdt
    for row in ws.iter_rows(min_row=2):
        for c in row:
            c.alignment = Alignment(wrap_text=True, vertical="top")
    sdv = DataValidation(type="whole", operator="between", formula1="1", formula2="5", allow_blank=True)
    ydv = DataValidation(type="list", formula1='"Y,N"', allow_blank=True)
    ws.add_data_validation(sdv); ws.add_data_validation(ydv)
    sdv.add(f"D2:H{len(order) + 1}"); ydv.add(f"I2:I{len(order) + 1}")
    ws.freeze_panes = "D2"
    wb.save(out / f"scoring_{rater}.xlsx")
    print(f"wrote scoring_{rater}.xlsx ({len(order)} reports)")


def reissue(name, rng):
    """Re-score the reliability subset on a fresh sheet without disturbing the primary rater's sheet or codes."""
    out = ROOT / "outputs" / "scoring"; keyp = out / "KEY_do_not_open.csv"
    if (out / f"scoring_{name}.xlsx").exists():
        raise SystemExit(f"scoring_{name}.xlsx already exists; pick a new name.")
    key = list(csv.DictReader(keyp.open()))
    used = {r["code"] for r in key}
    scen = {s["id"]: s for s in json.loads((ROOT / "scenarios.json").read_text())["scenarios"]}
    sub = {(s, v, m) for s, v, m in reliability_subset()}
    items = []
    for r in key:
        if (r["scenario"], r["version"], r["model"]) in sub and r["file"] not in {i["file"] for i in items}:
            items.append({**r, "input": scen[r["scenario"]]["input"], "report": (ROOT / "outputs" / "reports" / r["file"]).read_text()})
    assert len(items) == 60, len(items)
    pool = [c for c in range(1000, 10000) if f"R{c}" not in used]
    for it, c in zip(items, rng.sample(pool, len(items))):
        it["code"] = f"R{c}"
    with keyp.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["code", "scenario", "version", "model", "file"])
        [w.writerow({k: it[k] for k in w.fieldnames}) for it in items]
    rng.shuffle(items)
    write_sheet(out, name, items, (ROOT / "rubric.md").read_text(),
                note="Type each score and comment directly in the row of the report you just read. Do not sort, "
                     "filter, move or paste cells, and do not paste scores or comments from any other file or tool.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raters", nargs="+", default=["RaterA", "RaterB"])
    ap.add_argument("--subset", nargs="*", default=[], help="raters who score only the 60-report reliability subset")
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--reissue", metavar="NAME", help="write a fresh subset sheet scoring_NAME.xlsx with new codes and a "
                    "new order; existing sheets and key rows are left untouched (new rows are appended to the key)")
    args = ap.parse_args()
    rng = random.Random(args.seed)
    if args.reissue:
        return reissue(args.reissue, rng)

    scen = {s["id"]: s for s in json.loads((ROOT / "scenarios.json").read_text())["scenarios"]}
    rep = ROOT / "outputs" / "reports"
    items, missing = [], []
    for sid, v, m in human_sample():
        p = rep / f"{sid}_{v}_{m}_r1.md"
        if not p.exists():
            missing.append(p.name); continue
        items.append({"scenario": sid, "version": v, "model": m, "file": p.name,
                      "input": scen[sid]["input"], "report": p.read_text()})
    if missing:
        raise SystemExit(f"{len(missing)} sampled reports not generated yet, e.g. {missing[:3]}. Finish generate.py first.")
    codes = rng.sample(range(1000, 10000), len(items))
    for it, c in zip(items, codes):
        it["code"] = f"R{c}"

    out = ROOT / "outputs" / "scoring"; out.mkdir(parents=True, exist_ok=True)
    with (out / "KEY_do_not_open.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["code", "scenario", "version", "model", "file"])
        w.writeheader(); [w.writerow({k: it[k] for k in w.fieldnames}) for it in items]

    sub = {(s, v) for s, v, _ in reliability_subset()}
    rubric = (ROOT / "rubric.md").read_text()
    for rater in args.raters:
        order = items[:]; rng.shuffle(order)
        if rater in args.subset:
            order = [it for it in order if (it["scenario"], it["version"]) in sub]
        write_sheet(out, rater, order, rubric)


if __name__ == "__main__":
    main()
