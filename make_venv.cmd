@echo off

echo Installing venv...
python -m pip install virtualenv

echo[
echo Creating venv...
python -m venv venv
call venv\Scripts\activate.bat

echo[
echo Pulling dependencies...
pip install --upgrade pip
pip install -r requirements.txt

pause