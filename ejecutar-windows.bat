@echo off
cd /d "%~dp0"
where py >nul 2>&1
if errorlevel 1 (
    echo Necesitas Python 3.10 o superior.
    pause
    exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
    echo Se creara un entorno virtual y se instalaran las dependencias.
    choice /M "Continuar"
    if errorlevel 2 exit /b 1
    py -3 -m venv .venv || goto error
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt || goto error
)
".venv\Scripts\python.exe" launcher.py
if errorlevel 1 goto error
exit /b 0
:error
echo Se ha producido un error. Consulta el mensaje anterior.
pause
exit /b 1
