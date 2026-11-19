# ShiftReport AI: evaluation data and code

This folder contains everything needed to check or reproduce the evaluation reported in the paper *ShiftReport AI: Design and Evaluation of a Generative Language-Model Assistant for Manufacturing Shift Handover*. Every number in the paper is produced by `analyze.py` from the files here.

## What was evaluated

ShiftReport AI's prompt (`prompts/v4.txt`, identical to the system prompt in `../app.py`) was compared with three reduced versions:

| Version | Content |
|---|---|
| v1 | The original one-sentence instruction |
| v2 | v1 plus role statement, extraction steps, equipment registry and report template |
| v3 | v2 plus one worked example |
| v4 | v3 plus guardrails (the ShiftReport AI prompt) |

Each version was run on 30 synthetic supervisor notes with three open-weight models on Groq (GPT-OSS 20B, GPT-OSS 120B and Qwen3.8 27B), twice each, at temperature 0.3: 720 reports. A rule-based extractor (`baseline.py`) produced 30 more. Reports were scored by Gemini 3.5 Flash Lite (primary judge, all 750), Gemma 4 31B (all 750) and GPT-OSS 120B (the 120 human-rated reports), and by one blinded human rater (120 reports).

## Contents

| Path | What it is |
|---|---|
| `scenarios.json` | The 30 notes with answer keys (issues, acceptable severities, facts, missing information, contradictions, distractors) |
| `scenarios.pre-review.json`, `review_log.md` | The keys before review, and the edits made during review |
| `equipment.json` | The 16-machine equipment registry |
| `prompts/` | Prompt versions v1 to v4 |
| `rubric.md` | The 1 to 5 scoring rubric used by the human rater and the judges |
| `models.json` | Generator and judge models with their free-tier rate limits |
| `generate.py`, `baseline.py`, `judge.py` | Report generation, the rule-based baseline, and automated judging |
| `make_scoring_sheet.py` | Builds the blinded human scoring sheet |
| `analyze.py`, `figures.py` | All statistics and figures in the paper |
| `providers.py`, `check_providers.py`, `run_until_done.sh` | API pacing and retry helpers |
| `outputs/reports/` | All 750 generated reports (`<scenario>_<version>_<model>_r<run>.md`) |
| `outputs/generation_log.jsonl` | One line per report: returned model, finish reason, token counts, time |
| `outputs/judge/<judge>/` | One JSON judgement per report and judge |
| `outputs/scoring/human_scores.csv` | The human rater's 120 scores, linked to report files, with comments |
| `outputs/results/` | Analysis outputs; `summary.md` collects them |
| `outputs/figures/` | The paper's figures |

## Reproducing the analysis

The analysis needs no API keys:

```bash
cd evaluation
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python analyze.py --raters Adarsh    # writes outputs/results/
python figures.py                    # writes outputs/figures/
```

Run from these files, both scripts reproduce the released results and figures exactly.

Re-running generation or judging needs your own free API keys (Groq and Google AI Studio), set as `GROQ_API_KEY` and `GEMINI_API_KEY` in your shell. Never commit keys. Finished files are skipped, so delete the relevant outputs first if you want fresh runs. Hosted models change over time, so new runs will not match the released reports exactly.

## Notes

- The scenarios and answer keys were drafted with the help of a language model and then reviewed and edited by the first author before any reports were generated (`review_log.md`).
- The judge prompt was calibrated once in a pilot that is not part of the results; it was not changed afterwards.
- Human rating was done by a single rater, so no human inter-rater reliability is reported.

## Licence

Code in this folder is released under the MIT licence (`../LICENSE`). The data (scenarios, answer keys, prompts, rubric, generated reports, judgements, scores and results) are released under CC BY 4.0 (`DATA_LICENSE.md`).
