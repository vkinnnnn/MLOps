# Google Cloud Platform Deployment Guide

Complete guide to deploy the Loan Document Extractor Platform to Google Cloud with **free domain setup**.

## 🎯 What You'll Get

- ✅ **Free Domain** (using Freenom or other free providers)
- ✅ **Free SSL Certificate** (automatic with Cloud Run)
- ✅ **Scalable Infrastructure** (auto-scaling)
- ✅ **Production-Ready** (99.95% uptime SLA)

## 📋 Prerequisites

1. **Google Cloud Account**
   - Sign up: https://cloud.google.com/free
   - $300 free credits for 90 days
   - Always-free tier available

2. **gcloud CLI**
   ```bash
   # Install gcloud CLI
   # Windows: https://cloud.google.com/sdk/docs/install
   # Or use Cloud Shell (browser-based)
   ```

3. **Domain** (Free options available - see DOMAIN_SETUP.md)

## 🚀 Quick Deployment

### Step 1: Clone and Setup

```bash
# Navigate to your local project root (DocAI EXTRACTOR)
cd path\to\DocAI-EXTRACTOR
```

### Step 2: Configure Project

```bash
# Set your GCP project
export PROJECT_ID="rich-atom-476217-j9"
gcloud config set project $PROJECT_ID
```

### Step 3: Run Deployment Script

```bash
# Make script executable (Linux/Mac)
chmod +x deploy/gcp/deploy.sh

# Run deployment
./deploy/gcp/deploy.sh
```

**Or manually on Windows:**
```powershell
# Run each command from deploy.sh manually
```

### Step 4: Setup Free Domain

See [DOMAIN_SETUP.md](DOMAIN_SETUP.md) for detailed instructions.

**Quick version:**
1. Get free domain from Freenom (https://www.freenom.com)
2. Map domain to Cloud Run (see DOMAIN_SETUP.md)
3. Update frontend environment variables

## 🏗️ Architecture

```
┌─────────────────┐
│   Cloud Run     │  Frontend (React/Vite)
│   (Frontend)    │  https://yourdomain.com
└─────────────────┘
         │
         ▼
┌─────────────────┐
│   Cloud Run     │  API (FastAPI)
│   (API)         │  https://api.yourdomain.com
└─────────────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌─────────┐ ┌──────────┐
│Cloud SQL│ │Memorystore│
│PostgreSQL│ │  Redis   │
└─────────┘ └──────────┘
    │
    ▼
┌──────────────┐
│Cloud Storage │  Document storage
│  (GCS)       │  (replaces MinIO)
└──────────────┘
```

## 📦 Services Used

| Service | Purpose | Free Tier |
|---------|---------|-----------|
| **Cloud Run** | API & Frontend hosting | 2M requests/month |
| **Cloud SQL** | PostgreSQL database | db-f1-micro (limited) |
| **Memorystore** | Redis cache | None (pay-as-you-go) |
| **Cloud Storage** | Document storage | 5GB free |
| **Cloud Build** | CI/CD | 120 build-minutes/day |
| **Secret Manager** | API keys & secrets | Free |

## 🔧 Manual Deployment Steps

### 1. Enable APIs

```bash
gcloud services enable \
  run.googleapis.com \
  sql-component.googleapis.com \
  storage-component.googleapis.com \
  redis.googleapis.com \
  cloudbuild.googleapis.com
```

### 2. Create Cloud SQL Instance

```bash
gcloud sql instances create loan-extractor-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1
```

### 3. Create Database

```bash
gcloud sql databases create loanextractor \
  --instance=loan-extractor-db
```

### 4. Create Redis Instance

```bash
gcloud redis instances create loan-extractor-redis \
  --size=1 \
  --region=us-central1 \
  --tier=basic
```

### 5. Create Storage Bucket

```bash
gsutil mb -p $PROJECT_ID -c STANDARD -l us-central1 \
  gs://loan-documents-$PROJECT_ID
```

### 6. Build and Deploy API

```bash
# Build image
gcloud builds submit --tag gcr.io/$PROJECT_ID/loan-extractor-api

# Deploy to Cloud Run
gcloud run deploy loan-extractor-api \
  --image gcr.io/$PROJECT_ID/loan-extractor-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2
```

### 7. Build and Deploy Frontend

```bash
# Build frontend
cd frontend
npm run build

# Build Docker image
docker build -f ../deploy/gcp/Dockerfile.frontend -t gcr.io/$PROJECT_ID/loan-extractor-frontend .

# Push to GCR
docker push gcr.io/$PROJECT_ID/loan-extractor-frontend

# Deploy to Cloud Run
gcloud run deploy loan-extractor-frontend \
  --image gcr.io/$PROJECT_ID/loan-extractor-frontend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 512Mi \
  --port 3000
```

## 🌐 Domain Setup

See [DOMAIN_SETUP.md](DOMAIN_SETUP.md) for complete domain configuration.

**Quick Steps:**
1. Get free domain (Freenom, GitHub Student Pack, etc.)
2. Map domain to Cloud Run services
3. Configure DNS records
4. Wait for SSL certificate (automatic)

## 🔐 Environment Variables

Set these in Cloud Run:

```bash
# API Service
DATABASE_URL=postgresql://user:pass@/db?host=/cloudsql/PROJECT_ID:REGION:INSTANCE
REDIS_URL=redis://REDIS_IP:6379
GOOGLE_APPLICATION_CREDENTIALS=/app/service-account-key.json
S3_ENDPOINT=https://storage.googleapis.com
S3_BUCKET_NAME=loan-documents-PROJECT_ID

# Frontend Service
VITE_API_URL=https://api.yourdomain.com
```

## 📊 Monitoring

```bash
# View logs
gcloud logging read "resource.type=cloud_run_revision" --limit 50

# View metrics
gcloud monitoring dashboards list
```

## 💰 Cost Estimation

**Free Tier (Always Free):**
- Cloud Run: 2M requests/month
- Cloud SQL: db-f1-micro (limited)
- Cloud Storage: 5GB
- **Total: $0/month** (within free tier)

**Production (if exceeding free tier):**
- Cloud Run: ~$5-20/month
- Cloud SQL: ~$10-30/month
- Memorystore: ~$30/month
- **Total: ~$45-80/month**

## 🔄 CI/CD Setup

The `cloudbuild.yaml` file enables automatic deployments:

```bash
# Connect GitHub repository
gcloud builds triggers create github \
  --repo-name=DocAI-EXTRACTOR \
  --repo-owner=YOUR_GITHUB_USERNAME \
  --branch-pattern="^main$" \
  --build-config=deploy/gcp/cloudbuild.yaml
```

## 🆘 Troubleshooting

### Issue: Build fails
```bash
# Check build logs
gcloud builds list --limit=5
gcloud builds log BUILD_ID
```

### Issue: Service won't start
```bash
# Check service logs
gcloud run services logs read loan-extractor-api --region=us-central1
```

### Issue: Database connection fails
```bash
# Verify Cloud SQL connection
gcloud sql instances describe loan-extractor-db
```

## 📚 Additional Resources

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Cloud SQL Documentation](https://cloud.google.com/sql/docs)
- [Domain Mapping Guide](https://cloud.google.com/run/docs/mapping-custom-domains)
- [Free Tier Guide](https://cloud.google.com/free)

---

**Ready to deploy?** Start with `./deploy/gcp/deploy.sh` or follow the manual steps above!









