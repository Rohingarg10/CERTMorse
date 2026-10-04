param([int]$Bands = 20, [int]$MultiplicityBands = 10, [switch]$Resume, [ValidateSet('oracle','hoeffding','empirical')][string]$BandMode='oracle')
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'env.ps1')
$arguments = @('-m','certmorse.stage1','--bands',"$Bands",'--multiplicity-bands',"$MultiplicityBands",'--band-mode',$BandMode)
if ($Resume) { $arguments += '--resume' }
& (Join-Path (Split-Path -Parent $PSScriptRoot) 'venv-core\Scripts\python.exe') @arguments
if ($LASTEXITCODE -ne 0) { throw "R8a measurements exited $LASTEXITCODE" }
