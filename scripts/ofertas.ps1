param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$CliArguments
)

$repoRoot = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $venvPython)) {
    Write-Error "Falta .venv. Ejecuta primero scripts\bootstrap.ps1."
    exit 1
}

$env:PYTHONPATH = Join-Path $repoRoot "src"
Push-Location $repoRoot
try {
    & $venvPython -m ofertas @CliArguments
    $cliExitCode = $LASTEXITCODE
}
finally {
    Pop-Location
}
exit $cliExitCode
