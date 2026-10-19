"""Fill the API-format workflows in app/workflows with GUI settings and run them.

Node IDs below come from the converted workflows (see tools/ui_to_api.py and the skill docs). If a workflow
is re-exported, re-check these IDs.
"""
import json
import os

from . import comfy

WF_DIR = os.path.join(comfy.APP_DIR, "workflows")


def _load(name):
    with open(os.path.join(WF_DIR, name + ".json"), encoding="utf-8") as f:
        return json.load(f)


def _keep_only_outputs(graph, outputs):
    """Drop every node that doesn't feed one of `outputs` (so unused loaders aren't validated)."""
    keep, stack = set(), list(outputs)
    while stack:
        nid = stack.pop()
        if nid in keep:
            continue
        keep.add(nid)
        stack += [v[0] for v in graph[nid]["inputs"].values() if isinstance(v, list) and len(v) == 2 and isinstance(v[0], str)]
    return {k: v for k, v in graph.items() if k in keep}


def _files(outputs, node_id, kind):
    return [comfy.output_path(e) for e in outputs.get(node_id, {}).get(kind, [])]


# --- Trellis 2: image -> mesh -----------------------------------------------------------------------------

TRELLIS_UNET = {"low": "trellis_2_int8_convrot.safetensors", "high": "trellis_2_bf16.safetensors"}


def mesh(image, mode, texture_preview, faces, seed, on_progress=None):
    g = _load("trellis2")
    g["122"]["inputs"]["image"] = comfy.stage_input(image)
    g["40"]["inputs"]["unet_name"] = TRELLIS_UNET[mode]
    g["186"]["inputs"]["target_face_count"] = faces
    for sampler in ("3", "18", "23", "12"):
        g[sampler]["inputs"]["seed"] = seed
    outputs = ["900"] + (["901"] if texture_preview else [])
    g = _keep_only_outputs(g, outputs)
    out = comfy.run(g, on_progress)
    glb = _files(out, "900", "3d")[0]
    preview = _files(out, "901", "3d")[0] if texture_preview else None
    # CLAUDE-NOTE: the viewer shows the vertex-colored preview, but "Send to Texture" always passes the
    # untextured mesh: UltraTex re-unwraps and paints it from scratch.
    return {"glb": glb, "preview": preview}


# --- UltraTex: mesh + reference image -> PBR textures -----------------------------------------------------


def texture(mesh_path, image, mode, quality, resolution, steps, seed, texture_size, uv_mode, on_progress=None):
    if mode == "low":
        return _texture_low(mesh_path, image, resolution, steps, seed, texture_size, uv_mode, on_progress)
    return _texture_high(mesh_path, image, quality, resolution, steps, seed, texture_size, uv_mode, on_progress)


def _texture_high(mesh_path, image, quality, resolution, steps, seed, texture_size, uv_mode, on_progress):
    g = _load("ultratex_advanced" if quality == "advanced" else "ultratex_standard")
    bake = "26" if quality == "advanced" else "23"
    g["1"]["inputs"]["image"] = comfy.stage_input(image)
    g["2"]["inputs"]["glb_path"] = os.path.abspath(mesh_path)  # UltraTexLoadMesh accepts absolute paths
    g["14"]["inputs"]["uv_mode"] = uv_mode
    samplers = ["18", "20"] + (["24"] if quality == "advanced" else [])
    for s in samplers:
        g[s]["inputs"].update(seed=seed, steps=steps)
    # Albedo samplers follow the GUI resolution; the MR sampler stays at 1024 (upstream guidance).
    # CLAUDE-NOTE: in Advanced, RenderViews (23) and pass-2 sampler (24) must match pass-1 resolution.
    for s in ["18"] + (["23", "24"] if quality == "advanced" else []):
        g[s]["inputs"]["resolution"] = resolution
    g[bake]["inputs"]["texture_size"] = texture_size
    out = comfy.run(g, on_progress)
    glb = _files(out, bake, "3d")[0]
    # UltraTexBake only reports the GLB; the maps sit next to it as <base>_albedo.png / <base>_orm.png
    base = glb[: -len(".glb")]
    maps = [(base + "_albedo.png", "Albedo"), (base + "_orm.png", "ORM (G=roughness, B=metallic)")]
    return {"glb": glb, "maps": [m for m in maps if os.path.exists(m[0])]}


def _texture_low(mesh_path, image, resolution, steps, seed, texture_size, uv_mode, on_progress):
    g = _load("ultratex_lowvram")
    # Load3DAdvanced only accepts files inside ComfyUI/input (validated), so the mesh is staged into input/3d
    g["1"]["inputs"]["model_file"] = comfy.stage_input(mesh_path, "3d")
    g["3"]["inputs"]["image"] = comfy.stage_input(image)
    g["44"]["inputs"]["uv_mode"] = uv_mode
    for s in ("9", "20"):
        g[s]["inputs"].update(seed=seed, steps=steps)
    g["9"]["inputs"]["view_resolution"] = resolution  # MR views stay at 1024, as in the upstream workflow
    g["48"]["inputs"]["texture_size"] = texture_size
    out = comfy.run(g, on_progress)
    glb = _files(out, "13", "3d")[0]
    maps = [(_files(out, nid, "images")[0], label)
            for nid, label in (("14", "Base color"), ("22", "Roughness"), ("23", "Metallic"))]
    return {"glb": glb, "maps": maps}
