#!/usr/bin/env bash
# Step 4 — Create Cloud SQL (Postgres) instance, database, and user.

set -euo pipefail
source "$(dirname "$0")/env.sh"

echo "── Creating Cloud SQL instance (this takes ~5-10 min) ──"
gcloud sql instances create "$SQL_INSTANCE" \
  --database-version=POSTGRES_16 \
  --tier=db-f1-micro \
  --region="$REGION" \
  --project="$PROJECT_ID" \
  --storage-auto-increase \
  --backup-start-time=03:00 \
  --authorized-networks=0.0.0.0/0

echo ""
echo "── Creating database ──"
gcloud sql databases create "$DB_NAME" \
  --instance="$SQL_INSTANCE" \
  --project="$PROJECT_ID"

echo ""
echo "── Creating user ──"
gcloud sql users create "$DB_USER" \
  --instance="$SQL_INSTANCE" \
  --password="$DB_PASS" \
  --project="$PROJECT_ID"

echo ""
echo "── Fetching public IP ──"
SQL_IP=$(gcloud sql instances describe "$SQL_INSTANCE" \
  --project="$PROJECT_ID" \
  --format="value(ipAddresses[0].ipAddress)")
echo "Cloud SQL public IP: $SQL_IP"

export DATABASE_URL="postgresql://${DB_USER}:${DB_PASS}@${SQL_IP}:5432/${DB_NAME}"
echo ""
echo "DATABASE_URL=${DATABASE_URL}"
echo ""
echo "Save the DATABASE_URL above — you will need it in steps 05 and 06."
echo ""
echo "── Applying schema ──"
echo "Run this manually once you have psql or the Cloud SQL Auth Proxy:"
echo ""
echo "  psql \"${DATABASE_URL}\" -f platform/db/schema.sql"
echo ""
echo "Or use the Cloud SQL Studio in the GCP Console:"
echo "  https://console.cloud.google.com/sql/instances/${SQL_INSTANCE}/studio?project=${PROJECT_ID}"
