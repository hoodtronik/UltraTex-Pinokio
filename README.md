# UltraTex for Pinokio

A one-click Pinokio app that turns **an image into a textured 3D asset**:

1. **Generate Mesh**: [TRELLIS.2](https://github.com/microsoft/TRELLIS.2) (native in ComfyUI) builds a mesh from one image, decimated for texturing. An optional quick vertex-color preview is included.
2. **Texture**: [UltraTex](https://yiboz2001.github.io/UltraTex/) paints PBR textures (albedo + metallic/roughness) onto any untextured mesh from one front reference image. It uses PixelArtistry's three [workflows](https://github.com/pixelartistry/PixelArtistry-UltraTex): Standard, Advanced and Low VRAM.

Everything runs on a private ComfyUI inside this app, behind a simple Gradio GUI. **Windows + NVIDIA.**

## Use

1. **Install**, then **Start**, then **Open UltraTex**.
2. Pick a **VRAM mode** at the top:
   - **Low VRAM (default, 6–8 GB):** UltraTex runs on GGUF Q4 models; Trellis 2 runs int8.
   - **High VRAM (16 GB+):** UltraTex runs on FLUX.2 Klein fp8 with the **Standard (6 views)** or **Advanced (10 views)** workflow; Trellis 2 runs bf16.
3. **1 · Generate Mesh**: drop in an image, then click **Generate mesh**. Click **Send to Texture ▶** to hand the untextured mesh and the same image to tab 2.
4. **2 · Texture**: add a mesh (GLB/OBJ/PLY) and a sharp front reference image, then click **Texture mesh**. Outputs are a textured GLB plus the texture maps.

### Models

Models download automatically the first time a pipeline needs them. The **Models** tab shows each one and lets you pre-download a set.

| Set | Approx. download |
|---|---|
| Mesh · Low | ~9 GB |
| Mesh · High | ~14 GB |
| Texture · Low | ~12 GB |
| Texture · High | ~19 GB |

High VRAM texturing uses the **gated** `black-forest-labs/FLUX.2-klein-base-9b-fp8`. To get it:
1. Accept its license on Hugging Face.
2. Paste a free *Read* token in **Models → Hugging Face token**. It is stored only in `app/settings.json`, which is gitignored. If you already logged in with the Hugging Face CLI (`hf auth login`), you can skip this step: the app uses that login.

Models stay inside this app (`app/comfyui/models`), not Pinokio's shared drive.

### Tips

- UltraTex wants an untextured mesh with about 0.5–1M faces. Use a sharp, front-on reference image; any background is fine because it is removed automatically.
- **Keep my UVs** needs one material, UVs inside 0–1, and no overlapping or mirrored islands.
- In Low VRAM mode, use 4 steps for a preview and 25 for a final.

## API

The GUI is a Gradio app, so every run can also be scripted. Use the URL Pinokio shows for **Open UltraTex**.

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
