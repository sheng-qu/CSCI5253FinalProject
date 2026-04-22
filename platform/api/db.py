"""Postgres access helpers for the API layer """

import os
import psycopg
from psycopg.rows import dict_row

_DATABASE_URL = os.environ["DATABASE_URL"]


def _conn():
    return psycopg.connect(_DATABASE_URL, row_factory=dict_row)


def query_result(transaction_id: int) -> dict | None:
    with _conn() as c, c.cursor() as cur:
        cur.execute(
            """
            SELECT job_id::text, transaction_id, created_at, fraud_proba, top_signals
            FROM predictions
            WHERE transaction_id = %s
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (transaction_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        row["created_at"] = row["created_at"].isoformat()
        return row
