# Secrets Directory

This directory contains sensitive credentials and API keys for the Student Loan Document Extractor Platform.

## Files

### Required Files
- `service-account-key.json` - Google Cloud Service Account credentials for Document AI
- `.env` - Environment variables with API keys and configuration

### Templates
- `service-account-key.json.template` - Template for Google Cloud credentials
- `.env.example` - Template for environment variables (stored at project root)

## Setup Instructions

### 1. Google Cloud Service Account Key
1. Copy `service-account-key.json.template` to `service-account-key.json`
2. Replace placeholder values with your actual Google Cloud credentials
3. Ensure the service account has Document AI API access

### 2. Environment Variables
1. Copy `.env.example` from project root to `.env` in this directory (or project root)
2. Fill in all required API keys and configuration values

## Security Notes

 **NEVER commit actual credential files to version control**
- All files except templates and this README are gitignored
- Keep credentials secure and rotate regularly
- Use environment-specific credentials (dev, staging, prod)

## File Locations

The platform checks for credentials in the following order:
1. `./secrets/` directory
2. Project root directory
3. Environment variables

Choose the location that best fits your deployment strategy.
