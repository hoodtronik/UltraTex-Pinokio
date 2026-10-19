// CLAUDE-NOTE: the UltraTex node packs stay pinned (workflows depend on their widget order). Bump the
// commits here and in install.js together, then re-export app/workflows.
const ULTRATEX_VB = "8137da52ed8352305cb7825b39c36a250bf2507a"
const ULTRATEX_MAD = "8d434a2104be520ea699a9baac2327d124387111"

module.exports = {
  run: [
    {
      method: "shell.run",
      params: {
        path: "app",
        message: [
          "git -C comfyui pull || git clone https://github.com/comfyanonymous/ComfyUI comfyui",
          "git -C comfyui/custom_nodes/ComfyUI-UltraTex fetch || git clone https://github.com/visualbruno/ComfyUI-UltraTex comfyui/custom_nodes/ComfyUI-UltraTex",
          `git -C comfyui/custom_nodes/ComfyUI-UltraTex checkout ${ULTRATEX_VB}`,
          "git -C comfyui/custom_nodes/comfyui_ultratex_modular fetch || git clone https://github.com/Mstafa-awad/UltraTex-ComfyUI-nodes comfyui/custom_nodes/comfyui_ultratex_modular",
          `git -C comfyui/custom_nodes/comfyui_ultratex_modular checkout --force ${ULTRATEX_MAD}`,
          "git -C comfyui/custom_nodes/ComfyUI-GGUF pull || git clone https://github.com/city96/ComfyUI-GGUF comfyui/custom_nodes/ComfyUI-GGUF"
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
    { method: "script.start", params: { uri: "torch.js", params: { venv: "env", path: "app" } } }
  ]
}
