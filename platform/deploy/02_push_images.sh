#!/usr/bin/env bash
# Step 2 — Build Docker images using Cloud Build and push to Artifact Registry.
# Run from the fraud-platform/ directory:  bash deploy/02_push_images.sh
set -euo pipefail
source "$(dirname "$0")/env.sh"

AR_HOST="${REGION}-docker.pkg.dev"
IMAGE_PREFIX="${AR_HOST}/${PROJECT_ID}/${AR_REPO}"

echo "── Creating Artifact Registry repository ──"
gcloud artifacts repositories create "$AR_REPO" \
  --repository-format=docker \
  --location="$REGION" \
  --project="$PROJECT_ID" \
  --quiet 2>/dev/null || echo "Repository already exists, continuing."

echo ""
echo "── Building and pushing API image via Cloud Build ──"
gcloud builds submit . \
  --project="$PROJECT_ID" \
  --tag="${IMAGE_PREFIX}/api:latest" \
  --dockerfile=Dockerfile.api

echo ""
echo "── Building and pushing Worker image via Cloud Build ──"
gcloud builds submit . \
  --project="$PROJECT_ID" \
  --tag="${IMAGE_PREFIX}/worker:latest" \
  --dockerfile=Dockerfile.worker

echo ""
echo "Images pushed:"
echo "  API    → ${IMAGE_PREFIX}/api:latest"
echo "  Worker → ${IMAGE_PREFIX}/worker:latest"
