"""Convert a ComfyUI editor (UI/litegraph) workflow into API format, using a live server's /object_info.

Dev tool used to produce app/workflows/*.json. Usage:
    python tools/ui_to_api.py <ui_workflow.json> <out_api.json> [--comfy http://127.0.0.1:8188]
        [--set NODE_ID.input=json_value ...] [--switch NODE_ID=true|false ...] [--drop NODE_ID ...] [--add JSON]

--set     overrides an input value before pruning (e.g. a PrimitiveBoolean that drives switches).
--switch  resolves a ComfySwitchNode to one branch and removes it from the graph.
--drop    removes output nodes you don't want; nodes no longer feeding any output are pruned.
--add     JSON object of extra API nodes (e.g. new save nodes) merged in before pruning.
"""
import argparse
import json
import sys

import httpx

SKIP_TYPES = {"Note", "MarkdownNote", "PrimitiveNode", "Reroute"}


WIDGET_TYPES = ("INT", "FLOAT", "STRING", "BOOLEAN", "COMBO", "LOAD_3D", "COLOR")
DYNAMIC_COMBO = "COMFY_DYNAMICCOMBO_V3"


def widget_inputs(inputs_spec):
    """(name, type, opts) for every widget input, in widgets_values order."""
    out = []
    for section in ("required", "optional"):
        for name, spec in inputs_spec.get(section, {}).items():
            typ = spec[0]
            opts = spec[1] if len(spec) > 1 and isinstance(spec[1], dict) else {}
            if isinstance(typ, list) or typ in WIDGET_TYPES or typ == DYNAMIC_COMBO:
                out.append((name, typ, opts))
    return out


def consume_widgets(inputs_spec, values, inputs, prefix=""):
    for name, typ, opts in widget_inputs(inputs_spec):
        if not values:
            return
        key = prefix + name
        inputs[key] = values.pop(0)
        # Frontend-only companion widgets that store an extra value
        if opts.get("control_after_generate") or (typ == "INT" and name in ("seed", "noise_seed")):
            if values and values[0] in ("fixed", "increment", "decrement", "randomize"):
                values.pop(0)
        if opts.get("image_upload") or opts.get("video_upload") or opts.get("audio_upload"):
            if values and values[0] in ("image", "video", "audio", ""):
                values.pop(0)
        # CLAUDE-NOTE: a dynamic combo's chosen option adds its own sub-widgets right after it; the API
        # names them "<combo>.<sub>" (comfy_api finalize_prefix).
        if typ == DYNAMIC_COMBO:
            option = next((o for o in opts.get("options", []) if o["key"] == inputs[key]), None)
            if option:
                consume_widgets(option["inputs"], values, inputs, key + ".")


def convert(ui, object_info):
    nodes = {n["id"]: n for n in ui["nodes"]}
    links = {l[0]: l for l in ui["links"]}  # id, from_node, from_slot, to_node, to_slot, type

    def resolve(link_id):
        """Follow reroutes and frontend-only primitive nodes to a real (node, slot) or a literal value."""
        _, src, slot, *_ = links[link_id]
        n = nodes[src]
        if n["type"] == "Reroute":
            return resolve(n["inputs"][0]["link"])
        if n["type"] == "PrimitiveNode":
            return ("value", n["widgets_values"][0])
        return ("link", [str(src), slot])

    api = {}
    for nid, n in nodes.items():
        if n["type"] in SKIP_TYPES or n.get("mode") in (2, 4):
            continue
        info = object_info.get(n["type"])
        if info is None:
            raise SystemExit(f"node {nid}: class {n['type']} not installed on the server")
        inputs = {}
        values = list(n.get("widgets_values") or [])
        if isinstance(n.get("widgets_values"), dict):
            values = []
            inputs.update(n["widgets_values"])
        consume_widgets(info["input"], values, inputs)
        for inp in n.get("inputs", []):
            if inp.get("link") is None:
                continue
            kind, val = resolve(inp["link"])
            inputs[inp["name"]] = val
        api[str(nid)] = {"class_type": n["type"], "inputs": inputs, "_meta": {"title": n.get("title") or n["type"]}}
    return api


def is_link(v):
    return isinstance(v, list) and len(v) == 2 and isinstance(v[0], str)


def resolve_switch(api, sid, take_true):
    sw = api.pop(sid)
    key = "on_true" if take_true else "on_false"
    target = sw["inputs"][key]
    for node in api.values():
        for k, v in node["inputs"].items():
            if is_link(v) and v[0] == sid:
                node["inputs"][k] = target


def prune(api, object_info):
    keep = set()
    stack = [nid for nid, n in api.items() if object_info[n["class_type"]].get("output_node")]
    while stack:
        nid = stack.pop()
        if nid in keep:
            continue
        keep.add(nid)
        stack += [v[0] for v in api[nid]["inputs"].values() if is_link(v)]
    return {k: v for k, v in api.items() if k in keep}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--comfy", default="http://127.0.0.1:8188")
    ap.add_argument("--set", action="append", default=[])
    ap.add_argument("--switch", action="append", default=[])
    ap.add_argument("--drop", action="append", default=[])
    ap.add_argument("--add", default="{}")
    a = ap.parse_args()

    object_info = httpx.get(a.comfy.rstrip("/") + "/object_info", timeout=120).json()
    ui = json.load(open(a.src, encoding="utf-8"))
    api = convert(ui, object_info)
    for s in a.set:
        target, val = s.split("=", 1)
        nid, name = target.split(".", 1)
        api[nid]["inputs"][name] = json.loads(val)
    for s in a.switch:
        sid, val = s.split("=")
        resolve_switch(api, sid, val.lower() == "true")
    for d in a.drop:
        api.pop(d, None)
    api.update(json.loads(a.add))
    api = prune(api, object_info)
    json.dump(api, open(a.dst, "w", encoding="utf-8"), indent=2)
    print(f"wrote {a.dst}: {len(api)} nodes", file=sys.stderr)


if __name__ == "__main__":
    main()
