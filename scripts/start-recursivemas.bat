@echo off
REM Avvio Wrapper RecursiveMAS (Windows) - porta 8001, solo localhost
cd /d "%~dp0\.."
if exist "venv\Scripts\activate.bat" call venv\Scripts\activate.bat
set MAS_STYLE=sequential_scaled
set MAS_DEVICE=cuda
echo Avvio su http://127.0.0.1:8001 - Ctrl+C per fermare
python recursivemas\server.py
pause
