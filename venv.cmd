@echo off
python -m venv venv
CALL venv\scripts\activate.bat

python -m pip install --upgrade pip
pip install setuptools --upgrade
pip install -r requirements.txt

echo.
echo Installation completed.
pause
