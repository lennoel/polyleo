@echo off
REM Inicia el backend Django del asistente (http://localhost:8000)
cd /d "%~dp0backend"
"%~dp0.venv\Scripts\python.exe" manage.py runserver 8000
