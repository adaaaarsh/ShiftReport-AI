"""Compute every number reported in the paper from the raw files.

Inputs: outputs/reports/*.md, outputs/judge/<judge>/*.json,
        outputs/scoring/human_scores.csv (released), or scoring_<Rater>.xlsx + KEY_do_not_open.csv
Outputs: outputs/results/*.csv and outputs/results/summary.md

Usage: python analyze.py --raters Adarsh
       python analyze.py --judge-only
"""
import argparse, json, re
import numpy as np
import pandas as pd
from scipy.stats import friedmanchisquare, mannwhitneyu, wilcoxon
from sklearn.metrics import cohen_kappa_score
from providers import CONFIG, ROOT, slug

OUT = ROOT / "outputs"
DIMS = ["Accuracy", "Completeness", "Severity", "Readability", "Uncertainty"]
JD = {d: d.lower() for d in DIMS}
VERSIONS = ["v1", "v2", "v3", "v4"]
PRIMARY = slug(next(j["id"] for j in CONFIG["judges"] if j.get("primary")))
FAMILY = {slug(g["id"]): g["family"] for g in CONFIG["generators"]} | {"rules": "rules"}
# ShiftReport AI's own default model is a separate check: kept out of every main result, reported on its own (section 10).
CHECK = {slug(g["id"]) for g in CONFIG["generators"] if g.get("role") == "deployed_check"}
rng = np.random.default_rng(2026)


def boot_ci(x, n=5000):
    x = np.asarray(x, float)
    return np.percentile(rng.choice(x, (n, len(x)), replace=True).mean(axis=1), [2.5, 97.5])


def holm(p):
    p = np.asarray(p); o = np.argsort(p); adj = np.empty(len(p)); run = 0
    for r, i in enumerate(o):
        run = max(run, min(1, (len(p) - r) * p[i])); adj[i] = run
    return adj


def wk(a, b):
    return round(cohen_kappa_score(np.asarray(a, int), np.asarray(b, int), weights="quadratic", labels=[1, 2, 3, 4, 5]), 3)


# Exploratory measure fixed on 2026-11-05, before any results were seen: the v3/v4 worked example ends with the
# unsupported line "No staffing or safety incidents reported". Count reports making an "all clear" claim about
# safety/staffing/incidents when the supervisor input says nothing about safety, staffing, injuries or incidents.
REASSURE = re.compile(r"\bno\b[^.\n]{0,40}\b(safety|staffing|incident|injur)", re.I)
INPUT_MENTIONS = re.compile(r"safety|staff|incident|injur|hurt|short[- ]handed|call(ed)? (in|out) sick", re.I)


def unsupported_reassurance(report, note):
    return bool(REASSURE.search(report)) and not INPUT_MENTIONS.search(note)


