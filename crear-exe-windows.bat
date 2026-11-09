@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Ejecuta antes ejecutar-windows.bat
    pause
    exit /b 1
)
choice /M "Instalar PyInstaller y compilar PixelVault.exe"
if errorlevel 2 exit /b 0
".venv\Scripts\python.exe" -m pip install pyinstaller || goto error
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --onefile --windowed --name PixelVault --paths src launcher.py || goto error
echo EXE disponible en dist\PixelVault.exe
pause
exit /b 0
:error
echo Error en compilacion
pause
exit /b 1
