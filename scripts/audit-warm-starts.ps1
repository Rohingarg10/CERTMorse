$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'env.ps1')
& (Join-Path $PSScriptRoot '..\venv-core\Scripts\python.exe') (Join-Path $PSScriptRoot 'audit-warm-starts.py')
if ($LASTEXITCODE -ne 0) { throw 'Warm-start audit failed' }
