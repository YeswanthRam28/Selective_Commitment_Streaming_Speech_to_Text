<#
.SYNOPSIS
    Starts backend and frontend services on Windows concurrently.
#>
$RepoRoot = Split-Path -Parent $PSScriptRoot

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Starting TWO 26 Streaming ASR Subsystems..." -ForegroundColor Cyan
Write-Host "Repo Root: $RepoRoot" -ForegroundColor Gray
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Start Backend FastAPI
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$RepoRoot\backend'; .\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --lifespan on"

# 2. Start Frontend Vite
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$RepoRoot\frontend'; npm run dev"

Write-Host "Services started!" -ForegroundColor Green
Write-Host "Backend  : http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "Frontend : http://localhost:5173" -ForegroundColor Green

