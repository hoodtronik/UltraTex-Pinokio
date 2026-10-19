"""Minimal client for the private ComfyUI backend started by start.js."""
import json
import os
import shutil
import uuid

import httpx
import websocket

COMFY_URL = os.environ.get("COMFY_URL", "http://127.0.0.1:8188").rstrip("/")
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMFY_DIR = os.path.join(APP_DIR, "comfyui")
INPUT_DIR = os.path.join(COMFY_DIR, "input")
OUTPUT_DIR = os.path.join(COMFY_DIR, "output")
MODELS_DIR = os.path.join(COMFY_DIR, "models")


class ComfyError(RuntimeError):
    pass


def stage_input(path, subfolder=""):
    """Copy a local file into ComfyUI's input folder; return its name relative to input/.

    CLAUDE-NOTE: the GUI and ComfyUI share a machine, so a file copy replaces /upload/image. That also
    avoids the 100MB upload cap for big meshes and keeps the original extension for the 3D loaders.
    """
    dest_dir = os.path.join(INPUT_DIR, subfolder)
    os.makedirs(dest_dir, exist_ok=True)
    name = f"{uuid.uuid4().hex[:8]}_{os.path.basename(path)}"
    shutil.copyfile(path, os.path.join(dest_dir, name))
    return f"{subfolder}/{name}" if subfolder else name


def output_path(entry):
    """Absolute path of a {filename, subfolder, type} entry from /history."""
    base = OUTPUT_DIR if entry.get("type", "output") == "output" else os.path.join(COMFY_DIR, entry["type"])
    return os.path.join(base, entry.get("subfolder", ""), entry["filename"])


def run(prompt, on_progress=None):
    """Queue an API-format prompt, stream progress, and return its /history outputs dict.

    on_progress(fraction_or_None, text) is called for every sampler step and node change.
    """
    client_id = uuid.uuid4().hex
    ws = websocket.create_connection(
        COMFY_URL.replace("http", "ws", 1) + f"/ws?clientId={client_id}", timeout=None
    )
    try:
        r = httpx.post(f"{COMFY_URL}/prompt", json={"prompt": prompt, "client_id": client_id}, timeout=60)
        if r.status_code != 200:
            raise ComfyError(_format_validation_error(r))
        prompt_id = r.json()["prompt_id"]
        while True:
            msg = ws.recv()
            if not isinstance(msg, str):
                continue  # binary preview frames
            msg = json.loads(msg)
            data = msg.get("data", {})
            if data.get("prompt_id") not in (None, prompt_id):
                continue
            kind = msg["type"]
            if kind == "progress" and on_progress:
                node = prompt.get(str(data.get("node")), {})
                title = node.get("_meta", {}).get("title") or node.get("class_type", "")
                on_progress(data["value"] / max(data["max"], 1), f"{title}: {data['value']}/{data['max']}")
            elif kind == "executing" and data.get("node") is not None and on_progress:
                node = prompt.get(str(data["node"]), {})
                on_progress(None, node.get("_meta", {}).get("title") or node.get("class_type", ""))
            elif kind == "execution_error":
                raise ComfyError(f"{data.get('node_type')}: {data.get('exception_message', '').strip()}")
            elif kind == "execution_interrupted":
                raise ComfyError("Interrupted")
            elif kind == "executing" and data.get("node") is None:
                break
            elif kind == "execution_success":
                break
    finally:
        ws.close()
    hist = httpx.get(f"{COMFY_URL}/history/{prompt_id}", timeout=60).json()
    return hist[prompt_id]["outputs"]


def interrupt():
    httpx.post(f"{COMFY_URL}/interrupt", timeout=10)


def free_vram():
    httpx.post(f"{COMFY_URL}/free", json={"unload_models": True, "free_memory": True}, timeout=30)


def _format_validation_error(r):
    try:
        body = r.json()
    except ValueError:
        return r.text
    lines = [body.get("error", {}).get("message", "Prompt rejected")]
    for node_id, err in body.get("node_errors", {}).items():
        for e in err.get("errors", []):
            lines.append(f"node {node_id} ({err.get('class_type')}): {e.get('message')} {e.get('details', '')}")
    return "\n".join(lines)
