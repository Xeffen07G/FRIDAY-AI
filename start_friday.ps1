# F.R.I.D.A.Y. One-Click Startup Script (Windows PowerShell)

Write-Host "--- F.R.I.D.A.Y. AI ASSISTANT STARTUP ---" -ForegroundColor Cyan

# 1. Check for Ollama
Write-Host "[1/4] Checking Ollama service..." -ForegroundColor Yellow
$ollama = Get-Process ollama -ErrorAction SilentlyContinue
if (!$ollama) {
    Write-Host "WARNING: Ollama is not running. Attempting to start..." -ForegroundColor Red
    start-process "ollama" "serve" -WindowStyle Hidden
    Start-Sleep -Seconds 5
}

# 2. Setup Environment
Write-Host "[2/4] Validating environment..." -ForegroundColor Yellow
if (!(Test-Path ".env")) {
    Write-Host "Creating .env from example..."
    Copy-Item ".env.example" ".env"
}

# 3. Start Backend
Write-Host "[3/4] Launching F.R.I.D.A.Y. Core Backend..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; python -m uvicorn main:app --reload --port 8000" -WindowStyle Normal

# 4. Start Frontend
Write-Host "[4/4] Launching F.R.I.D.A.Y. Interface..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev" -WindowStyle Normal

Write-Host "System Boot Sequence Complete." -ForegroundColor Green
Write-Host "Backend: http://localhost:8000"
Write-Host "Frontend: http://localhost:5173"
