#!/usr/bin/env bash
# ============================================================
#  Fill in ALL values below before running any deploy script.
#  Then source this file:  source deploy/env.sh
# ============================================================

#GCP project ID (e.g. fraud-detection-12345)
export PROJECT_ID="csci5253-493920"

# GCP region to deploy everything into
export REGION="us-east1"

# Artifact Registry repo name 
export AR_REPO="fraud-platform"

# GCS bucket name for the model artifact (must be globally unique)
export GCS_BUCKET="fraud-artifact-${PROJECT_ID}"

# Cloud SQL instance name
export SQL_INSTANCE="fraud-pg"

# Postgres credentials (choose your own password)
export DB_NAME="fraud"
export DB_USER="fraud"
export DB_PASS="Fraud2024!"

# CloudAMQP URL — paste from your CloudAMQP dashboard
# Looks like: amqps://user:pass@host.cloudamqp.com/vhost
export CLOUDAMQP_URL="amqps://bttbkvmi:99YSG5psKf2HLAju42iMaIR-iTijUkyu@porpoise.rmq.cloudamqp.com/bttbkvmi"

# Cloud Run service name
export CLOUD_RUN_SVC="fraud-api"

# Compute Engine VM name and machine type
export VM_NAME="fraud-worker"
export VM_MACHINE="e2-standard-2"