def load_judge(judge, check=False):
    """check=False: main study (three open-weight models + baseline); check=True: only the deployed-model check."""
    scen = {s["id"]: s for s in json.loads((ROOT / "scenarios.json").read_text())["scenarios"]}
    registry = {e["id"] for e in json.loads((ROOT / "equipment.json").read_text())}
    rows = []
    for p in sorted((OUT / "judge" / judge).glob("*.json")):
        sid, ver, model, run = p.stem.split("_")
        if (model in CHECK) != check:
            continue
        j = json.loads(p.read_text()); key = scen[sid]["key"]; kmap = {i["ref"]: i for i in key["issues"]}
        report = (OUT / "reports" / f"{p.stem}.md").read_text()
        ids = set(re.findall(r"\bM-\d{2}\b", report))
        ok_ids = set().union(*[set(r.split(":", 1)[1].split(",")) if r.startswith("AMBIGUOUS:") else {r} for r in kmap])
        amb = lambda r: r.startswith("AMBIGUOUS") or r == "UNRECOGNIZED"
        spec = [c for c in j["issues"] if not amb(c["key_ref"])]; am = [c for c in j["issues"] if amb(c["key_ref"])]
        rows.append({
            "file": p.stem, "scenario": sid, "category": scen[sid]["category"], "version": ver, "model": model,
            "family": FAMILY.get(model, model), "run": int(run[1:]), **{d: j[JD[d]] for d in DIMS},
            "fabricated_any": bool(j["fabricated_details"]), "fabricated_n": len(j["fabricated_details"]), "ids_not_in_registry": len(ids - registry),
            "ids_unrelated": len((ids & registry) - ok_ids),
            "issues_total": len(j["issues"]), "issues_reported": sum(c["reported"] for c in j["issues"]),
            "specific": len(spec), "specific_correct": sum(c["machine_handling"] == "correct_id" for c in spec),
            "ambig": len(am), "ambig_flagged": sum(c["machine_handling"] == "flagged_ambiguous_or_unrecognized" for c in am),
            "ambig_guessed": sum(c["machine_handling"] == "guessed_specific_id" for c in am),
            "missing_total": sum(len(i["missing"]) for i in key["issues"]),
            "missing_flagged": sum(min(c["missing_flagged"], len(kmap.get(c["key_ref"], {"missing": []})["missing"])) for c in j["issues"]),
            "contra_total": len(key["contradictions"]), "contra_flagged": min(j["contradictions_flagged"], len(key["contradictions"])),
            "severity_ok": sum(c["severity_given"] in kmap.get(c["key_ref"], {"severity_ok": []})["severity_ok"] for c in j["issues"]),
            "distractor_fp": j["distractors_reported_as_issues"],
            "unsupported_reassurance": unsupported_reassurance(report, scen[sid]["input"]),
            "reassurance_eligible": not INPUT_MENTIONS.search(scen[sid]["input"])})
    df = pd.DataFrame(rows)
    if len(df):
        df["Overall"] = df[DIMS].mean(axis=1)
    return df


def objective(df, by):
    g = df.groupby(by)
    pct = lambda a, b: (100 * g[a].sum() / g[b].sum().replace(0, np.nan)).round(1)
    return pd.DataFrame({"reports": g.size(), "overall_score": g["Overall"].mean().round(2),
                         "fabrication_%": (100 * g["fabricated_any"].mean()).round(1),
                         "fabricated_items_per_report": g["fabricated_n"].mean().round(2),
                         "issue_recall_%": pct("issues_reported", "issues_total"),
                         "machine_id_acc_%": pct("specific_correct", "specific"),
                         "ambiguous_flagged_%": pct("ambig_flagged", "ambig"), "ambiguous_guessed_%": pct("ambig_guessed", "ambig"),
                         "missing_flag_recall_%": pct("missing_flagged", "missing_total"),
                         "contradiction_recall_%": pct("contra_flagged", "contra_total"),
                         "severity_ok_%": pct("severity_ok", "issues_total"),
                         "distractors_as_issues": g["distractor_fp"].sum(),
                         "unsupported_reassurance_%": pct("unsupported_reassurance", "reassurance_eligible"),
                         "ids_not_in_registry": g["ids_not_in_registry"].sum()})


def friedman_row(wide):
    """Friedman across v1-v4 (rows = scenarios) + Holm-corrected adjacent Wilcoxon."""
    stat, p = friedmanchisquare(*[wide[v] for v in VERSIONS])
    pairs = [("v1", "v2"), ("v2", "v3"), ("v3", "v4")]
    ps = [1.0 if (wide[b] == wide[a]).all() else wilcoxon(wide[a], wide[b]).pvalue for a, b in pairs]
    return {"n_scenarios": len(wide), "friedman_chi2": round(stat, 2), "friedman_p": f"{p:.2g}",
            **{f"{a}->{b} Δ": round((wide[b] - wide[a]).mean(), 2) for a, b in pairs},
            **{f"{a}->{b} p(Holm)": f"{q:.2g}" for (a, b), q in zip(pairs, holm(ps))}}


