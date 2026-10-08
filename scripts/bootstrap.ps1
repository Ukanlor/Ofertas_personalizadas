param(
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$venvPath = Join-Path $repoRoot ".venv"

& $Python -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)"
if ($LASTEXITCODE -ne 0) {
    throw "Se requiere Python 3.12 para crear el entorno del proyecto."
}

if (-not (Test-Path -LiteralPath $venvPath)) {
    # El núcleo usa solo la biblioteca estándar; pip se añadirá cuando exista
    # una dependencia real que lo justifique.
    & $Python -m venv --without-pip $venvPath
    if ($LASTEXITCODE -ne 0) {
        throw "No se pudo crear el entorno virtual en $venvPath."
    }
}

$venvPython = Join-Path $venvPath "Scripts\python.exe"
& $venvPython --version
if ($LASTEXITCODE -ne 0) {
    throw "El entorno virtual existe, pero Python no se puede ejecutar."
}

Write-Output "Entorno listo: $venvPath"
Write-Output "Entorno creado sin pip: esta capa no requiere paquetes externos."
