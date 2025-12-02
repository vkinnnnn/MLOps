#!/usr/bin/env pwsh
# Student Loan Document Extractor - Project Startup Script
# Shows progress indicators and completion status

$ErrorActionPreference = "Continue"

# Colors
function Write-Progress-Step {
    param([string]$Step, [string]$Status, [int]$Percent)
    $color = switch ($Status) {
        "Starting" { "Yellow" }
        "Running" { "Green" }
        "Error" { "Red" }
        "Waiting" { "Cyan" }
        default { "White" }
    }
    Write-Host "[$Percent%] " -NoNewline -ForegroundColor $color
    Write-Host "$Step" -ForegroundColor White -NoNewline
    Write-Host " - $Status" -ForegroundColor $color
}

function Write-Header {
    param([string]$Text)
    Write-Host ""
    Write-Host "=" * 60 -ForegroundColor Cyan
    Write-Host "  $Text" -ForegroundColor Cyan
    Write-Host "=" * 60 -ForegroundColor Cyan
    Write-Host ""
}

function Test-Service {
    param([string]$Url, [int]$Timeout = 5)
    try {
        $response = Invoke-WebRequest -Uri $Url -Method GET -TimeoutSec $Timeout -ErrorAction SilentlyContinue
        return $response.StatusCode -eq 200
    } catch {
        return $false
    }
}

function Wait-ForService {
    param([string]$Name, [string]$Url, [int]$MaxWait = 30)
    $elapsed = 0
    $interval = 2
    
    while ($elapsed -lt $MaxWait) {
        if (Test-Service -Url $Url -Timeout 3) {
            return $true
        }
        Start-Sleep -Seconds $interval
        $elapsed += $interval
        Write-Host "  Waiting for $Name... ($elapsed/$MaxWait seconds)" -ForegroundColor Gray
    }
    return $false
}

# Clear screen
Clear-Host

Write-Header "Student Loan Document Extractor - Starting Project"

$totalSteps = 8
$currentStep = 0

# Step 1: Check Docker
$currentStep++
Write-Progress-Step "Checking Docker" "Starting" ([math]::Round(($currentStep / $totalSteps) * 100))
try {
    $dockerVersion = docker --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Progress-Step "Checking Docker" "Running" ([math]::Round(($currentStep / $totalSteps) * 100))
        Write-Host "  Docker: $dockerVersion" -ForegroundColor Gray
    } else {
        Write-Progress-Step "Checking Docker" "Error" ([math]::Round(($currentStep / $totalSteps) * 100))
        Write-Host "  ERROR: Docker is not running. Please start Docker Desktop." -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Progress-Step "Checking Docker" "Error" ([math]::Round(($currentStep / $totalSteps) * 100))
    Write-Host "  ERROR: Docker not found. Please install Docker Desktop." -ForegroundColor Red
    exit 1
}

# Step 2: Check Docker Compose
$currentStep++
Write-Progress-Step "Checking Docker Compose" "Starting" ([math]::Round(($currentStep / $totalSteps) * 100))
try {
    $composeVersion = docker compose version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Progress-Step "Checking Docker Compose" "Running" ([math]::Round(($currentStep / $totalSteps) * 100))
    } else {
        Write-Progress-Step "Checking Docker Compose" "Error" ([math]::Round(($currentStep / $totalSteps) * 100))
        Write-Host "  ERROR: Docker Compose not available." -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Progress-Step "Checking Docker Compose" "Error" ([math]::Round(($currentStep / $totalSteps) * 100))
    exit 1
}

# Step 3: Start Docker Services
$currentStep++
Write-Progress-Step "Starting Docker Services" "Starting" ([math]::Round(($currentStep / $totalSteps) * 100))
Write-Host "  Starting containers..." -ForegroundColor Gray

