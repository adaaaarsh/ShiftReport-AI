"""Check that your free API keys work and that every configured model is reachable.

Usage:  python check_providers.py
Sends one tiny request per configured model (a few tokens each).
"""
from providers import CONFIG, Caller, client_for


def main():
    specs = {s["id"]: s for s in CONFIG["generators"] + CONFIG["judges"]}
    for provider in CONFIG["providers"]:
        ids = [i for i in specs if i.startswith(provider + ":")]
        if not ids:
            continue
        try:
            client, _ = client_for(ids[0])
            available = {m.id.removeprefix("models/") for m in client.models.list()}
        except SystemExit as e:
            print(f"[{provider}] skipped: {e}")
            continue
        for mid in ids:
            name = mid.split(":", 1)[1]
            if name not in available:
                print(f"[{provider}] MISSING {name}. Close matches: {sorted(a for a in available if name.split('-')[0] in a)[:8]}")
                continue
            try:
                r = Caller(specs[mid]).chat([{"role": "user", "content": "Reply with the single word: ready"}])
                print(f"[{provider}] OK {name}: {r.choices[0].message.content!r} (model reported: {r.model})")
            except Exception as e:
                print(f"[{provider}] FAIL {name}: {e}")


if __name__ == "__main__":
    main()
