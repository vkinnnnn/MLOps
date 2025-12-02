# Google Cloud Deployment Script for Windows PowerShell
# Deploys Loan Document Extractor to GCP with free domain setup

$PROJECT_ID = "rich-atom-476217-j9"
$REGION = "us-central1"
$SERVICE_ACCOUNT_KEY = Join-Path $PSScriptRoot "..\..\secrets\rich-atom-476217-j9-1a57070a97fd.json"

Write-Host "Starting GCP Deployment for Loan Document Extractor" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host ""

# Check if gcloud is installed
try {
    $null = gcloud --version 2>&1
    Write-Host "SUCCESS: gcloud CLI found" -ForegroundColor Green
} catch {
    Write-Host "ERROR: gcloud CLI not found. Please install it first:" -ForegroundColor Red
    Write-Host "   https://cloud.google.com/sdk/docs/install" -ForegroundColor Yellow
    exit 1
}

# Authenticate with service account if key file exists
if (Test-Path $SERVICE_ACCOUNT_KEY) {
    Write-Host "INFO: Authenticating with service account..." -ForegroundColor Cyan
    $authResult = gcloud auth activate-service-account --key-file=$SERVICE_ACCOUNT_KEY 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "SUCCESS: Service account authenticated" -ForegroundColor Green
    } else {
        Write-Host "WARNING: Service account authentication failed, using default credentials" -ForegroundColor Yellow
        Write-Host "   $authResult" -ForegroundColor Gray
    }
} else {
    Write-Host "INFO: Service account key not found, using default gcloud credentials" -ForegroundColor Yellow
    Write-Host "   Expected location: $SERVICE_ACCOUNT_KEY" -ForegroundColor Gray
}

# Set project
Write-Host "INFO: Setting GCP project..." -ForegroundColor Cyan
$projectResult = gcloud config set project $PROJECT_ID 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to set GCP project" -ForegroundColor Red
    Write-Host $projectResult -ForegroundColor Red
    exit 1
}

# Enable required APIs
Write-Host "CONFIG: Enabling required GCP APIs..." -ForegroundColor Cyan
$apis = @(
    "run.googleapis.com",
    "sql-component.googleapis.com",
    "sqladmin.googleapis.com",
    "storage-component.googleapis.com",
    "redis.googleapis.com",
    "cloudbuild.googleapis.com",
    "secretmanager.googleapis.com",
    "compute.googleapis.com"
)

$apiErrors = @()
foreach ($api in $apis) {
    Write-Host "   Enabling $api..." -ForegroundColor Gray
    $apiResult = gcloud services enable $api 2>&1
    if ($LASTEXITCODE -ne 0) {
        $apiErrors += "$api : $apiResult"
    }
}

if ($apiErrors.Count -eq 0) {
    Write-Host "SUCCESS: APIs enabled" -ForegroundColor Green
} else {
    Write-Host "WARNING: Some APIs failed to enable:" -ForegroundColor Yellow
    foreach ($apiError in $apiErrors) {
        Write-Host "   $apiError" -ForegroundColor Yellow
    }
}
Write-Host ""

# Create Cloud SQL instance
Write-Host "DATABASE: Creating Cloud SQL PostgreSQL instance..." -ForegroundColor Cyan
$null = gcloud sql instances describe loan-extractor-db --format="value(name)" 2>&1
$dbExists = $LASTEXITCODE -eq 0

if (-not $dbExists) {
    Write-Host "   Creating new database instance..." -ForegroundColor Gray
    # Generate secure password (alphanumeric, 16 characters)
    $password = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 16 | ForEach-Object {[char]$_})
    
    $createResult = gcloud sql instances create loan-extractor-db `
        --database-version=POSTGRES_15 `
        --tier=db-f1-micro `
        --region=$REGION `
        --root-password=$password `
        --storage-type=SSD `
        --storage-size=20GB 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "SUCCESS: Database instance created" -ForegroundColor Green
        Write-Host "   Root password has been set (save this securely)" -ForegroundColor Gray
    } else {
        Write-Host "ERROR: Failed to create database instance" -ForegroundColor Red
        Write-Host $createResult -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "WARNING: Database instance already exists" -ForegroundColor Yellow
}

# Create database
Write-Host "DATA: Creating database..." -ForegroundColor Cyan
$dbCreateResult = gcloud sql databases create loanextractor --instance=loan-extractor-db 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "SUCCESS: Database created" -ForegroundColor Green
} else {
    # Check if error is because database already exists
    if ($dbCreateResult -match "already exists") {
        Write-Host "WARNING: Database already exists" -ForegroundColor Yellow
    } else {
        Write-Host "ERROR: Failed to create database" -ForegroundColor Red
        Write-Host $dbCreateResult -ForegroundColor Red
        exit 1
    }
}

# Create Redis instance
Write-Host "REDIS: Creating Memorystore Redis instance..." -ForegroundColor Cyan
$null = gcloud redis instances describe loan-extractor-redis --region=$REGION --format="value(name)" 2>&1
$redisExists = $LASTEXITCODE -eq 0

if (-not $redisExists) {
    Write-Host "   Creating Redis instance (this may take 10-15 minutes)..." -ForegroundColor Gray
    $redisCreateResult = gcloud redis instances create loan-extractor-redis `
        --size=1 `
        --region=$REGION `
        --redis-version=redis_7_0 `
        --tier=basic 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "SUCCESS: Redis instance created" -ForegroundColor Green
    } else {
        Write-Host "ERROR: Failed to create Redis instance" -ForegroundColor Red
        Write-Host $redisCreateResult -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "WARNING: Redis instance already exists" -ForegroundColor Yellow
}

# Create Storage bucket
Write-Host "STORAGE: Creating Cloud Storage bucket..." -ForegroundColor Cyan
$bucketName = "loan-documents-$PROJECT_ID"
$bucketResult = gsutil mb -p $PROJECT_ID -c STANDARD -l $REGION "gs://$bucketName" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "SUCCESS: Storage bucket created" -ForegroundColor Green
} else {
    # Check if error is because bucket already exists
    if ($bucketResult -match "already exists" -or $bucketResult -match "409") {
        Write-Host "WARNING: Bucket already exists" -ForegroundColor Yellow
    } else {
        Write-Host "ERROR: Failed to create storage bucket" -ForegroundColor Red
        Write-Host $bucketResult -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "SUCCESS: Infrastructure setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "NOTE: Next Steps:" -ForegroundColor Cyan
Write-Host "   1. Build and deploy services:" -ForegroundColor White
Write-Host "      gcloud builds submit --config=deploy/gcp/cloudbuild.yaml" -ForegroundColor Gray
Write-Host ""
Write-Host "   2. Get a free domain from Freenom:" -ForegroundColor White
Write-Host "      https://www.freenom.com" -ForegroundColor Gray
Write-Host ""
Write-Host "   3. Map domain to Cloud Run (see deploy/gcp/DOMAIN_SETUP.md)" -ForegroundColor White
Write-Host ""
Write-Host "   4. Update frontend environment variables" -ForegroundColor White
Write-Host ""



