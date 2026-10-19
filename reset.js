module.exports = {
  run: [
    { method: "fs.rm", params: { path: "app/comfyui" } },
    { method: "fs.rm", params: { path: "app/env" } }
  ]
}
