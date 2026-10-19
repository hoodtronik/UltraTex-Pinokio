// CLAUDE-NOTE: node packs are pinned to the commits PixelArtistry's Install-UltraTex.bat pins, because the
// API-format workflows in app/workflows depend on each node's exact widget order.
const ULTRATEX_VB = "8137da52ed8352305cb7825b39c36a250bf2507a"
const ULTRATEX_MAD = "8d434a2104be520ea699a9baac2327d124387111"

// CLAUDE-NOTE: no fs.link to Pinokio's shared drive on purpose. On this machine the shared drive lives on C:
// (partly inside Pinokio's program folder), and the user chose to keep the ~40 GB of models on the app's drive.
module.exports = {
  requires: { bundle: "ai" },
  run: [
    {
      method: "shell.run",
      params: {
        path: "app",
        message: [
          "git clone https://github.com/comfyanonymous/ComfyUI comfyui",
          "git clone https://github.com/visualbruno/ComfyUI-UltraTex comfyui/custom_nodes/ComfyUI-UltraTex",
          `git -C comfyui/custom_nodes/ComfyUI-UltraTex checkout ${ULTRATEX_VB}`,
          "git clone https://github.com/Mstafa-awad/UltraTex-ComfyUI-nodes comfyui/custom_nodes/comfyui_ultratex_modular",
          `git -C comfyui/custom_nodes/comfyui_ultratex_modular checkout --force ${ULTRATEX_MAD}`,
          "git clone https://github.com/city96/ComfyUI-GGUF comfyui/custom_nodes/ComfyUI-GGUF"
        ]
      }
    },
    {
      method: "shell.run",
      params: {
        venv: "env",
        path: "app",
        message: [
          "uv pip install -r comfyui/requirements.txt",
          "uv pip install -r comfyui/custom_nodes/ComfyUI-UltraTex/requirements.txt",
          "uv pip install -r comfyui/custom_nodes/comfyui_ultratex_modular/requirements.txt",
          "uv pip install -r comfyui/custom_nodes/ComfyUI-GGUF/requirements.txt",
          "uv pip install -r requirements.txt"
        ]
      }
    },
    {
      method: "script.start",
      params: {
        uri: "torch.js",
        params: { venv: "env", path: "app" }
      }
    },
    {
      // Real GPU test of UltraTex's Triton sparse attention (same check as Install-UltraTex.bat)
      method: "shell.run",
      params: {
        venv: "env",
        path: "app",
        message: "python tools/triton_check.py comfyui/custom_nodes/ComfyUI-UltraTex"
      }
    }
  ]
}
