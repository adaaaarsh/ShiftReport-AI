"""Generate reports for every scenario x prompt version x generator model x run.

Uses free Groq endpoints (see models.json). The user message wrapper and temperature
match the deployed app (files/app.py). Resumable: finished files are skipped, and the
script stops cleanly when a model's daily token cap is hit. Just re-run it the next day.

Usage:
    export GROQ_API_KEY=...          # in your own terminal; never commit it
    python generate.py --runs 2
    python generate.py --models groq:qwen/qwen3.8-27b --runs 1
Output: outputs/reports/<scenario>_<version>_<model>_r<run>.md + outputs/generation_log.jsonl
"""
import argparse, json
from datetime import datetime, timezone
from providers import CONFIG, ROOT, Caller, DailyLimitReached, slug, strip_reasoning

VERSIONS = ["v1", "v2", "v3", "v4"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="*", help="model ids from models.json (default: all generators)")
    ap.add_argument("--runs", type=int, default=2)
    ap.add_argument("--temperature", type=float, default=0.3)
    args = ap.parse_args()

    gens = [g for g in CONFIG["generators"] if not args.models or g["id"] in args.models]
    scenarios = json.loads((ROOT / "scenarios.json").read_text())["scenarios"]
    prompts = {v: (ROOT / "prompts" / f"{v}.txt").read_text() for v in VERSIONS}
    out = ROOT / "outputs" / "reports"; out.mkdir(parents=True, exist_ok=True)
    log = (ROOT / "outputs" / "generation_log.jsonl").open("a")

    for g in gens:
        caller, ms = Caller(g), slug(g["id"])
        try:
            for run in range(1, args.runs + 1):
                for s in scenarios:
                    for v in VERSIONS:
                        path = out / f"{s['id']}_{v}_{ms}_r{run}.md"
                        if path.exists():
                            continue
                        resp = caller.chat(
                            [{"role": "system", "content": prompts[v]},
                             {"role": "user", "content": f"Here is my shift update:\n\n{s['input'].strip()}"}],
                            temperature=args.temperature)
                        choice = resp.choices[0]
                        text = strip_reasoning(choice.message.content)
                        if not text:
                            print(f"  empty output for {path.name} (finish_reason={choice.finish_reason}); will retry next run")
                            continue
                        path.write_text(text)
                        log.write(json.dumps({
                            "file": path.name, "scenario": s["id"], "version": v, "model": g["id"], "run": run,
                            "returned_model": resp.model, "temperature": args.temperature,
                            "finish_reason": choice.finish_reason,
                            "prompt_tokens": resp.usage.prompt_tokens if resp.usage else None,
                            "completion_tokens": resp.usage.completion_tokens if resp.usage else None,
                            "utc": datetime.now(timezone.utc).isoformat()}) + "\n")
                        log.flush()
                        flag = "" if choice.finish_reason == "stop" else f"  [finish_reason={choice.finish_reason}]"
                        print(f"ok {path.name}{flag}", flush=True)
        except DailyLimitReached as e:
            print(f"STOPPED {g['id']}: {e}", flush=True)


if __name__ == "__main__":
    main()
