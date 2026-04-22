"""RabbitMQ consumer that scores transactions and persists results to Postgres.
Run locally:
    python -m worker.worker
"""

import json
import logging
import os
import signal
import sys
import traceback

import pika
import psycopg

from .scorer import Scorer

log = logging.getLogger("worker")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

RABBITMQ_URL = os.environ["RABBITMQ_URL"]
DATABASE_URL = os.environ["DATABASE_URL"]
ARTIFACT_PATH = os.environ["ARTIFACT_PATH"]
QUEUE_NAME = os.environ.get("QUEUE_NAME", "fraud_scoring")
PREFETCH = int(os.environ.get("WORKER_PREFETCH", "10"))


def write_prediction(conn, job_id: str, payload: dict, result: dict):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO predictions (job_id, transaction_id, fraud_proba, top_signals, raw_payload)
            VALUES (%s, %s, %s, %s::jsonb, %s::jsonb)
            ON CONFLICT (job_id) DO NOTHING
            """,
            (
                job_id,
                int(payload["TransactionID"]),
                result["fraud_proba"],
                json.dumps(result["top_signals"]),
                json.dumps(payload, default=str),
            ),
        )
    conn.commit()


def append_velocity_event(conn, payload: dict, uid: str):
    """Append one event per entity so future requests see this transaction."""
    with conn.cursor() as cur:
        for entity_type, entity_value in [("uid", uid), ("card1", payload.get("card1"))]:
            if entity_value is None:
                continue
            cur.execute(
                """
                INSERT INTO velocity_events (entity_type, entity_value, transaction_dt)
                VALUES (%s, %s, %s)
                ON CONFLICT DO NOTHING
                """,
                (entity_type, str(entity_value), int(payload["TransactionDT"])),
            )
    conn.commit()


def build_handler(scorer: Scorer, db_conn):
    def handle(ch, method, _props, body):
        try:
            msg = json.loads(body)
            payload = msg["payload"]
            job_id = msg["job_id"]
            result = scorer.score(payload, db_conn=db_conn)
            write_prediction(db_conn, job_id, payload, result)
            uid = scorer._build_uid(payload)
            append_velocity_event(db_conn, payload, uid)
            log.info(
                "scored job=%s txn=%s proba=%.4f",
                job_id, payload.get("TransactionID"), result["fraud_proba"],
            )
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception:
            log.error("scoring failed:\n%s", traceback.format_exc())
            # Reject without requeue → dead-letter (define DLQ in RabbitMQ for prod).
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    return handle


def main():
    log.info("loading model artifact from %s", ARTIFACT_PATH)
    scorer = Scorer(ARTIFACT_PATH)

    log.info("connecting to Postgres")
    db_conn = psycopg.connect(DATABASE_URL, autocommit=False)

    log.info("connecting to RabbitMQ")
    conn = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
    ch = conn.channel()
    ch.queue_declare(queue=QUEUE_NAME, durable=True)
    ch.basic_qos(prefetch_count=PREFETCH)
    ch.basic_consume(queue=QUEUE_NAME, on_message_callback=build_handler(scorer, db_conn))

    def shutdown(*_):
        log.info("shutting down")
        try: ch.stop_consuming()
        except Exception: pass
        try: conn.close()
        except Exception: pass
        try: db_conn.close()
        except Exception: pass
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    log.info("worker ready, consuming from %s", QUEUE_NAME)
    ch.start_consuming()


if __name__ == "__main__":
    main()
