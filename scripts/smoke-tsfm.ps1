$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'env.ps1')
$env:HF_HUB_OFFLINE = '1'
& $env:CERTMORSE_TSFM_PYTHON tsfm_scripts/forecast.py --smoke --out docs/tsfm-smoke.json
if ($LASTEXITCODE -ne 0) { throw "TimesFM smoke exited $LASTEXITCODE" }
