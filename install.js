// CLAUDE-NOTE: node packs are pinned to the commits PixelArtistry's Install-UltraTex.bat pins, because the
// API-format workflows in app/workflows depend on each node's exact widget order.
const ULTRATEX_VB = "8137da52ed8352305cb7825b39c36a250bf2507a"
const ULTRATEX_MAD = "8d434a2104be520ea699a9baac2327d124387111"

// CLAUDE-NOTE: no fs.link to Pinokio's shared drive on purpose. On this machine the shared drive lives on C:
// (partly inside Pinokio's program folder), and the user chose to keep the ~40 GB of models on the app's drive.
// CLAUDE-NOTE: git must never pop up a login window (credential helper picker / GitHub sign-in). Public repos
// need no login; an empty credential.helper + these env vars make a bad URL or private repo fail fast instead.
// Keep the same lines in install.js, update.js and update_deps.js.
const NO_GIT_LOGIN = { GIT_TERMINAL_PROMPT: "0", GCM_INTERACTIVE: "never" }

module.exports = {
  requires: { bundle: "ai" },
  run: [
    {
      method: "shell.run",
      params: {
        path: "app",
        message: [
          "git -c credential.helper= clone https://github.com/comfyanonymous/ComfyUI comfyui",
          "git -c credential.helper= clone https://github.com/visualbruno/ComfyUI-UltraTex comfyui/custom_nodes/ComfyUI-UltraTex",
          `git -c credential.helper= -C comfyui/custom_nodes/ComfyUI-UltraTex checkout ${ULTRATEX_VB}`,
          "git -c credential.helper= clone https://github.com/Mstafa-awad/UltraTex-ComfyUI-nodes comfyui/custom_nodes/comfyui_ultratex_modular",
          `git -c credential.helper= -C comfyui/custom_nodes/comfyui_ultratex_modular checkout --force ${ULTRATEX_MAD}`,
          "git -c credential.helper= clone https://github.com/city96/ComfyUI-GGUF comfyui/custom_nodes/ComfyUI-GGUF"
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
