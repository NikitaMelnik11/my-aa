@echo off
echo Setting up ChatConnect...
echo Installing dependencies...
pip install -r requirements.txt
echo.
echo Starting ChatConnect...
python app.py
pause
