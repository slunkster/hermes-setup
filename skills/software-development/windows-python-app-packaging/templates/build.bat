@echo off
REM Build a onefile Windows exe for a Python CLI/GUI tool.
REM Prerequisite: python -m pip install pyinstaller
REM Adjust: NAME, the --add-data asset list, --hidden-import, --collect-all.
cd /d "%~dp0"
set NAME=earve
python -m PyInstaller --noconfirm --clean --onefile --name %NAME% ^
  --add-data "gui.html;." ^
  --add-data "config.example.json;." ^
  --hidden-import gui ^
  --collect-all reportlab ^
  earve.py
if errorlevel 1 goto :err
copy /Y dist\%NAME%.exe %NAME%.exe >nul
echo.
echo Valmis: %CD%\%NAME%.exe
goto :eof
:err
echo Build failed.
exit /b 1
