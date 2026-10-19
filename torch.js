module.exports = {
  run: [
    // windows nvidia
    {
      // CLAUDE-NOTE: torch 2.10 is pinned so triton-windows (<3.7, per the UltraTex installer's torch->triton
      // table) and the UltraTex sparse-attention kernels match. cu130 needs driver >= 580, else cu128.
      "when": "{{gpu === 'nvidia' && platform === 'win32'}}",
      "method": "shell.run",
      "params": {
        "venv": "{{args && args.venv ? args.venv : null}}",
        "path": "{{args && args.path ? args.path : '.'}}",
        "message": [
          "uv pip install torch==2.10.0 torchvision==0.25.0 torchaudio==2.10.0 --index-url https://download.pytorch.org/whl/{{Number.parseFloat(gpu_driver || '0') >= 580 ? 'cu130' : 'cu128'}} --force-reinstall --no-deps",
          "uv pip install \"triton-windows<3.7\""
        ]
      },
      "next": null
    },
    // linux nvidia (untested; UltraTex upstream targets Windows)
    {
      "when": "{{gpu === 'nvidia' && platform === 'linux'}}",
      "method": "shell.run",
      "params": {
        "venv": "{{args && args.venv ? args.venv : null}}",
        "path": "{{args && args.path ? args.path : '.'}}",
        "message": [
          "uv pip install torch==2.10.0 torchvision==0.25.0 torchaudio==2.10.0 --index-url https://download.pytorch.org/whl/cu130 --force-reinstall",
          "uv pip install triton"
        ]
      },
      "next": null
    }
  ]
}
