@echo off
setlocal
cd /d "%~dp0"

where node >nul 2>nul
if errorlevel 1 (
  echo Node.js 22 or newer is required. Install it from https://nodejs.org/ then run this file again.
  pause
  exit /b 1
)

start "" http://127.0.0.1:4173
npm start
pause
