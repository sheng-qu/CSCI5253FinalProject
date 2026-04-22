#!/usr/bin/env bash
# Step 3 — Upload fraud_artifact.joblib to Cloud Storage.
# Run from the FinalProject/ root directory:
#   bash platform/deploy/03_upload_artifact.sh
set -euo pipefail
source "$(dirname "$0")/env.sh"

ARTIFACT_LOCAL="model_output/fraud_artifact.joblib"

if [ ! -f "$ARTIFACT_LOCAL" ]; then
  echo "ERROR: $ARTIFACT_LOCAL not found."
  echo "Run this script from the FinalProject/ root directory."
  exit 1
fi

echo "── Creating GCS bucket ──"
gcloud storage buckets create "gs://${GCS_BUCKET}" \
  --project="$PROJECT_ID" \
  --location="$REGION" \
  --uniform-bucket-level-access \
  2>/dev/null || echo "Bucket already exists, continuing."

echo ""
echo "── Uploading artifact ──"
gcloud storage cp "$ARTIFACT_LOCAL" "gs://${GCS_BUCKET}/fraud_artifact.joblib"

echo ""
echo "Artifact uploaded to: gs://${GCS_BUCKET}/fraud_artifact.joblib"
