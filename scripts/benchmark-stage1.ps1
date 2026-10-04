param([double]$Limit=600,[int]$Repeats=3,[switch]$Resume)
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'env.ps1')
$arguments=@((Join-Path $PSScriptRoot 'benchmark-stage1.py'),'--limit',"$Limit",'--repeats',"$Repeats")
if ($Resume) { $arguments+='--resume' }
& (Join-Path $PSScriptRoot '..\venv-core\Scripts\python.exe') @arguments
if ($LASTEXITCODE -ne 0) { throw 'Benchmark failed' }