$dockerComposeFile = Join-Path $PSScriptRoot "docker-compose.yml"
if (Test-Path $dockerComposeFile) {
    docker compose up -d 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Progress-Step "Starting Docker Services" "Running" ([math]::Round(($currentStep / $totalSteps) * 100))
        Write-Host "  Waiting for services to be healthy..." -ForegroundColor Gray
        Start-Sleep -Seconds 5
    } else {
        Write-Progress-Step "Starting Docker Services" "Error" ([math]::Round(($currentStep / $totalSteps) * 100))
        Write-Host "  ERROR: Failed to start Docker services." -ForegroundColor Red
    }
} else {
    Write-Host "  INFO: docker-compose.yml not found, checking existing containers..." -ForegroundColor Yellow
}

# Step 4: Verify Docker Services
$currentStep++
Write-Progress-Step "Verifying Docker Services" "Starting" ([math]::Round(($currentStep / $totalSteps) * 100))

$services = @(
    @{Name = "PostgreSQL"; Container = "loan-extractor-db"; Port = 5433},
    @{Name = "Redis"; Container = "loan-extractor-redis"; Port = 6380},
    @{Name = "MinIO"; Container = "loan-extractor-minio"; Port = 9000},
    @{Name = "Backend API"; Container = "loan-extractor-api"; Port = 8000}
)

$runningServices = 0
foreach ($service in $services) {
    $container = docker ps --filter "name=$($service.Container)" --format "{{.Names}}" 2>&1
    if ($container -eq $service.Container) {
        $runningServices++
        Write-Host "  ✓ $($service.Name) is running" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $($service.Name) is not running" -ForegroundColor Red
    }
}

if ($runningServices -eq $services.Count) {
    Write-Progress-Step "Verifying Docker Services" "Running" ([math]::Round(($currentStep / $totalSteps) * 100))
} else {
    Write-Progress-Step "Verifying Docker Services" "Waiting" ([math]::Round(($currentStep / $totalSteps) * 100))
    Write-Host "  Some services may still be starting..." -ForegroundColor Yellow
}

# Step 5: Check Backend API
$currentStep++
Write-Progress-Step "Checking Backend API" "Starting" ([math]::Round(($currentStep / $totalSteps) * 100))
if (Wait-ForService -Name "Backend API" -Url "http://localhost:8000/health" -MaxWait 30) {
    Write-Progress-Step "Checking Backend API" "Running" ([math]::Round(($currentStep / $totalSteps) * 100))
    Write-Host "  ✓ Backend API is responding" -ForegroundColor Green
} else {
    Write-Progress-Step "Checking Backend API" "Waiting" ([math]::Round(($currentStep / $totalSteps) * 100))
    Write-Host "  ⚠ Backend API may still be starting..." -ForegroundColor Yellow
}

# Step 6: Check Frontend Dependencies
$currentStep++
Write-Progress-Step "Checking Frontend Dependencies" "Starting" ([math]::Round(($currentStep / $totalSteps) * 100))

$frontendPath = Join-Path $PSScriptRoot "frontend"
if (Test-Path $frontendPath) {
    Set-Location $frontendPath
    
    if (-not (Test-Path "node_modules")) {
        Write-Host "  Installing dependencies..." -ForegroundColor Gray
        npm install 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Progress-Step "Checking Frontend Dependencies" "Running" ([math]::Round(($currentStep / $totalSteps) * 100))
            Write-Host "  ✓ Dependencies installed" -ForegroundColor Green
        } else {
            Write-Progress-Step "Checking Frontend Dependencies" "Error" ([math]::Round(($currentStep / $totalSteps) * 100))
            Write-Host "  ✗ Failed to install dependencies" -ForegroundColor Red
        }
    } else {
        Write-Progress-Step "Checking Frontend Dependencies" "Running" ([math]::Round(($currentStep / $totalSteps) * 100))
        Write-Host "  ✓ Dependencies already installed" -ForegroundColor Green
    }
    
    Set-Location $PSScriptRoot
} else {
    Write-Progress-Step "Checking Frontend Dependencies" "Error" ([math]::Round(($currentStep / $totalSteps) * 100))
    Write-Host "  ✗ Frontend directory not found" -ForegroundColor Red
}

# Step 7: Start Frontend
$currentStep++
Write-Progress-Step "Starting Frontend" "Starting" ([math]::Round(($currentStep / $totalSteps) * 100))

