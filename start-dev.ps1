<#
.SYNOPSIS
    Start Django Backend and React Frontend simultaneously for HR Policy Assistant.

.DESCRIPTION
    This script launches both the Django backend (port 8000) and the Vite React
    frontend (port 5173) for the HR Policy Assistant application.

    Prerequisites:
    - Python 3.x with Django and dependencies installed
    - Node.js with Vite and frontend dependencies installed
    - PostgreSQL running with hr_assistant database
    - .env file present at backend/ with valid configuration
    - .env file present at frontend/hr-frontend/ with VITE_API_BASE_URL

.GUI
    Does not open a GUI; outputs commands to console.

.RUNNOTES
    Example: PowerShell 7.x
        powershell -ExecutionPolicy Bypass -File "start-dev.ps1"

    Or run individual commands from the script below.
#>

# -------------------------------------------------------
# Configuration
# -------------------------------------------------------
$BASE_DIR = "D:\web projects\HR_Policy_Assistant"
$BACKEND_DIR = Join-Path $BASE_DIR "backend"
$FRONTEND_DIR = Join-Path $BASE_DIR "frontend\hr-frontend"

$BACKEND_PORT = 8000
$FRONTEND_PORT = 5173

# -------------------------------------------------------
# Step 1: Verify PostgreSQL is running
# -------------------------------------------------------
Write-Host "=== Step 1: Checking PostgreSQL ===" -ForegroundColor Cyan

$pgTest = Try {
    $result = & psql -U postgres -c "SELECT 1" -h localhost 2>&1
    Write-Host "PostgreSQL reachable." -ForegroundColor Green
    $true
} Catch {
    Write-Warning "PostgreSQL not reachable at localhost:5432."
    Write-Warning "Start Docker Desktop and ensure the database service is running."
    $false
}

# -------------------------------------------------------
# Step 2: Start Django Backend
# -------------------------------------------------------
Write-Host "`n=== Step 2: Starting Django Backend (port $BACKEND_PORT) ===" -ForegroundColor Cyan

$backendEnv = @{
    "POSTGRES_DB" = "hr_assistant"
    "POSTGRES_USER" = "postgres"
    "POSTGRES_PASSWORD" = "sql@321"
    "POSTGRES_HOST" = "localhost"
    "POSTGRES_PORT" = "5432"
    "GEMINI_API_KEY" = ""
    "DJANGO_SECRET_KEY" = "django-insecure-dev-key-change-in-production"
    "DJANGO_DEBUG" = "True"
    "RAG_SIMILARITY_THRESHOLD" = "0.7"
    "RAG_RETRIEVAL_LIMIT" = "5"
}

# Check if manage.py exists
if (-not (Test-Path Join-Path $BACKEND_DIR "manage.py")) {
    Write-Error "backend/manage.py not found at $BACKEND_DIR"
    Write-Error "Expected path: $BACKEND_DIR/manage.py"
    return 1
}

Write-Host "Launching: cd /d `"$BACKEND_DIR`" && & .\manage.py runserver 0.0.0.0:$BACKEND_PORT" -ForegroundColor Yellow

$backendCmd = "cd /d `"$BACKEND_DIR`" && & .\manage.py runserver 0.0.0.0:$BACKEND_PORT"
$backendProcess = Start-Process python -ArgumentList ".\manage.py runserver 0.0.0.0:$BACKEND_PORT" -WorkingDirectory $BACKEND_DIR -NoNewWindow -PassThru 2>$null

# Wait a moment for backend to start
Start-Sleep -Seconds 3

# -------------------------------------------------------
# Step 3: Verify Backend API is reachable
# -------------------------------------------------------
Write-Host "`n=== Step 3: Verifying Backend API ===" -ForegroundColor Cyan

$apiUrl = "http://localhost:$BACKEND_PORT/api/v1/auth/token/"
Write-Host "Testing: $apiUrl" -ForegroundColor Yellow

$apiReady = $false
for ($i = 0; $i -lt 10; $i++) {
    $response = Try { Invoke-RestMethod -Method Get -Uri $apiUrl -TimeoutSec 5 } Catch { $null }
    if ($response -ne $null) {
        Write-Host "Backend API is reachable (status: $($response.statusCode -or 'ok'))" -ForegroundColor Green
        $apiReady = $true
        break
    }
    Write-Host "Waiting for backend... ($($i+1)/10)" -ForegroundColor Yellow
    Start-Sleep -Seconds 2
}

if (-not $apiReady) {
    Write-Warning "Backend API did not become reachable within 20 seconds."
    Write-Warning "Check: backend/manage.py, database connection, and .env configuration."
    Write-Warning "The backend may still be starting up - continue anyway if you see the server prompt."
}

# -------------------------------------------------------
# Step 4: Start React Frontend (Vite)
# -------------------------------------------------------
Write-Host "`n=== Step 4: Starting React Frontend (port $FRONTEND_PORT) ===" -ForegroundColor Cyan

if (-not (Test-Path Join-Path $FRONTEND_DIR "package.json")) {
    Write-Error "frontend/hr-frontend/package.json not found at $FRONTEND_DIR"
    Write-Error "Expected path: $FRONTEND_DIR/package.json"
    return 1
}

Write-Host "Launching: cd /d `"$FRONTEND_DIR`" && npm run dev" -ForegroundColor Yellow

$frontendProcess = Start-Process npm -ArgumentList "run dev" -WorkingDirectory $FRONTEND_DIR -NoNewWindow -PassThru 2>$null

# Wait a moment for frontend to start
Start-Sleep -Seconds 4

# -------------------------------------------------------
# Step 5: Final Summary
# -------------------------------------------------------
Write-Host "`n=== HR Policy Assistant Development Environment ===" -ForegroundColor Green
Write-Host "---------------------------------------------" -ForegroundColor Green
Write-Host "Backend API:    http://localhost:$BACKEND_PORT" -ForegroundColor White
Write-Host "Frontend UI:    http://localhost:$FRONTEND_PORT" -ForegroundColor White
Write-Host "Admin UI:       http://localhost:$FRONTEND_PORT/" -ForegroundColor White
Write-Host "Admin Dashboard: http://localhost:$FRONTEND_PORT/hr-admin-dashboard" -ForegroundColor White
Write-Host "Employee UI:    http://localhost:$FRONTEND_PORT/employee-dashboard" -ForegroundColor White
Write-Host "Login:          http://localhost:$FRONTEND_PORT/login" -ForegroundColor White
Write-Host "About:          http://localhost:$FRONTEND_PORT/about" -ForegroundColor White
Write-Host "---------------------------------------------" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the processes." -ForegroundColor DarkYellow
Write-Host "       Or close this PowerShell window." -ForegroundColor DarkYellow

# Keep the script running so both processes stay alive
try {
    # Wait for either process to exit
    $wait = Wait-Process -Id $backendProcess.Id -Id $frontendProcess.Id -Timeout 3600 -ErrorAction SilentlyContinue
} catch {
    Write-Host "One or both processes have stopped." -ForegroundColor Red
}

# Do not auto-kill the processes on script exit
Remove-Variable backendEnv frontendEnv backendCmd frontendProcess apiUrl apiReady wait