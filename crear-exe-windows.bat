@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Primero ejecuta ejecutar-windows.bat
    pause
    exit /b 1
)
choice /M "Instalar PyInstaller y crear PIXEL VAULT con icono propio"
if errorlevel 2 exit /b 0
".venv\Scripts\python.exe" -m pip install pyinstaller || goto error
".venv\Scripts\python.exe" scripts\create_icon.py || goto error
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --onefile --windowed --name PixelVault --icon assets\pixelvault.ico --add-data "assets\pixelvault.png;assets" --paths src --collect-all PySide6.QtMultimedia --collect-all PySide6.QtMultimediaWidgets --collect-all assimp_py launcher.py || goto error
echo EXE creado en dist\PixelVault.exe
echo Para obtener el instalador completo, descarga el artifact "Windows Installer" de GitHub Actions.
pause
exit /b 0
:error
echo Error: consulta la salida anterior.
pause
exit /b 1
