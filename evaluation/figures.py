"""Draw the paper's figures from the analysis outputs (run analyze.py first).

Usage: python figures.py   ->  outputs/figures/fig*.png (300 dpi)
Every plotted value comes from outputs/results/*.csv or the raw judge/score files; nothing is typed in by hand.
"""
import re
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np
import pandas as pd
from analyze import OUT, DIMS, load_judge

RES, FIG = OUT / "results", OUT / "figures"
FIG.mkdir(exist_ok=True)
plt.rcParams.update({"font.family": "serif", "font.serif": ["DejaVu Serif"], "font.size": 9, "axes.spines.top": False,
                     "axes.spines.right": False, "savefig.dpi": 300, "savefig.bbox": "tight"})
NAVY, SLATE, SAGE, TAUPE, TAN, GREY = "#1d2b4a", "#4c6a8a", "#5b7d6a", "#8a8077", "#c4a57f", "#4a5568"
MODELS = {"openai-gpt-oss-120b": ("GPT-OSS 120B", NAVY, "o"), "openai-gpt-oss-20b": ("GPT-OSS 20B", SLATE, "s"),
          "qwen-qwen3.8-27b": ("Qwen3.8 27B", SAGE, "^")}
V = ["v1", "v2", "v3", "v4"]
VLAB = ["v1", "v2\n+registry", "v3\n+example", "v4\n+guard-\nrails"]


def parse(cell):
    """'10.22 (9.12–11.33)' -> (10.22, 9.12, 11.33)"""
    m = re.match(r"([\d.]+) \(([\d.]+)–([\d.]+)\)", str(cell))
    return tuple(map(float, m.groups())) if m else (np.nan,) * 3


# ---------- Figure 0: ShiftReport AI (system overview; text taken from the prompt's worked example) ----------
def fig_system():
    fig, ax = plt.subplots(figsize=(7.2, 3.4)); ax.set_xlim(0, 120); ax.set_ylim(-4, 57); ax.axis("off")

    def box(x, y, w, h, fc, ec="#2d3748", lw=0.9, ls="-"):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=1.2", fc=fc, ec=ec, lw=lw, ls=ls))

    def arrow(x1, y1, x2, y2, label=""):
        ax.annotate("", (x2, y2), (x1, y1), arrowprops=dict(arrowstyle="-|>", color=GREY, lw=1, mutation_scale=8, shrinkA=0, shrinkB=0))
        if label:
            ax.text((x1 + x2) / 2, y1 + 1.2, label, ha="center", va="bottom", fontsize=5.2, color=GREY, style="italic")

    # supervisor note
    box(0, 17, 21, 26, "#e2e2e2")
    ax.text(10.5, 39.5, "Outgoing\nsupervisor", ha="center", va="center", fontsize=6.8, weight="bold", color="#2d3748")
    ax.text(10.5, 26.5, "\u201cMachine 7 on line B\nstarted making weird\nnoises around 2pm, had\nto slow it down to 50%.\nCalled maintenance but\nthey haven't come yet\u2026\u201d",
            ha="center", va="center", fontsize=5.1, style="italic", color="#2d3748", linespacing=1.3)

    # application frame
    box(25, 3, 52, 51, "white", ec=NAVY, lw=1.2, ls="--")
    ax.text(51, 50.8, "ShiftReport AI (web application)", ha="center", va="center", fontsize=7.2, weight="bold", color=NAVY)
    comps = [("Role and task steps", "extract, match, classify"), ("Equipment registry", "16 machines, 5 plant areas"),
             ("Report template", "issue blocks + pending items"), ("Worked example", "one note and its report"),
             ("Guardrails", "never invent; flag gaps")]
    cols = [TAUPE, SLATE, SLATE, SAGE, NAVY]
    ax.text(41, 46.2, "Prompt (system message)", ha="center", fontsize=5.6, color=GREY, style="italic")
    for i, ((t, sub), c) in enumerate(zip(comps, cols)):
        y = 37 - i * 8
        box(27, y, 28, 6.6, c)
        ax.text(41, y + 4.4, t, ha="center", va="center", fontsize=6, weight="bold", color="white")
        ax.text(41, y + 1.9, sub, ha="center", va="center", fontsize=4.9, style="italic", color="white")
    box(59, 21, 16, 14, GREY)
    ax.text(67, 30.5, "Language\nmodel", ha="center", va="center", fontsize=6.6, weight="bold", color="white", linespacing=1.1)
    ax.text(67, 24.3, "user-selected\ntemperature 0.3", ha="center", va="center", fontsize=4.9, style="italic", color="white", linespacing=1.2)
    arrow(55, 28, 59, 28)
    ax.plot([21, 23, 23, 67, 67], [30, 30, -0.5, -0.5, 19], color=GREY, lw=1); arrow(67, 19, 67, 21)
    ax.text(45, -1.3, "note (user message)", ha="center", va="top", fontsize=5.2, color=GREY, style="italic")

    # draft report
    box(80, 6, 40, 48, "#f7f5f2")
    ax.text(100, 50.5, "Draft handover report", ha="center", va="center", fontsize=7, weight="bold", color="#2d3748")
    lines = [("1. M-07 CNC Milling Machine (Line B)", "bold", NAVY),
             ("Issue: unusual noises; speed reduced to 50%", "normal", "#2d3748"),
             ("Severity: High    Status: Ongoing", "normal", "#2d3748"),
             ("Action taken: slowed; maintenance called", "normal", "#2d3748"),
             ("Clarifications needed: has the machine been", "normal", "#9c4a1a"),
             ("cleared for continued operation at 50%?", "normal", "#9c4a1a"),
             ("Issues 2 and 3 not shown", "normal", "#2d3748"),
             ("Pending items for next shift", "bold", NAVY),
             ("\u2022 Follow up on maintenance visit for M-07", "normal", "#2d3748"),
             ("General notes", "bold", NAVY)]
    for i, (t, w, c) in enumerate(lines):
        ax.text(82, 46 - i * 3.4, t, ha="left", va="center", fontsize=5.0, weight=w, color=c)
    ax.text(100, 9.6, "flags: needs clarification \u00b7 unknown severity \u00b7\nunrecognized equipment", ha="center", va="center",
            fontsize=5, style="italic", color="#9c4a1a", linespacing=1.2)
    arrow(75, 28, 80, 28)
    ax.text(100, 1.5, "read on screen or downloaded,\nthen passed to the incoming crew", ha="center", va="center", fontsize=5.4, style="italic", color=GREY, linespacing=1.2)
    fig.savefig(FIG / "fig0_shiftreport_ai.png"); plt.close(fig)


