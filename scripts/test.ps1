param([ValidateSet('core','ttk','all')][string]$Component = 'core')
$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $taskRoot
if ($Component -in @('ttk','all')) { . (Join-Path $PSScriptRoot 'env.ps1') }
$testArgs = @('-m','pytest','-q')
if ($Component -eq 'core') { $testArgs += @('-m','not ttk and not tsfm and not gurobi') }
if ($Component -eq 'ttk') { $testArgs += @('-m','ttk') }
& (Join-Path $taskRoot 'venv-core\Scripts\python.exe') @testArgs
if ($LASTEXITCODE -ne 0) { throw "Tests exited $LASTEXITCODE" }
