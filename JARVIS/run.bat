@echo off
echo ========================================
echo   J.A.R.V.I.S. - Starting...
echo ========================================
echo.
pip install -r requirements.txt 2>nul
python main.py
pause
