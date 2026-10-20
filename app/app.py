"""UltraTex GUI: Trellis 2 image-to-mesh + UltraTex PBR texturing on a private ComfyUI backend."""
import os
import random
import threading

import gradio as gr

from ultratex_gui import comfy, models, pipelines, settings

VRAM_CHOICES = [("Low VRAM (6-8 GB, GGUF)", "low"), ("High VRAM (16 GB+)", "high")]
_download_lock = threading.Lock()

CSS = """
.ut-note {font-size: 0.85em; opacity: 0.75}
"""


def ensure_models(task, mode, progress):
    """Download missing models for a pipeline before running it (models are fetched on demand)."""
    todo = models.missing(task, mode)
    if not todo:
        return
    with _download_lock:
        for i, key in enumerate(todo):
            name, size = models.MODELS[key][4], models.MODELS[key][5]
            progress(i / len(todo), desc=f"Downloading {name} ({size:g} GB) — first run only")
            models.download(key, settings.hf_token())


def _progress_cb(progress):
    def cb(frac, text):
        progress(frac if frac is not None else 0, desc=text)
    return cb


def _seed(seed):
    return random.randint(0, 2**31 - 1) if seed is None or seed < 0 else int(seed)


def run_mesh(image, mode, texture_preview, faces, seed, progress=gr.Progress()):
    if not image:
        raise gr.Error("Add an image first.")
    try:
        ensure_models("mesh", mode, progress)
        seed = _seed(seed)
        res = pipelines.mesh(image, mode, texture_preview, int(faces), seed, _progress_cb(progress))
    except (comfy.ComfyError, RuntimeError) as e:
        raise gr.Error(str(e))
    return res["preview"] or res["glb"], res["glb"], res["glb"], f"Mesh ready: `{os.path.basename(res['glb'])}` · seed {seed}"


def run_texture(mesh, image, mode, quality, resolution, steps, seed, texture_size, uv_mode, progress=gr.Progress()):
    if not mesh:
        raise gr.Error("Add a mesh (GLB / OBJ / PLY) or send one from the Generate Mesh tab.")
    if not image:
        raise gr.Error("Add a front reference image.")
    try:
        ensure_models("texture", mode, progress)
        seed = _seed(seed)
        res = pipelines.texture(
            mesh, image, mode, quality, int(resolution), int(steps), seed, int(texture_size), uv_mode,
            _progress_cb(progress),
        )
    except (comfy.ComfyError, RuntimeError) as e:
        raise gr.Error(str(e))
    files = [res["glb"]] + [p for p, _ in res["maps"]]
    return res["glb"], res["maps"], files, f"Done · seed {seed}"


def save_token(token):
    settings.save(hf_token=token.strip())
    return "Token saved to app/settings.json (local only)."


def download_set(task, mode, progress=gr.Progress()):
    try:
        for t in (("mesh", "texture") if task == "all" else (task,)):
            ensure_models(t, mode, progress)
    except RuntimeError as e:
        raise gr.Error(str(e))
    what = "the full pipeline (mesh + texture)" if task == "all" else task
    return models.status_rows(), f"All models for {what} ({mode} VRAM) are installed."


