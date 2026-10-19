"""Real GPU test of UltraTex's Triton sparse attention.

Mirrors the check in PixelArtistry's Install-UltraTex.bat. Never fails the install:
without Triton the High VRAM workflows fall back to comfy_default attention, but
the Low VRAM (GGUF) workflow needs it, so we print a loud warning.
"""
import sys

node_dir = sys.argv[1]
sys.path.insert(0, node_dir)
try:
    from ultratex_core.optim import check_sparse_attention

    err = check_sparse_attention()
except Exception as e:  # import errors mean the same thing to the user: no Triton
    err = repr(e)

if err is None:
    print("[UltraTex] Triton sparse attention: OK")
else:
    print("[UltraTex] WARNING: Triton sparse attention FAILED: " + str(err))
    print("[UltraTex] Low VRAM mode will not work; High VRAM mode will use comfy_default attention.")
