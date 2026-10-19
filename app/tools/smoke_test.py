"""Headless smoke test of the pipelines against a running ComfyUI (set COMFY_URL).

Run from app/:
    smoke_test.py mesh_<low|high>[_preview] IMAGE
    smoke_test.py texture_<low|high>_<standard|advanced> MESH IMAGE
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ultratex_gui import pipelines  # noqa: E402


def prog(frac, text):
    print(f"  {text}" + (f" {frac:.0%}" if frac is not None else ""), flush=True)


what = sys.argv[1]
t0 = time.time()
if what.startswith("mesh"):
    mode = what.split("_")[1]
    r = pipelines.mesh(os.path.abspath(sys.argv[2]), mode, "preview" in what, 700000, 42, prog)
else:
    _, mode, quality = what.split("_")
    steps = 4 if mode == "low" else 25
    r = pipelines.texture(os.path.abspath(sys.argv[2]), os.path.abspath(sys.argv[3]), mode, quality,
                          1024, steps, 42, 2048, "comfy_gpu", prog)
print("RESULT", r, f"{time.time() - t0:.0f}s", flush=True)
