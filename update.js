// Bootstrap only: pull the launcher, then run update_deps.js from the freshly pulled version.
// CLAUDE-NOTE: git must never pop up a login window (credential helper picker / GitHub sign-in). Public repos
// need no login; an empty credential.helper + these env vars make a bad URL or private repo fail fast instead.
// Keep the same lines in install.js, update.js and update_deps.js.
const NO_GIT_LOGIN = { GIT_TERMINAL_PROMPT: "0", GCM_INTERACTIVE: "never" }

module.exports = {
  run: [
    { method: "shell.run", params: { env: NO_GIT_LOGIN, message: "git -c credential.helper= pull" } },
    { method: "script.start", params: { uri: "update_deps.js" } }
  ]
}
