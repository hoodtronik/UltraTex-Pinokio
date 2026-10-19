---
name: ultratex-pinokio
description: Operate and maintain the UltraTex Pinokio app (F:\pinokio\api\UltraTex), which runs TRELLIS.2 image-to-mesh and UltraTex PBR texturing on a private ComfyUI with a Gradio GUI. Use when installing, starting or debugging the app through Pinokio/pterm, generating meshes or textures (GUI, Gradio API or ComfyUI API), adding models, re-exporting or editing the API workflows in app/workflows, bumping the pinned UltraTex node commits, or changing the GUI. Trigger on "UltraTex", "Trellis 2 mesh", "texture this mesh", "PixelArtistry workflow", "ultratex pinokio".
---

# UltraTex Pinokio app

## Layout

| Path | Role |
|---|---|
| `pinokio.js`, `install.js`, `start.js`, `update.js` → `update_deps.js`, `reset.js`, `torch.js` | Pinokio launcher. Root only; never put app code here. |
| `app/app.py` | Gradio GUI (tabs: Generate Mesh, Texture, Models). API names `/generate_mesh`, `/texture_mesh`. |
| `app/ultratex_gui/comfy.py` | ComfyUI client: queue `/prompt`, websocket progress, `/history`, stage files into `input/`. |
| `app/ultratex_gui/pipelines.py` | Fills workflow node inputs by **node ID** and runs them. |
| `app/ultratex_gui/models.py` | Model registry (`MODELS`, `REQUIRED[(task, mode)]`) + HF/ModelScope downloader. |
| `app/workflows/*.json` | API-format workflows: `trellis2`, `ultratex_standard`, `ultratex_advanced`, `ultratex_lowvram`. |
| `app/tools/ui_to_api.py` | Converts editor-format workflows to API format via a live `/object_info`. |
| `app/comfyui/`, `app/env/` | Created by install.js (gitignored). Models live in `app/comfyui/models` (no shared drive). |

## Operate

Use pterm (`F:\pinokio\bin\npm\pterm.cmd`), never ad-hoc launches, for real runs:

```bash
pterm start install.js --ref pinokio://127.0.0.1:42000/api/UltraTex
pterm start start.js   --ref pinokio://127.0.0.1:42000/api/UltraTex
pterm status pinokio://127.0.0.1:42000/api/UltraTex      # running_scripts, ready_url
pterm stop  start.js   --ref pinokio://127.0.0.1:42000/api/UltraTex
```

- start.js picks a free port for ComfyUI (`local.comfy_port`) and passes `COMFY_URL` to the GUI. ComfyUI is **not** on 8188.
- Logs: `logs/api/<script>/` (newest numbered file). Check them before guessing.
- Headless smoke test (ComfyUI already running): from `app/`, run `COMFY_URL=http://127.0.0.1:<port> env/Scripts/python.exe ../logs/test_run.py mesh_low` (see the script for other modes).

## Pipelines and node IDs

When a workflow is re-exported, node IDs can change. Re-check every ID below against the new JSON.

- **trellis2**: `122` LoadImage, `40` UNETLoader (`trellis_2_int8_convrot` low / `trellis_2_bf16` high), `186` DecimateMesh `target_face_count`, KSamplers `3 18 23 12` (seed). Outputs: `900` SaveGLB of the untextured mesh (`trellis/mesh`), `901` SaveGLB of the PaintMesh vertex-color preview. Drop `901` (and prune) for mesh-only runs.
- **ultratex_standard / advanced** (High VRAM, visualbruno nodes):
  - `1` LoadImage. `2` UltraTexLoadMesh `glb_path` takes an absolute path. `14` UltraTexPrep `uv_mode`.
  - Samplers `18` (albedo), `20` (MR), and `24` (pass 2, advanced only).
  - Bake is `23` (standard) or `26` (advanced).
  - Advanced: `23` RenderViews and `24` must use the same resolution as `18`.
- **ultratex_lowvram** (GGUF, MostAadTech nodes):
  - `1` Load3DAdvanced `model_file` must be relative to `input/` (e.g. `3d/x.glb`). Stage the file with `comfy.stage_input(path, "3d")`.
  - `3` LoadImage. `44` unwrap `uv_mode`. `9`/`20` generate views (albedo/MR). `48` baker `texture_size` must be 1024, 2048 or 4096.
  - Outputs: `13` SaveGLB, `14` base_color, `22` roughness, `23` metallic.

## Output files

- UltraTex Bake reports only the GLB in `/history` (`ui["3d"]`). The maps sit next to it as `<base>_albedo.png` and `<base>_orm.png`, where `<base>` is the GLB path minus `.glb` (note the double underscore). The ORM map has G = roughness, B = metallic.
- SaveGLB and SaveImage outputs come from `/history` `3d` / `images` entries; resolve them with `comfy.output_path`.

## Maintain

### Re-export a workflow

ComfyUI must be running with the pinned node packs.

```bash
cd app
env/Scripts/python.exe tools/ui_to_api.py <editor.json> workflows/<name>.json --comfy <COMFY_URL> \
  --drop <preview node ids> [--switch ID=true] [--set ID.input=json] [--add '{"900": {...}}']
```

- The converter skips frontend-only widget values (`control_after_generate`, upload buttons) and treats `LOAD_3D` as a widget.
- `--switch` resolves a `ComfySwitchNode`. Pruning keeps only ancestors of output nodes, so drop the preview nodes.
- The Trellis graph comes from ComfyUI's template `3d_pixal3d_trellis2_image_to_model.json` (in `env/Lib/site-packages/comfyui_workflow_templates_json/templates/`), built with `--switch 314=true --switch 315=true --switch 318=true`, the previews dropped, and save nodes `900` (mesh←`238`) and `901` (preview←`252`) added.

### Bump the UltraTex nodes

1. Change the commit constants in **both** `install.js` and `update_deps.js`.
2. Re-run the update, then re-export the three UltraTex workflows (widget order can change between commits).
3. Re-check the node IDs above.

### Add a model

Add it to `MODELS` and `REQUIRED` in `models.py`. The saved filename must match what the workflow JSON references.

## Gotchas

- Quote pip version specifiers in Pinokio `shell.run` (`"triton-windows<3.8"`). Unquoted `<` and `>` are redirects on Windows.
- Torch is pinned to 2.13 cu130 with `triton-windows<3.8`, the newest pair in UltraTex's torch→triton table. torchaudio has no cu130 build past 2.11 and is not installed.
- **Don't use `fs.link`.** On this machine Pinokio's shared drive is on C: (partly inside Pinokio's program folder); the user chose to keep models on F:. If the links ever reappear, remove the junctions with `cmd /c rmdir`. Never use `rm -rf`, which deletes the shared models.
- `FLUX.2-klein-base-9b-fp8` (High VRAM texture) is gated and needs an HF token (Models tab → `app/settings.json`, or the `HF_TOKEN` env var). Only the **base** Klein works, not the distilled one.
- The Trellis template's CLIP vision model is `dino_v3_L_naf_fp32.safetensors` from **Comfy-Org/Pixal3D**, not `dino_v3_vit_l` from Comfy-Org/TRELLIS.2.
- Low VRAM UltraTex has no fallback without Triton. install.js runs `tools/triton_check.py`; look for `Triton sparse attention: OK` in the install log.
- Gradio serves files only from `allowed_paths` (ComfyUI `output/`).
