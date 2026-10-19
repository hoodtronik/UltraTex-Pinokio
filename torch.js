module.exports = {
  run: [
    // windows nvidia
    {
      // CLAUDE-NOTE: torch 2.13 is the newest version in the UltraTex installer's torch->triton table
      // (2.12/2.13 -> triton-windows<3.8). cu130 has no torchaudio past 2.11 and nothing here needs it.
      // cu130 needs driver >= 580, else cu128.
      "when": "{{gpu === 'nvidia' && platform === 'win32'}}",
      "method": "shell.run",
      "params": {
        "venv": "{{args && args.venv ? args.venv : null}}",
        "path": "{{args && args.path ? args.path : '.'}}",
        "message": [
          "uv pip install torch==2.13.0 torchvision==0.28.0 --index-url https://download.pytorch.org/whl/{{Number.parseFloat(gpu_driver || '0') >= 580 ? 'cu130' : 'cu128'}} --force-reinstall --no-deps",
          "uv pip install \"triton-windows<3.8\""
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
          "uv pip install torch==2.13.0 torchvision==0.28.0 --index-url https://download.pytorch.org/whl/cu130 --force-reinstall",
          "uv pip install triton"
        ]
      },
      "next": null
    }
  ]
}
