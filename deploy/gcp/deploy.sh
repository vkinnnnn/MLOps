#!/bin/bash
# Google Cloud Platform Deployment Script
# This script deploys the Loan Document Extractor to GCP with free domain setup

set -e

PROJECT_ID="rich-atom-476217-j9"
REGION="us-central1"
ZONE="us-central1-a"

echo "🚀 Starting GCP Deployment for Loan Document Extractor"
echo "=================================================="

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found. Please install it first:"
    echo "   https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Set project
echo "📋 Setting GCP project..."
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "🔧 Enabling required GCP APIs..."
gcloud services enable \
    run.googleapis.com \
    sql-component.googleapis.com \
    sqladmin.googleapis.com \
    storage-component.googleapis.com \
    redis.googleapis.com \
    cloudbuild.googleapis.com \
    secretmanager.googleapis.com \
    compute.googleapis.com

# Create Cloud SQL PostgreSQL instance
echo "🗄️  Creating Cloud SQL PostgreSQL instance..."
gcloud sql instances create loan-extractor-db \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region=$REGION \
    --root-password=$(openssl rand -base64 32) \
    --storage-type=SSD \
    --storage-size=20GB \
    --backup-start-time=03:00 \
    --enable-bin-log \
    --maintenance-window-day=SUN \
    --maintenance-window-hour=04 \
    || echo "⚠️  Database instance may already exist"

# Create database
echo "📊 Creating database..."
gcloud sql databases create loanextractor \
    --instance=loan-extractor-db \
    || echo "⚠️  Database may already exist"

# Create Memorystore Redis instance
echo "🔴 Creating Memorystore Redis instance..."
gcloud redis instances create loan-extractor-redis \
    --size=1 \
    --region=$REGION \
    --redis-version=redis_7_0 \
    --tier=basic \
    || echo "⚠️  Redis instance may already exist"

# Create Cloud Storage bucket
echo "📦 Creating Cloud Storage bucket..."
gsutil mb -p $PROJECT_ID -c STANDARD -l $REGION gs://loan-documents-$PROJECT_ID \
    || echo "⚠️  Bucket may already exist"

# Create service account for Cloud Run
echo "👤 Creating service account..."
gcloud iam service-accounts create loan-extractor-sa \
    --display-name="Loan Extractor Service Account" \
    || echo "⚠️  Service account may already exist"

# Grant permissions
echo "🔐 Granting permissions..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:loan-extractor-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/cloudsql.client"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:loan-extractor-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/storage.objectAdmin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:loan-extractor-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/documentai.apiUser"

# Store secrets
echo "🔒 Storing secrets..."
if [ -f "secrets/service-account-key.json" ]; then
    gcloud secrets create service-account-key \
        --data-file=secrets/service-account-key.json \
        || gcloud secrets versions add service-account-key \
            --data-file=secrets/service-account-key.json
fi

# Get database connection name
DB_INSTANCE=$(gcloud sql instances describe loan-extractor-db --format="value(connectionName)")

# Get Redis IP
REDIS_IP=$(gcloud redis instances describe loan-extractor-redis --region=$REGION --format="value(host)")

# Build and deploy API
echo "🏗️  Building and deploying API..."
gcloud builds submit --config=deploy/gcp/cloudbuild.yaml

# Get Cloud Run URLs
API_URL=$(gcloud run services describe loan-extractor-api --region=$REGION --format="value(status.url)")
FRONTEND_URL=$(gcloud run services describe loan-extractor-frontend --region=$REGION --format="value(status.url)")

echo ""
echo "✅ Deployment Complete!"
echo "======================"
echo "API URL: $API_URL"
echo "Frontend URL: $FRONTEND_URL"
echo ""
echo "📝 Next Steps:"
echo "1. Map custom domain (see deploy/gcp/DOMAIN_SETUP.md)"
echo "2. Update frontend .env with API URL: $API_URL"
echo "3. Test the deployment"









