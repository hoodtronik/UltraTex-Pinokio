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


def hf_token():
    # CLAUDE-NOTE: fall back to the machine's `hf auth login` token, so users who already logged in with
    # the HF CLI don't have to paste a token. This is why ENVIRONMENT must not override HF_HOME.
    from huggingface_hub import get_token

    return os.environ.get("HF_TOKEN") or load()["hf_token"] or get_token() or ""
