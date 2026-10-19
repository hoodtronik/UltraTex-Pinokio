module.exports = {
  version: "8.0.0",
  title: "UltraTex",
  description: "Trellis 2 image-to-mesh + UltraTex PBR texturing in a simple GUI on a private ComfyUI backend.",
  icon: "icon.png",
  menu: async (kernel, info) => {
    let installed = info.exists("app/env")
    let running = {
      install: info.running("install.js"),
      start: info.running("start.js"),
      update: info.running("update.js") || info.running("update_deps.js"),
      reset: info.running("reset.js"),
    }
    if (running.install) {
      return [{ default: true, icon: "fa-solid fa-plug", text: "Installing", href: "install.js" }]
    }
    if (!installed) {
      return [{ default: true, icon: "fa-solid fa-plug", text: "Install", href: "install.js" }]
    }
    if (running.start) {
      let local = info.local("start.js")
      let items = []
      if (local && local.url) {
        items.push({ default: true, icon: "fa-solid fa-rocket", text: "Open UltraTex", href: local.url + "?ts=" + Date.now() })
      }
      if (local && local.comfy_url) {
        items.push({ icon: "fa-solid fa-diagram-project", text: "Open ComfyUI", href: local.comfy_url })
      }
      items.push({ default: !(local && local.url), icon: "fa-solid fa-terminal", text: "Terminal", href: "start.js" })
      return items
    }
    if (running.update) {
      return [{ default: true, icon: "fa-solid fa-terminal", text: "Updating", href: "update.js" }]
    }
    if (running.reset) {
      return [{ default: true, icon: "fa-solid fa-terminal", text: "Resetting", href: "reset.js" }]
    }
    return [
      { default: true, icon: "fa-solid fa-power-off", text: "Start", href: "start.js?ts=" + Date.now() },
      { icon: "fa-solid fa-plug", text: "Update", href: "update.js" },
      { icon: "fa-solid fa-plug", text: "Install", href: "install.js" },
      { icon: "fa-regular fa-circle-xmark", text: "Reset", href: "reset.js", confirm: "Remove ComfyUI and the Python env? (Models in the shared drive are kept.)" }
    ]
  }
}
