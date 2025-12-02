# 🚀 Quick Start: Deploy to Google Cloud with Free Domain

## ⚡ 5-Minute Setup

### Step 1: Get Free Domain (2 minutes)

1. **Visit Freenom:** https://www.freenom.com
2. **Search domain:** e.g., "loanai" or "loandocs"
3. **Select free TLD:** .tk, .ml, .ga, or .cf
4. **Complete registration** (FREE, no credit card needed)
5. **Verify email** and activate

**Alternative:** Use GitHub Student Pack for free .me domain

---

### Step 2: Setup Google Cloud (1 minute)

```bash
# Install gcloud CLI (if not installed)
# Windows: Download from https://cloud.google.com/sdk/docs/install

# Login to Google Cloud
gcloud auth login

# Set project
gcloud config set project rich-atom-476217-j9
```

---

### Step 3: Deploy Application (2 minutes)

```bash
# Navigate to project root (DocAI EXTRACTOR)
cd path\to\DocAI-EXTRACTOR

# Run deployment script
# Windows PowerShell:
.\deploy\gcp\deploy.sh

# Or use Cloud Shell (browser-based, no installation needed)
# Visit: https://shell.cloud.google.com
```

---

### Step 4: Map Your Domain (1 minute)

```bash
# Replace 'yourdomain.tk' with your actual domain
DOMAIN="yourdomain.tk"

# Map frontend
gcloud run domain-mappings create \
  --service=loan-extractor-frontend \
  --domain=$DOMAIN \
  --region=us-central1

# Map API
gcloud run domain-mappings create \
  --service=loan-extractor-api \
  --domain=api.$DOMAIN \
  --region=us-central1

# Get DNS records to add
gcloud run domain-mappings describe $DOMAIN --region=us-central1
```

---

### Step 5: Configure DNS (1 minute)

1. **Login to Freenom** (or your domain provider)
2. **Go to:** My Domains > Manage Domain > Management Tools > Nameservers
3. **Add DNS records** from Step 4:
   - Type: CNAME
   - Name: @ (or leave blank for root)
   - Value: `ghs.googlehosted.com`
4. **Add API subdomain:**
   - Type: CNAME
   - Name: api
   - Value: `ghs.googlehosted.com`
5. **Save changes**

---

## ✅ Done!

**Wait 5-60 minutes** for DNS propagation, then:

- 🌐 **Frontend:** https://yourdomain.tk
- 🔌 **API:** https://api.yourdomain.tk
- 📊 **API Docs:** https://api.yourdomain.tk/docs

**SSL certificates are automatically provisioned!** 🔒

---

## 🎁 What You Get

✅ **Free Domain** (Freenom)  
✅ **Free SSL** (Cloud Run automatic)  
✅ **Free Hosting** (Cloud Run free tier)  
✅ **Auto-scaling** (handles traffic spikes)  
✅ **99.95% Uptime** (production SLA)  

---

## 💡 Pro Tips

1. **Use Cloudflare** for better performance (free CDN)
2. **Enable Cloud Monitoring** for insights (free tier)
3. **Set up alerts** for service health
4. **Use Cloud Build** for automatic deployments

---

## 🆘 Need Help?

- **Domain issues?** See [DOMAIN_SETUP.md](DOMAIN_SETUP.md)
- **Deployment issues?** See [README.md](README.md)
- **Google Cloud docs:** https://cloud.google.com/run/docs

---

**Total Cost: $0/month** (within free tier limits) 🎉









