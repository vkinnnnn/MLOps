# Free Domain Setup Guide for Google Cloud Deployment

## 🆓 Free Domain Options

### Option 1: Freenom (Free .tk, .ml, .ga, .cf domains)
**Best for:** Testing and development

1. **Get Free Domain:**
   - Visit: https://www.freenom.com
   - Search for available domain (e.g., `loanai.tk`)
   - Add to cart and complete registration (FREE)
   - Verify email and activate domain

2. **Configure DNS:**
   - Go to Freenom DNS Management
   - Add A record pointing to Cloud Run IP (we'll get this)
   - Add CNAME for www subdomain

### Option 2: GitHub Student Pack (Free .me domain)
**Best for:** Students

1. **Get GitHub Student Pack:**
   - Visit: https://education.github.com/pack
   - Verify student status
   - Get free Namecheap domain (.me)

2. **Use Namecheap DNS:**
   - Point to Cloud Run

### Option 3: Cloudflare (Free domain + DNS)
**Best for:** Production (best performance)

1. **Transfer domain to Cloudflare:**
   - Sign up at https://cloudflare.com
   - Add your domain
   - Use Cloudflare's free DNS

2. **Benefits:**
   - Free SSL/TLS
   - CDN included
   - DDoS protection
   - Fast DNS

### Option 4: Google Domains (Paid but reliable)
**Best for:** Production

- Visit: https://domains.google
- Search and purchase domain ($12/year)
- Integrated with Google Cloud

---

## 🔧 Mapping Domain to Cloud Run

### Step 1: Get Cloud Run Service URL

```bash
# Get API URL
API_URL=$(gcloud run services describe loan-extractor-api \
  --region=us-central1 \
  --format="value(status.url)")

# Get Frontend URL  
FRONTEND_URL=$(gcloud run services describe loan-extractor-frontend \
  --region=us-central1 \
  --format="value(status.url)")

echo "API: $API_URL"
echo "Frontend: $FRONTEND_URL"
```

### Step 2: Map Custom Domain to Cloud Run

```bash
# Map domain to API service
gcloud run domain-mappings create \
  --service=loan-extractor-api \
  --domain=api.yourdomain.com \
  --region=us-central1

# Map domain to Frontend service
gcloud run domain-mappings create \
  --service=loan-extractor-frontend \
  --domain=yourdomain.com \
  --region=us-central1
```

### Step 3: Get DNS Records

```bash
# Get DNS records for API
gcloud run domain-mappings describe api.yourdomain.com \
  --region=us-central1 \
  --format="value(status.resourceRecords)"

# Get DNS records for Frontend
gcloud run domain-mappings describe yourdomain.com \
  --region=us-central1 \
  --format="value(status.resourceRecords)"
```

### Step 4: Configure DNS at Your Domain Provider

Add the DNS records from Step 3 to your domain provider:

**Example DNS Records:**
```
Type: CNAME
Name: api
Value: ghs.googlehosted.com

Type: CNAME  
Name: @ (or root)
Value: ghs.googlehosted.com
```

### Step 5: Wait for DNS Propagation

- DNS changes take 5-60 minutes
- Check status: `gcloud run domain-mappings describe yourdomain.com --region=us-central1`
- Status should show "ACTIVE" when ready

---

## 🔒 Free SSL Certificate

Cloud Run **automatically provides free SSL certificates** for custom domains!

- No additional setup needed
- Auto-renewal
- HTTPS enabled automatically

---

## 📋 Complete Example: Freenom Setup

### 1. Get Free Domain
```
1. Go to https://www.freenom.com
2. Search: "loanai"
3. Select .tk domain (FREE)
4. Complete registration
```

### 2. Configure Freenom DNS
```
1. Login to Freenom
2. Go to "My Domains" > "Manage Domain"
3. Go to "Management Tools" > "Nameservers"
4. Use Cloud Run's nameservers (from Step 3 above)
```

### 3. Map to Cloud Run
```bash
# Map root domain
gcloud run domain-mappings create \
  --service=loan-extractor-frontend \
  --domain=loanai.tk \
  --region=us-central1

# Map API subdomain
gcloud run domain-mappings create \
  --service=loan-extractor-api \
  --domain=api.loanai.tk \
  --region=us-central1
```

### 4. Update Frontend Environment
```bash
# Update frontend .env
VITE_API_URL=https://api.loanai.tk
```

---

## 🎯 Quick Start Script

Run this after getting your domain:

```bash
# Set your domain
DOMAIN="yourdomain.com"
API_SUBDOMAIN="api.yourdomain.com"

# Map domains
gcloud run domain-mappings create \
  --service=loan-extractor-frontend \
  --domain=$DOMAIN \
  --region=us-central1

gcloud run domain-mappings create \
  --service=loan-extractor-api \
  --domain=$API_SUBDOMAIN \
  --region=us-central1

# Get DNS records
echo "Add these DNS records to your domain provider:"
gcloud run domain-mappings describe $DOMAIN --region=us-central1
```

---

## ✅ Verification

After DNS propagation:

```bash
# Check domain status
gcloud run domain-mappings list --region=us-central1

# Test API
curl https://api.yourdomain.com/health

# Test Frontend
curl https://yourdomain.com
```

---

## 💰 Cost Breakdown

**Free Tier (Always Free):**
- Cloud Run: 2 million requests/month
- Cloud SQL: db-f1-micro (limited hours)
- Cloud Storage: 5GB
- Cloud Build: 120 build-minutes/day

**Estimated Monthly Cost (if exceeding free tier):**
- Cloud Run: ~$5-20
- Cloud SQL: ~$10-30
- Memorystore: ~$30
- **Total: ~$45-80/month**

**With Free Domain:**
- Domain: $0 (Freenom)
- SSL: $0 (Cloud Run provides)
- **Total: Same as above**

---

## 🚀 Production Recommendations

For production, consider:
1. **Cloudflare** - Free CDN + DNS
2. **Custom Domain** - Professional appearance
3. **Monitoring** - Cloud Monitoring (free tier)
4. **Backup** - Cloud SQL automated backups

---

**Need Help?** Check Google Cloud documentation:
- https://cloud.google.com/run/docs/mapping-custom-domains
- https://cloud.google.com/sql/docs/postgres









