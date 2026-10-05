param([ValidateSet('oracle', 'probes', 'all')][string]$Phase = 'all')
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'env.ps1')
$taskRoot = Split-Path -Parent $PSScriptRoot
Add-Type -TypeDefinition @'
using System.Runtime.InteropServices;
public static class CertMorseCompletionPower {
    [DllImport("kernel32.dll")]
    public static extern uint SetThreadExecutionState(uint flags);
}
'@
$previous = [CertMorseCompletionPower]::SetThreadExecutionState([uint32]2147483649)
if ($previous -eq 0) { throw 'Windows rejected the temporary system wake request.' }
try {
    & (Join-Path $taskRoot 'venv-core\Scripts\python.exe') -u (Join-Path $PSScriptRoot 'complete-stage1-v1.8.4.py') --phase $Phase
    if ($LASTEXITCODE -ne 0) { throw "Stage 1 completion exited with code $LASTEXITCODE" }
}
finally {
    [CertMorseCompletionPower]::SetThreadExecutionState($previous) | Out-Null
}
