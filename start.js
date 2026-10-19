module.exports = {
  daemon: true,
  run: [
    {
      // CLAUDE-NOTE: pick a free port once and reuse it ({{port}} re-evaluates each step), so this
      // private ComfyUI never collides with other ComfyUI apps on 8188.
      method: "local.set",
      params: { comfy_port: "{{port}}" }
    },
    {
      method: "shell.run",
      params: {
        venv: "env",
        env: { TOKENIZERS_PARALLELISM: "false" },
        path: "app",
        message: [
          // --max-upload-size: meshes are uploaded to input/3d for the Low VRAM workflow (default cap is 100MB)
          "python comfyui/main.py --listen 127.0.0.1 --port {{local.comfy_port}} --max-upload-size 2048"
        ],
        on: [{
          event: "/To see the GUI go to:\s+(http:\/\/\S+)/",
          done: true
        }, {
          event: "/errno/i",
          break: false
        }, {
          event: "/error:/i",
          break: false
        }]
      }
    },
    {
      method: "local.set",
      params: { comfy_url: "{{input.event[1]}}" }
    },
    {
      method: "shell.run",
      params: {
        venv: "env",
        env: { COMFY_URL: "{{local.comfy_url}}" },
        path: "app",
        message: ["python app.py"],
        on: [{
          event: "/Running on local URL:\s+(http:\/\/[0-9.:]+)/",
          done: true
        }]
      }
    },
    {
      method: "local.set",
      params: { url: "{{input.event[1]}}" }
    }
  ]
}
