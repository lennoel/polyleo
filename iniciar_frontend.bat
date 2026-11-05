@echo off
REM Inicia el frontend React/Vite del asistente (http://localhost:5173)
set PATH=%~dp0.tools\node-v24.21.0-win-x64;%PATH%
cd /d "%~dp0frontend"
npm.cmd run dev
