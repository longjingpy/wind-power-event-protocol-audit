$ErrorActionPreference = 'Stop'
python (Join-Path $PSScriptRoot 'run_detection_hpo_v16.py') @args
exit $LASTEXITCODE
