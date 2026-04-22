#!/usr/bin/env bash
# Step 5 — Deploy the API to Cloud Run.
# Fill in DATABASE_URL below with the value from step 04.
set -euo pipefail
source "$(dirname "$0")/env.sh"

AR_HOST="${REGION}-docker.pkg.dev"
IMAGE="${AR_HOST}/${PROJECT_ID}/${AR_REPO}/api:latest"

# Paste the DATABASE_URL printed by step 04
DATABASE_URL="postgresql://${DB_USER}:${DB_PASS}@YOUR_CLOUDSQL_IP:5432/${DB_NAME}"

echo "── Deploying API to Cloud Run ──"
gcloud run deploy "$CLOUD_RUN_SVC" \
  --image="$IMAGE" \
  --region="$REGION" \
  --project="$PROJECT_ID" \
  --platform=managed \
  --allow-unauthenticated \
  --port=8000 \
  --cpu=1 \
  --memory=1Gi \
  --min-instances=1 \
  --max-instances=3 \
  --set-env-vars="RABBITMQ_URL=${CLOUDAMQP_URL}" \
  --set-env-vars="DATABASE_URL=${DATABASE_URL}" \
  --set-env-vars="ARTIFACT_PATH=/app/artifacts/fraud_artifact.joblib" \
  --set-env-vars="QUEUE_NAME=fraud_scoring" \
  --set-env-vars="GCS_ARTIFACT=gs://${GCS_BUCKET}/fraud_artifact.joblib"

echo ""
echo "── Getting service URL ──"
SERVICE_URL=$(gcloud run services describe "$CLOUD_RUN_SVC" \
  --region="$REGION" \
  --project="$PROJECT_ID" \
  --format="value(status.url)")

echo ""
echo "API deployed at: ${SERVICE_URL}"
echo "Swagger UI:      ${SERVICE_URL}/docs"
echo ""
echo "Test it:"
echo "  curl -X POST ${SERVICE_URL}/score/sync \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"TransactionID\":1,\"TransactionDT\":86400,\"TransactionAmt\":50,\"ProductCD\":\"W\"}'"
