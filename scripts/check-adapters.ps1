. (Join-Path $PSScriptRoot 'env.ps1')
& (Join-Path (Split-Path -Parent $PSScriptRoot) 'venv-core\Scripts\python.exe') -m pytest -q tests/test_external_adapters.py
if ($LASTEXITCODE -ne 0) { throw "Adapter tests exited $LASTEXITCODE" }
