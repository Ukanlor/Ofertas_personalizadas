@echo off
setlocal

set "PYTHON_COMMAND=%~1"
if "%PYTHON_COMMAND%"=="" set "PYTHON_COMMAND=python"

set "REPO_ROOT=%~dp0.."
set "VENV_PATH=%REPO_ROOT%\.venv"
set "VENV_PYTHON=%VENV_PATH%\Scripts\python.exe"

"%PYTHON_COMMAND%" -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)"
if errorlevel 1 (
    echo Error: se requiere Python 3.12 para crear el entorno del proyecto. 1>&2
    exit /b 1
)

if not exist "%VENV_PYTHON%" (
    "%PYTHON_COMMAND%" -m venv --without-pip "%VENV_PATH%"
    if errorlevel 1 (
        echo Error: no se pudo crear el entorno virtual en "%VENV_PATH%". 1>&2
        exit /b 1
    )
)

"%VENV_PYTHON%" --version
if errorlevel 1 (
    echo Error: el entorno virtual existe, pero Python no se puede ejecutar. 1>&2
    exit /b 1
)

echo Entorno listo: %VENV_PATH%
echo Entorno creado sin pip: esta capa no requiere paquetes externos.
