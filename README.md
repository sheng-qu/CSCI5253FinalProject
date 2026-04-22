# Graph-Based Fraud Detection Platform
**Team: Sheng Qu**

End-to-end fraud detection system: ingests transactions via API, scores them using XGBoost + graph features, and stores results in Postgres. Uses RabbitMQ for queuing and a worker VM for async processing.

---

## Repository Structure

```
FinalProject/
├── code/                 # ML Model training & testing notebooks 
├── model_output/         # Trained artifacts
├── platform/
│   ├── api/
│   │   ├── main.py          # Endpoints
│   │   ├── queue_client.py   # Publishes transaction to RabbitMQ
│   │   └── db.py            # Postgres read/write helpers
│   ├── worker/
│   │   ├── worker.py       # Consumes RabbitMQ queue, writes results to Postgres
│   │   └── scorer.py       # Feature pipeline + XGBoost + SHAP inference
│   ├── db/
│   │   └── schema.sql    # Tables: predictions, entity_stats, velocity_events
│   ├── deploy/
│   │   ├── env.sh          # all GCP config variables
│   │   ├── 01_enable_apis.sh  # Enable GCP APIs
│   │   ├── 02_push_images.sh   # Build & push Docker images via Cloud Build
│   │   ├── 03_upload_artifact.sh  # Upload model artifact to Cloud Storage
│   │   ├── 04_setup_cloudsql.sh   # Create Postgres instance & apply schema
│   │   ├── 05_deploy_cloudrun.sh  # Deploy API to Cloud Run
│   │   └── 06_setup_worker_vm.sh  # Create Compute Engine VM & start worker
│   ├── docker-compose.yml         # Local dev environment
│   └── demo.sh                    # Live demo against deployed GCP API
├── requirements.txt
```

---

## Train the Model

Skip if `fraud_artifact.joblib` already exists.

1. Download IEEE-CIS dataset → `ieee-fraud-detection/`
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run notebooks `01` → `06`

Output: `model_output/fraud_artifact.joblib`

---
## Deploy to GCP

### Setup

- GCP project + billing
- `gcloud auth login`
- CloudAMQP instance

Edit:

```
platform/deploy/env.sh
```

### Deploy Steps

```bash
source platform/deploy/env.sh
```

1. Enable APIs
   ```bash
   bash platform/deploy/01_enable_apis.sh
   ```
2. Build + push images
   ```bash
   bash platform/deploy/02_push_images.sh
   ```
3. Upload model
   ```bash
   bash platform/deploy/03_upload_artifact.sh
   ```
4. Create database
   ```bash
   bash platform/deploy/04_setup_cloudsql.sh
   ```
5. Deploy API
   ```bash
   bash platform/deploy/05_deploy_cloudrun.sh
   ```
6. Start worker
   ```bash
   bash platform/deploy/06_setup_worker_vm.sh
   ```

### Test

```bash
curl -X POST https://<url>/score \
  -H 'Content-Type: application/json' \
  -d '{"TransactionID":1,"TransactionDT":86400,"TransactionAmt":68.5}'
```

```bash
curl https://<url>/results/1
```

---

## API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/score` | POST | Submit transaction |
| `/results/{id}` | GET | Get prediction |
| `/health` | GET | Health check |
| `/docs` | GET | Swagger UI |
