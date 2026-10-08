@echo off
setlocal

set "REPO_ROOT=%~dp0.."
set "VENV_PYTHON=%REPO_ROOT%\.venv\Scripts\python.exe"

if not exist "%VENV_PYTHON%" (
    echo Error: falta .venv. Ejecuta primero scripts\bootstrap.cmd. 1>&2
    exit /b 1
)

set "PYTHONPATH=%REPO_ROOT%\src"
pushd "%REPO_ROOT%"
"%VENV_PYTHON%" -m ofertas %*
set "CLI_EXIT_CODE=%ERRORLEVEL%"
popd
exit /b %CLI_EXIT_CODE%