# ---------- Figure 1: study design ----------
def fig_design():
    fig, ax = plt.subplots(figsize=(7.2, 3.3)); ax.set_xlim(0, 120); ax.set_ylim(0, 55); ax.axis("off")

    def box(x, y, w, h, title, sub="", fc=GREY, tc="white"):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=1.5", fc=fc, ec="#2d3748", lw=0.9))
        nt = title.count("\n")
        ax.text(x + w / 2, y + h / 2 + (2.4 + nt if sub else 0), title, ha="center", va="center", color=tc, fontsize=6.8, weight="bold", linespacing=1.1)
        if sub:
            ax.text(x + w / 2, y + h / 2 - 2.6 - nt, sub, ha="center", va="center", color=tc, fontsize=5.6, style="italic", linespacing=1.25)

    def arrow(x1, y1, x2, y2):
        ax.annotate("", (x2, y2), (x1, y1), arrowprops=dict(arrowstyle="-|>", color=GREY, lw=1, mutation_scale=8, shrinkA=0, shrinkB=0))

    box(0, 21, 17, 16, "30 supervisor\nnotes", "5 categories × 6\nanswer key\nper note", "#e2e2e2", "#2d3748")
    ys, subs = [43, 32, 21, 10], ["one-sentence instruction", "+ template & 16-machine registry", "+ one worked example", "+ guardrails (ShiftReport AI)"]
    for i, (y, sub) in enumerate(zip(ys, subs)):
        box(21, y, 30, 9, f"Prompt v{i + 1}", sub, [TAUPE, SLATE, SAGE, NAVY][i])
    for y in ys[1:]:
        arrow(36, y + 11, 36, y + 9)
    ax.text(36, 53.5, "cumulative versions", ha="center", fontsize=6, color=GREY, style="italic")
    arrow(17, 29, 22, 29)
    box(56, 26, 27, 16, "3 open-weight models", "GPT-OSS 20B, GPT-OSS 120B,\nQwen3.8 27B; 2 runs each\n→ 720 reports", SLATE)
    arrow(50, 34, 56, 34)
    box(56, 4, 27, 11, "Rule-based baseline", "no language model\n→ 30 reports", TAUPE)
    ax.plot([8.5, 8.5, 53], [21, 1.5, 1.5], color=GREY, lw=1); ax.plot([53, 53], [1.5, 9.5], color=GREY, lw=1); arrow(53, 9.5, 56, 9.5)
    box(90, 31, 30, 15, "Automated judges", "Gemini 3.5 Flash Lite and\nGemma 4 31B: all 750 reports\nGPT-OSS 120B: 120 reports", GREY)
    box(90, 8, 30, 15, "Human rater (blinded)", "120 reports, shuffled\nrubric + fabrication flag", "#e2e2e2", "#2d3748")
    ax.plot([83, 86.5], [34, 34], color=GREY, lw=1); ax.plot([83, 86.5], [9.5, 9.5], color=GREY, lw=1)
    ax.plot([86.5, 86.5], [9.5, 38.5], color=GREY, lw=1); arrow(86.5, 38.5, 90, 38.5); arrow(86.5, 15.5, 90, 15.5)
    ax.text(105, 49.5, "5 rubric dimensions\n+ answer-key failure modes", ha="center", fontsize=6, color=GREY, style="italic")
    fig.savefig(FIG / "fig1_study_design.png"); plt.close(fig)


