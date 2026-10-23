"""Small persisted settings (HF token, last VRAM mode) in app/settings.json (gitignored)."""
import json
import os

from .comfy import APP_DIR

PATH = os.path.join(APP_DIR, "settings.json")
DEFAULTS = {"hf_token": "", "vram_mode": "low"}


def load():
    try:
        with open(PATH, encoding="utf-8") as f:
            return {**DEFAULTS, **json.load(f)}
    except (OSError, ValueError):
        return dict(DEFAULTS)


def save(**changes):
    data = {**load(), **changes}
    with open(PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return data


def _user_login_token():
    # CLAUDE-NOTE: Pinokio's GLOBAL ENVIRONMENT sets HF_HOME=<pinokio>/cache/HF_HOME for every app, so get_token()
    # looks there and misses the token `hf auth login` saved in the user's own HF home (MEASURED 2026-10-22: a gated
    # FLUX download failed with a valid login on the machine). Read that default location directly as a last resort.
    path = os.path.join(os.path.expanduser("~"), ".cache", "huggingface", "token")
    try:
        with open(path, encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return ""


def hf_token():
    # CLAUDE-NOTE: fall back to the machine's `hf auth login` token, so users who already logged in with
    # the HF CLI don't have to paste a token. This app's ENVIRONMENT leaves HF_HOME alone, but Pinokio's global
    # one still redirects it, hence the explicit user-home fallback.
    from huggingface_hub import get_token

    return os.environ.get("HF_TOKEN") or load()["hf_token"] or get_token() or _user_login_token() or ""
