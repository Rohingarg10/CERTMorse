$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'env.ps1')
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
& (Join-Path $PSScriptRoot '..\venv-core\Scripts\python.exe') (Join-Path $PSScriptRoot 'stage1-gate.py')
if ($LASTEXITCODE -ne 0) { throw 'Stage 1 v1.8.4 gate failed; see docs/stage1-gate-v1.8.4.json' }
