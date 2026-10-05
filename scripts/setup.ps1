param([ValidateSet('all','core','ttk','tsfm','inventory')][string]$Component = 'all')
$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
. (Join-Path $PSScriptRoot 'text-output.ps1')
Set-Location -LiteralPath $taskRoot
$toolDir = Join-Path $taskRoot '.tools'
New-Item -ItemType Directory -Force -Path $toolDir | Out-Null
$env:UV_CACHE_DIR = Join-Path $toolDir 'uv-cache'
$env:UV_PYTHON_INSTALL_DIR = Join-Path $toolDir 'python'
$env:HF_HOME = Join-Path $toolDir 'huggingface'
$env:MAMBA_ROOT_PREFIX = Join-Path $toolDir 'mamba'
$env:CONDA_PKGS_DIRS = Join-Path $taskRoot '.p'
function Run-Native([string]$Exe, [string[]]$Arguments) {
    & $Exe @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Exe exited $LASTEXITCODE" }
}
$uv = Join-Path $toolDir 'uv\uv.exe'
if (-not (Test-Path -LiteralPath $uv)) {
    $archive = Join-Path $toolDir 'uv.zip'
    Run-Native 'curl.exe' @('-fL','--retry','3','https://github.com/astral-sh/uv/releases/latest/download/uv-x86_64-pc-windows-msvc.zip','-o',$archive)
    Expand-Archive -LiteralPath $archive -DestinationPath (Join-Path $toolDir 'uv') -Force
}
Run-Native $uv @('python','install','3.11','--no-bin')
$corePython = Join-Path $taskRoot 'venv-core\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $corePython)) { Run-Native $uv @('venv','--python','3.11','venv-core') }
if ($Component -in @('all','core')) {
    Run-Native $uv @('pip','install','--python',$corePython,'-r','requirements.in')
    & $uv pip freeze --python $corePython | Write-Utf8Lf -LiteralPath 'requirements.txt'
    Run-Native $corePython @('-m','pip','--version')
}
if ($Component -in @('all','ttk')) {
    $cacheDrive = $null
    try {
        $mamba = Join-Path $toolDir 'micromamba\Library\bin\micromamba.exe'
        if (-not (Test-Path -LiteralPath $mamba)) {
            $archive = Join-Path $toolDir 'micromamba.tar.bz2'
            Run-Native 'curl.exe' @('-fL','--retry','3','https://micro.mamba.pm/api/micromamba/win-64/latest','-o',$archive)
            New-Item -ItemType Directory -Force -Path (Join-Path $toolDir 'micromamba') | Out-Null
            Run-Native 'tar.exe' @('-xf',$archive,'-C',(Join-Path $toolDir 'micromamba'))
        }
        # conda-forge's archive paths exceed MAX_PATH even with a short folder
        # name. A temporary drive alias keeps extraction inside this workspace.
        foreach ($letter in @('Z','Y','X','W')) {
            if (-not (Test-Path ($letter + ':\'))) {
                Run-Native 'subst.exe' @(($letter + ':'),$taskRoot)
                $cacheDrive = $letter + ':'
                $env:CONDA_PKGS_DIRS = $cacheDrive + '\.p-short'
                break
            }
        }
        Run-Native $mamba @('create','-y','-p',(Join-Path $taskRoot 'venv-ttk'),'-c','conda-forge','topologytoolkit','paraview')
    } catch { $_ | Out-String | Write-Utf8Lf -LiteralPath (Join-Path $toolDir 'ttk-setup-error.txt'); Write-Warning $_ }
    finally { if ($cacheDrive) { & subst.exe $cacheDrive /D } }
}
if ($Component -in @('all','tsfm')) {
    try {
        $tsPython = Join-Path $taskRoot 'venv-tsfm\Scripts\python.exe'
        if (-not (Test-Path -LiteralPath $tsPython)) { Run-Native $uv @('venv','--python','3.11','venv-tsfm') }
        Run-Native $uv @('pip','install','--python',$tsPython,'torch','--index-url','https://download.pytorch.org/whl/cpu')
        Run-Native $uv @('pip','install','--python',$tsPython,'timesfm[torch]','huggingface-hub','numpy')
        & $uv pip freeze --python $tsPython | Write-Utf8Lf -LiteralPath 'requirements-tsfm.txt'
        Run-Native $tsPython @('-c',"from huggingface_hub import snapshot_download; snapshot_download('google/timesfm-3.0-pytorch')")
    } catch { $_ | Out-String | Write-Utf8Lf -LiteralPath (Join-Path $toolDir 'tsfm-setup-error.txt'); Write-Warning $_ }
}
try {
    $cpu = Get-CimInstance Win32_Processor | Select-Object Name,NumberOfCores,NumberOfLogicalProcessors
    $system = Get-CimInstance Win32_ComputerSystem | Select-Object TotalPhysicalMemory
    @{cpu=$cpu;system=$system;date=(Get-Date -Format o)} | ConvertTo-Json -Depth 5 | Write-Utf8Lf -LiteralPath (Join-Path $toolDir 'hardware.json')
} catch { Write-Warning "Hardware inventory unavailable: $_" }
if (Test-Path -LiteralPath (Join-Path $taskRoot 'venv-ttk\conda-meta')) {
    $packageLines = & (Join-Path $toolDir 'micromamba\Library\bin\micromamba.exe') list --explicit -p (Join-Path $taskRoot 'venv-ttk')
    $lockLines = @('# Platform: win-64','@EXPLICIT') + @($packageLines | Where-Object { $_ -match '^https://' })
    $lockLines | Write-Utf8Lf -LiteralPath (Join-Path $taskRoot 'requirements-ttk.txt')
}
