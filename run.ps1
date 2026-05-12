# MRI AI Tumor Detection System - Single Launcher
# Run this file to start all services at once

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host @"

╔═══════════════════════════════════════════════════════════════╗
║     MRI AI Tumor & Anomaly Detection System                   ║
║     Starting All Services...                                  ║
╚═══════════════════════════════════════════════════════════════╝

"@ -ForegroundColor Cyan

# Start Backend
Write-Host "[1/3] Starting Backend (port 8000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", @"
cd '$projectRoot\backend'
. .\.venv\Scripts\Activate
uvicorn app.main:app --reload --port 8000
"@ -WindowStyle Normal

Start-Sleep -Seconds 2

# Start Frontend
Write-Host "[2/3] Starting Frontend (port 5173)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", @"
cd '$projectRoot\frontend'
npm run dev
"@ -WindowStyle Normal

Start-Sleep -Seconds 2

# Start AI Service
Write-Host "[3/3] Starting AI Service (port 8001)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", @"
cd '$projectRoot\ai'
. .\.venv\Scripts\Activate
python service.py
"@ -WindowStyle Normal

Write-Host @"

═══════════════════════════════════════════════════════════════
   All Services Started Successfully!
═══════════════════════════════════════════════════════════════

   📍 Backend API:    http://localhost:8000
   🌐 Frontend UI:   http://localhost:5173  
   🤖 AI Service:    http://localhost:8001

   Open http://localhost:5173 in your browser to use the system

   Press Ctrl+C in any terminal window to stop that service

"@ -ForegroundColor Green