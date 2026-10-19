# Learnings (one-line gotchas, <15 words each)

- Quote pip version specifiers on Windows: unquoted `>=` becomes a redirect.
- UltraTex WF3 Load3DAdvanced needs mesh under ComfyUI/input/3d, not absolute path.
- UltraTex Bake PNG names: `<prefix>_NNNNN__albedo.png` (double underscore), only GLB in history.
- Trellis 2 is native ComfyUI (>=0.34); no compiled wheels needed.
- start.js regex strings need doubled backslashes; single ones silently never match.
- pterm start must stay attached; killing the client stalls the script mid-step.
- Template widgets: COLOR and COMFY_DYNAMICCOMBO_V3 (sub-inputs named combo.sub).
- /prompt returns 200 even with node_errors; check them or outputs silently skip.
- Trellis dino model is dino_v3_L_naf_fp32 from Comfy-Org/Pixal3D.
