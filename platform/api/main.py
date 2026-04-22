"""FastAPI entry point.

Endpoints:
    GET  /health                 
    POST /score                   
    GET  /results/{transaction_id} 
"""

import os
from uuid import uuid4

from fastapi import FastAPI, HTTPException

from . import db, queue_client
from .schemas import (
    ResultResponse,
    ScoreResponse,
    SyncScoreResponse,
    TransactionIn,
)

app = FastAPI(
    title="Graph-Based Fraud Detection API",
    version="0.1.0",
    description="Accepts raw transactions, scores them via an XGBoost model "
                "enriched with graph-based features.",
)

# Lazy-loaded synchronous scorer
_sync_scorer = None


def _get_sync_scorer():
    global _sync_scorer
    if _sync_scorer is None:
        from worker.scorer import Scorer
        _sync_scorer = Scorer(os.environ["ARTIFACT_PATH"])
    return _sync_scorer


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/score", response_model=ScoreResponse, status_code=202)
def score_async(txn: TransactionIn):
    """Enqueue a transaction for scoring. Poll GET /results/{id} for the result."""
    job_id = str(uuid4())
    queue_client.publish({
        "job_id": job_id,
        "payload": txn.model_dump(exclude_none=False),
    })
    return ScoreResponse(job_id=job_id, transaction_id=txn.TransactionID)


@app.post("/score/sync", response_model=SyncScoreResponse)
def score_sync(txn: TransactionIn):
    """Score in-process and return immediately. Useful for demos / low-QPS clients."""
    scorer = _get_sync_scorer()
    result = scorer.score(txn.model_dump(exclude_none=False), db_conn=None)
    return SyncScoreResponse(
        transaction_id=txn.TransactionID,
        fraud_proba=result["fraud_proba"],
        top_signals=result["top_signals"],
    )


@app.get("/results/{transaction_id}", response_model=ResultResponse)
def results(transaction_id: int):
    row = db.query_result(transaction_id)
    if not row:
        raise HTTPException(404, "Not scored yet")
    return ResultResponse(**row)