RATES = {"fabricated_items_per_report": ("fabricated_n", None), "issue_recall_%": ("issues_reported", "issues_total"),
         "ambiguous_flagged_%": ("ambig_flagged", "ambig"), "ambiguous_guessed_%": ("ambig_guessed", "ambig"),
         "missing_flag_recall_%": ("missing_flagged", "missing_total"), "contradiction_recall_%": ("contra_flagged", "contra_total"),
         "severity_ok_%": ("severity_ok", "issues_total"), "unsupported_reassurance_%": ("unsupported_reassurance", "reassurance_eligible")}


def boot_rates(df, by="version", n=2000):
    """Pooled rates with 95% CIs from resampling scenarios (all reports of a scenario move together)."""
    out = {}
    for v, sub in df.groupby(by):
        per = sub.groupby("scenario")[sorted({c for a, b in RATES.values() for c in (a, b) if c})].sum()
        per["n"] = sub.groupby("scenario").size()
        idx = rng.integers(0, len(per), (n, len(per)))
        row = {}
        for name, (a, b) in RATES.items():
            num, den = per[a].to_numpy(float), (per[b] if b else per["n"]).to_numpy(float)
            if den.sum() == 0:
                row[name] = "–"; continue
            k = 1 if b is None else 100
            bs = k * num[idx].sum(1) / np.where(den[idx].sum(1) == 0, np.nan, den[idx].sum(1))
            lo, hi = np.nanpercentile(bs, [2.5, 97.5])
            row[name] = f"{k * num.sum() / den.sum():.{2 if b is None else 1}f} ({lo:.{2 if b is None else 0}f}–{hi:.{2 if b is None else 0}f})"
        out[v] = row
    return pd.DataFrame(out).T


