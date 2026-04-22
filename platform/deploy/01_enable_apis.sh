#!/usr/bin/env bash
# Step 1 — Enable required GCP APIs.
# Run once per project.
set -euo pipefail
source "$(dirname "$0")/env.sh"

echo "Enabling GCP APIs for project: $PROJECT_ID"

gcloud services enable \
  run.googleapis.com \
  compute.googleapis.com \
  sqladmin.googleapis.com \
  artifactregistry.googleapis.com \
  storage.googleapis.com \
  cloudresourcemanager.googleapis.com \
  --project="$PROJECT_ID"

echo "Done — all APIs enabled."
