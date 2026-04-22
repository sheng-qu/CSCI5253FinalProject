#!/usr/bin/env bash

export PROJECT_ID="csci5253-493920"

export REGION="us-east1"

export AR_REPO="fraud-platform"

export GCS_BUCKET="fraud-artifact-${PROJECT_ID}"

export SQL_INSTANCE="fraud-pg"

export DB_NAME="fraud"
export DB_USER="fraud"
export DB_PASS="Fraud2024!"

export CLOUDAMQP_URL="amqps://bttbkvmi:99YSG5psKf2HLAju42iMaIR-iTijUkyu@porpoise.rmq.cloudamqp.com/bttbkvmi"

export CLOUD_RUN_SVC="fraud-api"

export VM_NAME="fraud-worker"
export VM_MACHINE="e2-standard-2"
