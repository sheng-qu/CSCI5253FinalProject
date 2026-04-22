#!/usr/bin/env bash
# Step 7 — Seed Postgres and smoke-test the live API.

set -euo pipefail
source "$(dirname "$0")/env.sh"

# Paste the Cloud Run URL from step 05 output
API_URL="https://YOUR_CLOUD_RUN_URL"

echo "── Running bootstrap (seed entity_stats + velocity_events) ──"
gcloud compute ssh "$VM_NAME" \
  --project="$PROJECT_ID" \
  --zone="${REGION}-a" \
  --command="
    docker exec fraud-worker python -m db.bootstrap
  "

echo ""
echo "── Smoke test — synchronous score ──"
curl -s -X POST "${API_URL}/score/sync" \
  -H "Content-Type: application/json" \
  -d '{
    "TransactionID": 5000001,
    "TransactionDT": 86400,
    "TransactionAmt": 68.5,
    "ProductCD": "W",
    "card1": 9500,
    "card4": "visa",
    "card6": "debit",
    "addr1": 315,
    "P_emaildomain": "gmail.com",
    "D1": 14
  }' | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('fraud_proba:', d.get('fraud_proba'))
print('top_signals:')
for s in d.get('top_signals', []):
    print(f\"  {s['feature']:30s}  shap={s['shap_contribution']:+.4f}\")
"

echo ""
echo "── Smoke test — async score ──"
curl -s -X POST "${API_URL}/score" \
  -H "Content-Type: application/json" \
  -d '{
    "TransactionID": 5000002,
    "TransactionDT": 86460,
    "TransactionAmt": 500.0,
    "ProductCD": "H",
    "card1": 9500,
    "P_emaildomain": "gmail.com"
  }'

echo ""
echo ""
echo "Check results after a few seconds:"
echo "  curl ${API_URL}/results/5000002"
echo ""
echo "Swagger UI: ${API_URL}/docs"