# ---------- Figure 2: failure modes by version (pooled, 95% CI) ----------
def fig_failure_modes():
    t = pd.read_csv(RES / "rates_by_version_ci.csv", index_col=0)
    panels = [("fabricated_items_per_report", "Unsupported details listed\nper report", False, True),
              ("ambiguous_guessed_%", "Unclear machine references\nguessed as one ID (%)", False, True),
              ("ambiguous_flagged_%", "Unclear machine references\nflagged (%)", True, True),
              ("missing_flag_recall_%", "Missing information\nflagged (%)", True, True),
              ("contradiction_recall_%", "Contradictions\nflagged (%)", True, True),
              ("unsupported_reassurance_%", 'Unsupported "no incidents"\nstatement (%)', False, True)]
    fig, axs = plt.subplots(2, 3, figsize=(7.2, 4.6), sharex=True)
    for ax, (col, title, higher_better, base) in zip(axs.flat, panels):
        est = np.array([parse(t.loc[v, col]) for v in V])
        ax.fill_between(range(4), est[:, 1], est[:, 2], color=SLATE, alpha=0.18, lw=0)
        ax.plot(range(4), est[:, 0], "-o", color=NAVY, ms=4, lw=1.4)
        b = parse(t.loc["baseline", col])[0]
        ax.axhline(b, color=TAN, ls="--", lw=1.1)
        ax.set_title(title, fontsize=8.5, loc="left")
        ax.text(0.98, 0.04 if higher_better else 0.96, "higher is better" if higher_better else "lower is better",
                transform=ax.transAxes, ha="right", va="bottom" if higher_better else "top", fontsize=6.5, color=GREY, style="italic")
        if "%" in col:
            ax.set_ylim(0, 100)
        else:
            ax.set_ylim(0, None)
        ax.set_xticks(range(4)); ax.set_xticklabels(VLAB, fontsize=6.8)
    axs.flat[0].plot([], [], "-o", color=NAVY, ms=4, label="Pooled LLM reports (95% CI)")
    axs.flat[0].plot([], [], "--", color=TAN, label="Rule-based baseline")
    fig.legend(*axs.flat[0].get_legend_handles_labels(), loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(0.5, -0.03))
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(FIG / "fig2_failure_modes.png"); plt.close(fig)


# ---------- Figure 3: per-model view of the two side effects ----------
def fig_side_effects():
    t = pd.read_csv(RES / "objective_by_model_version.csv")
    fig, axs = plt.subplots(1, 2, figsize=(7.2, 2.9), sharey=True)
    for ax, col, title in [(axs[0], "ambiguous_guessed_%", "(a) Unclear references guessed as one machine ID"),
                           (axs[1], "unsupported_reassurance_%", '(b) Unsupported "no incidents" statements')]:
        for m, (lab, c, mk) in MODELS.items():
            s = t[t.model == m].set_index("version").loc[V, col]
            ax.plot(range(4), s, "-" + mk, color=c, ms=4.5, lw=1.4, label=lab)
        ax.set_title(title, fontsize=8.5, loc="left"); ax.set_xticks(range(4)); ax.set_xticklabels(VLAB, fontsize=6.8); ax.set_ylim(0, 100)
    axs[0].set_ylabel("% of opportunities")
    axs[0].axvspan(0.5, 2.5, color=TAN, alpha=0.12, lw=0); axs[0].text(1.5, 95, "registry, no flag rule", ha="center", fontsize=6.8, color=GREY, style="italic")
    axs[1].axvspan(1.5, 3.5, color=TAN, alpha=0.12, lw=0); axs[1].text(2.5, 95, "example present", ha="center", fontsize=6.8, color=GREY, style="italic")
    axs[1].legend(frameon=False, fontsize=7, loc="lower right")
    fig.tight_layout(); fig.savefig(FIG / "fig3_side_effects.png"); plt.close(fig)


