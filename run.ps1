$ErrorActionPreference = 'Stop'
$arguments = $args
if ($arguments.Count -eq 0) {
    $arguments = @('--test', '--repository', 'data/branch.json',
                   '--package', 'A', '--version', '1.0.0')
}

Push-Location -LiteralPath $PSScriptRoot
try {
    if (Get-Command python -ErrorAction SilentlyContinue) {
        & python -m src.main @arguments
    } else {
        & py -3 -m src.main @arguments
    }
    $exitCode = $LASTEXITCODE
} finally {
    Pop-Location
}
exit $exitCode
