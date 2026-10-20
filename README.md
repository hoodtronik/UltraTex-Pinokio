# Trellis2 + UltraTex for Pinokio

A one-click Pinokio app that turns **an image into a textured 3D asset**:

1. **Generate Mesh**: [TRELLIS.2](https://github.com/microsoft/TRELLIS.2) (native in ComfyUI) builds a mesh from one image, decimated for texturing. An optional quick vertex-color preview is included.
2. **Texture**: [UltraTex](https://yiboz2001.github.io/UltraTex/) paints PBR textures (albedo + metallic/roughness) onto any untextured mesh from one front reference image. It uses PixelArtistry's three [workflows](https://github.com/pixelartistry/PixelArtistry-UltraTex): Standard, Advanced and Low VRAM.

Everything runs on a private ComfyUI inside this app, behind a simple Gradio GUI. **Windows + NVIDIA.**

## Requirements

- **Windows 10/11** with an **NVIDIA GPU**: 8 GB VRAM for Low VRAM mode, 16 GB+ for High VRAM mode. A recent NVIDIA driver is recommended (driver 580+ gets the CUDA 13 build of PyTorch, older drivers get CUDA 12.8).
- **[Pinokio](https://pinokio.co)** (it provides Python, Git, conda and uv; nothing else needs to be installed by hand).
- **Disk space:** about 15 GB for the app itself plus 20 GB (Low) to 33 GB (High) of models. Install Pinokio on a drive with room to spare.

## Install

1. Open Pinokio and click **Discover** → **Download from URL** (or the **+** button).
2. Paste this repo's URL, `https://github.com/hoodtronik/UltraTex-Pinokio`, and click **Download**.
3. Open the app and click **Install**. This clones ComfyUI and the UltraTex/GGUF node packs at pinned versions and installs PyTorch. It takes about 10–20 minutes; the log ends with `Triton sparse attention: OK`.
4. Click **Start**. When the button **Open Trellis2 + UltraTex** appears, click it to open the GUI.

Models are **not** downloaded during install. They download the first time you run a step (or from the **Models** tab), so the first run of each mode takes longer.

## Directions

### Pick a VRAM mode

At the top of the GUI:
- **Low VRAM (default, 8 GB):** UltraTex runs on GGUF Q4 models; Trellis 2 runs int8.
- **High VRAM (16 GB+):** UltraTex runs on FLUX.2 Klein fp8 with the **Standard (6 views)** or **Advanced (10 views)** workflow; Trellis 2 runs bf16. Needs a free Hugging Face login (see [Models](#models)).

### Image → textured 3D model

1. Open **1 · Generate Mesh** and drop in an image of a single object (a front view on a plain background works best).
2. Leave **Target faces** at 700k, optionally tick **Quick Trellis texture preview**, and click **Generate mesh**. The mesh appears in the viewer; **Download GLB** below it saves the untextured mesh.
3. Click **Send to Texture ▶**. This moves the untextured mesh and the same image to tab 2.
4. In **2 · Texture**, choose the settings (see below) and click **Texture mesh**.
5. Get the results from **Downloads**: the **textured GLB** plus the **albedo** and **ORM** maps (G = roughness, B = metallic).

### Texture a mesh you already have

Open **2 · Texture** directly, add your mesh (GLB/OBJ/PLY) and a sharp front reference image, then click **Texture mesh**.

### Texture settings

| Setting | What it does |
|---|---|
| **Quality** (High VRAM only) | **Standard** paints 6 views (front, back, sides, top, bottom). **Advanced** adds a second pass at 45° angles (10 views) for better coverage on rounded shapes like characters. |
| **View resolution** | Size of each generated view. 1024 for tests, 2048 for finals (slower). |
| **Steps** | 25 for a final; 4 is a quick preview in Low VRAM mode. |
| **Seed** | -1 = random. The seed used is shown in the status line, so you can repeat a result. |
| **Texture size** | Size of the baked texture maps: 1024, 2048 or 4096. |
| **UVs** | **Auto unwrap (GPU)** (fast, default) or **Auto unwrap (xatlas)** (CPU, much slower) make new UVs; **Keep my UVs** keeps your mesh's UVs. |

How long it takes, measured on an RTX 6000 Ada (48 GB): a mesh takes about 90–110 s, and texturing takes about 160 s (High · Standard), 190 s (High · Advanced) or 200 s (Low, 4 steps). Smaller GPUs are slower.

### Buttons at the top

- **Stop** cancels the running job.
- **Free VRAM** unloads models from the GPU, which is useful before switching modes or running other GPU apps.

### Where files go

Results are saved in `app/comfyui/output` (meshes in `trellis/`, textures in `UltraTex/`) inside the app folder. In Pinokio, use the app's folder icon to open it.

### Update, reset and ComfyUI

- **Update** pulls the latest launcher and reinstalls the pinned dependencies. Downloaded models are kept.
- **Reset** deletes ComfyUI and the Python environment (`app/comfyui` and `app/env`), **including downloaded models**. Run **Install** again afterwards.
- While the app is running, **Open ComfyUI** opens the private ComfyUI backend, which is handy for debugging the workflows.

### Models

Models download automatically the first time a pipeline needs them. The **Models** tab shows each one and lets you pre-download a set.

| Set | Approx. download |
|---|---|
| Mesh · Low | ~9 GB |
| Mesh · High | ~14 GB |
| Texture · Low | ~12 GB |
| Texture · High | ~19 GB |
| Textured mesh · Low (mesh + texture) | ~20 GB |
| Textured mesh · High (mesh + texture) | ~33 GB |

High VRAM texturing uses the **gated** `black-forest-labs/FLUX.2-klein-base-9b-fp8`. To get it:
1. Accept its license on Hugging Face.
2. Paste a free *Read* token in **Models → Hugging Face token**. It is stored only in `app/settings.json`, which is gitignored. If you already logged in with the Hugging Face CLI (`hf auth login`), you can skip this step: the app uses that login.

Models stay inside this app (`app/comfyui/models`), not Pinokio's shared drive.

## Troubleshooting

- **"... is gated" error in High VRAM mode:** accept the FLUX license and add a Hugging Face token (see [Models](#models)).
- **Out of memory:** switch to Low VRAM mode, click **Free VRAM**, or close other GPU apps.
- **Bad texture on the back or sides:** use a sharper, front-on reference image, or try **Advanced** quality.
- **Mesh too dense or slow to texture:** lower **Target faces** in tab 1. UltraTex works best with about 0.5–1M faces.
- **Keep my UVs fails or looks wrong:** it needs one material, UVs inside 0–1, and no overlapping or mirrored islands.
- **Something else:** check the logs in the app folder under `logs/api/`. Click **Stop**, then **Start** again; if it still fails, run **Update**.

## API

The GUI is a Gradio app, so every run can also be scripted. Use the URL Pinokio shows for **Open Trellis2 + UltraTex**.

### Python (`pip install gradio_client`)

```python
from gradio_client import Client, handle_file

c = Client("http://127.0.0.1:7860")
mesh = c.predict(handle_file("chair.png"), "low", False, 700000, -1, api_name="/generate_mesh")
glb = mesh[1]  # untextured mesh path
textured = c.predict(
    handle_file(glb), handle_file("chair.png"),
    "low", "standard", 1024, 25, -1, 2048, "comfy_gpu",
    api_name="/texture_mesh",
)
print(textured[0])  # textured GLB
```

### JavaScript (`npm i @gradio/client`)

```js
import { Client, handle_file } from "@gradio/client";
const c = await Client.connect("http://127.0.0.1:7860");
const r = await c.predict("/generate_mesh", [handle_file(blob), "low", false, 700000, -1]);
console.log(r.data);
```

### curl

```bash
# 1) queue the job (image is a URL or uploaded file path)
curl -s -X POST http://127.0.0.1:7860/gradio_api/call/generate_mesh \
  -H "Content-Type: application/json" \
  -d '{"data":[{"path":"https://example.com/chair.png"},"low",false,700000,-1]}'
# -> {"event_id":"..."}
# 2) stream the result
curl -N http://127.0.0.1:7860/gradio_api/call/generate_mesh/<event_id>
```

`texture_mesh` takes `[mesh, image, vram_mode, quality, resolution, steps, seed, texture_size, uv_mode]`:
- `vram_mode`: `low` or `high`
- `quality`: `standard` or `advanced` (used in High mode only)
- `uv_mode`: `comfy_gpu`, `xatlas` or `keep_existing`

## Licenses

- **This launcher:** MIT.
- **UltraTex code and visualbruno's nodes:** MIT.
- **MostAadTech's low-VRAM nodes:** GPL-3.0. They are cloned at install time, not bundled.
- **TRELLIS.2:** MIT.
- **FLUX.2 Klein base 9B, including the GGUF versions:** FLUX Non-Commercial License. Black Forest Labs claims no ownership of outputs. Commercial use of the model itself needs a license from [bfl.ai](https://bfl.ai/licensing).

## Credits

- UltraTex paper (SIGGRAPH Asia 2026) and models: Yibo Zhang et al.
- Workflows and installer: [PixelArtistry](https://github.com/pixelartistry/PixelArtistry-UltraTex).
- Nodes: [visualbruno](https://github.com/visualbruno/ComfyUI-UltraTex), [MostAadTech](https://github.com/Mstafa-awad/UltraTex-ComfyUI-nodes) and [city96](https://github.com/city96/ComfyUI-GGUF).
- TRELLIS.2: Microsoft; ComfyUI integration: Comfy-Org.
