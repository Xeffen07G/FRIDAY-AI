@echo off
echo Starting F.R.I.D.A.Y. Backend API...
cd %~dp0\backend
call ..\venv\Scripts\activate.bat
uvicorn main:app --reload
pause
