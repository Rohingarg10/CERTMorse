function Write-Utf8Lf {
    param(
        [Parameter(Mandatory=$true)][string]$LiteralPath,
        [Parameter(ValueFromPipeline=$true)]$InputObject
    )
    begin { $taskLines = [Collections.Generic.List[string]]::new() }
    process { $taskLines.Add([string]$InputObject) }
    end {
        $taskText = ($taskLines -join "`n").Replace("`r`n", "`n").Replace("`r", "`n")
        [IO.File]::WriteAllText($LiteralPath, $taskText.TrimEnd("`n") + "`n", [Text.UTF8Encoding]::new($false))
    }
}
