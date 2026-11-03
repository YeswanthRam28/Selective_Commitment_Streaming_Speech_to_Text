@echo off
title TWO 26 Services Launcher
cd /d "%~dp0\.."

echo ==========================================================
echo Starting TWO 26 Streaming ASR Backend and Frontend Services
echo ==========================================================

start "TWO 26 Backend (FastAPI)" cmd /k "cd backend && venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --lifespan on"

start "TWO 26 Frontend (Vite)" cmd /k "cd frontend && npm run dev"

echo Both services launched in independent background windows.
echo Backend  : http://127.0.0.1:8000
echo Frontend : http://localhost:5173
pause

