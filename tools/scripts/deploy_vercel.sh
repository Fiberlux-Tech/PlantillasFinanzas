#!/bin/bash
# Vercel Deployment Script for CI/CD Pipeline
#
# This script deploys the application to Vercel and captures the deployment URL.
# It handles both staging and production deployments.
#
# Usage:
#   bash tools/scripts/deploy_vercel.sh <staging|production>
#
# Required Environment Variables:
#   - VERCEL_TOKEN: Vercel authentication token
#   - VERCEL_ORG_ID: Vercel organization/team ID
#   - VERCEL_PROJECT_ID: Vercel project ID
#
# GitHub Actions Output:
#   - deployment_url: The URL of the deployed application

set -euo pipefail  # Exit on error, undefined variables, and pipe failures

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1" >&2
}

# Check arguments
if [ $# -ne 1 ]; then
    log_error "Usage: $0 <staging|production>"
    exit 1
fi

ENVIRONMENT=$1

if [[ "$ENVIRONMENT" != "staging" && "$ENVIRONMENT" != "production" ]]; then
    log_error "Invalid environment: $ENVIRONMENT. Must be 'staging' or 'production'."
    exit 1
fi

# Validate required environment variables
if [ -z "${VERCEL_TOKEN:-}" ]; then
    log_error "VERCEL_TOKEN is not set. Add it to GitHub Secrets."
    exit 1
fi

if [ -z "${VERCEL_ORG_ID:-}" ]; then
    log_error "VERCEL_ORG_ID is not set. Add it to GitHub Secrets."
    exit 1
fi

if [ -z "${VERCEL_PROJECT_ID:-}" ]; then
    log_error "VERCEL_PROJECT_ID is not set. Add it to GitHub Secrets."
    exit 1
fi

echo "============================================================"
echo "Vercel Deployment - ${ENVIRONMENT^^}"
echo "============================================================"
echo ""

# Step 1: Install Vercel CLI
log_info "Step 1: Installing Vercel CLI..."
npm install --global vercel@latest
echo ""

# Step 2: Pull Vercel environment configuration
log_info "Step 2: Pulling Vercel environment configuration..."

if [ "$ENVIRONMENT" == "production" ]; then
    vercel pull --yes --environment=production --token="$VERCEL_TOKEN"
else
    vercel pull --yes --environment=preview --token="$VERCEL_TOKEN"
fi

echo ""

# Step 3: Build the project
log_info "Step 3: Building project..."

if [ "$ENVIRONMENT" == "production" ]; then
    vercel build --prod --token="$VERCEL_TOKEN"
else
    vercel build --token="$VERCEL_TOKEN"
fi

echo ""

# Step 4: Deploy to Vercel
log_info "Step 4: Deploying to Vercel..."

if [ "$ENVIRONMENT" == "production" ]; then
    DEPLOYMENT_OUTPUT=$(vercel deploy --prebuilt --prod --token="$VERCEL_TOKEN" 2>&1)
else
    DEPLOYMENT_OUTPUT=$(vercel deploy --prebuilt --token="$VERCEL_TOKEN" 2>&1)
fi

DEPLOYMENT_STATUS=$?

if [ $DEPLOYMENT_STATUS -ne 0 ]; then
    log_error "Deployment failed with exit code $DEPLOYMENT_STATUS"
    echo "$DEPLOYMENT_OUTPUT"
    exit 1
fi

echo "$DEPLOYMENT_OUTPUT"
echo ""

# Step 5: Extract deployment URL
log_info "Step 5: Extracting deployment URL..."

# Vercel CLI outputs the deployment URL on the last line
DEPLOYMENT_URL=$(echo "$DEPLOYMENT_OUTPUT" | tail -n 1 | grep -oE 'https://[^ ]+' | head -n 1)

if [ -z "$DEPLOYMENT_URL" ]; then
    log_error "Failed to extract deployment URL from Vercel output"
    exit 1
fi

log_info "Deployment URL: $DEPLOYMENT_URL"
echo ""

# Step 6: Set GitHub Actions output
if [ "${GITHUB_ACTIONS:-false}" == "true" ]; then
    log_info "Step 6: Setting GitHub Actions output..."
    echo "deployment_url=$DEPLOYMENT_URL" >> "$GITHUB_OUTPUT"
    echo ""
fi

echo "============================================================"
log_info "Vercel deployment completed successfully"
echo "============================================================"
echo ""
echo "Environment: $ENVIRONMENT"
echo "URL: $DEPLOYMENT_URL"
echo ""

exit 0
