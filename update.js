// Bootstrap only: pull the launcher, then run update_deps.js from the freshly pulled version.
module.exports = {
  run: [
    { method: "shell.run", params: { message: "git pull" } },
    { method: "script.start", params: { uri: "update_deps.js" } }
  ]
}
