#!/usr/bin/env bash
# Step 6 — Create a Compute Engine VM and start the worker container.

set -euo pipefail
source "$(dirname "$0")/env.sh"

AR_HOST="${REGION}-docker.pkg.dev"
WORKER_IMAGE="${AR_HOST}/${PROJECT_ID}/${AR_REPO}/worker:latest"

# Paste the DATABASE_URL printed by step 04
DATABASE_URL="postgresql://${DB_USER}:${DB_PASS}@YOUR_CLOUDSQL_IP:5432/${DB_NAME}"

echo "── Creating Compute Engine VM ──"
gcloud compute instances create "$VM_NAME" \
  --project="$PROJECT_ID" \
  --zone="${REGION}-a" \
  --machine-type="$VM_MACHINE" \
  --image-family=debian-12 \
  --image-project=debian-cloud \
  --boot-disk-size=20GB \
  --scopes=cloud-platform \
  --tags=fraud-worker \
  --metadata=startup-script="$(cat <<'STARTUP'
#!/bin/bash
set -e

# Install Docker
apt-get update -qq
apt-get install -y -qq docker.io
systemctl enable docker
systemctl start docker

# Authenticate with Artifact Registry
apt-get install -y -qq google-cloud-sdk
gcloud auth configure-docker REGION-docker.pkg.dev --quiet
STARTUP
)"

echo ""
echo "── VM created. SSHing in to start the worker container ──"
echo "Waiting 30s for VM to finish booting..."
sleep 30

gcloud compute ssh "$VM_NAME" \
  --project="$PROJECT_ID" \
  --zone="${REGION}-a" \
  --command="
    set -e

    # Authenticate Docker with Artifact Registry
    gcloud auth configure-docker ${REGION}-docker.pkg.dev --quiet

    # Pull the worker image
    docker pull ${WORKER_IMAGE}

    # Download the artifact from GCS
    mkdir -p /app/artifacts
    gsutil cp gs://${GCS_BUCKET}/fraud_artifact.joblib /app/artifacts/fraud_artifact.joblib

    # Run the worker
    docker run -d \
      --name fraud-worker \
      --restart=unless-stopped \
      -e RABBITMQ_URL='${CLOUDAMQP_URL}' \
      -e DATABASE_URL='${DATABASE_URL}' \
      -e ARTIFACT_PATH='/app/artifacts/fraud_artifact.joblib' \
      -e QUEUE_NAME='fraud_scoring' \
      -e WORKER_PREFETCH='10' \
      -v /app/artifacts:/app/artifacts:ro \
      ${WORKER_IMAGE}

    echo 'Worker container started.'
    docker ps
  "

echo ""
echo "Worker VM is running. To check logs:"
echo "  gcloud compute ssh ${VM_NAME} --zone=${REGION}-a --command='docker logs fraud-worker --tail=50'"
