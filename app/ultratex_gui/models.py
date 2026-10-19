"""Model registry and on-demand downloader (Hugging Face + ModelScope)."""
import os
import shutil

from .comfy import MODELS_DIR

HF = "hf"
MS = "modelscope"

# key -> (source, repo, file in repo, models subfolder, saved filename, size GB, gated)
# CLAUDE-NOTE: filenames must match what app/workflows/*.json reference. The ModelScope LoRAs are both
# called dit_lora.safetensors upstream, so they are renamed on download (same as Install-UltraTex.bat).
MODELS = {
    "flux2_vae": (HF, "Comfy-Org/flux2-dev", "split_files/vae/flux2-vae.safetensors", "vae", "flux2-vae.safetensors", 0.34, False),
    "birefnet": (HF, "Comfy-Org/BiRefNet", "background_removal/birefnet.safetensors", "background_removal", "birefnet.safetensors", 0.44, False),
    "ultratex_lora": (MS, "Yibo-Zhang/UltraTex", "flux2/lora/dit_lora.safetensors", "loras", "ultratex_flux2.safetensors", 0.2, False),
    "ultratex_lora_mr": (MS, "Yibo-Zhang/UltraTex", "flux2_mr/lora/dit_lora.safetensors", "loras", "ultratex_flux2_mr.safetensors", 0.2, False),
    "ultratex_decoder": (MS, "Yibo-Zhang/UltraTex", "flux2/decoder.pt", "ultratex", "ultratex_flux2_decoder.pt", 0.1, False),
    "klein_fp8": (HF, "black-forest-labs/FLUX.2-klein-base-9b-fp8", "flux-2-klein-base-9b-fp8.safetensors", "diffusion_models", "flux-2-klein-base-9b-fp8.safetensors", 9.4, True),
    "qwen_fp8": (HF, "Comfy-Org/flux2-klein-9B", "split_files/text_encoders/qwen_3_8b_fp8mixed.safetensors", "text_encoders", "qwen_3_8b_fp8mixed.safetensors", 8.7, False),
    "klein_gguf": (HF, "unsloth/FLUX.2-klein-base-9B-GGUF", "flux-2-klein-base-9b-Q4_0.gguf", "diffusion_models", "flux-2-klein-base-9b-Q4_0.gguf", 5.6, False),
    "qwen_gguf": (HF, "unsloth/Qwen3-8B-GGUF", "Qwen3-8B-Q4_K_M.gguf", "text_encoders", "Qwen3-8B-Q4_K_M.gguf", 5.0, False),
    "trellis_bf16": (HF, "Comfy-Org/TRELLIS.2", "diffusion_models/trellis_2_bf16.safetensors", "diffusion_models", "trellis_2_bf16.safetensors", 10.3, False),
    "trellis_int8": (HF, "Comfy-Org/TRELLIS.2", "diffusion_models/trellis_2_int8_convrot.safetensors", "diffusion_models", "trellis_2_int8_convrot.safetensors", 5.3, False),
    "trellis_shape_vae": (HF, "Comfy-Org/TRELLIS.2", "vae/trellis_2_shape_vae_bf16.safetensors", "vae", "trellis_2_shape_vae_bf16.safetensors", 1.1, False),
    "trellis_texture_vae": (HF, "Comfy-Org/TRELLIS.2", "vae/trellis_2_texture_vae_bf16.safetensors", "vae", "trellis_2_texture_vae_bf16.safetensors", 0.95, False),
    "dino_v3": (HF, "Comfy-Org/Pixal3D", "clip_vision/dino_v3_L_naf_fp32.safetensors", "clip_vision", "dino_v3_L_naf_fp32.safetensors", 1.2, False),
}

_ULTRATEX_COMMON = ["flux2_vae", "birefnet", "ultratex_lora", "ultratex_lora_mr", "ultratex_decoder"]
_TRELLIS_COMMON = ["trellis_shape_vae", "trellis_texture_vae", "dino_v3", "birefnet"]

# Model sets each pipeline needs, keyed by (task, vram mode)
REQUIRED = {
    ("texture", "low"): _ULTRATEX_COMMON + ["klein_gguf", "qwen_gguf"],
    ("texture", "high"): _ULTRATEX_COMMON + ["klein_fp8", "qwen_fp8"],
    ("mesh", "low"): _TRELLIS_COMMON + ["trellis_int8"],
    ("mesh", "high"): _TRELLIS_COMMON + ["trellis_bf16"],
}


def path_of(key):
    _, _, _, folder, name, _, _ = MODELS[key]
    return os.path.join(MODELS_DIR, folder, name)


def missing(task, mode):
    return [k for k in REQUIRED[(task, mode)] if not os.path.exists(path_of(k))]


def status_rows():
    rows = []
    for key, (src, repo, _, folder, name, size, gated) in MODELS.items():
        used_by = [f"{t} ({m})" for (t, m), keys in REQUIRED.items() if key in keys]
        rows.append([
            "✅" if os.path.exists(path_of(key)) else "—",
            name, folder, f"{size:g} GB", ", ".join(used_by),
            f"{repo}{' (gated: accept license + HF token)' if gated else ''}",
        ])
    return rows


def download(key, hf_token=None):
    src, repo, file, folder, name, _, gated = MODELS[key]
    dest = path_of(key)
    if os.path.exists(dest):
        return dest
    if gated and not hf_token:
        raise RuntimeError(
            f"{name} is gated. Accept the license at https://huggingface.co/{repo} and paste a Read token in Models."
        )
    tmp = os.path.join(MODELS_DIR, ".download_tmp")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    if src == HF:
        from huggingface_hub import hf_hub_download

        got = hf_hub_download(repo_id=repo, filename=file, local_dir=tmp, token=hf_token or None)
    else:
        from modelscope.hub.file_download import model_file_download

        got = model_file_download(model_id=repo, file_path=file, local_dir=tmp)
    shutil.move(got, dest)
    shutil.rmtree(tmp, ignore_errors=True)  # repo subfolders + HF/ModelScope metadata left behind
    return dest