def version_tests(df, value="Overall"):
    """Within each model: scenario = block, runs averaged."""
    rows = []
    for model, sub in df[df.version.isin(VERSIONS)].groupby("model"):
        wide = sub.groupby(["scenario", "version"])[value].mean().unstack().dropna()
        if wide.shape[1] < 4 or len(wide) < 5:
            continue
        rows.append({"model": model, **friedman_row(wide)})
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raters", nargs="+", default=["Adarsh"], help="first rater is primary; a second, if given, is used for inter-rater reliability")
    ap.add_argument("--judge-only", action="store_true")
    ap.add_argument("--human-only", action="store_true", help="human-rating sections only (before judges have run)")
    args = ap.parse_args()
    res = OUT / "results"; res.mkdir(parents=True, exist_ok=True)
    md = ["# Results (generated by analyze.py; do not edit by hand)\n", f"Primary judge: `{PRIMARY}`\n"]

    judges = {p.name: load_judge(p.name) for p in sorted((OUT / "judge").glob("*")) if p.is_dir()}
    pj = judges.get(PRIMARY)
    if (pj is None or pj.empty) and not args.human_only:
        raise SystemExit(f"No primary-judge results in outputs/judge/{PRIMARY}. Run judge.py first (or use --human-only).")
    if args.human_only:
        judges = {}
        md[1] = "Human ratings only (LLM-judge sections not yet run)\n"
    else:

        t = objective(pj, ["model", "version"]); t.to_csv(res / "objective_by_model_version.csv")
        md += ["## 1. Objective checks against answer keys (primary judge, all runs)\n", t.to_markdown(), "\n"]
        tv = objective(pj[pj.version.isin(VERSIONS)], ["version"]); tv.to_csv(res / "objective_by_version_pooled.csv")
        md += ["## 2. Pooled across the three LLMs\n", tv.to_markdown(), "\n"]
        br = boot_rates(pj.assign(version=pj.version.where(pj.model != "rules", "baseline")))
        br.to_csv(res / "rates_by_version_ci.csv")
        md += ["## 2a. Pooled rates by version with 95% bootstrap CIs (scenarios resampled)\n", br.to_markdown(), "\n"]
        c4 = objective(pj[pj.version == "v4"], ["category"]); c4.to_csv(res / "objective_v4_by_category.csv")
        md += ["## 3b. Deployed prompt (v4) by input category, pooled models\n", c4.to_markdown(), "\n"]
        cat = pj[pj.version.isin(VERSIONS)].groupby(["category", "version"])["Overall"].mean().unstack().round(2)
        cat.to_csv(res / "overall_by_category.csv")
        md += ["## 3. Judge overall score by input category (pooled models)\n", cat.to_markdown(), "\n"]
        vt = version_tests(pj); vt.to_csv(res / "version_tests_by_model.csv", index=False)
        md += ["## 4. Effect of prompt version within each model (Friedman; adjacent Wilcoxon, Holm)\n", vt.to_markdown(index=False), "\n"]

        # Judges list every detail not stated in the input (derived times, inferred status, recommendations, "no other issues"),
        # so the any-fabrication flag sits near ceiling; the number of listed items per report is the graded measure.
        fc = pd.DataFrame({name: jdf.groupby("version")["fabricated_n"].mean().round(2) for name, jdf in judges.items() if len(jdf)})
        fn = pd.DataFrame({name: jdf.groupby("version").size() for name, jdf in judges.items() if len(jdf)})
        fc.to_csv(res / "judge_fabricated_items_by_version.csv")
        md += ["## 4b. Judge-listed unsupported details per report (mean), by version\n", fc.to_markdown(), "\n",
               "Reports per cell\n", fn.to_markdown(), "\n"]
        ft = version_tests(pj, value="fabricated_n"); ft.to_csv(res / "version_tests_fabricated_items.csv", index=False)
        md += ["## 4c. Effect of prompt version on judge-listed unsupported details (primary judge; Friedman; Holm)\n", ft.to_markdown(index=False), "\n"]

        multi = pj[pj.version.isin(VERSIONS)].pivot_table(index=["scenario", "version", "model"], columns="run", values="Overall")
        if multi.shape[1] >= 2:
            cons = pd.DataFrame({"mean_abs_diff_run1_run2": (multi[1] - multi[2]).abs().groupby(level="model").mean().round(3),
                                 "identical_%": (100 * (multi[1] == multi[2]).groupby(level="model").mean()).round(1)})
            cons.to_csv(res / "run_consistency.csv"); md += ["## 5. Run-to-run consistency (overall score)\n", cons.to_markdown(), "\n"]

        if len(judges) > 1:
            rows = []
            for name, jdf in judges.items():
                if name == PRIMARY or jdf.empty:
                    continue
                m = pj.merge(jdf, on="file", suffixes=("_p", "_s"))
                for d in DIMS:
                    rows.append({"judge_pair": f"{PRIMARY} vs {name}", "dimension": d, "n": len(m), "weighted_kappa": wk(m[f"{d}_p"], m[f"{d}_s"]),
                                 "exact_%": round(100 * (m[f"{d}_p"] == m[f"{d}_s"]).mean(), 1),
                                 "within_1_%": round(100 * ((m[f"{d}_p"] - m[f"{d}_s"]).abs() <= 1).mean(), 1)})
                sp = m.groupby("family_p").apply(lambda x: (x["Overall_s"] - x["Overall_p"]).mean(), include_groups=False).round(3)
                md += [f"## 6b. Self-preference check: mean({name} − {PRIMARY}) by generator family\n", sp.to_frame("mean_diff").to_markdown(), "\n"]
            jj = pd.DataFrame(rows); jj.to_csv(res / "judge_vs_judge.csv", index=False)
            md += ["## 6. Agreement between judges\n", jj.to_markdown(index=False), "\n"]


    if not args.judge_only:
        public = OUT / "scoring" / "human_scores.csv"  # released scores, already linked to report files (no blinding key)
        if not (OUT / "scoring" / "KEY_do_not_open.csv").exists() and public.exists():
            raters = [pd.read_csv(public).set_index("file", drop=False).sort_index()]
            args.raters = args.raters[:1]
        else:
            key = pd.read_csv(OUT / "scoring" / "KEY_do_not_open.csv")
            raters = []
            for r in args.raters:
                s = pd.read_excel(OUT / "scoring" / f"scoring_{r}.xlsx", sheet_name="Scores").rename(columns={"Code": "code"}).merge(key, on="code")
                if s[DIMS].isna().any().any():
                    raise SystemExit(f"{r} has blank scores; finish scoring first.")
                raters.append(s.set_index("file", drop=False).sort_index())  # match raters by report, not code (codes differ when a sheet is re-issued)
        a = raters[0]  # primary rater (all 120)
        b = raters[1] if len(raters) > 1 else None
        both = a.index.intersection(b.index) if b is not None else a.index[:0]
        irr = pd.DataFrame() if b is None else pd.DataFrame([{"dimension": d, "n": len(both), "weighted_kappa": wk(a.loc[both, d], b.loc[both, d]),
                             "exact_%": round(100 * (a.loc[both, d] == b.loc[both, d]).mean(), 1),
                             "within_1_%": round(100 * ((a.loc[both, d] - b.loc[both, d]).abs() <= 1).mean(), 1)} for d in DIMS])
        if b is not None:
            irr.to_csv(res / "inter_rater_human.csv", index=False)
        human = a[["scenario", "version", "model", "file"] + DIMS].reset_index(drop=True)
        human["Overall"] = human[DIMS].mean(axis=1)
        human["file"] = human["file"].str.removesuffix(".md")
        hv = pd.DataFrame([{"version": v, "dimension": d, "mean": round(x[d].mean(), 2),
                            "ci95": "–".join(f"{c:.2f}" for c in boot_ci(x[d])), "n": len(x)}
                           for v, x in human.groupby("version") for d in DIMS + ["Overall"]])
        hv.to_csv(res / "human_scores_by_version.csv", index=False)
        fab = (a.assign(fab=a["Fabricated detail? (Y/N)"].astype(str).str.strip().str.upper().eq("Y"))
               .groupby("version")["fab"].agg(n="size", flagged="sum").assign(**{"flagged_%": lambda x: (100 * x.flagged / x.n).round(1)}))
        fab.to_csv(res / "human_fabrication_flag_by_version.csv")
        if b is not None:
            fab_irr = pd.crosstab(a.loc[both, "Fabricated detail? (Y/N)"].str.upper(), b.loc[both, "Fabricated detail? (Y/N)"].str.upper())
            fk = round(cohen_kappa_score(a.loc[both, "Fabricated detail? (Y/N)"].str.upper(), b.loc[both, "Fabricated detail? (Y/N)"].str.upper()), 3)
            rm = pd.DataFrame({r: x.loc[both, DIMS].mean().round(2) for r, x in zip(args.raters[:2], (a, b))})
        hj = []
        for name, jdf in judges.items():
            m = human.merge(jdf, on="file", suffixes=("_h", "_j"))
            hj += [{"judge": name, "dimension": d, "n": len(m), "weighted_kappa": wk(np.rint(m[f"{d}_h"]), m[f"{d}_j"]),
                    "mean_abs_diff": round((m[f"{d}_h"] - m[f"{d}_j"]).abs().mean(), 2),
                    "human_mean": round(m[f"{d}_h"].mean(), 2), "judge_mean": round(m[f"{d}_j"].mean(), 2),
                    "exact_%": round(100 * (m[f"{d}_h"] == m[f"{d}_j"]).mean(), 1),
                    "within_1_%": round(100 * ((m[f"{d}_h"] - m[f"{d}_j"]).abs() <= 1).mean(), 1)} for d in DIMS]
        hj = pd.DataFrame(hj); hj.to_csv(res / "human_vs_judge.csv", index=False)
        hfab = human.assign(h=a["Fabricated detail? (Y/N)"].astype(str).str.strip().str.upper().eq("Y").values)
        fj = []
        for name, jdf in judges.items():
            m = hfab.merge(jdf[["file", "fabricated_any"]], on="file")
            if len(m):
                fj.append({"judge": name, "n": len(m), "human_flag_%": round(100 * m.h.mean(), 1), "judge_flag_%": round(100 * m.fabricated_any.mean(), 1),
                           "agreement_%": round(100 * (m.h == m.fabricated_any).mean(), 1), "kappa": round(cohen_kappa_score(m.h, m.fabricated_any), 3)})
        fj = pd.DataFrame(fj); fj.to_csv(res / "human_vs_judge_fabrication.csv", index=False)
        # Human sample has one report per scenario x version (models rotate), so scenario is the block.
        ht = pd.DataFrame([{"dimension": d, **friedman_row(human.pivot(index="scenario", columns="version", values=d)[VERSIONS])}
                           for d in DIMS + ["Overall"]])
        ht.to_csv(res / "human_version_tests.csv", index=False)
        hc = []
        for name, jdf in judges.items():
            m = hfab.merge(jdf[["file", "fabricated_n"]], on="file")
            if len(m) and m.h.any():
                hc.append({"judge": name, "n": len(m), "items_when_human_flagged": round(m[m.h].fabricated_n.mean(), 2),
                           "items_when_human_not_flagged": round(m[~m.h].fabricated_n.mean(), 2),
                           "mannwhitney_p": f"{mannwhitneyu(m[m.h].fabricated_n, m[~m.h].fabricated_n).pvalue:.2g}"})
        hc = pd.DataFrame(hc); hc.to_csv(res / "judge_items_vs_human_flag.csv", index=False)
        hci = hv.pivot(index="dimension", columns="version", values="ci95")
        md += ["## 7. Human rubric scores by prompt version (primary rater, n=120; 95% bootstrap CI)\n",
               hv.pivot(index="dimension", columns="version", values="mean").to_markdown(), "\n",
               "95% bootstrap CIs\n", hci.to_markdown(), "\n",
               "## 7a. Effect of prompt version on human scores (scenario = block; Friedman; adjacent Wilcoxon, Holm)\n", ht.to_markdown(index=False), "\n",
               "## 7b. Primary rater's 'fabricated detail' flag by prompt version\n", fab.to_markdown(), "\n",
               *(["## 8. Inter-rater reliability (both raters, shared reports)\n", irr.to_markdown(index=False), "\n",
                  f"Fabricated-detail flag agreement (unweighted Cohen's kappa) = {fk}\n", fab_irr.to_markdown(), "\n",
                  "Rater means on the shared reports (systematic leniency check)\n", rm.to_markdown(), "\n"] if b is not None
                 else ["## 8. Inter-rater reliability\n", "Not estimated: single human rater.\n"]),
               "## 9. Human vs LLM judges\n", hj.to_markdown(index=False), "\n",
               "## 9b. Fabrication flag: human vs each judge (any fabricated detail)\n", fj.to_markdown(index=False) if len(fj) else "No judge results yet.", "\n",
               "## 9c. Judge-listed unsupported details in reports the human did / did not flag\n", hc.to_markdown(index=False) if len(hc) else "No judge results yet.", "\n"]

    if not args.human_only and CHECK:
        md += ["## 10. Deployed-model check: ShiftReport AI's default model (not part of the main results)\n"]
        for name in sorted(p.name for p in (OUT / "judge").glob("*") if p.is_dir()):
            cj = load_judge(name, check=True)
            if cj.empty:
                continue
            tag = name.replace(".", "-")
            ob = objective(cj, ["version"]); ob.to_csv(res / f"deployed_check_objective_{tag}.csv")
            md += [f"### Judge {name}: {len(cj)} reports\n", ob.to_markdown(), "\n"]
            if name == PRIMARY:
                cr = boot_rates(cj); cr.to_csv(res / "deployed_check_rates_ci.csv")
                cv = version_tests(cj); cv.to_csv(res / "deployed_check_version_tests.csv", index=False)
                cf = version_tests(cj, value="fabricated_n"); cf.to_csv(res / "deployed_check_version_tests_fabricated.csv", index=False)
                md += ["Rates with 95% bootstrap CIs (scenarios resampled)\n", cr.to_markdown(), "\n",
                       "Overall score by version (Friedman; adjacent Wilcoxon, Holm)\n", cv.to_markdown(index=False), "\n",
                       "Judge-listed unsupported details by version (Friedman; Holm)\n", cf.to_markdown(index=False), "\n"]

    (res / "summary.md").write_text("\n".join(md))
    print((res / "summary.md").read_text())


if __name__ == "__main__":
    main()
