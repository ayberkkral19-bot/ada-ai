@echo off
echo ========================================
echo   J.A.R.V.I.S. - Building EXE...
echo ========================================
echo.
pip install -r requirements.txt
pip install pyinstaller
python build.py
echo.
echo Build complete! Check the dist folder.
pause