def build():
    prefs = settings.load()
    with gr.Blocks(title="Trellis2 + UltraTex", css=CSS, theme=gr.themes.Soft()) as demo:
        gr.Markdown("# Trellis2 + UltraTex\nImage → mesh with **Trellis 2**, then mesh + reference image → PBR textures with **UltraTex**.")
        with gr.Row():
            vram = gr.Radio(VRAM_CHOICES, value=prefs["vram_mode"], label="VRAM mode", scale=3)
            stop_btn = gr.Button("Stop", variant="stop", scale=1)
            free_btn = gr.Button("Free VRAM", scale=1)
        vram.change(lambda m: settings.save(vram_mode=m) and None, vram, None, api_name=False)
        stop_btn.click(lambda: comfy.interrupt(), None, None, api_name=False)
        free_btn.click(lambda: comfy.free_vram(), None, None, api_name=False)

        with gr.Tabs() as tabs:
            with gr.Tab("1 · Generate Mesh", id="mesh"):
                with gr.Row():
                    with gr.Column():
                        m_image = gr.Image(type="filepath", label="Image (object on any background)", height=360)
                        m_preview = gr.Checkbox(value=False, label="Quick Trellis texture preview (UltraTex will replace it)")
                        with gr.Accordion("Settings", open=False):
                            m_faces = gr.Slider(100_000, 2_000_000, value=700_000, step=50_000, label="Target faces (UltraTex likes 0.5–1M)")
                            m_seed = gr.Number(value=-1, precision=0, label="Seed (-1 = random)")
                        m_btn = gr.Button("Generate mesh", variant="primary")
                    with gr.Column():
                        m_view = gr.Model3D(label="Mesh", height=420)
                        m_file = gr.File(label="Download GLB")
                        m_status = gr.Markdown()
                        m_send = gr.Button("Send to Texture ▶")
                m_glb = gr.State()

            with gr.Tab("2 · Texture", id="texture"):
                with gr.Row():
                    with gr.Column():
                        t_mesh = gr.File(label="Mesh (GLB / OBJ / PLY, untextured, ideally 0.5–1M faces)",
                                         file_types=[".glb", ".obj", ".ply"], type="filepath")
                        t_image = gr.Image(type="filepath", label="Front reference image (sharp, front view)", height=300)
                        t_quality = gr.Radio([("Standard (6 views)", "standard"), ("Advanced (10 views, fixes smearing)", "advanced")],
                                             value="standard", label="Quality (High VRAM mode)")
                        with gr.Accordion("Settings", open=False):
                            t_res = gr.Dropdown([1024, 1536, 2048], value=1024, label="View resolution (1024 tests, 2048 finals)")
                            t_steps = gr.Slider(4, 40, value=25, step=1, label="Steps (Low VRAM: 4 preview, 25 final)")
                            t_seed = gr.Number(value=-1, precision=0, label="Seed (-1 = random)")
                            t_tex = gr.Dropdown([1024, 2048, 4096], value=2048, label="Texture size")
                            t_uv = gr.Radio([("Auto unwrap (GPU)", "comfy_gpu"), ("Auto unwrap (xatlas)", "xatlas"),
                                             ("Keep my UVs", "keep_existing")], value="comfy_gpu", label="UVs")
                        t_btn = gr.Button("Texture mesh", variant="primary")
                    with gr.Column():
                        t_view = gr.Model3D(label="Textured mesh", height=420)
                        t_maps = gr.Gallery(label="Texture maps", columns=3, height=220)
                        t_files = gr.File(label="Downloads", file_count="multiple")
                        t_status = gr.Markdown()
                gr.Markdown("UltraTex runs on FLUX.2 Klein base 9B (FLUX Non-Commercial License). Black Forest Labs "
                            "claims no ownership of outputs; commercial use of the model itself needs a license from bfl.ai.",
                            elem_classes="ut-note")

            with gr.Tab("Models", id="models"):
                gr.Markdown("Models download automatically the first time a pipeline needs them. "
                            "The High VRAM FLUX model is **gated**: accept the license at "
                            "[black-forest-labs/FLUX.2-klein-base-9b-fp8](https://huggingface.co/black-forest-labs/FLUX.2-klein-base-9b-fp8) "
                            "and paste a free Hugging Face *Read* token below.")
                with gr.Row():
                    token = gr.Textbox(value=prefs["hf_token"], type="password", label="Hugging Face token", scale=4)
                    token_btn = gr.Button("Save token", scale=1)
                token_msg = gr.Markdown()
                table = gr.Dataframe(models.status_rows(), headers=["", "File", "Folder", "Size", "Used by", "Source"],
                                     interactive=False, wrap=True)
                with gr.Row():
                    dl = {}
                    for task, mode, label in [("mesh", "low", "Mesh · Low"), ("mesh", "high", "Mesh · High"),
                                              ("texture", "low", "Texture · Low"), ("texture", "high", "Texture · High"),
                                              ("all", "low", "Textured mesh · Low"), ("all", "high", "Textured mesh · High")]:
                        dl[(task, mode)] = gr.Button(f"Download {label}")
                dl_msg = gr.Markdown()
                token_btn.click(save_token, token, token_msg, api_name=False)
                for (task, mode), btn in dl.items():
                    btn.click(lambda t=task, m=mode, progress=gr.Progress(): download_set(t, m, progress), None, [table, dl_msg], api_name=False)

        m_btn.click(run_mesh, [m_image, vram, m_preview, m_faces, m_seed], [m_view, m_file, m_glb, m_status], api_name="generate_mesh")
        m_send.click(lambda g, img: (g, img, gr.Tabs(selected="texture")), [m_glb, m_image], [t_mesh, t_image, tabs], api_name=False)
        t_btn.click(run_texture, [t_mesh, t_image, vram, t_quality, t_res, t_steps, t_seed, t_tex, t_uv],
                    [t_view, t_maps, t_files, t_status], api_name="texture_mesh")
    return demo


if __name__ == "__main__":
    build().queue().launch(server_name="127.0.0.1", allowed_paths=[comfy.OUTPUT_DIR])