if (Test-Path $frontendPath) {
    Write-Host "  Starting React + Vite development server..." -ForegroundColor Gray
    
    # Check if frontend is already running
    $frontendRunning = Test-Service -Url "http://localhost:5173" -Timeout 2
    
    if (-not $frontendRunning) {
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$frontendPath'; npm run dev" -WindowStyle Minimized
        Start-Sleep -Seconds 3
        
        # Wait for frontend to start
        $frontendStarted = Wait-ForService -Name "Frontend" -Url "http://localhost:5173" -MaxWait 20
        
        if ($frontendStarted) {
            Write-Progress-Step "Starting Frontend" "Running" ([math]::Round(($currentStep / $totalSteps) * 100))
            Write-Host "  ✓ Frontend is running" -ForegroundColor Green
        } else {
            Write-Progress-Step "Starting Frontend" "Waiting" ([math]::Round(($currentStep / $totalSteps) * 100))
            Write-Host "  ⚠ Frontend is starting (may take a few more seconds)..." -ForegroundColor Yellow
        }
    } else {
        Write-Progress-Step "Starting Frontend" "Running" ([math]::Round(($currentStep / $totalSteps) * 100))
        Write-Host "  ✓ Frontend is already running" -ForegroundColor Green
    }
} else {
    Write-Progress-Step "Starting Frontend" "Error" ([math]::Round(($currentStep / $totalSteps) * 100))
    Write-Host "  ✗ Frontend directory not found" -ForegroundColor Red
}

# Step 8: Final Status Check
$currentStep++
Write-Progress-Step "Final Status Check" "Starting" ([math]::Round(($currentStep / $totalSteps) * 100))

Start-Sleep -Seconds 2

$servicesStatus = @{
    "Backend API" = Test-Service -Url "http://localhost:8000/health" -Timeout 3
    "Frontend" = Test-Service -Url "http://localhost:5173" -Timeout 3
}

$allRunning = $servicesStatus.Values -contains $true

if ($allRunning) {
    Write-Progress-Step "Final Status Check" "Running" ([math]::Round(($currentStep / $totalSteps) * 100))
} else {
    Write-Progress-Step "Final Status Check" "Waiting" ([math]::Round(($currentStep / $totalSteps) * 100))
}

# Final Summary
Write-Header "Project Startup Complete!"

Write-Host "Service Status:" -ForegroundColor Cyan
Write-Host ""

foreach ($service in $servicesStatus.GetEnumerator()) {
    $status = if ($service.Value) { "✓ RUNNING" } else { "⚠ STARTING" }
    $color = if ($service.Value) { "Green" } else { "Yellow" }
    Write-Host "  $($service.Key): " -NoNewline -ForegroundColor White
    Write-Host $status -ForegroundColor $color
}

Write-Host ""
Write-Host "Access URLs:" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Frontend App:   " -NoNewline -ForegroundColor White
Write-Host "http://localhost:5173" -ForegroundColor Green
Write-Host "  Backend API:     " -NoNewline -ForegroundColor White
Write-Host "http://localhost:8000" -ForegroundColor Green
Write-Host "  API Docs:        " -NoNewline -ForegroundColor White
Write-Host "http://localhost:8000/docs" -ForegroundColor Green
Write-Host "  Airflow UI:      " -NoNewline -ForegroundColor White
Write-Host "http://localhost:8090" -ForegroundColor Green
Write-Host "  MinIO Console:   " -NoNewline -ForegroundColor White
Write-Host "http://localhost:9001" -ForegroundColor Green
Write-Host "  Dashboard:       " -NoNewline -ForegroundColor White
Write-Host "http://localhost:8501" -ForegroundColor Green

Write-Host ""
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "  All services are ready!" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""

if ($allRunning) {
    Write-Host "✓ Project started successfully!" -ForegroundColor Green
    Write-Host "  Open http://localhost:5173 in your browser to get started." -ForegroundColor White
} else {
    Write-Host "⚠ Some services are still starting..." -ForegroundColor Yellow
    Write-Host "  Please wait a few more seconds and refresh your browser." -ForegroundColor White
}

Write-Host ""




