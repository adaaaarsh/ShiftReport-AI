"""Shared helpers for free OpenAI-compatible endpoints (Groq, Gemini).

Pacing: after each call we sleep long enough to stay under the model's RPM and TPM.
Daily caps: if the server asks us to wait more than DAILY_WAIT seconds we stop cleanly;
every script skips finished items, so just re-run it after the daily reset.
"""
import json, os, pathlib, re, time
from openai import OpenAI, RateLimitError, APIStatusError, APIConnectionError

ROOT = pathlib.Path(__file__).parent
CONFIG = json.loads((ROOT / "models.json").read_text())
DAILY_WAIT = 1800  # Groq daily caps roll; waits up to 30 min are worth sitting out


class DailyLimitReached(Exception):
    pass


def slug(model_id: str) -> str:
    return re.sub(r"[^a-zA-Z0-9.]+", "-", model_id.split(":", 1)[1]).strip("-").lower()


def client_for(model_id: str) -> tuple[OpenAI, str]:
    provider, model = model_id.split(":", 1)
    p = CONFIG["providers"][provider]
    key = os.environ.get(p["key_env"])
    if not key:
        raise SystemExit(f"{p['key_env']} is not set. Export it in your own terminal first.")
    return OpenAI(base_url=p["base_url"], api_key=key, max_retries=0, timeout=180), model


def strip_reasoning(text: str) -> str:
    return re.sub(r"<(think|thought)>.*?</\1>", "", text or "", flags=re.S).strip()


class Caller:
    """One paced, retrying caller per model."""

    def __init__(self, spec: dict):
        self.spec = spec
        self.client, self.model = client_for(spec["id"])
        self.min_gap = 60.0 / spec["rpm"]

    def chat(self, messages, temperature=None, response_format=None):
        kwargs = dict(model=self.model, messages=messages, max_tokens=self.spec["max_tokens"])
        if temperature is not None:
            kwargs["temperature"] = temperature
        if response_format is not None:
            kwargs["response_format"] = response_format
        if self.spec.get("extra"):
            kwargs["extra_body"] = self.spec["extra"]
        attempt = 0  # counts real errors only; rate-limit waits are expected on free tiers and don't count
        last_err = "none"
        blind = 0.0  # seconds spent on 429s that gave no retry-after (Gemini's daily cap looks like this)
        while attempt < 8:
            t0 = time.time()
            try:
                resp = self.client.chat.completions.create(**kwargs)
            except RateLimitError as e:
                hdr = e.response.headers.get("retry-after")
                wait = float(hdr) if hdr else min(60 * 2 ** (blind // 300), 300)
                if hdr is None:
                    blind += wait
                if wait > DAILY_WAIT or blind > 900:
                    raise DailyLimitReached(f"{self.spec['id']}: rate limited for {blind or wait:.0f}s (daily cap). Re-run after reset.")
                print(f"    rate limited, waiting {wait:.0f}s")
                time.sleep(wait + 1)
                continue
            except (APIConnectionError, APIStatusError) as e:
                m = re.search(r"Limit (\d+), Requested (\d+)", str(e))
                if isinstance(e, APIStatusError) and e.status_code == 413 and m:
                    # Groq counts max_tokens against the per-minute limit; shrink the output cap so the request fits
                    kwargs["max_tokens"] -= int(m[2]) - int(m[1]) + 200
                    print(f"    request too large, max_tokens -> {kwargs['max_tokens']}")
                    attempt += 1
                    continue
                if isinstance(e, APIStatusError) and e.status_code < 500:
                    raise
                last_err = f"{type(e).__name__} {getattr(e, 'status_code', '')}".strip()
                time.sleep(2 ** attempt * 3)
                attempt += 1
                continue
            used = resp.usage.total_tokens if resp.usage else 0
            gap = max(self.min_gap, 60.0 * used / self.spec["tpm"])
            time.sleep(max(0.0, gap - (time.time() - t0)))
            return resp
        raise RuntimeError(f"{self.spec['id']}: gave up after repeated errors (last: {last_err})")