# ---------- Figure 4: overall judge score by category and version (redrawn from measured data) ----------
def fig_heatmap():
    t = pd.read_csv(RES / "overall_by_category.csv", index_col=0)
    order = ["Simple/Clean", "Multi-Issue", "Vague/Ambiguous", "Contradictory", "Complex Edge"]
    t = t.loc[order, V]
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list("earth", ["#c9a98b", "#b8a473", "#9a9f7a", "#6f8f6f", "#4b6e52"])
    fig, ax = plt.subplots(figsize=(5.2, 3.2))
    im = ax.imshow(t.values, cmap=cmap, vmin=2.5, vmax=5, aspect="auto")
    for i in range(t.shape[0]):
        for j in range(t.shape[1]):
            ax.text(j, i, f"{t.values[i, j]:.2f}", ha="center", va="center", fontsize=9, weight="bold", color="#1a1a1a")
    ax.set_xticks(range(4)); ax.set_xticklabels([f"Prompt {v}" for v in V]); ax.set_yticks(range(len(order))); ax.set_yticklabels([o.replace("/", " / ") for o in order])
    for s in ax.spines.values():
        s.set_visible(False)
    cb = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.03); cb.set_label("Mean overall judge score (1–5)", fontsize=8)
    fig.tight_layout(); fig.savefig(FIG / "fig4_category_heatmap.png"); plt.close(fig)


# ---------- Figure 5: human vs judge accuracy scores ----------
def fig_human_vs_judge():
    public = OUT / "scoring" / "human_scores.csv"  # released scores, already linked to report files
    if not (OUT / "scoring" / "KEY_do_not_open.csv").exists() and public.exists():
        h = pd.read_csv(public)
    else:
        key = pd.read_csv(OUT / "scoring" / "KEY_do_not_open.csv")
        h = pd.read_excel(OUT / "scoring" / "scoring_Adarsh.xlsx", sheet_name="Scores").rename(columns={"Code": "code"}).merge(key, on="code")
    h["file"] = h["file"].str.removesuffix(".md")
    raters = {"Human rater": h.set_index("file")}
    for name, lab in [("gemini-3.5-flash-lite", "Gemini"), ("gemma-4-31b-it", "Gemma"), ("openai-gpt-oss-120b", "GPT-OSS")]:
        raters[lab] = load_judge(name).set_index("file")
    files = raters["Human rater"].index
    fig, axs = plt.subplots(1, 2, figsize=(7.2, 2.9), sharey=True)
    for ax, d, title in [(axs[0], "Accuracy", "(a) Accuracy"), (axs[1], "Uncertainty", "(b) Uncertainty handling")]:
        names = list(raters)
        bottom = np.zeros(len(names))
        cols = ["#c9a98b", "#d8c29d", "#b9bfa3", "#7f9c84", "#4b6e52"]
        for score, c in zip(range(1, 6), cols):
            share = np.array([100 * (raters[n].loc[files, d].round() == score).mean() for n in names])
            ax.barh(names, share, left=bottom, color=c, edgecolor="white", lw=0.6, label=str(score))
            for k, (s, b) in enumerate(zip(share, bottom)):
                if s >= 9:
                    ax.text(b + s / 2, k, f"{s:.0f}", ha="center", va="center", fontsize=6.8)
            bottom += share
        ax.set_title(title, fontsize=8.5, loc="left"); ax.set_xlim(0, 100); ax.set_xlabel("% of the 120 human-rated reports")
        ax.invert_yaxis() if ax is axs[0] else None
    axs[1].legend(title="Score", ncol=5, frameon=False, fontsize=7, title_fontsize=7, loc="upper center", bbox_to_anchor=(0, -0.28))
    fig.tight_layout(); fig.savefig(FIG / "fig5_human_vs_judge.png"); plt.close(fig)


if __name__ == "__main__":
    fig_system(); fig_design(); fig_failure_modes(); fig_side_effects(); fig_heatmap(); fig_human_vs_judge()
    print("written:", sorted(p.name for p in FIG.glob("*.png")))
